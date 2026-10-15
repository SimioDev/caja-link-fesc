import os

import pytest

NORTE_URL = os.environ.get("CAJA_NORTE_URL", "http://caja-norte:9001")
NORTE_API_KEY = os.environ["CAJA_NORTE_API_KEY"]
ORIENTE_URL = os.environ.get("CAJA_ORIENTE_URL", "http://caja-oriente:9002/ws/AfiliacionService")
ORIENTE_USER = os.environ["CAJA_ORIENTE_USER"]
ORIENTE_PASSWORD = os.environ["CAJA_ORIENTE_PASSWORD"]
CENTRO_DIR = os.environ.get("CAJA_CENTRO_DIR", "/data/caja-centro")


@pytest.fixture(scope="session")
def norte_url() -> str:
    return NORTE_URL


@pytest.fixture(scope="session")
def norte_api_key() -> str:
    return NORTE_API_KEY


@pytest.fixture(scope="session")
def oriente_url() -> str:
    return ORIENTE_URL


@pytest.fixture(scope="session")
def oriente_credentials() -> tuple[str, str]:
    return ORIENTE_USER, ORIENTE_PASSWORD


@pytest.fixture(scope="session")
def centro_dir() -> str:
    return CENTRO_DIR


@pytest.fixture(scope="session")
def known_norte_document(norte_url, norte_api_key) -> str:
    """Primer documento que Caja Norte reconoce, preguntado a su propia interfaz
    publica (nunca a los datos internos de la caja simulada)."""
    import requests

    from src.documents import normalize

    candidates = ["8873901472", "91336507", "3712776370", "1098765432"]
    for candidate in candidates:
        response = requests.get(
            f"{norte_url}/api/v1/afiliados/{normalize(candidate)}",
            headers={"X-Api-Key": norte_api_key},
            timeout=5,
        )
        if response.status_code == 200:
            return normalize(candidate)
    pytest.skip("Ningun documento de muestra existe en Caja Norte; ajustar la lista de candidatos")
