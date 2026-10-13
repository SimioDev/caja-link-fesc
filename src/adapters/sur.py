import logging
from datetime import date

import httpx

from .base import CajaAdapter
from .models import AffiliateType, CajaLookup, Membership

logger = logging.getLogger(__name__)

_CATEGORY_MAP = {
    "DEPENDENT": AffiliateType.DEPENDIENTE,
    "SELF_EMPLOYED": AffiliateType.INDEPENDIENTE,
    "RETIREE": AffiliateType.PENSIONADO,
}


class SurAdapter(CajaAdapter):
    name = "SUR"

    def __init__(self, client: httpx.AsyncClient, base_url: str, token: str, timeout: float = 2.5):
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout

    async def lookup(self, document: str) -> CajaLookup:
        url = f"{self._base_url}/v2/people/{document}/memberships"
        try:
            response = await self._client.get(
                url, headers={"Authorization": f"Bearer {self._token}"}, timeout=self._timeout
            )
        except httpx.HTTPError:
            logger.warning("Caja Sur no disponible consultando %s", document)
            return CajaLookup(caja=self.name, available=False)

        if response.status_code == 404:
            return CajaLookup(caja=self.name, available=True, memberships=())
        if response.status_code != 200:
            logger.warning("Caja Sur respondio %s consultando %s", response.status_code, document)
            return CajaLookup(caja=self.name, available=False)

        body = response.json()
        memberships = tuple(
            Membership(
                valid_from=date.fromisoformat(m["start"]),
                valid_to=date.fromisoformat(m["end"]) if m.get("end") else None,
                affiliate_type=_CATEGORY_MAP[m["category"]],
            )
            for m in body.get("memberships", [])
        )
        return CajaLookup(caja=self.name, available=True, memberships=memberships)
