"""
Runtime Rust/Python (Fases 5–7).

Responsable de cargar extensiones compiladas y realizar el hot-swap de funciones.
"""

from __future__ import annotations

import _ctypes
import ctypes
import logging
import sys
import tempfile
import time
from dataclasses import dataclass
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Callable, Dict, Iterable, Optional

from pyrust.cache import CacheManager


@dataclass
class LoadedModule:
    name: str
    path: Path
    module: object


@dataclass
class ReloadMetrics:
    duration_s: float
    swap_count: int
    used_cache: bool
    forced_recompile: bool
    retry_count: int = 0
    failure_cause: Optional[str] = None


@dataclass
class ReloadResult:
    loaded: LoadedModule
    from_cache: bool
    metrics: ReloadMetrics
    runtime_manager: "RuntimeManager | None" = None


class RuntimeManager:
    """
    Gestiona módulos compilados y substitución en caliente.

    Implementación inicial: registro en memoria y carga explícita.
    """

    def __init__(
        self,
        *,
        cache_manager: Optional[CacheManager] = None,
        compiler: Optional[Callable[[str, object], Path]] = None,
        event_hooks: Optional[Dict[str, Iterable[Callable[..., None]]]] = None,
    ) -> None:
        self._modules: Dict[str, LoadedModule] = {}
        self._logger = logging.getLogger(__name__)
        self._cache = cache_manager or CacheManager()
        self._compiler = compiler or self._default_compiler
        self._event_hooks: Dict[str, list[Callable[..., None]]] = {
            key: list(value) for key, value in (event_hooks or {}).items()
        }
        self._swap_count = 0
        self._staging_dir = Path(tempfile.mkdtemp(prefix="pyrust_runtime_"))
        self._last_metrics: Optional[ReloadMetrics] = None

    @property
    def last_metrics(self) -> Optional[ReloadMetrics]:
        return self._last_metrics

    def add_event_hook(self, event: str, callback: Callable[..., None]) -> None:
        self._event_hooks.setdefault(event, []).append(callback)

    def load_extension(
        self,
        module_name: str,
        path: Optional[Path] = None,
        validate: Optional[Callable[[object], bool]] = None,
    ) -> LoadedModule:
        """Carga un módulo compilado con rollback seguro.

        Si la carga o la validación fallan, el gestor mantiene intacta la
        referencia previa y elimina cualquier rastro del intento fallido.
        """

        previous_loaded = self._modules.get(module_name)
        previous_sys_module = sys.modules.get(module_name)
        rollback_needed = True

        self._logger.info("Iniciando carga transaccional de %s", module_name)
        try:
            module = self._load_module(module_name, path)

            if validate and not validate(module):
                raise RuntimeError(f"Validación fallida para {module_name}")

            loaded = LoadedModule(name=module_name, path=path or Path("."), module=module)
            self._modules[module_name] = loaded
            sys.modules[module_name] = module

            self._logger.info("%s cargado correctamente; liberando versión previa", module_name)
            if previous_loaded:
                try:
                    self._cleanup_module(previous_loaded.module)
                except Exception:
                    self._logger.error(
                        "Fallo en cleanup de %s; revirtiendo al estado previo",
                        module_name,
                        exc_info=True,
                    )
                    raise

            rollback_needed = False

            return loaded
        except Exception as exc:  # pragma: no cover - re-raises
            self._logger.error(
                "Fallo al cargar %s: %s. Revirtiendo a la versión previa.",
                module_name,
                exc,
            )
            if rollback_needed:
                self._rollback(module_name, previous_loaded, previous_sys_module)
            raise

    def get(self, module_name: str) -> Optional[LoadedModule]:
        return self._modules.get(module_name)

    def replace_function(self, owner: object, attr: str, replacement: Callable) -> None:
        setattr(owner, attr, replacement)

    def reload(
        self,
        extension_name: str,
        source: object = None,
        *,
        validate: Optional[Callable[[object], bool]] = None,
        force_recompile: bool = False,
        invalidate_cache: bool = False,
        use_cache: bool = True,
        on_success: Optional[Callable[[str, LoadedModule, ReloadMetrics], None]] = None,
        on_failure: Optional[Callable[[str, Exception], None]] = None,
        on_rollback: Optional[Callable[[str, LoadedModule], None]] = None,
    ) -> ReloadResult:
        """Compila/obtiene una extensión y realiza hot-swap con rollback seguro."""

        previous_loaded = self._modules.get(extension_name)
        hooks = {
            "success": [on_success] if on_success else [],
            "failure": [on_failure] if on_failure else [],
            "rollback": [on_rollback] if on_rollback else [],
        }

        start = time.perf_counter()
        used_cache = False
        retry_count = 0
        forced_flag = force_recompile

        def _compile_and_load(force: bool, invalidate: bool) -> LoadedModule:
            nonlocal used_cache
            artifact, used_cache = self._resolve_artifact(
                extension_name,
                source,
                force_recompile=force,
                invalidate_cache=invalidate,
                use_cache=use_cache,
            )
            loaded_module = self.load_extension(extension_name, path=artifact, validate=validate)
            return loaded_module

        try:
            loaded = _compile_and_load(force_recompile, invalidate_cache)
        except Exception as exc:  # pragma: no cover - re-raises
            if used_cache and source is not None and not force_recompile:
                self._logger.warning(
                    "Carga desde caché de %s falló (%s); reintentando con recompilación",
                    extension_name,
                    exc,
                )
                retry_count = 1
                forced_flag = True
                try:
                    loaded = _compile_and_load(True, True)
                except Exception as retry_exc:  # pragma: no cover - re-raises
                    exc = retry_exc
                else:
                    self._swap_count += 1
                    metrics = ReloadMetrics(
                        duration_s=time.perf_counter() - start,
                        swap_count=self._swap_count,
                        used_cache=False,
                        forced_recompile=True,
                        retry_count=retry_count,
                    )
                    self._last_metrics = metrics
                    self._logger.info(
                        "Recarga de %s completada tras recompilar en %.3fs (swap #%d, reintentos=%d)",
                        extension_name,
                        metrics.duration_s,
                        metrics.swap_count,
                        metrics.retry_count,
                    )
                    self._run_hooks("success", extension_name, metrics, loaded, hooks)
                    return ReloadResult(
                        loaded=loaded,
                        from_cache=False,
                        metrics=metrics,
                        runtime_manager=self,
                    )

            metrics = ReloadMetrics(
                duration_s=time.perf_counter() - start,
                swap_count=self._swap_count,
                used_cache=used_cache,
                forced_recompile=forced_flag,
                retry_count=retry_count,
                failure_cause=str(exc),
            )
            self._last_metrics = metrics
            self._run_hooks("failure", extension_name, metrics, exc, hooks)
            if previous_loaded:
                self._run_hooks("rollback", extension_name, metrics, previous_loaded, hooks)
            self._logger.error(
                "Recarga de %s falló tras %.3fs (reintentos=%d): %s",
                extension_name,
                metrics.duration_s,
                metrics.retry_count,
                exc,
            )
            raise

        self._swap_count += 1
        metrics = ReloadMetrics(
            duration_s=time.perf_counter() - start,
            swap_count=self._swap_count,
            used_cache=used_cache,
            forced_recompile=forced_flag,
            retry_count=retry_count,
        )
        self._last_metrics = metrics
        self._logger.info(
            "Recarga de %s completada en %.3fs (swap #%d, cache=%s, reintentos=%d)",
            extension_name,
            metrics.duration_s,
            metrics.swap_count,
            metrics.used_cache,
            metrics.retry_count,
        )
        self._run_hooks("success", extension_name, metrics, loaded, hooks)
        return ReloadResult(
            loaded=loaded,
            from_cache=used_cache,
            metrics=metrics,
            runtime_manager=self,
        )

    def _load_module(self, module_name: str, path: Optional[Path]) -> object:
        previous_sys_module = sys.modules.get(module_name)
        if path is None:
            try:
                return import_module(module_name)
            except Exception:
                if previous_sys_module is None:
                    sys.modules.pop(module_name, None)
                else:
                    sys.modules[module_name] = previous_sys_module
                raise

        spec = spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"No se pudo crear un spec para {module_name} desde {path}")

        module = module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            if previous_sys_module is None:
                sys.modules.pop(module_name, None)
            else:
                sys.modules[module_name] = previous_sys_module
            raise
        return module

    def _cleanup_module(self, module: object) -> None:
        cleanup_hook = getattr(module, "__pyrust_cleanup__", None) or getattr(
            module, "__pyrust_release__", None
        )
        if callable(cleanup_hook):
            try:
                cleanup_hook()
            except Exception as exc:  # pragma: no cover - logging only
                self._logger.warning("Cleanup falló en %s: %s", module, exc)

        for name, value in vars(module).items():
            close_method = getattr(value, "close", None)
            if callable(close_method):
                try:
                    close_method()
                    continue
                except Exception as exc:  # pragma: no cover - logging only
                    self._logger.warning("No se pudo cerrar %s: %s", name, exc)

            if isinstance(value, ctypes.CDLL):
                try:
                    _ctypes.dlclose(value._handle)
                except Exception as exc:  # pragma: no cover - logging only
                    self._logger.warning("No se pudo liberar handle de %s: %s", name, exc)

    def _rollback(
        self,
        module_name: str,
        previous_loaded: Optional[LoadedModule],
        previous_sys_module: Optional[object],
    ) -> None:
        if previous_loaded:
            self._modules[module_name] = previous_loaded
        else:
            self._modules.pop(module_name, None)

        if previous_sys_module is not None:
            sys.modules[module_name] = previous_sys_module
        else:
            sys.modules.pop(module_name, None)

    def _default_compiler(self, extension_name: str, source: object) -> Path:
        if source is None:
            raise ValueError("Se requiere 'source' para compilar la extensión")

        if isinstance(source, Path):
            return source

        target = self._staging_dir / f"{extension_name}.py"
        target.write_text(str(source), encoding="utf-8")
        return target

    def _resolve_artifact(
        self,
        extension_name: str,
        source: object,
        *,
        force_recompile: bool,
        invalidate_cache: bool,
        use_cache: bool,
    ) -> tuple[Optional[Path], bool]:
        if invalidate_cache:
            self._cache.invalidate(extension_name)

        payload = self._extract_payload(source)
        if use_cache and not force_recompile and payload:
            cached = self._cache.fetch(extension_name, payload)
            if cached:
                return cached.artifact, True

        if source is None:
            return None, False

        artifact = self._compiler(extension_name, source)
        if use_cache and payload:
            self._cache.store(extension_name, payload, artifact)

        return artifact, False

    def _extract_payload(self, source: object) -> Optional[str]:
        if source is None:
            return None

        if isinstance(source, Path):
            return source.read_text(encoding="utf-8")

        return str(source)

    def _run_hooks(
        self,
        event: str,
        extension_name: str,
        metrics: ReloadMetrics,
        payload: object,
        local_hooks: Dict[str, Iterable[Callable[..., None]]],
    ) -> None:
        callbacks = [
            *(self._event_hooks.get(event, []) or []),
            *(local_hooks.get(event, []) or []),
        ]
        for callback in callbacks:
            try:
                callback(extension_name, payload if event != "success" else payload, metrics)
            except Exception as exc:  # pragma: no cover - logging only
                self._logger.warning("Hook '%s' falló para %s: %s", event, extension_name, exc)


def reload_extension(
    extension_name: str,
    source: object = None,
    *,
    cache_dir: str | Path | None = None,
    cache_manager: CacheManager | None = None,
    compiler: Optional[Callable[[str, object], Path]] = None,
    event_hooks: Optional[Dict[str, Iterable[Callable[..., None]]]] = None,
    runtime_manager: "RuntimeManager | None" = None,
    validate: Optional[Callable[[object], bool]] = None,
    force_recompile: bool = False,
    invalidate_cache: bool = False,
    use_cache: bool = True,
    on_success: Optional[Callable[[str, LoadedModule, ReloadMetrics], None]] = None,
    on_failure: Optional[Callable[[str, Exception, ReloadMetrics], None]] = None,
    on_rollback: Optional[Callable[[str, LoadedModule, ReloadMetrics], None]] = None,
) -> ReloadResult:
    """Fachada sencilla para recargar extensiones con hot-swap seguro.

    Si no se proporciona ``runtime_manager`` se crea una instancia temporal
    configurada con las opciones de caché y compilador suministradas. Devuelve
    el :class:`ReloadResult` producido por :meth:`RuntimeManager.reload`,
    incluyendo una referencia al gestor utilizado en ``runtime_manager``.
    """

    if runtime_manager is not None and any(
        option is not None for option in (cache_dir, cache_manager, compiler, event_hooks)
    ):
        raise ValueError(
            "No se pueden mezclar 'runtime_manager' existente con opciones de inicialización"
        )

    manager = runtime_manager
    if manager is None:
        resolved_cache = cache_manager
        if resolved_cache is None:
            resolved_cache = CacheManager(cache_dir=Path(cache_dir) if cache_dir else None)

        manager = RuntimeManager(
            cache_manager=resolved_cache, compiler=compiler, event_hooks=event_hooks
        )

    return manager.reload(
        extension_name,
        source=source,
        validate=validate,
        force_recompile=force_recompile,
        invalidate_cache=invalidate_cache,
        use_cache=use_cache,
        on_success=on_success,
        on_failure=on_failure,
        on_rollback=on_rollback,
    )


__all__ = [
    "LoadedModule",
    "ReloadMetrics",
    "ReloadResult",
    "RuntimeManager",
    "reload_extension",
]
