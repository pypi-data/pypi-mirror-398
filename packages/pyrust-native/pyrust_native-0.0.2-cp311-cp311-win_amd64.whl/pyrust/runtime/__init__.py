"""
Runtime Rust/Python (Fases 5–7).

Responsable de cargar extensiones compiladas y realizar el hot-swap de funciones.
"""

from __future__ import annotations

import _ctypes
import atexit
import ctypes
import logging
import shutil
import sys
import tempfile
import time
import threading
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


def _close_shared_runtime_manager() -> None:
    """Cierra la instancia compartida inicializada vía ``get_runtime_manager``."""

    api_module = sys.modules.get("pyrust.api") or import_module("pyrust.api")
    shutdown_runtime = getattr(api_module, "shutdown_runtime", None)
    if shutdown_runtime is None:
        return

    shutdown_runtime()


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
        self._staging_dir: Path | None = Path(tempfile.mkdtemp(prefix="pyrust_runtime_"))
        self._last_metrics: Optional[ReloadMetrics] = None
        self._lock = threading.RLock()

    def __enter__(self) -> "RuntimeManager":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

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

        if path is None:
            raise ValueError(
                "No se resolvió un artefacto para la extensión; especifica 'path' explícito"
            )

        with self._lock:
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
        with self._lock:
            return self._modules.get(module_name)

    def replace_function(self, owner: object, attr: str, replacement: Callable) -> None:
        setattr(owner, attr, replacement)

    def close(self) -> None:
        """Libera el directorio temporal usado para artefactos en caliente."""
        with self._lock:
            staging_dir = self._staging_dir
            if staging_dir is None:
                return

            try:
                shutil.rmtree(staging_dir)
            except FileNotFoundError:
                pass
            except Exception as exc:  # pragma: no cover - logging only
                self._logger.error("No se pudo eliminar el staging dir %s: %s", staging_dir, exc)
            finally:
                self._staging_dir = None

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
        on_failure: Optional[Callable[[str, Exception, ReloadMetrics], None]] = None,
        on_rollback: Optional[Callable[[str, LoadedModule, ReloadMetrics], None]] = None,
    ) -> ReloadResult:
        """Compila/obtiene una extensión y realiza hot-swap con rollback seguro.

        Los callbacks ``on_success``, ``on_failure`` y ``on_rollback`` reciben
        siempre tres argumentos: ``extension_name``, el payload asociado al
        evento (``LoadedModule`` para éxito/rollback o la ``Exception`` para
        fallo) y ``ReloadMetrics`` con los detalles de la operación.
        """

        with self._lock:
            self._validate_extension_name(extension_name)

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
                if artifact is None:
                    raise ValueError(
                        "No se pudo resolver un artefacto para la extensión; proporciona 'source' o caché válida"
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
            raise ValueError(
                "No se resolvió un artefacto para la extensión; especifica 'path' explícito"
            )

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

        self._validate_extension_name(extension_name)

        if isinstance(source, Path):
            return source

        target = self._ensure_staging_dir() / f"{extension_name}.py"
        target.write_text(str(source), encoding="utf-8")
        return target

    def _validate_extension_name(self, extension_name: str) -> None:
        name_path = Path(extension_name)

        has_separator = any(sep in extension_name for sep in ("/", "\\"))
        has_backtrack = any(part in {"..", "."} for part in name_path.parts)

        if name_path.is_absolute() or has_separator or has_backtrack or len(name_path.parts) > 1:
            raise ValueError(
                "Nombre de extensión inválido: no puede contener separadores, rutas absolutas"
                " ni componentes de retroceso"
            )

    def _resolve_artifact(
        self,
        extension_name: str,
        source: object,
        *,
        force_recompile: bool,
        invalidate_cache: bool,
        use_cache: bool,
    ) -> tuple[Optional[Path], bool]:
        with self._lock:
            self._validate_extension_name(extension_name)

            safe_extension_name = extension_name

            if invalidate_cache:
                self._cache.invalidate(safe_extension_name)

            cached_entry = None
            if use_cache and not force_recompile:
                cached_entry = self._cache.fetch_from_metadata(safe_extension_name)

            try:
                payload = self._extract_payload(source)
            except OSError as exc:
                if cached_entry:
                    self._logger.warning(
                        "No se pudo leer el source de %s; reutilizando artefacto cacheado: %s",
                        extension_name,
                        exc,
                    )
                    return cached_entry.artifact, True
                raise RuntimeError(
                    "No se pudo leer el source y no hay caché válido disponible para "
                    f"'{extension_name}'"
                ) from exc

            if use_cache and not force_recompile and payload:
                cached = self._cache.fetch(safe_extension_name, payload)
                if cached:
                    return cached.artifact, True

            if cached_entry and source is None and use_cache and not force_recompile:
                return cached_entry.artifact, True

            if source is None:
                return None, False

            artifact = self._compiler(safe_extension_name, source)
            if use_cache and payload:
                cached_artifact = artifact
                try:
                    resolved_artifact = artifact.resolve()
                except OSError:
                    resolved_artifact = artifact

                if not resolved_artifact.is_relative_to(self._cache._cache_dir):
                    digest = self._cache.hash_payload(payload)
                    cached_artifact = (
                        self._cache._cache_dir
                        / f"{safe_extension_name}_{digest}{resolved_artifact.suffix or '.py'}"
                    )
                    cached_artifact.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.copy2(artifact, cached_artifact)
                    except OSError as exc:  # pragma: no cover - exercised via tests
                        self._logger.warning(
                            "No se pudo copiar el artefacto de %s a la caché: %s",
                            extension_name,
                            exc,
                        )
                        cached_artifact = artifact
                    else:
                        stored = self._cache.store(
                            safe_extension_name, payload, cached_artifact
                        )
                        if stored:
                            artifact = stored.artifact
                else:
                    stored = self._cache.store(safe_extension_name, payload, cached_artifact)
                    if stored:
                        artifact = stored.artifact

            return artifact, False

    def _extract_payload(self, source: object) -> Optional[bytes | str]:
        if source is None:
            return None

        if isinstance(source, Path):
            return source.read_bytes()

        if isinstance(source, (bytes, bytearray)):
            return bytes(source)

        return str(source)

    def _ensure_staging_dir(self) -> Path:
        with self._lock:
            if self._staging_dir is None:
                self._staging_dir = Path(tempfile.mkdtemp(prefix="pyrust_runtime_"))
            return self._staging_dir

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
                callback(extension_name, payload, metrics)
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

    Los callbacks opcionales ``on_success``, ``on_failure`` y ``on_rollback``
    reciben siempre ``extension_name``, el payload del evento (``LoadedModule``
    o la ``Exception``) y los ``ReloadMetrics`` correspondientes.
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

    manager._validate_extension_name(extension_name)

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


atexit.register(_close_shared_runtime_manager)


__all__ = [
    "LoadedModule",
    "ReloadMetrics",
    "ReloadResult",
    "RuntimeManager",
    "reload_extension",
]
