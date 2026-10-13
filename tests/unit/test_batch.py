import asyncio

import pytest

from src.adapters.base import CajaAdapter
from src.adapters.models import CajaLookup
from src.batch import BatchStore


class _StubAdapter(CajaAdapter):
    def __init__(self, name: str):
        self.name = name

    async def lookup(self, document: str) -> CajaLookup:
        return CajaLookup(caja=self.name, available=True, memberships=())


def test_parse_documents_reads_the_document_column():
    csv_bytes = b"document\n1098765432\n 882 463 32 \n"
    documents = BatchStore.parse_documents(csv_bytes)
    assert documents == ["1098765432", "882 463 32"]


def test_parse_documents_rejects_a_csv_without_the_required_column():
    with pytest.raises(ValueError):
        BatchStore.parse_documents(b"documento\n123\n")


@pytest.mark.asyncio
async def test_same_idempotency_key_returns_the_same_job_id():
    store = BatchStore(concurrency=5)
    adapters = [_StubAdapter("NORTE"), _StubAdapter("ORIENTE")]
    first = await store.get_or_create("clave-1", ["1098765432"], "CENTRO", adapters)
    second = await store.get_or_create("clave-1", ["1098765432"], "CENTRO", adapters)
    assert first == second

    for _ in range(50):
        if store.get(first).status == "DONE":
            break
        await asyncio.sleep(0.05)


@pytest.mark.asyncio
async def test_a_batch_job_eventually_reaches_done_with_one_result_per_document():
    store = BatchStore(concurrency=5)
    adapters = [_StubAdapter("NORTE"), _StubAdapter("ORIENTE")]
    job_id = await store.get_or_create("clave-2", ["1111111111", "2222222222"], "CENTRO", adapters)

    for _ in range(50):
        job = store.get(job_id)
        if job.status == "DONE":
            break
        await asyncio.sleep(0.05)

    job = store.get(job_id)
    assert job.status == "DONE"
    assert {r.document for r in job.results} == {"1111111111", "2222222222"}
