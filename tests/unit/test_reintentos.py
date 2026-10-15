import time

import httpx
import pytest

from src.adapters.norte import NorteAdapter
from src.adapters.sur import SurAdapter

_NORTE_OK = {"afiliaciones": [{"fechaInicio": "2019-02-06", "fechaFin": None, "tipoAfiliado": "DEPENDIENTE"}]}
_SUR_OK = {"memberships": [{"start": "2021-06-01", "end": None, "category": "DEPENDENT"}]}


def _client(respuestas):
    llamadas = []

    def handler(request):
        llamadas.append(request)
        respuesta = respuestas[min(len(llamadas), len(respuestas)) - 1]
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta

    return httpx.AsyncClient(transport=httpx.MockTransport(handler)), llamadas


def _norte(respuestas):
    client, llamadas = _client(respuestas)
    return NorteAdapter(client, "http://norte", "k"), llamadas


@pytest.mark.asyncio
async def test_norte_reintenta_un_503_pasajero_y_responde_bien():
    adapter, llamadas = _norte([httpx.Response(503, json={}), httpx.Response(200, json=_NORTE_OK)])
    lookup = await adapter.lookup("8873901472")
    assert lookup.available and lookup.memberships
    assert len(llamadas) == 2


@pytest.mark.asyncio
async def test_norte_reintenta_una_conexion_caida():
    adapter, llamadas = _norte([httpx.ConnectError("caida"), httpx.Response(200, json=_NORTE_OK)])
    assert (await adapter.lookup("8873901472")).available
    assert len(llamadas) == 2


@pytest.mark.asyncio
async def test_norte_caida_persistente_sigue_siendo_no_disponible_tras_tres_intentos():
    adapter, llamadas = _norte([httpx.Response(503, json={})])
    assert not (await adapter.lookup("8873901472")).available
    assert len(llamadas) == 3


@pytest.mark.asyncio
async def test_norte_conexion_caida_persistente_es_no_disponible():
    adapter, llamadas = _norte([httpx.ConnectError("caida")])
    assert not (await adapter.lookup("8873901472")).available
    assert len(llamadas) == 3


@pytest.mark.asyncio
async def test_norte_nunca_reintenta_un_timeout_para_respetar_los_cinco_segundos():
    adapter, llamadas = _norte([httpx.ReadTimeout("lenta"), httpx.Response(200, json=_NORTE_OK)])
    assert not (await adapter.lookup("8873901472")).available
    assert len(llamadas) == 1


@pytest.mark.asyncio
async def test_norte_no_reintenta_un_no_encontrado():
    adapter, llamadas = _norte([httpx.Response(404, json={"error": "NO_ENCONTRADO"})])
    lookup = await adapter.lookup("123")
    assert lookup.available and lookup.memberships == ()
    assert len(llamadas) == 1


@pytest.mark.asyncio
async def test_norte_no_reintenta_credenciales_invalidas():
    adapter, llamadas = _norte([httpx.Response(401, json={"error": "API_KEY_INVALIDA"})])
    assert not (await adapter.lookup("123")).available
    assert len(llamadas) == 1


@pytest.mark.asyncio
async def test_los_reintentos_agregan_menos_de_medio_segundo():
    adapter, _ = _norte([httpx.Response(503, json={})])
    inicio = time.perf_counter()
    await adapter.lookup("8873901472")
    assert time.perf_counter() - inicio < 0.5


@pytest.mark.asyncio
async def test_sur_reintenta_un_503_pasajero():
    client, llamadas = _client([httpx.Response(503, json={}), httpx.Response(200, json=_SUR_OK)])
    lookup = await SurAdapter(client, "http://sur", "t").lookup("1098765432")
    assert lookup.available and lookup.memberships
    assert len(llamadas) == 2
