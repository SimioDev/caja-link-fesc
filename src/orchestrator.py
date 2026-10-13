import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Sequence, Tuple

from .adapters.base import CajaAdapter
from .adapters.models import CajaLookup, Membership
from .schemas import (
    AffiliationMatchV1,
    AffiliationMatchV2,
    AffiliationResponseV1,
    AffiliationResponseV2,
    ConsultaResultado,
    FuenteMatch,
)


async def _safe_lookup(adapter: CajaAdapter, document: str) -> CajaLookup:
    try:
        return await adapter.lookup(document)
    except Exception:  # un adaptador nunca debe tumbar la consulta agregada
        return CajaLookup(caja=adapter.name, available=False)


@dataclass
class _Agregado:
    result: ConsultaResultado
    unavailable: List[str]
    matched: List[Tuple[CajaLookup, Membership, date]] = field(default_factory=list)


async def _agregar(document: str, requester: str, adapters: Sequence[CajaAdapter], today: date) -> _Agregado:
    relevantes = [a for a in adapters if a.name != requester]
    lookups = await asyncio.gather(*(_safe_lookup(a, document) for a in relevantes))

    matched: List[Tuple[CajaLookup, Membership, date]] = []
    unavailable: List[str] = []
    for lookup in lookups:
        if not lookup.available:
            unavailable.append(lookup.caja)
            continue
        as_of = lookup.as_of if lookup.source == "FILE" and lookup.as_of else today
        for membership in lookup.memberships:
            if membership.is_active(as_of):
                matched.append((lookup, membership, as_of))

    if matched:
        result = ConsultaResultado.AFILIADO_OTRA_CAJA
    elif unavailable:
        result = ConsultaResultado.INDETERMINADO
    else:
        result = ConsultaResultado.NO_AFILIADO
    return _Agregado(result=result, unavailable=unavailable, matched=matched)


async def consultar_v1(
    document: str, requester: str, adapters: Sequence[CajaAdapter], today: Optional[date] = None
) -> AffiliationResponseV1:
    agregado = await _agregar(document, requester, adapters, today or date.today())
    matches = [
        AffiliationMatchV1(
            caja=lookup.caja,
            validFrom=membership.valid_from,
            validTo=membership.valid_to,
            source=FuenteMatch(lookup.source),
            asOf=as_of,
        )
        for lookup, membership, as_of in agregado.matched
    ]
    return AffiliationResponseV1(
        requestId=str(uuid.uuid4()), result=agregado.result, matches=matches, unavailable=agregado.unavailable
    )


async def consultar_v2(
    document: str, requester: str, adapters: Sequence[CajaAdapter], today: Optional[date] = None
) -> AffiliationResponseV2:
    agregado = await _agregar(document, requester, adapters, today or date.today())
    matches = [
        AffiliationMatchV2(
            caja=lookup.caja,
            validFrom=membership.valid_from,
            validTo=membership.valid_to,
            source=FuenteMatch(lookup.source),
            asOf=as_of,
            affiliateType=membership.affiliate_type.value,
        )
        for lookup, membership, as_of in agregado.matched
    ]
    return AffiliationResponseV2(
        requestId=str(uuid.uuid4()), result=agregado.result, matches=matches, unavailable=agregado.unavailable
    )
