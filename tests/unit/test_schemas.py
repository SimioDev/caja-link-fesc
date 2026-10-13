from datetime import date

from src.schemas import (
    AffiliationMatchV1,
    AffiliationResponseV1,
    ConsultaResultado,
    FuenteMatch,
)


def test_affiliation_response_serializes_without_forbidden_fields():
    response = AffiliationResponseV1(
        requestId="01J-test",
        result=ConsultaResultado.AFILIADO_OTRA_CAJA,
        matches=[
            AffiliationMatchV1(
                caja="NORTE",
                validFrom=date(2019, 2, 1),
                validTo=None,
                source=FuenteMatch.ONLINE,
                asOf=date(2026, 10, 3),
            )
        ],
        unavailable=[],
    )
    dumped = response.model_dump(mode="json")
    forbidden = {"nombre", "direccion", "telefono", "correo", "salario", "beneficiarios", "titular"}
    assert forbidden.isdisjoint(dumped["matches"][0].keys())
    assert dumped["result"] == "AFILIADO_OTRA_CAJA"
    assert dumped["matches"][0]["caja"] == "NORTE"
