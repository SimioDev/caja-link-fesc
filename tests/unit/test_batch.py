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


class _RecordingAdapter(CajaAdapter):
    def __init__(self, name: str):
        self.name = name
        self.seen: list[str] = []

    async def lookup(self, document: str) -> CajaLookup:
        self.seen.append(document)
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
async def test_same_idempotency_key_from_a_different_caja_creates_a_different_job():
    store = BatchStore(concurrency=5)
    adapters = [_StubAdapter("NORTE"), _StubAdapter("ORIENTE")]
    de_norte = await store.get_or_create("misma-clave", ["1098765432"], "NORTE", adapters)
    de_oriente = await store.get_or_create("misma-clave", ["1098765432"], "ORIENTE", adapters)
    assert de_norte != de_oriente
    assert store.get(de_norte).requester == "NORTE"
    assert store.get(de_oriente).requester == "ORIENTE"

    for job_id in (de_norte, de_oriente):
        for _ in range(50):
            if store.get(job_id).status == "DONE":
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


@pytest.mark.asyncio
async def test_batch_normalizes_documents_before_querying_adapters():
    store = BatchStore(concurrency=5)
    recorder = _RecordingAdapter("NORTE")
    adapters = [recorder, _StubAdapter("ORIENTE")]
    job_id = await store.get_or_create("clave-3", ["1.098.765.432", "002222222222"], "CENTRO", adapters)

    for _ in range(50):
        job = store.get(job_id)
        if job.status == "DONE":
            break
        await asyncio.sleep(0.05)

    assert sorted(recorder.seen) == ["1098765432", "2222222222"]
    # el documento original (con formato) se conserva en el resultado para que el cliente lo reconozca
    assert {r.document for r in job.results} == {"1.098.765.432", "002222222222"}
