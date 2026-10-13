import pytest

from src.audit import AuditLog
from src.schemas import ConsultaResultado


@pytest.mark.asyncio
async def test_registrar_masks_the_document_and_keeps_required_fields():
    log = AuditLog()
    await log.registrar("NORTE", "VALIDACION_AFILIACION", ConsultaResultado.NO_AFILIADO, "1098765432")

    entries = await log.recientes()
    assert len(entries) == 1
    entry = entries[0]
    assert entry.requestingCaja == "NORTE"
    assert entry.purpose == "VALIDACION_AFILIACION"
    assert entry.result == ConsultaResultado.NO_AFILIADO
    assert entry.documentMasked == "******5432"
    assert entry.timestamp


@pytest.mark.asyncio
async def test_recientes_respects_the_limit_and_keeps_the_most_recent():
    log = AuditLog()
    for document in ["1111111111", "2222222222", "3333333333"]:
        await log.registrar("NORTE", "VALIDACION_AFILIACION", ConsultaResultado.NO_AFILIADO, document)

    entries = await log.recientes(limit=2)
    assert len(entries) == 2
    assert entries[-1].documentMasked.endswith("3333")
