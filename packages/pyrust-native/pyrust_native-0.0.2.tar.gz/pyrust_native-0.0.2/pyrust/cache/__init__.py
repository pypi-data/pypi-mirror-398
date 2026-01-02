"""
Cache y hashing de compilaciones (Fase 6).

Gestiona la relación entre hash de AST/función y binarios compilados.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional


logger = logging.getLogger(__name__)

# Formato de metadata v2: cada entrada incluye hash del payload, checksum del
# artefacto (SHA256) y marca temporal. Las entradas se almacenan en la clave
# "entries" de la metadata junto a la versión del formato.
CACHE_VERSION = 2


@dataclass(slots=True)
class CacheEntry:
    function: str
    hash: str
    artifact: Path
    checksum: str
    timestamp: float

    def to_dict(self) -> Dict[str, str | float]:
        return {
            "function": self.function,
            "hash": self.hash,
            "artifact": str(self.artifact),
            "checksum": self.checksum,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> Optional["CacheEntry"]:
        try:
            function = str(data["function"])
            digest = str(data["hash"])
            artifact = Path(str(data["artifact"]))
            checksum = str(data["checksum"])
            timestamp = float(data["timestamp"])
        except (KeyError, TypeError, ValueError):
            return None
        return cls(
            function=function,
            hash=digest,
            artifact=artifact,
            checksum=checksum,
            timestamp=timestamp,
        )


class CacheManager:
    """Cache binaria con soporte de persistencia e integridad."""

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        self._cache_dir = (cache_dir or Path.home() / ".cache" / "pyrust").resolve()
        self._metadata_file = self._cache_dir / "cache.json"
        self._entries: Dict[str, CacheEntry] = {}
        self._load_metadata()

    def hash_payload(self, payload: str | bytes) -> str:
        if isinstance(payload, str):
            payload_bytes = payload.encode("utf-8")
        else:
            payload_bytes = bytes(payload)

        return hashlib.sha256(payload_bytes).hexdigest()

    def store(
        self, function: str, payload: str | bytes, artifact: Path
    ) -> Optional[CacheEntry]:
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        resolved_artifact = self._ensure_artifact_in_cache(artifact, function)
        if resolved_artifact is None:
            return None

        digest = self.hash_payload(payload)
        try:
            checksum = self._artifact_checksum(resolved_artifact)
        except OSError:
            logger.warning(
                "No se pudo leer el artefacto de '%s' para calcular el checksum; descartando",
                function,
            )
            return None
        entry = CacheEntry(
            function=function,
            hash=digest,
            artifact=resolved_artifact,
            checksum=checksum,
            timestamp=time.time(),
        )
        self._entries[function] = entry
        self._persist()
        return entry

    def fetch(self, function: str, payload: str | bytes) -> Optional[CacheEntry]:
        entry = self._entries.get(function)
        if entry is None:
            return None

        resolved_entry = self.fetch_from_metadata(function)
        if resolved_entry is None:
            return None

        digest = self.hash_payload(payload)
        if digest != resolved_entry.hash:
            self._remove(function)
            return None

        return resolved_entry

    def fetch_from_metadata(self, function: str) -> Optional[CacheEntry]:
        entry = self._entries.get(function)
        if entry is None:
            return None

        resolved_artifact = self._ensure_artifact_in_cache(entry.artifact, function)
        if resolved_artifact is None:
            self._remove(function)
            return None
        entry.artifact = resolved_artifact

        if not entry.artifact.exists():
            logger.warning("Artefacto faltante para '%s'; limpiando entrada de caché", function)
            self._remove(function)
            return None

        try:
            checksum = self._artifact_checksum(entry.artifact)
        except OSError:
            logger.warning(
                "No se pudo leer el artefacto de '%s' para verificar el checksum; invalidando",
                function,
            )
            self._remove(function)
            return None

        if checksum != entry.checksum:
            logger.warning(
                "Checksum del artefacto de '%s' no coincide; invalidando caché", function
            )
            self._remove(function)
            return None

        return entry

    def _artifact_checksum(self, artifact: Path) -> str:
        return hashlib.sha256(artifact.read_bytes()).hexdigest()

    def _metadata_path_is_link(self, path: Path) -> bool:
        try:
            stats = path.lstat()
        except FileNotFoundError:
            return False
        except OSError:
            logger.warning(
                "No se pudo inspeccionar '%s' para validar enlaces de metadata", path
            )
            return True

        return path.is_symlink() or stats.st_nlink > 1

    def _persist(self) -> None:
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        tmp_file = self._metadata_file.with_suffix(".tmp")

        if self._metadata_path_is_link(self._metadata_file):
            logger.warning(
                "El archivo de metadata es un enlace simbólico o duro; evitando escritura"
            )
            return

        if self._metadata_path_is_link(tmp_file):
            logger.warning(
                "El archivo temporal de metadata es un enlace simbólico o duro; evitando escritura"
            )
            return

        data = {
            "version": CACHE_VERSION,
            "entries": [entry.to_dict() for entry in self._entries.values()],
        }
        payload = json.dumps(data, indent=2).encode("utf-8")
        with tmp_file.open("wb") as handler:
            handler.write(payload)
            handler.flush()
            os.fsync(handler.fileno())
        tmp_file.replace(self._metadata_file)

    def invalidate(self, function: str) -> None:
        """Elimina una entrada del cache y actualiza el índice en disco."""

        self._remove(function)

    def _load_metadata(self) -> None:
        if not self._metadata_file.exists():
            return

        try:
            resolved_metadata = self._metadata_file.resolve(strict=False)
        except OSError:
            logger.warning("No se pudo resolver la ruta de metadata; reiniciando índice")
            self._entries = {}
            return

        if self._metadata_file.is_symlink() and not resolved_metadata.is_relative_to(
            self._cache_dir
        ):
            logger.warning(
                "Metadata de caché apunta fuera del directorio de caché; ignorando contenido"
            )
            self._entries = {}
            return

        try:
            raw = json.loads(self._metadata_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.warning("Metadata de caché corrupta; reiniciando índice")
            self._entries = {}
            return

        if not isinstance(raw, dict):
            logger.warning("Estructura de metadata inválida; reiniciando índice")
            self._entries = {}
            return

        if raw.get("version") != CACHE_VERSION:
            logger.warning("Versión de cache.json no soportada; ignorando contenido")
            self._entries = {}
            return

        entries: Iterable[object] = raw.get("entries", [])
        if not isinstance(entries, list):
            logger.warning("La sección 'entries' de la metadata es inválida; reiniciando índice")
            self._entries = {}
            return

        cleaned = False
        for item in entries:
            if not isinstance(item, dict):
                logger.warning("Entrada de metadata con tipo inesperado; descartando")
                cleaned = True
                continue
            cache_entry = CacheEntry.from_dict(item)
            if cache_entry is None:
                logger.warning("Entrada de metadata mal formada; descartando")
                cleaned = True
                continue
            resolved_artifact = self._ensure_artifact_in_cache(
                cache_entry.artifact, cache_entry.function
            )
            if resolved_artifact is None:
                cleaned = True
                continue
            cache_entry.artifact = resolved_artifact
            if not cache_entry.artifact.exists():
                logger.warning(
                    "Artefacto faltante para '%s' encontrado durante la carga; descartando",
                    cache_entry.function,
                )
                cleaned = True
                continue

            try:
                checksum = self._artifact_checksum(cache_entry.artifact)
            except OSError:
                logger.warning(
                    "No se pudo leer el artefacto de '%s' al cargar la caché; descartando",
                    cache_entry.function,
                )
                cleaned = True
                continue

            if checksum != cache_entry.checksum:
                logger.warning(
                    "Checksum inconsistente para '%s' en metadata; descartando", cache_entry.function
                )
                cleaned = True
                continue
            self._entries[cache_entry.function] = cache_entry

        if cleaned and self._metadata_file.exists():
            self._persist()

    def _remove(self, function: str) -> None:
        self._entries.pop(function, None)
        self._persist()

    def _ensure_artifact_in_cache(self, artifact: Path, function: str) -> Optional[Path]:
        try:
            resolved = artifact.resolve()
        except OSError:
            logger.warning(
                "No se pudo resolver la ruta del artefacto para '%s'; descartando entrada",
                function,
            )
            return None

        if not resolved.is_relative_to(self._cache_dir):
            logger.warning(
                "Artefacto de '%s' fuera del directorio de caché; descartando entrada",
                function,
            )
            return None

        return resolved


__all__ = ["CacheEntry", "CacheManager"]
