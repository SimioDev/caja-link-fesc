import httpx
import pytest

from src.adapters.norte import NorteAdapter


@pytest.mark.asyncio
async def test_norte_adapter_finds_a_known_document(norte_url, norte_api_key, known_norte_document):
    async with httpx.AsyncClient() as client:
        adapter = NorteAdapter(client, norte_url, norte_api_key)
        lookup = await adapter.lookup(known_norte_document)
    assert lookup.available is True
    assert lookup.caja == "NORTE"


@pytest.mark.asyncio
async def test_norte_adapter_marks_unknown_document_as_available_with_no_memberships(norte_url, norte_api_key):
    async with httpx.AsyncClient() as client:
        adapter = NorteAdapter(client, norte_url, norte_api_key)
        lookup = await adapter.lookup("9999999999999")
    assert lookup.available is True
    assert lookup.memberships == ()


@pytest.mark.asyncio
async def test_norte_adapter_treats_wrong_api_key_as_unavailable(norte_url):
    async with httpx.AsyncClient() as client:
        adapter = NorteAdapter(client, norte_url, "llave-equivocada")
        lookup = await adapter.lookup("1098765432")
    assert lookup.available is False
