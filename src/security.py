import hmac
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request

from .config import Settings

VALID_PURPOSES = {"TARIFA_SUBSIDIADA", "SUBSIDIO_MONETARIO", "VALIDACION_AFILIACION"}


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def requester_from_token(
    authorization: Optional[str] = Header(default=None), settings: Settings = Depends(get_settings)
) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Falta token Bearer")
    token = authorization.removeprefix("Bearer ").strip()
    for caja, expected in settings.tokens.items():
        if caja != "ADMIN" and expected and hmac.compare_digest(token, expected):
            return caja
    raise HTTPException(status_code=401, detail="Token invalido")


def require_admin(
    authorization: Optional[str] = Header(default=None), settings: Settings = Depends(get_settings)
) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Falta token Bearer")
    token = authorization.removeprefix("Bearer ").strip()
    expected = settings.tokens.get("ADMIN")
    if not expected or not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=403, detail="Requiere ADMIN_TOKEN")


def validar_purpose(purpose: Optional[str] = None) -> str:
    if not purpose or purpose not in VALID_PURPOSES:
        raise HTTPException(status_code=400, detail="purpose ausente o invalido")
    return purpose
