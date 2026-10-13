import logging
from datetime import date, datetime
from xml.etree import ElementTree as ET

import httpx

from .base import CajaAdapter
from .models import AffiliateType, CajaLookup, Membership
from ..documents import to_oriente_format

logger = logging.getLogger(__name__)

_SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
_ORI_NS = "http://cajaoriente.example/afiliacion"
_TIPO_MAP = {"D": AffiliateType.DEPENDIENTE, "I": AffiliateType.INDEPENDIENTE, "P": AffiliateType.PENSIONADO}


def _envelope(user: str, password: str, documento_12: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<soapenv:Envelope xmlns:soapenv="{_SOAP_NS}" xmlns:ori="{_ORI_NS}">'
        f"<soapenv:Header><ori:Credenciales><ori:Usuario>{user}</ori:Usuario>"
        f"<ori:Clave>{password}</ori:Clave></ori:Credenciales></soapenv:Header>"
        "<soapenv:Body><ori:ConsultarAfiliacionRequest>"
        f"<ori:NumeroDocumento>{documento_12}</ori:NumeroDocumento>"
        "</ori:ConsultarAfiliacionRequest></soapenv:Body></soapenv:Envelope>"
    )


def _parse_fecha(value: str) -> date:
    return datetime.strptime(value, "%d/%m/%Y").date()


class OrienteAdapter(CajaAdapter):
    name = "ORIENTE"

    def __init__(self, client: httpx.AsyncClient, base_url: str, user: str, password: str, timeout: float = 2.5):
        self._client = client
        self._base_url = base_url
        self._user = user
        self._password = password
        self._timeout = timeout

    async def lookup(self, document: str) -> CajaLookup:
        payload = _envelope(self._user, self._password, to_oriente_format(document))
        try:
            response = await self._client.post(
                self._base_url,
                content=payload.encode("utf-8"),
                headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": "ConsultarAfiliacion"},
                timeout=self._timeout,
            )
        except httpx.HTTPError:
            logger.warning("Caja Oriente no disponible consultando %s", document)
            return CajaLookup(caja=self.name, available=False)

        try:
            root = ET.fromstring(response.text)
        except ET.ParseError:
            logger.warning("Caja Oriente devolvio XML invalido")
            return CajaLookup(caja=self.name, available=False)

        if root.find(f".//{{{_SOAP_NS}}}Fault") is not None:
            logger.warning("Caja Oriente devolvio SOAP Fault (credenciales o formato)")
            return CajaLookup(caja=self.name, available=False)

        if root.findtext(f".//{{{_ORI_NS}}}Encontrado") != "true":
            return CajaLookup(caja=self.name, available=True, memberships=())

        memberships = []
        for afiliacion in root.iterfind(f".//{{{_ORI_NS}}}Afiliacion"):
            retiro = afiliacion.findtext(f"{{{_ORI_NS}}}FechaRetiro")
            memberships.append(
                Membership(
                    valid_from=_parse_fecha(afiliacion.findtext(f"{{{_ORI_NS}}}FechaIngreso")),
                    valid_to=_parse_fecha(retiro) if retiro else None,
                    affiliate_type=_TIPO_MAP[afiliacion.findtext(f"{{{_ORI_NS}}}TipoAfiliado")],
                )
            )
        return CajaLookup(caja=self.name, available=True, memberships=tuple(memberships))
