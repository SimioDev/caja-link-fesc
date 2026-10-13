import hmac
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request

from .config import Settings
from .documents import is_valid, normalize

VALID_PURPOSES = {"TARIFA_SUBSIDIADA", "SUBSIDIO_MONETARIO", "VALIDACION_AFILIACION"}


def _tokens_match(a: str, b: str) -> bool:
    """Comparacion en tiempo constante que tolera tokens no-ASCII (hmac.compare_digest
    con str exige ASCII puro; comparamos en bytes para evitar un 500 con input raro)."""
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def requester_from_token(
    authorization: Optional[str] = Header(default=None), settings: Settings = Depends(get_settings)
) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Falta token Bearer")
    token = authorization.removeprefix("Bearer ").strip()
    for caja, expected in settings.tokens.items():
        if caja != "ADMIN" and expected and _tokens_match(token, expected):
            return caja
    raise HTTPException(status_code=401, detail="Token invalido")


def require_admin(
    authorization: Optional[str] = Header(default=None), settings: Settings = Depends(get_settings)
) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Falta token Bearer")
    token = authorization.removeprefix("Bearer ").strip()
    expected = settings.tokens.get("ADMIN")
    if not expected or not _tokens_match(token, expected):
        raise HTTPException(status_code=403, detail="Requiere ADMIN_TOKEN")


def validar_purpose(purpose: Optional[str] = None) -> str:
    if not purpose or purpose not in VALID_PURPOSES:
        raise HTTPException(status_code=400, detail="purpose ausente o invalido")
    return purpose


def validar_documento(document: str) -> str:
    """Devuelve el documento normalizado o 400 si no contiene digitos utiles, para
    no responder NO_AFILIADO sobre algo que no es un documento."""
    canonico = normalize(document)
    if not is_valid(canonico):
        raise HTTPException(status_code=400, detail="document invalido: debe contener digitos")
    return canonico
