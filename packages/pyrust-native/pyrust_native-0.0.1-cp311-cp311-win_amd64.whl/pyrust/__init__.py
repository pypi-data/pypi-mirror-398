"""
PyRust: librería orientada a rustyficar hotspots de Python de forma automática.

Este paquete expone una API pública mínima y módulos internos separados por capas
según la hoja de ruta: profiler, analyzer, transpiler, runtime y cache.
"""

from importlib import metadata

from .api import (
    AutoRustyficationConfig,
    AutoRustyficationReport,
    add,
    analyze_project,
    enable_auto_rustyfication,
    get_runtime_manager,
    hello,
    profile_project,
    reload_extension,
    transpile_with_analysis,
)

try:
    __version__ = metadata.version("pyrust")
except metadata.PackageNotFoundError:  # pragma: no cover - editable installs sin metadata
    __version__ = "0.0.0"

__all__ = [
    "AutoRustyficationConfig",
    "AutoRustyficationReport",
    "add",
    "analyze_project",
    "enable_auto_rustyfication",
    "get_runtime_manager",
    "hello",
    "profile_project",
    "reload_extension",
    "transpile_with_analysis",
]
