import logging
from datetime import date

import httpx

from .base import CajaAdapter
from .reintentos import get_con_reintentos
from .models import AffiliateType, CajaLookup, Membership

logger = logging.getLogger(__name__)

_TIPO_MAP = {
    "DEPENDIENTE": AffiliateType.DEPENDIENTE,
    "INDEPENDIENTE": AffiliateType.INDEPENDIENTE,
    "PENSIONADO": AffiliateType.PENSIONADO,
}


class NorteAdapter(CajaAdapter):
    name = "NORTE"

    def __init__(self, client: httpx.AsyncClient, base_url: str, api_key: str, timeout: float = 2.5):
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout

    async def lookup(self, document: str) -> CajaLookup:
        url = f"{self._base_url}/api/v1/afiliados/{document}"
        try:
            response = await get_con_reintentos(self._client, url, {"X-Api-Key": self._api_key}, self._timeout)
        except httpx.HTTPError:
            logger.warning("Caja Norte no disponible consultando %s", document)
            return CajaLookup(caja=self.name, available=False)

        if response.status_code == 404:
            return CajaLookup(caja=self.name, available=True, memberships=())
        if response.status_code != 200:
            logger.warning("Caja Norte respondio %s consultando %s", response.status_code, document)
            return CajaLookup(caja=self.name, available=False)

        body = response.json()
        memberships = tuple(
            Membership(
                valid_from=date.fromisoformat(a["fechaInicio"]),
                valid_to=date.fromisoformat(a["fechaFin"]) if a.get("fechaFin") else None,
                affiliate_type=_TIPO_MAP[a["tipoAfiliado"]],
            )
            for a in body.get("afiliaciones", [])
        )
        return CajaLookup(caja=self.name, available=True, memberships=memberships)
