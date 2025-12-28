"""
Profilador (Fase 2): identifica hotspots antes de rustyficar.

En modo predeterminado (`use_sys_profile=True`) las muestras provienen de
`cProfile`, mientras que `use_sys_profile=False` emplea un gancho ligero sobre
`sys.setprofile` (útil para excluir stdlib/venvs al medir). Si el `path` apunta
a un archivo se ejecuta directamente vía `runpy.run_path`; si es un directorio
se intenta `__main__.py` o se puede especificar un `entrypoint` o `command` para
evitar heurísticas frágiles.
"""

from __future__ import annotations

import json
import runpy
import sys
import sysconfig
import time
from cProfile import Profile
from dataclasses import dataclass, field
from pathlib import Path
from pstats import Stats
from types import FrameType
from typing import Callable, Dict, List, Optional


@dataclass(slots=True)
class ProfileSample:
    """Métrica agregada por función."""

    qualified_name: str
    total_time: float
    call_count: int
    primitive_call_count: int
    self_time: float

    @property
    def avg_time(self) -> float:
        return self.total_time / self.call_count if self.call_count else 0.0

    def to_dict(self) -> Dict[str, float | int | str]:
        return {
            "qualified_name": self.qualified_name,
            "total_time": self.total_time,
            "call_count": self.call_count,
            "primitive_call_count": self.primitive_call_count,
            "self_time": self.self_time,
            "avg_time": self.avg_time,
        }


@dataclass(slots=True)
class ProfileSummary:
    """Resultado del perfilado de un proyecto/paquete."""

    source: Path
    total_runtime: float
    samples: List[ProfileSample] = field(default_factory=list)

    def top_hotspots(self, limit: int = 10) -> List[ProfileSample]:
        return sorted(self.samples, key=lambda s: s.total_time, reverse=True)[:limit]

    def to_table(self, limit: int = 10) -> str:
        """
        Devuelve una tabla legible de hotspots.

        Incluye ranking (ordenado por ``total_time``), ``call_count`` y tiempo
        medio. ``limit`` recorta el número máximo de filas mostradas.
        """

        hotspots = self.top_hotspots(limit)
        if not hotspots:
            return "No se registraron muestras de profiling."

        header = "# | total_time (s) | runtime (%) | call_count | avg_time (s) | function"
        separator = "-" * len(header)
        rows = []
        for idx, sample in enumerate(hotspots, start=1):
            runtime_pct = (sample.total_time / self.total_runtime * 100) if self.total_runtime else 0.0
            rows.append(
                f"{idx:>2} | {sample.total_time:>14.6f} | {runtime_pct:>11.2f} | "
                f"{sample.call_count:>10} | {sample.avg_time:>12.6f} | {sample.qualified_name}"
            )
        return "\n".join([header, separator, *rows])

    def to_dict(self) -> Dict[str, object]:
        return {
            "source": str(self.source),
            "total_runtime": self.total_runtime,
            "samples": [sample.to_dict() for sample in self.samples],
        }

    def to_json(self, path: Optional[str | Path] = None, *, indent: int = 2) -> str:
        payload = json.dumps(self.to_dict(), indent=indent)
        if path is not None:
            output_path = Path(path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(payload, encoding="utf-8")
        return payload


class Profiler:
    """
    Orquestador de perfilado.

    Ejecuta un target Python bajo `cProfile`. El target puede ser:
    - Un archivo (se ejecuta con `runpy.run_path`).
    - Un directorio con `__main__.py`.
    - Un directorio con un `entrypoint` explícito.
    - Un `command` callable alternativo.

    Si no hay ninguna de las opciones anteriores se devuelve un error claro.
    """

    def profile_path(
        self,
        path: Path,
        *,
        entrypoint: Optional[str | Path] = None,
        command: Optional[Callable[[], object]] = None,
        limit: Optional[int] = None,
        use_sys_profile: bool = True,
        include_stdlib: bool = False,
        excluded_dirs: Optional[List[str | Path]] = None,
        output_path: Optional[str | Path] = None,
    ) -> ProfileSummary:
        """
        Ejecuta y perfila el objetivo especificado por ``path``.

        - Si ``path`` es un archivo, se ejecuta con ``runpy.run_path``.
        - Si es un directorio, se intenta ``__main__.py`` o el ``entrypoint`` proporcionado.
        - Si se pasa ``command``, debe ser un callable listo para ejecutar el target
          y se usará en lugar de las heurísticas de rutas.
        - ``use_sys_profile`` activa o desactiva el uso de ``cProfile``.
        - ``include_stdlib`` permite incluir o no llamadas provenientes de la stdlib en el
          resumen: en ``cProfile`` controla tanto módulos de stdlib como builtins, mientras
          que el hook solo rastrea funciones Python (las builtins no generan eventos incluso
          cuando se activa).
        - ``limit`` recorta el número de funciones que se devuelven en el resumen.
        - ``excluded_dirs`` permite excluir rutas concretas (útil para carpetas generadas o vendorizadas).

        El tiempo total de ejecución se mide con ``time.perf_counter`` alrededor del
        perfilado. Si no existe el path o no hay un objetivo ejecutable, se lanza
        ``FileNotFoundError``; si se combinan ``entrypoint`` y ``command`` se lanza
        ``ValueError``.
        """
        if not path.exists():
            raise FileNotFoundError(f"No se encontró el path a perfilar: {path}")

        runner = self._resolve_runner(path, entrypoint=entrypoint, command=command)
        profiler = Profile() if use_sys_profile else None
        source_root = path if path.is_dir() else path.parent
        hook_stats: Dict[str, _HookAggregate] = {}
        original_profile = sys.getprofile()
        should_trace = self._make_should_trace(
            source_root=source_root,
            include_stdlib=include_stdlib,
            excluded_dirs=excluded_dirs,
        )

        start = time.perf_counter()
        if profiler is not None:
            profiler.enable()

        if not use_sys_profile:
            sys.setprofile(self._tracefunc(accumulator=hook_stats, should_trace=should_trace))

        try:
            runner()
        finally:
            sys.setprofile(original_profile)
            if profiler is not None:
                profiler.disable()

        total_runtime = time.perf_counter() - start

        stats = Stats(profiler) if profiler is not None else None
        samples = self._build_samples(
            stats,
            hook_stats,
            should_trace=should_trace,
            use_sys_profile=use_sys_profile,
        )
        if limit is not None:
            samples = samples[:limit]
        summary = ProfileSummary(source=path, total_runtime=total_runtime, samples=samples)
        if output_path is not None:
            summary.to_json(output_path)
        return summary

    def _resolve_runner(
        self,
        path: Path,
        *,
        entrypoint: Optional[str | Path],
        command: Optional[Callable[[], object]],
    ) -> Callable[[], object]:
        if entrypoint and command:
            raise ValueError("No se puede usar entrypoint y command a la vez.")

        if command is not None:
            return command

        if path.is_file():
            script_path = path
        else:
            candidate = Path(entrypoint) if entrypoint else path / "__main__.py"
            if not candidate.is_absolute():
                candidate = path / candidate
            if not candidate.exists():
                raise FileNotFoundError(
                    f"No se encontró cómo ejecutar {path}. Añade __main__.py o un entrypoint."
                )
            script_path = candidate

        def _run_script() -> None:
            runpy.run_path(str(script_path), run_name="__main__")

        return _run_script

    def _tracefunc(
        self,
        *,
        accumulator: Dict[str, "_HookAggregate"],
        should_trace: Callable[[str], bool],
    ) -> Callable[[FrameType, str, object], None]:
        active_calls: Dict[int, "_ActiveCall"] = {}

        @dataclass(slots=True)
        class _ActiveCall:
            start: float
            qualified_name: str
            child_time: float = 0.0

        def _qualified_name(frame: FrameType) -> str:
            filename = Path(frame.f_code.co_filename).resolve()
            return f"{filename}:{frame.f_code.co_firstlineno}:{frame.f_code.co_name}"

        def _handler(frame: FrameType, event: str, arg: object) -> None:
            if event == "call":
                if should_trace(frame.f_code.co_filename):
                    active_calls[id(frame)] = _ActiveCall(time.perf_counter(), _qualified_name(frame))
                return

            if event == "return":
                active = active_calls.pop(id(frame), None)
                if active is None:
                    return
                elapsed = time.perf_counter() - active.start
                self_time = elapsed - active.child_time
                aggregate = accumulator.setdefault(active.qualified_name, _HookAggregate())
                aggregate.total_time += elapsed
                aggregate.call_count += 1
                aggregate.primitive_call_count += 1
                aggregate.self_time += self_time if self_time > 0 else 0.0

                parent_frame = frame.f_back
                if parent_frame is not None:
                    parent_active = active_calls.get(id(parent_frame))
                    if parent_active is not None:
                        parent_active.child_time += elapsed

        return _handler

    def _build_samples(
        self,
        stats: Optional[Stats],
        hook_stats: Dict[str, "_HookAggregate"],
        *,
        should_trace: Callable[[str], bool],
        use_sys_profile: bool,
    ) -> List[ProfileSample]:
        aggregates: Dict[str, _HookAggregate] = {}

        if stats is not None:
            for (file, line, func), raw_stats in stats.stats.items():
                if not should_trace(file):
                    continue
                ccalls, ncalls, tottime, cumtime, _ = raw_stats
                qualified_name = f"{file}:{line}:{func}"
                aggregates[qualified_name] = _HookAggregate(
                    total_time=cumtime,
                    call_count=ncalls,
                    primitive_call_count=ccalls,
                    self_time=tottime,
                )

        if not use_sys_profile:
            for qualified_name, aggregate in hook_stats.items():
                filename, _, _ = qualified_name.partition(":")
                if filename and not should_trace(filename):
                    continue
                target = aggregates.setdefault(qualified_name, _HookAggregate())
                target.total_time += aggregate.total_time
                target.call_count += aggregate.call_count
                target.primitive_call_count += aggregate.primitive_call_count
                target.self_time += aggregate.self_time

        samples: List[ProfileSample] = []
        for qualified_name, aggregate in aggregates.items():
            samples.append(
                ProfileSample(
                    qualified_name=qualified_name,
                    total_time=aggregate.total_time,
                    call_count=aggregate.call_count,
                    primitive_call_count=aggregate.primitive_call_count,
                    self_time=aggregate.self_time,
                )
            )

        return sorted(samples, key=lambda s: s.total_time, reverse=True)

    def _make_should_trace(
        self,
        *,
        source_root: Path,
        include_stdlib: bool,
        excluded_dirs: Optional[List[str | Path]] = None,
    ) -> Callable[[str], bool]:
        source_root = source_root.resolve()
        stdlib_paths = tuple(
            Path(sysconfig.get_path(name)).resolve()
            for name in ("stdlib", "platstdlib")
            if sysconfig.get_path(name)
        )
        excluded_paths = tuple(Path(excluded).resolve() for excluded in excluded_dirs) if excluded_dirs else ()
        venv_root = Path(sys.prefix).resolve()
        base_prefix = Path(getattr(sys, "base_prefix", sys.prefix)).resolve()
        builtin_markers = ("<built-in ", "{built-in ")
        vendor_markers = ("site-packages", "dist-packages")

        def _is_builtin(filename: str) -> bool:
            return filename == "~" or filename.startswith(builtin_markers)

        def _should_trace(filename: str) -> bool:
            if _is_builtin(filename):
                return include_stdlib
            path = Path(filename).resolve()
            if any(self._is_relative_to(path, excluded) for excluded in excluded_paths):
                return False
            if any(marker in path.parts for marker in vendor_markers):
                return False
            if venv_root != base_prefix and venv_root in path.parents and base_prefix not in path.parents:
                return False
            is_stdlib = any(self._is_relative_to(path, std) for std in stdlib_paths)
            if is_stdlib:
                return include_stdlib
            return self._is_relative_to(path, source_root)

        return _should_trace


    @staticmethod
    def _is_relative_to(path: Path, parent: Path) -> bool:
        try:
            path.relative_to(parent)
            return True
        except ValueError:
            return False


@dataclass(slots=True)
class _HookAggregate:
    total_time: float = 0.0
    call_count: int = 0
    primitive_call_count: int = 0
    self_time: float = 0.0


__all__ = ["Profiler", "ProfileSample", "ProfileSummary"]
