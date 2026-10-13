import pytest
from fastapi import HTTPException

from src.config import CajaDeclaration, Settings
from src.security import require_admin, requester_from_token, validar_documento, validar_purpose


def _settings() -> Settings:
    return Settings(
        tokens={"NORTE": "token-norte", "ORIENTE": "token-oriente", "CENTRO": "", "SUR": "", "ADMIN": "token-admin"},
        norte_url="", norte_api_key="", oriente_url="", oriente_user="", oriente_password="",
        centro_dir="/data/caja-centro", sur_url="", sur_token="", sur_enabled=False,
        cajas_declaradas=(CajaDeclaration(nombre="norte", adaptador="rest_api_key"),),
    )


def test_requester_from_token_resolves_the_caja_that_owns_the_token():
    assert requester_from_token("Bearer token-norte", _settings()) == "NORTE"


def test_requester_from_token_rejects_missing_header():
    with pytest.raises(HTTPException) as excinfo:
        requester_from_token(None, _settings())
    assert excinfo.value.status_code == 401


def test_requester_from_token_rejects_the_admin_token_as_a_caja():
    with pytest.raises(HTTPException) as excinfo:
        requester_from_token("Bearer token-admin", _settings())
    assert excinfo.value.status_code == 401


def test_requester_from_token_rejects_non_ascii_token_with_401_not_500():
    with pytest.raises(HTTPException) as excinfo:
        requester_from_token("Bearer ét", _settings())
    assert excinfo.value.status_code == 401


def test_require_admin_accepts_only_the_admin_token():
    require_admin("Bearer token-admin", _settings())  # no lanza
    with pytest.raises(HTTPException) as excinfo:
        require_admin("Bearer token-norte", _settings())
    assert excinfo.value.status_code == 403


def test_validar_purpose_accepts_only_the_three_known_values():
    assert validar_purpose("VALIDACION_AFILIACION") == "VALIDACION_AFILIACION"
    with pytest.raises(HTTPException) as excinfo:
        validar_purpose(None)
    assert excinfo.value.status_code == 400
    with pytest.raises(HTTPException):
        validar_purpose("MERCADEO")


def test_validar_documento_returns_the_canonical_document():
    assert validar_documento("001.098.765.432") == "1098765432"


@pytest.mark.parametrize("raw", ["abc", "...", " ", "000"])
def test_validar_documento_rejects_documents_without_digits_with_400(raw):
    with pytest.raises(HTTPException) as excinfo:
        validar_documento(raw)
    assert excinfo.value.status_code == 400
