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


def _es_conexion_contaminada(response: httpx.Response) -> bool:
    """Tras responder 503 sin leer el cuerpo SOAP, el servidor deja esos bytes en la
    conexion keep-alive; la siguiente peticion llega mezclada y recibe un 400 en HTML
    (no SOAP) con la conexion cerrada. Se detecta para reintentar una sola vez."""
    return response.status_code == 400 and "xml" not in response.headers.get("content-type", "").lower()


class OrienteAdapter(CajaAdapter):
    name = "ORIENTE"

    def __init__(self, client: httpx.AsyncClient, base_url: str, user: str, password: str, timeout: float = 2.5):
        self._client = client
        self._base_url = base_url
        self._user = user
        self._password = password
        self._timeout = timeout

    async def _post(self, payload: bytes) -> httpx.Response:
        return await self._client.post(
            self._base_url,
            content=payload,
            headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": "ConsultarAfiliacion"},
            timeout=self._timeout,
        )

    async def lookup(self, document: str) -> CajaLookup:
        payload = _envelope(self._user, self._password, to_oriente_format(document)).encode("utf-8")
        try:
            try:
                response = await self._post(payload)
            except httpx.TimeoutException:
                raise  # caja lenta: nunca se reintenta, para no pasar del limite de 5 s
            except httpx.TransportError:
                response = await self._post(payload)  # conexion reutilizada que el servidor ya cerro
            else:
                if _es_conexion_contaminada(response):
                    response = await self._post(payload)
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

        encontrado = root.findtext(f".//{{{_ORI_NS}}}Encontrado")
        if response.status_code != 200 or encontrado not in ("true", "false"):
            # Solo un 200 con <Encontrado> explicito es una respuesta de negocio; una
            # pagina de error u otro cuerpo inesperado nunca puede leerse como
            # "no afiliado".
            logger.warning("Caja Oriente devolvio una respuesta inesperada (HTTP %s)", response.status_code)
            return CajaLookup(caja=self.name, available=False)

        if encontrado == "false":
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
