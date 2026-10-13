import logging
import re
from datetime import date
from pathlib import Path
from typing import Optional

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


class CentroAdapter(CajaAdapter):
    """Caja Centro no tiene servicio en vivo: lee el archivo plano diario mas
    reciente del directorio publicado (nunca mocks/data)."""

    name = "CENTRO"

    def __init__(self, directory):
        self._directory = Path(directory)

    def _latest_file(self) -> Optional[Path]:
        if not self._directory.is_dir():
            return None
        candidates = sorted(
            (p for p in self._directory.glob("centro_afiliados_*.txt") if _FILENAME.match(p.name)),
            key=lambda p: _FILENAME.match(p.name).group(1),
        )
        return candidates[-1] if candidates else None

    async def lookup(self, document: str) -> CajaLookup:
        path = self._latest_file()
        if path is None:
            logger.warning("Caja Centro: no hay archivo centro_afiliados_*.txt en %s", self._directory)
            return CajaLookup(caja=self.name, available=False)

        as_of: Optional[date] = None
        found: Optional[Membership] = None
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
                if numero_documento.lstrip("0") != document.lstrip("0"):
                    continue
                found = Membership(
                    valid_from=_parse_fecha_fila(fecha_inicio),
                    valid_to=_parse_fecha_fila(fecha_fin) if fecha_fin else None,
                    affiliate_type=_TIPO_MAP[tipo_afiliado],
                )

        return CajaLookup(
            caja=self.name,
            available=True,
            memberships=(found,) if found else (),
            source="FILE",
            as_of=as_of,
        )
