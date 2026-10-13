import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Optional, Tuple

from .base import CajaAdapter
from .models import AffiliateType, CajaLookup, Membership

logger = logging.getLogger(__name__)

_TIPO_MAP = {"DEP": AffiliateType.DEPENDIENTE, "IND": AffiliateType.INDEPENDIENTE, "PEN": AffiliateType.PENSIONADO}
_FILENAME = re.compile(r"^centro_afiliados_(\d{8})\.txt$")


def _parse_fecha_fila(value: str) -> date:
    """Fechas de cada registro: YYYYMMDD, sin separadores."""
    return date(int(value[0:4]), int(value[4:6]), int(value[6:8]))


def _parse_fecha_corte(value: str) -> date:
    """FECHA_CORTE del encabezado: ISO (YYYY-MM-DD)."""
    return date.fromisoformat(value)


@dataclass(frozen=True)
class _CentroSnapshot:
    """Archivo plano ya parseado. Solo guarda los campos del dato minimo: el
    nombre y el salario del archivo nunca se cargan en memoria."""

    file_key: Tuple[str, int, int]  # (ruta, mtime_ns, tamano)
    as_of: Optional[date]
    memberships: Dict[str, Tuple[Membership, ...]]


def _parse_file(path: Path, file_key: Tuple[str, int, int]) -> _CentroSnapshot:
    as_of: Optional[date] = None
    index: Dict[str, list] = {}
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("TIPO_DOC|"):
                continue
            if line.startswith("FECHA_CORTE|"):
                as_of = _parse_fecha_corte(line.split("|", 1)[1])
                continue
            fields = line.split("|")
            if len(fields) < 7:
                continue
            _, numero_documento, fecha_inicio, fecha_fin, tipo_afiliado = fields[:5]
            index.setdefault(numero_documento.lstrip("0"), []).append(
                Membership(
                    valid_from=_parse_fecha_fila(fecha_inicio),
                    valid_to=_parse_fecha_fila(fecha_fin) if fecha_fin else None,
                    affiliate_type=_TIPO_MAP[tipo_afiliado],
                )
            )
    return _CentroSnapshot(
        file_key=file_key, as_of=as_of, memberships={doc: tuple(rows) for doc, rows in index.items()}
    )


class CentroAdapter(CajaAdapter):
    """Caja Centro no tiene servicio en vivo: lee el archivo plano diario mas
    reciente del directorio publicado (nunca mocks/data).

    El archivo se parsea una sola vez y se cachea en memoria; solo se vuelve a
    leer cuando aparece un archivo mas reciente o cambia su mtime/tamano."""

    name = "CENTRO"

    def __init__(self, directory):
        self._directory = Path(directory)
        self._snapshot: Optional[_CentroSnapshot] = None
        self._lock = asyncio.Lock()

    def _latest_file(self) -> Optional[Path]:
        if not self._directory.is_dir():
            return None
        candidates = sorted(
            (p for p in self._directory.glob("centro_afiliados_*.txt") if _FILENAME.match(p.name)),
            key=lambda p: _FILENAME.match(p.name).group(1),
        )
        return candidates[-1] if candidates else None

    async def _current_snapshot(self, path: Path) -> _CentroSnapshot:
        stat = path.stat()
        file_key = (str(path), stat.st_mtime_ns, stat.st_size)
        snapshot = self._snapshot
        if snapshot is not None and snapshot.file_key == file_key:
            return snapshot
        async with self._lock:
            # Otra corrutina pudo recargarlo mientras esperabamos el lock.
            if self._snapshot is None or self._snapshot.file_key != file_key:
                logger.info("Caja Centro: cargando %s", path.name)
                self._snapshot = await asyncio.to_thread(_parse_file, path, file_key)
            return self._snapshot

    async def lookup(self, document: str) -> CajaLookup:
        path = self._latest_file()
        if path is None:
            logger.warning("Caja Centro: no hay archivo centro_afiliados_*.txt en %s", self._directory)
            return CajaLookup(caja=self.name, available=False)

        snapshot = await self._current_snapshot(path)
        return CajaLookup(
            caja=self.name,
            available=True,
            memberships=snapshot.memberships.get(document.lstrip("0"), ()),
            source="FILE",
            as_of=snapshot.as_of,
        )
