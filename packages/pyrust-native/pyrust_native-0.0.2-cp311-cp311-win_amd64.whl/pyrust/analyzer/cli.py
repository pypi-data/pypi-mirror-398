from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, Optional

from pyrust.api import analyze_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analiza la rustyficabilidad de archivos/directorios Python y resume hallazgos."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Ruta a un archivo o directorio Python a analizar.",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        action="append",
        dest="excluded_dirs",
        default=[],
        help="Nombres de directorios a omitir (se comparan por segmento de ruta).",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json", "markdown"],
        default="table",
        help="Formato de salida: tabla legible, JSON o Markdown.",
    )
    parser.add_argument(
        "--show-reasons",
        action="store_true",
        help="Muestra todas las razones encontradas por objetivo (tabla) o las expone en JSON.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Número máximo de elementos a mostrar en las listas parciales/bloqueantes (table).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Ruta opcional para escribir el informe generado (Markdown o JSON).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="PyRust analyzer CLI",
    )
    return parser

def _run(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        summary = analyze_summary(args.path, excluded_dirs=args.excluded_dirs or None)
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))

    if args.format == "json":
        payload = summary.to_dict()
        if args.show_reasons:
            payload["reasons_by_target"] = {
                result.target: list(result.reasons) for result in summary.results
            }
            payload["total_reasons"] = summary.total_reasons
        rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    elif args.format == "markdown":
        rendered = summary.to_markdown(limit=args.limit, show_reasons=args.show_reasons)
    else:
        rendered = summary.to_table(limit=args.limit, show_reasons=args.show_reasons)

    if args.output:
        try:
            args.output.write_text(rendered, encoding="utf-8")
        except OSError as exc:
            parser.error(f"No se pudo escribir el informe en {args.output}: {exc}")
    print(rendered)

    return 0


def main(argv: Optional[Iterable[str]] = None) -> None:
    sys.exit(_run(argv))


if __name__ == "__main__":  # pragma: no cover
    main()
