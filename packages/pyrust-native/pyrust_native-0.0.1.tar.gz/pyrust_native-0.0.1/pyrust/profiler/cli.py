from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Callable, Iterable, Optional

from . import Profiler


def _parse_command(command: str) -> Callable[[], object]:
    """
    Convierte una ruta con formato ``modulo:callable`` en un callable real.
    """

    if ":" not in command:
        raise ValueError("Usa el formato modulo:callable para --command")

    module_name, func_name = command.rsplit(":", 1)
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        raise ValueError(f"No se pudo importar el módulo {module_name}") from exc
    try:
        func = getattr(module, func_name)
    except AttributeError as exc:  # pragma: no cover - parse_args captura y reporta
        raise ValueError(f"No se encontró {func_name} en {module_name}") from exc

    if not callable(func):
        raise ValueError(f"{module_name}:{func_name} no es callable")
    return func


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Perfilador ligero de PyRust: identifica hotspots y muestra ranking."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Ruta a un archivo o directorio Python a perfilar.",
    )
    parser.add_argument(
        "--entrypoint",
        type=str,
        help="Ruta relativa o absoluta al script dentro del directorio objetivo.",
    )
    parser.add_argument(
        "--command",
        type=str,
        help="Callable alternativo en formato modulo:funcion. Se ignora entrypoint.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Número máximo de filas en la tabla de hotspots.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        help="Ruta opcional para guardar el JSON resultante del perfilado.",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--use-sys-profile",
        dest="use_sys_profile",
        action="store_true",
        default=True,
        help="Usa cProfile (por defecto).",
    )
    group.add_argument(
        "--no-use-sys-profile",
        dest="use_sys_profile",
        action="store_false",
        help="Desactiva cProfile y usa el hook ligero.",
    )

    parser.add_argument(
        "--include-stdlib",
        action="store_true",
        help="Incluye llamadas de la stdlib/builtins en el ranking.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="PyRust profiler CLI",
    )
    return parser


def _run(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    command_callable = None
    if args.command:
        try:
            command_callable = _parse_command(args.command)
        except ValueError as exc:
            parser.error(str(exc))

    profiler = Profiler()
    try:
        summary = profiler.profile_path(
            args.path,
            entrypoint=args.entrypoint,
            command=command_callable,
            limit=args.limit,
            use_sys_profile=args.use_sys_profile,
            include_stdlib=args.include_stdlib,
            output_path=args.output_path,
        )
    except FileNotFoundError as exc:
        parser.error(str(exc))
    except ValueError as exc:
        parser.error(str(exc))

    print(summary.to_table(limit=args.limit or 10))
    if args.output_path:
        print(f"\nPerfil JSON guardado en: {args.output_path.resolve()}")
    return 0


def main(argv: Optional[Iterable[str]] = None) -> None:
    sys.exit(_run(argv))


if __name__ == "__main__":  # pragma: no cover
    main()
