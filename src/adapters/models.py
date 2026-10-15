from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional, Tuple


class AffiliateType(str, Enum):
    DEPENDIENTE = "DEPENDIENTE"
    INDEPENDIENTE = "INDEPENDIENTE"
    PENSIONADO = "PENSIONADO"


@dataclass(frozen=True)
class Membership:
    valid_from: date
    valid_to: Optional[date]
    affiliate_type: AffiliateType

    def is_active(self, as_of: date) -> bool:
        return self.valid_from <= as_of and (self.valid_to is None or self.valid_to >= as_of)


@dataclass(frozen=True)
class CajaLookup:
    """Resultado de preguntarle a una caja por un documento. Interno: nunca se
    serializa tal cual hacia la API (eso lo hace el orquestador, construyendo
    los modelos de schemas.py campo por campo)."""

    caja: str
    available: bool
    memberships: Tuple[Membership, ...] = field(default_factory=tuple)
    source: str = "ONLINE"  # "ONLINE" | "FILE"
    as_of: Optional[date] = None  # solo relevante cuando source == "FILE"
