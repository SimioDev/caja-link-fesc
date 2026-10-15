import httpx
import pytest

from src.adapters.oriente import OrienteAdapter

_OK = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
    'xmlns:ori="http://cajaoriente.example/afiliacion"><soapenv:Body><ori:ConsultarAfiliacionResponse>'
    "<ori:Encontrado>true</ori:Encontrado><ori:Afiliaciones><ori:Afiliacion>"
    "<ori:FechaIngreso>20/06/2020</ori:FechaIngreso><ori:FechaRetiro></ori:FechaRetiro>"
    "<ori:TipoAfiliado>D</ori:TipoAfiliado></ori:Afiliacion></ori:Afiliaciones>"
    "</ori:ConsultarAfiliacionResponse></soapenv:Body></soapenv:Envelope>"
)
_HTML_400 = "<!DOCTYPE HTML><html><body>Bad request syntax ('...soapenv:Envelope...')</body></html>"


def _adapter(respuestas):
    llamadas = []

    def handler(request):
        llamadas.append(request)
        respuesta = respuestas[len(llamadas) - 1]
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return OrienteAdapter(client, "http://oriente/ws", "u", "p"), llamadas


@pytest.mark.asyncio
async def test_reintenta_una_vez_si_la_conexion_quedo_contaminada_tras_un_503():
    adapter, llamadas = _adapter([
        httpx.Response(400, text=_HTML_400, headers={"Content-Type": "text/html;charset=utf-8"}),
        httpx.Response(200, text=_OK, headers={"Content-Type": "text/xml; charset=utf-8"}),
    ])
    lookup = await adapter.lookup("91336507")
    assert lookup.available and lookup.memberships
    assert len(llamadas) == 2


@pytest.mark.asyncio
async def test_reintenta_una_vez_ante_conexion_cerrada_por_el_servidor():
    adapter, llamadas = _adapter([
        httpx.RemoteProtocolError("Server disconnected"),
        httpx.Response(200, text=_OK, headers={"Content-Type": "text/xml; charset=utf-8"}),
    ])
    assert (await adapter.lookup("91336507")).available
    assert len(llamadas) == 2


@pytest.mark.asyncio
async def test_no_reintenta_un_timeout_para_respetar_el_limite_de_cinco_segundos():
    adapter, llamadas = _adapter([httpx.ReadTimeout("lenta"), httpx.Response(200, text=_OK)])
    assert not (await adapter.lookup("91336507")).available
    assert len(llamadas) == 1


@pytest.mark.asyncio
async def test_caja_caida_sigue_siendo_no_disponible_sin_reintentar():
    adapter, llamadas = _adapter([httpx.Response(503, json={"error": "SERVICIO_NO_DISPONIBLE"}), httpx.Response(200, text=_OK)])
    assert not (await adapter.lookup("91336507")).available
    assert len(llamadas) == 1


@pytest.mark.asyncio
async def test_reintenta_como_maximo_una_vez():
    html = httpx.Response(400, text=_HTML_400, headers={"Content-Type": "text/html"})
    adapter, llamadas = _adapter([html, html, httpx.Response(200, text=_OK)])
    assert not (await adapter.lookup("91336507")).available
    assert len(llamadas) == 2


@pytest.mark.asyncio
async def test_una_pagina_de_error_bien_formada_nunca_se_lee_como_no_afiliado():
    pagina = "<!DOCTYPE html><html><body><p>Error interno</p></body></html>"
    adapter, _ = _adapter([httpx.Response(502, text=pagina, headers={"Content-Type": "text/html"})])
    assert not (await adapter.lookup("91336507")).available


@pytest.mark.asyncio
async def test_un_200_sin_elemento_encontrado_no_se_lee_como_no_afiliado():
    raro = '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><soapenv:Body/></soapenv:Envelope>'
    adapter, _ = _adapter([httpx.Response(200, text=raro, headers={"Content-Type": "text/xml"})])
    assert not (await adapter.lookup("91336507")).available


@pytest.mark.asyncio
async def test_encontrado_false_sigue_siendo_disponible_sin_afiliaciones():
    no = ('<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
          'xmlns:ori="http://cajaoriente.example/afiliacion"><soapenv:Body><ori:ConsultarAfiliacionResponse>'
          "<ori:Encontrado>false</ori:Encontrado></ori:ConsultarAfiliacionResponse></soapenv:Body></soapenv:Envelope>")
    adapter, _ = _adapter([httpx.Response(200, text=no, headers={"Content-Type": "text/xml"})])
    lookup = await adapter.lookup("123")
    assert lookup.available and lookup.memberships == ()
