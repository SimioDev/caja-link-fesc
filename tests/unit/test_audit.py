import pytest

from src.audit import AUDIT_MAX_LIMIT, AuditLog
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


@pytest.mark.asyncio
async def test_recientes_clamps_negative_or_oversized_limit():
    log = AuditLog()
    for document in ["1111111111", "2222222222", "3333333333"]:
        await log.registrar("NORTE", "VALIDACION_AFILIACION", ConsultaResultado.NO_AFILIADO, document)

    assert await log.recientes(limit=-5) == []
    assert len(await log.recientes(limit=10_000)) == 3


@pytest.mark.asyncio
async def test_recientes_with_zero_or_negative_limit_never_dumps_the_whole_log():
    log = AuditLog()
    for i in range(10):
        await log.registrar("NORTE", "VALIDACION_AFILIACION", ConsultaResultado.NO_AFILIADO, f"10000000{i:02d}")

    assert await log.recientes(limit=0) == []
    assert await log.recientes(limit=-3) == []


@pytest.mark.asyncio
async def test_recientes_never_returns_more_than_the_max_limit():
    log = AuditLog()
    for i in range(AUDIT_MAX_LIMIT + 5):
        await log.registrar("NORTE", "VALIDACION_AFILIACION", ConsultaResultado.NO_AFILIADO, f"{i:010d}")

    assert len(await log.recientes(limit=AUDIT_MAX_LIMIT + 5)) == AUDIT_MAX_LIMIT
