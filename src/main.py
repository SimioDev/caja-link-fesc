import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request

from .adapters.registry import build_adapters
from .audit import AuditLog
from .config import Settings
from .documents import normalize
from .orchestrator import consultar_v1, consultar_v2
from .schemas import AffiliationResponseV1, AffiliationResponseV2, AuditEntry
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
