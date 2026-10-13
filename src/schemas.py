from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ConsultaResultado(str, Enum):
    AFILIADO_OTRA_CAJA = "AFILIADO_OTRA_CAJA"
    NO_AFILIADO = "NO_AFILIADO"
    INDETERMINADO = "INDETERMINADO"


class FuenteMatch(str, Enum):
    ONLINE = "ONLINE"
    FILE = "FILE"


class AffiliationMatchV1(BaseModel):
    caja: str
    validFrom: date
    validTo: Optional[date] = None
    source: FuenteMatch
    asOf: date


class AffiliationMatchV2(AffiliationMatchV1):
    affiliateType: str


class AffiliationResponseV1(BaseModel):
    requestId: str
    result: ConsultaResultado
    matches: List[AffiliationMatchV1] = Field(default_factory=list)
    unavailable: List[str] = Field(default_factory=list)


class AffiliationResponseV2(BaseModel):
    requestId: str
    result: ConsultaResultado
    matches: List[AffiliationMatchV2] = Field(default_factory=list)
    unavailable: List[str] = Field(default_factory=list)


class BatchJobAccepted(BaseModel):
    jobId: str


class BatchResultItem(BaseModel):
    document: str
    result: ConsultaResultado
    matches: List[AffiliationMatchV1] = Field(default_factory=list)
    unavailable: List[str] = Field(default_factory=list)


class BatchJobStatus(BaseModel):
    status: str  # "PENDING" | "RUNNING" | "DONE"
    results: List[BatchResultItem] = Field(default_factory=list)


class AuditEntry(BaseModel):
    timestamp: str
    requestingCaja: str
    purpose: str
    result: ConsultaResultado
    documentMasked: str
