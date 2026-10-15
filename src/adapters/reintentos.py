import asyncio
from typing import Mapping

import httpx

# Codigos que indican una falla pasajera de la caja (no una respuesta de negocio).
_TRANSITORIOS = {502, 503, 504}
_ESPERAS = (0.05, 0.15)  # segundos antes del 2.o y 3.er intento


async def get_con_reintentos(
    client: httpx.AsyncClient, url: str, headers: Mapping[str, str], timeout: float
) -> httpx.Response:
    """GET con hasta dos reintentos rapidos ante fallas pasajeras (5xx transitorio o
    conexion caida). Un timeout nunca se reintenta: la caja esta lenta y repetir
    duplicaria la espera, pasando del limite de 5 s del contrato. Si todos los
    intentos fallan, devuelve la ultima respuesta o propaga el ultimo error, y el
    adaptador marca la caja como no disponible (nunca NO_AFILIADO)."""
    for espera in (*_ESPERAS, None):
        try:
            response = await client.get(url, headers=dict(headers), timeout=timeout)
        except httpx.TimeoutException:
            raise
        except httpx.TransportError:
            if espera is None:
                raise
        else:
            if response.status_code not in _TRANSITORIOS or espera is None:
                return response
        await asyncio.sleep(espera)
    raise AssertionError("inalcanzable")
