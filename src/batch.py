import asyncio
import csv
import io
import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Sequence, Tuple

from .adapters.base import CajaAdapter
from .documents import normalize
from .orchestrator import consultar_v1
from .schemas import BatchResultItem


@dataclass
class BatchJob:
    job_id: str
    requester: str
    status: str = "PENDING"
    results: List[BatchResultItem] = field(default_factory=list)


class BatchStore:
    """Jobs de lote en memoria, con idempotencia por Idempotency-Key. Vive
    mientras vive el proceso: no se exige persistencia entre reinicios para
    este reto (ver docs/adr/ para la justificacion)."""

    def __init__(self, concurrency: int = 50) -> None:
        self._jobs: Dict[str, BatchJob] = {}
        self._idempotency: Dict[Tuple[str, str], str] = {}
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(concurrency)
        self._background_tasks: set = set()

    @staticmethod
    def parse_documents(csv_bytes: bytes) -> List[str]:
        text = csv_bytes.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None or "document" not in reader.fieldnames:
            raise ValueError("El CSV debe tener una columna 'document'")
        return [row["document"].strip() for row in reader if row.get("document", "").strip()]

    async def get_or_create(
        self, idempotency_key: str, documents: Sequence[str], requester: str, adapters: Sequence[CajaAdapter]
    ) -> str:
        scoped_key = (requester, idempotency_key)
        async with self._lock:
            existing = self._idempotency.get(scoped_key)
            if existing:
                return existing
            job_id = str(uuid.uuid4())
            self._idempotency[scoped_key] = job_id
            self._jobs[job_id] = BatchJob(job_id=job_id, requester=requester)

        task = asyncio.create_task(self._run(job_id, documents, requester, adapters))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return job_id

    async def _run(
        self, job_id: str, documents: Sequence[str], requester: str, adapters: Sequence[CajaAdapter]
    ) -> None:
        job = self._jobs[job_id]
        job.status = "RUNNING"
        today = date.today()

        async def procesar(document: str) -> BatchResultItem:
            async with self._semaphore:
                respuesta = await consultar_v1(normalize(document), requester, adapters, today)
            return BatchResultItem(
                document=document, result=respuesta.result, matches=respuesta.matches, unavailable=respuesta.unavailable
            )

        job.results = await asyncio.gather(*(procesar(d) for d in documents))
        job.status = "DONE"

    def get(self, job_id: str):
        return self._jobs.get(job_id)

    def get_owned(self, job_id: str, requester: str):
        """Como `get`, pero solo devuelve el job si pertenece a `requester`
        (evita que una caja lea el lote de otra)."""
        job = self._jobs.get(job_id)
        return job if job and job.requester == requester else None
