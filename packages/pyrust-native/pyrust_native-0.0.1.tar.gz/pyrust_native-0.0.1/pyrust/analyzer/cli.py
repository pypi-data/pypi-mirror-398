from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, Optional

from pyrust.api import AnalysisSummary, analyze_summary
from pyrust.analyzer import Rustyfiability


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
        choices=["table", "json"],
        default="table",
        help="Formato de salida: tabla legible o JSON estructurado.",
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
        "--version",
        action="version",
        version="PyRust analyzer CLI",
    )
    return parser


def _format_table(
    summary: AnalysisSummary, *, limit: Optional[int], show_reasons: bool
) -> str:
    lines = []
    lines.append("Resumen de rustyficabilidad")
    lines.append(f"Total de objetivos analizados: {summary.total_targets}")
    if show_reasons:
        total_reasons = sum(len(result.reasons) for result in summary.results)
        lines.append(f"Total de razones registradas: {total_reasons}")
    lines.append("")
    lines.append("Conteos por veredicto:")
    for verdict in Rustyfiability:
        lines.append(f"  - {verdict.name:<7}: {summary.counts.get(verdict, 0)}")

    def render_section(title: str, items: list) -> None:
        lines.append("")
        lines.append(title)
        if not items:
            lines.append("  (sin elementos)")
            return

        display = items if limit is None else items[:limit]
        for result in display:
            lines.append(f"  - {result.target} [{result.verdict.name}]")
            if result.reasons:
                if show_reasons:
                    for reason in result.reasons:
                        lines.append(f"      - {reason}")
                else:
                    lines.append(f"      > {result.reasons[0]}")

        if limit is not None and len(items) > limit:
            lines.append(f"  ... {len(items) - limit} más")

    render_section("Objetivos parcialmente convertibles", summary.partial)
    render_section("Bloqueantes (requieren refactor)", summary.blockers)

    return "\n".join(lines)


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
            payload["total_reasons"] = sum(
                len(result.reasons) for result in summary.results
            )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_format_table(summary, limit=args.limit, show_reasons=args.show_reasons))

    return 0


def main(argv: Optional[Iterable[str]] = None) -> None:
    sys.exit(_run(argv))


if __name__ == "__main__":  # pragma: no cover
    main()
