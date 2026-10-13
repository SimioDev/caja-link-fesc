import httpx
import pytest

from src.adapters.registry import build_adapters
from src.config import CajaDeclaration, Settings


def _settings(sur_enabled: bool) -> Settings:
    return Settings(
        tokens={},
        norte_url="http://caja-norte:9001",
        norte_api_key="norte-key",
        oriente_url="http://caja-oriente:9002/ws/AfiliacionService",
        oriente_user="caja-link",
        oriente_password="oriente-pass",
        centro_dir="/data/caja-centro",
        sur_url="http://caja-sur:9004",
        sur_token="sur-token",
        sur_enabled=sur_enabled,
        cajas_declaradas=(
            CajaDeclaration(nombre="norte", adaptador="rest_api_key"),
            CajaDeclaration(nombre="oriente", adaptador="soap"),
            CajaDeclaration(nombre="centro", adaptador="archivo_plano"),
            CajaDeclaration(nombre="sur", adaptador="rest_bearer_v2"),
        ),
    )


@pytest.mark.asyncio
async def test_build_adapters_excludes_sur_when_disabled():
    async with httpx.AsyncClient() as client:
        adapters = build_adapters(_settings(sur_enabled=False), client)
    assert {a.name for a in adapters} == {"NORTE", "ORIENTE", "CENTRO"}


@pytest.mark.asyncio
async def test_build_adapters_includes_sur_when_enabled():
    async with httpx.AsyncClient() as client:
        adapters = build_adapters(_settings(sur_enabled=True), client)
    assert {a.name for a in adapters} == {"NORTE", "ORIENTE", "CENTRO", "SUR"}
