"""
API pública de PyRust.

Siguiendo la hoja de ruta, este módulo expone puntos de entrada mínimos y define
stubs que se ampliarán en fases posteriores. Incluye la API de análisis de
rustificabilidad y el perfilador inicial.
"""

from __future__ import annotations

import ast
import logging
import os
import sys
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

_FORCE_PYTHON_FALLBACK = os.environ.get("PYRUST_FORCE_PYTHON_FALLBACK", "").lower() in {
    "1",
    "true",
    "yes",
}

try:
    if _FORCE_PYTHON_FALLBACK:
        raise ImportError("PYRUST_FORCE_PYTHON_FALLBACK activo; se usará la ruta Python.")
    from . import _native  # type: ignore
except ImportError:  # pragma: no cover - entornos sin compilación de Rust o forzado
    _native = None

from .analyzer import AnalysisResult, Analyzer, Rustyfiability
from .cache import CacheManager
from .profiler import ProfileSummary, Profiler
from .runtime import (
    LoadedModule,
    ReloadMetrics,
    ReloadResult,
    RuntimeManager,
)
from .transpiler import IRFunction, IRValidationError, RustTemplateBackend, Transpiler, TranspilerBackend

_runtime_manager: RuntimeManager | None = None


@dataclass(slots=True)
class AnalysisSummary:
    """
    Resumen agregado del análisis de rustyficabilidad.

    Incluye los conteos por veredicto y listas separadas de objetivos
    parcialmente compatibles o bloqueantes.
    """

    results: List[AnalysisResult]
    counts: Dict[Rustyfiability, int]
    partial: List[AnalysisResult]
    blockers: List[AnalysisResult]

    @property
    def total_targets(self) -> int:
        return len(self.results)

    def to_dict(self) -> Dict[str, Any]:
        def _serialize(result: AnalysisResult) -> Dict[str, Any]:
            return {
                "target": result.target,
                "verdict": result.verdict.name,
                "reasons": list(result.reasons),
            }

        return {
            "total_targets": self.total_targets,
            "counts": {verdict.name: self.counts.get(verdict, 0) for verdict in Rustyfiability},
            "partial": [_serialize(result) for result in self.partial],
            "blockers": [_serialize(result) for result in self.blockers],
            "results": [_serialize(result) for result in self.results],
        }


def hello() -> str:
    """
    Devuelve un saludo básico.

    Si el módulo nativo está disponible se usa como verificación rápida de
    compilación Rust; en caso contrario se responde desde Python.
    """

    if _native:
        return _native.hello()
    return "hello from pyrust (python fallback)"


def add(a: int, b: int) -> int:
    """
    Ejemplo de función compartida (Python + Rust) para validar la integración.
    """

    if _native:
        return int(_native.add(int(a), int(b)))
    return int(a) + int(b)


def analyze_project(
    path: str | Path, *, excluded_dirs: list[str | Path] | None = None
) -> list[AnalysisResult]:
    """
    Fase 3: análisis de rustyficabilidad.

    Recorre un archivo o directorio Python y clasifica cada función en términos
    de compatibilidad con la conversión a Rust. ``excluded_dirs`` permite
    omitir rutas por nombre de segmento.
    """

    analyzer = Analyzer()
    exclusions = [str(item) for item in (excluded_dirs or [])]
    return analyzer.analyze_path(Path(path), excluded_dirs=exclusions)


def analyze_summary(
    path: str | Path, *, excluded_dirs: list[str | Path] | None = None
) -> AnalysisSummary:
    """
    Ejecuta :func:`analyze_project` y devuelve un resumen agregado.

    El resumen incluye conteos por :class:`Rustyfiability` y listas de
    objetivos parcialmente convertibles o bloqueantes (veredicto ``NO``).
    """

    results = analyze_project(path, excluded_dirs=excluded_dirs)
    counts: Counter[Rustyfiability] = Counter(result.verdict for result in results)
    for verdict in Rustyfiability:
        counts.setdefault(verdict, 0)

    partial = [result for result in results if result.verdict is Rustyfiability.PARTIAL]
    blockers = [result for result in results if result.verdict is Rustyfiability.NO]

    return AnalysisSummary(
        results=results,
        counts=dict(counts),
        partial=partial,
        blockers=blockers,
    )


def profile_project(
    path: str | Path,
    *,
    entrypoint: Optional[str | Path] = None,
    command: Optional[Callable[[], object]] = None,
    limit: int | None = None,
    use_sys_profile: bool = True,
    include_stdlib: bool = False,
    excluded_dirs: list[str | Path] | None = None,
    output_path: str | Path | None = None,
) -> ProfileSummary:
    """
    Fase 2: perfilado automático.

    Esta función delega en :class:`Profiler` y servirá como API pública para
    identificar hotspots. ``include_stdlib`` controla si se mantienen las
    funciones de la biblioteca estándar en el resumen: con ``cProfile`` también
    activa/desactiva builtins (p. ej., ``time.sleep``), mientras que el hook de
    ``sys.setprofile`` solo rastrea funciones Python (las builtins no emiten
    eventos aunque se habilite).

    La implementación inicial devuelve métricas mínimas y deja pasos claros para
    futuras iteraciones.
    """

    profiler = Profiler()
    return profiler.profile_path(
        Path(path),
        entrypoint=entrypoint,
        command=command,
        limit=limit,
        use_sys_profile=use_sys_profile,
        include_stdlib=include_stdlib,
        excluded_dirs=excluded_dirs,
        output_path=output_path,
    )


def get_runtime_manager(
    *,
    cache_dir: str | Path | None = None,
    cache_manager: CacheManager | None = None,
    compiler: Optional[Callable[[str, object], Path]] = None,
    event_hooks: Optional[Dict[str, Iterable[Callable[..., None]]]] = None,
) -> RuntimeManager:
    """Devuelve una instancia compartida de :class:`RuntimeManager`.

    Si el runtime aún no está inicializado, se configura con la caché y
    compilador suministrados. Los parámetros adicionales solo se aceptan en la
    primera llamada; posteriores invocaciones deben reutilizar la instancia
    existente o proporcionar un ``runtime_manager`` explícito a
    :func:`reload_extension`.
    """

    global _runtime_manager

    if _runtime_manager is not None and any(
        option is not None for option in (cache_dir, cache_manager, compiler, event_hooks)
    ):
        raise ValueError(
            "El runtime compartido ya está inicializado; no se pueden modificar sus parámetros"
        )

    if _runtime_manager is None:
        resolved_cache = cache_manager or CacheManager(cache_dir=Path(cache_dir) if cache_dir else None)
        _runtime_manager = RuntimeManager(
            cache_manager=resolved_cache, compiler=compiler, event_hooks=event_hooks
        )

    return _runtime_manager


def reload_extension(
    extension_name: str,
    *,
    source: object,
    cache_dir: str | Path | None = None,
    cache_manager: CacheManager | None = None,
    compiler: Optional[Callable[[str, object], Path]] = None,
    event_hooks: Optional[Dict[str, Iterable[Callable[..., None]]]] = None,
    runtime_manager: RuntimeManager | None = None,
    validate: Optional[Callable[[object], bool]] = None,
    force_recompile: bool = False,
    invalidate_cache: bool = False,
    use_cache: bool = True,
    on_success: Optional[Callable[[str, LoadedModule, ReloadMetrics], None]] = None,
    on_failure: Optional[Callable[[str, Exception, ReloadMetrics], None]] = None,
    on_rollback: Optional[Callable[[str, LoadedModule, ReloadMetrics], None]] = None,
) -> ReloadResult:
    """Recarga una extensión y realiza hot-swap usando un runtime persistente.

    Este envoltorio reutiliza un :class:`RuntimeManager` compartido para evitar
    reinicios, pero admite pasar una instancia dedicada mediante
    ``runtime_manager``. Si se proporciona un runtime explícito no se pueden
    mezclar opciones de inicialización como ``cache_dir`` o ``compiler``.
    """

    if runtime_manager is not None and any(
        option is not None for option in (cache_dir, cache_manager, compiler, event_hooks)
    ):
        raise ValueError(
            "No se pueden combinar 'runtime_manager' con parámetros de inicialización"
        )

    manager = runtime_manager or get_runtime_manager(
        cache_dir=cache_dir, cache_manager=cache_manager, compiler=compiler, event_hooks=event_hooks
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


@dataclass(slots=True)
class TranspilationResult:
    """
    Resultado de transpilar una función tras pasar por el analizador.

    Incluye el veredicto original, las razones del análisis, el IR generado y
    el código renderizado. Si la función fue marcada como ``NO`` o falló el
    renderizado, ``skipped`` será ``True`` y ``rendered`` permanecerá vacío.
    """

    target: str
    verdict: Rustyfiability
    reasons: List[str]
    skipped: bool
    ir: IRFunction | None = None
    rendered: str | None = None
    error: str | None = None


@dataclass(slots=True)
class AutoRustyficationConfig:
    """Parámetros de la fase de auto-rustyficación."""

    hotspot_limit: int = 5
    min_runtime_pct: float = 5.0
    profile_limit: int | None = 25
    use_sys_profile: bool = True
    include_stdlib: bool = False
    include_partial: bool = False
    excluded_dirs: list[str | Path] | None = None
    entrypoint: str | Path | None = None
    command: Callable[[], object] | None = None
    backend: TranspilerBackend | None = None
    compiler: Optional[Callable[[str, object], Path]] = None
    cache_dir: str | Path | None = None
    cache_manager: CacheManager | None = None
    event_hooks: Optional[Dict[str, Iterable[Callable[..., None]]]] = None
    module_builder: Optional[Callable[[TranspilationResult], object]] = None
    force_recompile: bool = False
    invalidate_cache: bool = False
    use_cache: bool = True
    log_level: int = logging.INFO


@dataclass(slots=True)
class AutoRustyficationReport:
    """Resultado completo del pipeline automático."""

    project_root: Path
    config: AutoRustyficationConfig
    profile: ProfileSummary
    analysis: AnalysisSummary
    transpilation: list[TranspilationResult]
    selected_targets: list[str] = field(default_factory=list)
    reloaded: list[ReloadResult] = field(default_factory=list)
    swapped_targets: list[str] = field(default_factory=list)


def transpile_with_analysis(
    path: str | Path,
    *,
    backend: TranspilerBackend | None = None,
    excluded_dirs: list[str | Path] | None = None,
) -> list[TranspilationResult]:
    """
    Ejecuta el analizador antes de transpilar y evita funciones bloqueadas.

    Pasos:

    1. Usa :class:`Analyzer` para obtener veredictos por función.
    2. Salta cualquier objetivo con veredicto ``NO`` (``skipped=True``).
    3. Para el resto, genera IR con :class:`Transpiler` incluyendo el veredicto
       y razones como metadatos en :class:`IRFunction`.
    4. Renderiza con el backend indicado (``RustTemplateBackend`` por defecto).

    Devuelve una lista ordenada acorde a los resultados del analizador para
    preservar la trazabilidad.
    """

    analyzer = Analyzer()
    results = analyzer.analyze_path(Path(path), excluded_dirs=[str(item) for item in (excluded_dirs or [])])

    backend = backend or RustTemplateBackend()
    transpiler = Transpiler()

    function_nodes = _collect_function_nodes(results)

    transpiled: list[TranspilationResult] = []
    for result in results:
        if result.verdict is Rustyfiability.NO:
            transpiled.append(
                TranspilationResult(
                    target=result.target,
                    verdict=result.verdict,
                    reasons=list(result.reasons),
                    skipped=True,
                )
            )
            continue

        node = function_nodes.get(result.target)
        if node is None:
            transpiled.append(
                TranspilationResult(
                    target=result.target,
                    verdict=result.verdict,
                    reasons=list(result.reasons),
                    skipped=True,
                    error="Nodo de función no encontrado para el objetivo analizado",
                )
            )
            continue

        try:
            ir = transpiler.function_to_ir(
                node,
                verdict=result.verdict,
                analysis_reasons=result.reasons,
            )
            rendered = transpiler.render(ir, backend)
            transpiled.append(
                TranspilationResult(
                    target=result.target,
                    verdict=result.verdict,
                    reasons=list(result.reasons),
                    skipped=False,
                    ir=ir,
                    rendered=rendered,
                )
            )
        except IRValidationError as exc:
            transpiled.append(
                TranspilationResult(
                    target=result.target,
                    verdict=result.verdict,
                    reasons=list(result.reasons),
                    skipped=True,
                    error=str(exc),
                )
            )

    return transpiled


def _collect_function_nodes(results: list[AnalysisResult]) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    """Construye un mapa ``target -> nodo AST`` alineado con el analizador."""

    paths = {Path(result.target.split(":", 1)[0]) for result in results}
    nodes: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}

    for file_path in paths:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        class _Visitor(ast.NodeVisitor):
            def __init__(self) -> None:
                self.context: list[str] = []

            def visit_ClassDef(self, node: ast.ClassDef) -> None:
                self.context.append(node.name)
                self.generic_visit(node)
                self.context.pop()

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                qualified = ".".join([*self.context, node.name])
                nodes[f"{file_path}:{qualified}"] = node
                self.context.append(node.name)
                self.generic_visit(node)
                self.context.pop()

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                qualified = ".".join([*self.context, node.name])
                nodes[f"{file_path}:{qualified}"] = node
                self.context.append(node.name)
                self.generic_visit(node)
                self.context.pop()

        _Visitor().visit(tree)

    return nodes


def enable_auto_rustyfication(
    project_root: Optional[str | Path] = None, *, config: AutoRustyficationConfig | None = None
) -> AutoRustyficationReport:
    """Ejecuta el pipeline completo de rustyficación automática (fase 7)."""

    cfg = config or AutoRustyficationConfig()
    root = Path(project_root) if project_root is not None else Path.cwd()
    logger = logging.getLogger(__name__)
    logger.setLevel(cfg.log_level)

    logger.info("Iniciando auto-rustyficación en %s", root)
    profile_summary = profile_project(
        root,
        entrypoint=cfg.entrypoint,
        command=cfg.command,
        limit=cfg.profile_limit,
        use_sys_profile=cfg.use_sys_profile,
        include_stdlib=cfg.include_stdlib,
        excluded_dirs=cfg.excluded_dirs,
    )
    analysis = analyze_summary(root, excluded_dirs=cfg.excluded_dirs)
    transpilation = transpile_with_analysis(root, backend=cfg.backend, excluded_dirs=cfg.excluded_dirs)

    selected, reloads, swapped = _auto_select_and_reload(
        root,
        cfg,
        profile_summary,
        transpilation,
        logger=logger,
    )

    return AutoRustyficationReport(
        project_root=root,
        config=cfg,
        profile=profile_summary,
        analysis=analysis,
        transpilation=transpilation,
        selected_targets=selected,
        reloaded=reloads,
        swapped_targets=swapped,
    )


def _auto_select_and_reload(
    project_root: Path,
    config: AutoRustyficationConfig,
    profile: ProfileSummary,
    transpilation: list[TranspilationResult],
    *,
    logger: logging.Logger,
) -> tuple[list[str], list[ReloadResult], list[str]]:
    total_runtime = profile.total_runtime
    selected: list[tuple[TranspilationResult, float]] = []
    for sample in profile.top_hotspots(config.hotspot_limit):
        runtime_pct = (sample.total_time / total_runtime * 100) if total_runtime else 0.0
        if runtime_pct < config.min_runtime_pct:
            logger.debug(
                "Saltando %s por debajo del umbral mínimo de runtime: %.2f%% < %.2f%%",
                sample.qualified_name,
                runtime_pct,
                config.min_runtime_pct,
            )
            continue

        match = _match_transpilation_to_sample(
            sample.qualified_name, transpilation, include_partial=config.include_partial
        )
        if match is None:
            logger.info("No se encontraron coincidencias para %s", sample.qualified_name)
            continue
        selected.append((match, runtime_pct))

    if not selected:
        logger.info("No hay hotspots seleccionados para rustyficación")
        return [], [], []

    manager = get_runtime_manager(
        cache_dir=config.cache_dir,
        cache_manager=config.cache_manager,
        compiler=config.compiler,
        event_hooks=config.event_hooks,
    )
    reloaded: list[ReloadResult] = []
    swapped: list[str] = []
    selected_targets: list[str] = []

    with _temporary_syspath(project_root):
        for result, runtime_pct in selected:
            payload = config.module_builder(result) if config.module_builder else result.rendered
            if payload is None:
                logger.warning("No hay payload para recargar %s", result.target)
                continue

            extension_name = _extension_name_from_target(result.target)
            logger.info(
                "Recargando %s (hotspot: %.2f%% del runtime)", result.target, runtime_pct
            )
            reload_result = reload_extension(
                extension_name,
                source=payload,
                runtime_manager=manager,
                force_recompile=config.force_recompile,
                invalidate_cache=config.invalidate_cache,
                use_cache=config.use_cache,
            )
            reloaded.append(reload_result)
            selected_targets.append(result.target)

            owner, attr = _resolve_owner_for_target(result.target, project_root)
            compiled_fn = getattr(reload_result.loaded.module, attr, None)
            if owner is None or compiled_fn is None:
                logger.info(
                    "No se pudo intercambiar la función %s: owner=%s, compiled=%s",
                    result.target,
                    owner,
                    compiled_fn,
                )
                continue

            manager.replace_function(owner, attr, compiled_fn)
            swapped.append(result.target)

    return selected_targets, reloaded, swapped


def _match_transpilation_to_sample(
    qualified_name: str, results: list[TranspilationResult], *, include_partial: bool
) -> TranspilationResult | None:
    filename, _, tail = qualified_name.partition(":")
    _, _, func_name = tail.partition(":")
    resolved = Path(filename).resolve()

    for result in results:
        if result.skipped or result.verdict is Rustyfiability.NO:
            continue
        if (not include_partial) and result.verdict is Rustyfiability.PARTIAL:
            continue

        target_file, _, target_qualname = result.target.partition(":")
        if Path(target_file).resolve() != resolved:
            continue
        target_func = target_qualname.split(".")[-1]
        if target_func == func_name:
            return result
    return None


def _extension_name_from_target(target: str) -> str:
    file_part, _, qualified = target.partition(":")
    stem = Path(file_part).stem or "module"
    func = qualified.split(".")[-1] if qualified else stem
    safe_func = func.replace("<", "_").replace(">", "_")
    return f"pyrust_auto_{stem}_{safe_func}"


def _resolve_owner_for_target(target: str, project_root: Path) -> tuple[object | None, str]:
    file_part, _, qualified = target.partition(":")
    if not qualified:
        return None, ""

    module_name = _module_name_from_path(Path(file_part), project_root)
    if module_name is None:
        return None, qualified.split(".")[-1]

    module = import_module(module_name)
    owner: object | None = module
    segments = qualified.split(".")
    for segment in segments[:-1]:
        owner = getattr(owner, segment, None)
        if owner is None:
            return None, segments[-1]

    return owner, segments[-1]


def _module_name_from_path(file_path: Path, project_root: Path) -> str | None:
    try:
        relative = file_path.resolve().relative_to(project_root.resolve())
    except ValueError:
        relative = file_path

    if relative.name == "__init__.py":
        relative = relative.parent
    else:
        relative = relative.with_suffix("")

    if not relative.parts:
        return None

    return ".".join(relative.parts)


@contextmanager
def _temporary_syspath(root: Path):
    root_str = str(root.resolve())
    already_present = root_str in sys.path
    if not already_present:
        sys.path.insert(0, root_str)
    try:
        yield
    finally:
        if not already_present:
            sys.path.remove(root_str)
