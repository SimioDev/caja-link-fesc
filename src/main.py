import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request

from .adapters.registry import build_adapters
from .audit import AuditLog
from .batch import BatchStore
from .config import Settings
from .documents import normalize
from .orchestrator import consultar_v1, consultar_v2
from .schemas import (
    AffiliationResponseV1,
    AffiliationResponseV2,
    AuditEntry,
    BatchJobAccepted,
    BatchJobStatus,
)
from .security import require_admin, requester_from_token, validar_purpose

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings.load()
    client = httpx.AsyncClient(limits=httpx.Limits(max_connections=300, max_keepalive_connections=50))
    app.state.settings = settings
    app.state.http_client = client
    app.state.adapters = build_adapters(settings, client)
    app.state.audit = AuditLog()
    app.state.batch_store = BatchStore(concurrency=50)
    try:
        yield
    finally:
        await client.aclose()


app = FastAPI(title="Caja Link", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"status": "UP"}


@app.get("/api/v1/affiliations/{document}", response_model=AffiliationResponseV1)
async def consulta_v1(
    document: str,
    request: Request,
    requester: str = Depends(requester_from_token),
    purpose: str = Depends(validar_purpose),
) -> AffiliationResponseV1:
    canonico = normalize(document)
    respuesta = await consultar_v1(canonico, requester, request.app.state.adapters)
    await request.app.state.audit.registrar(requester, purpose, respuesta.result, canonico)
    return respuesta


@app.get("/api/v2/affiliations/{document}", response_model=AffiliationResponseV2)
async def consulta_v2(
    document: str,
    request: Request,
    requester: str = Depends(requester_from_token),
    purpose: str = Depends(validar_purpose),
) -> AffiliationResponseV2:
    canonico = normalize(document)
    respuesta = await consultar_v2(canonico, requester, request.app.state.adapters)
    await request.app.state.audit.registrar(requester, purpose, respuesta.result, canonico)
    return respuesta


@app.get("/api/v1/audit", response_model=list[AuditEntry])
async def auditoria(request: Request, limit: int = 100, _: None = Depends(require_admin)) -> list[AuditEntry]:
    return await request.app.state.audit.recientes(limit)


@app.post("/api/v1/batch-checks", status_code=202, response_model=BatchJobAccepted)
async def crear_lote(
    request: Request,
    requester: str = Depends(requester_from_token),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
) -> BatchJobAccepted:
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        upload = form.get("file")
        if upload is None:
            raise HTTPException(status_code=400, detail="Falta el campo 'file'")
        csv_bytes = await upload.read()
    else:
        csv_bytes = await request.body()

    try:
        documentos = request.app.state.batch_store.parse_documents(csv_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    job_id = await request.app.state.batch_store.get_or_create(
        idempotency_key, documentos, requester, request.app.state.adapters
    )
    return BatchJobAccepted(jobId=job_id)


@app.get("/api/v1/batch-checks/{job_id}", response_model=BatchJobStatus)
async def estado_lote(
    job_id: str, request: Request, requester: str = Depends(requester_from_token)
) -> BatchJobStatus:
    job = request.app.state.batch_store.get_owned(job_id, requester)
    if job is None:
        raise HTTPException(status_code=404, detail="jobId desconocido")
    return BatchJobStatus(status=job.status, results=job.results)
