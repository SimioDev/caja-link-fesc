import httpx
import pytest

from src.adapters.centro import CentroAdapter
from src.adapters.oriente import OrienteAdapter
from src.documents import normalize


@pytest.mark.asyncio
async def test_oriente_adapter_rejects_wrong_credentials_as_unavailable(oriente_url):
    async with httpx.AsyncClient() as client:
        adapter = OrienteAdapter(client, oriente_url, "usuario-malo", "clave-mala")
        lookup = await adapter.lookup("1098765432")
    assert lookup.available is False


@pytest.mark.asyncio
async def test_oriente_adapter_reports_not_found_as_available_with_no_memberships(oriente_url, oriente_credentials):
    user, password = oriente_credentials
    async with httpx.AsyncClient() as client:
        adapter = OrienteAdapter(client, oriente_url, user, password)
        lookup = await adapter.lookup("00000000001")
    assert lookup.available is True
    assert lookup.memberships == ()


@pytest.mark.asyncio
async def test_centro_adapter_reads_the_latest_flat_file(centro_dir):
    adapter = CentroAdapter(centro_dir)
    lookup = await adapter.lookup(normalize("1098765432"))
    assert lookup.available is True
    assert lookup.source == "FILE"
    assert lookup.as_of is not None


@pytest.mark.asyncio
async def test_centro_adapter_reports_unavailable_when_directory_is_missing(tmp_path):
    adapter = CentroAdapter(tmp_path / "no-existe")
    lookup = await adapter.lookup("1098765432")
    assert lookup.available is False
