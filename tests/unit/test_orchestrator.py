from dataclasses import dataclass
from datetime import date

import pytest

from src.adapters.base import CajaAdapter
from src.adapters.models import AffiliateType, CajaLookup, Membership
from src.orchestrator import consultar_v1, consultar_v2
from src.schemas import ConsultaResultado


@dataclass
class FakeAdapter(CajaAdapter):
    name: str
    result: CajaLookup

    async def lookup(self, document: str) -> CajaLookup:
        return self.result


def _activo(caja: str) -> FakeAdapter:
    return FakeAdapter(
        name=caja,
        result=CajaLookup(
            caja=caja,
            available=True,
            memberships=(Membership(date(2019, 2, 1), None, AffiliateType.DEPENDIENTE),),
        ),
    )


def _sin_afiliacion(caja: str) -> FakeAdapter:
    return FakeAdapter(name=caja, result=CajaLookup(caja=caja, available=True, memberships=()))


def _caida(caja: str) -> FakeAdapter:
    return FakeAdapter(name=caja, result=CajaLookup(caja=caja, available=False))


@pytest.mark.asyncio
async def test_afiliado_otra_caja_when_one_adapter_has_an_active_membership():
    adapters = [_activo("NORTE"), _sin_afiliacion("ORIENTE")]
    response = await consultar_v1("1098765432", requester="CENTRO", adapters=adapters)
    assert response.result == ConsultaResultado.AFILIADO_OTRA_CAJA
    assert [m.caja for m in response.matches] == ["NORTE"]
    assert response.unavailable == []


@pytest.mark.asyncio
async def test_no_afiliado_when_every_adapter_responds_without_a_match():
    adapters = [_sin_afiliacion("NORTE"), _sin_afiliacion("ORIENTE")]
    response = await consultar_v1("1098765432", requester="CENTRO", adapters=adapters)
    assert response.result == ConsultaResultado.NO_AFILIADO


@pytest.mark.asyncio
async def test_indeterminado_when_a_caja_is_down_and_nothing_else_matches():
    adapters = [_caida("NORTE"), _sin_afiliacion("ORIENTE")]
    response = await consultar_v1("1098765432", requester="CENTRO", adapters=adapters)
    assert response.result == ConsultaResultado.INDETERMINADO
    assert response.unavailable == ["NORTE"]


@pytest.mark.asyncio
async def test_never_reports_no_afiliado_when_a_caja_is_down_even_if_others_match():
    adapters = [_caida("NORTE"), _activo("ORIENTE")]
    response = await consultar_v1("1098765432", requester="CENTRO", adapters=adapters)
    assert response.result == ConsultaResultado.AFILIADO_OTRA_CAJA
    assert "NORTE" in response.unavailable


@pytest.mark.asyncio
async def test_requesting_caja_is_excluded_even_if_it_would_have_matched():
    adapters = [_activo("NORTE"), _activo("ORIENTE")]
    response = await consultar_v1("1098765432", requester="NORTE", adapters=adapters)
    assert "NORTE" not in [m.caja for m in response.matches]
    assert "NORTE" not in response.unavailable


@pytest.mark.asyncio
async def test_v2_includes_affiliate_type_and_v1_never_does():
    adapters = [_activo("NORTE")]
    v1 = await consultar_v1("1098765432", requester="CENTRO", adapters=adapters)
    v2 = await consultar_v2("1098765432", requester="CENTRO", adapters=adapters)
    assert "affiliateType" not in v1.model_dump(mode="json")["matches"][0]
    assert v2.matches[0].affiliateType == "DEPENDIENTE"


@pytest.mark.asyncio
async def test_an_adapter_that_raises_counts_as_unavailable_not_as_a_crash():
    class BoomAdapter(CajaAdapter):
        name = "ORIENTE"

        async def lookup(self, document: str) -> CajaLookup:
            raise RuntimeError("fallo inesperado del adaptador")

    adapters = [_sin_afiliacion("NORTE"), BoomAdapter()]
    response = await consultar_v1("1098765432", requester="CENTRO", adapters=adapters)
    assert response.result == ConsultaResultado.INDETERMINADO
    assert "ORIENTE" in response.unavailable
