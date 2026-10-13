from typing import List

import httpx

from ..config import Settings
from .base import CajaAdapter
from .centro import CentroAdapter
from .norte import NorteAdapter
from .oriente import OrienteAdapter
from .sur import SurAdapter

_BUILDERS = {
    "rest_api_key": lambda client, settings: NorteAdapter(client, settings.norte_url, settings.norte_api_key),
    "soap": lambda client, settings: OrienteAdapter(
        client, settings.oriente_url, settings.oriente_user, settings.oriente_password
    ),
    "archivo_plano": lambda client, settings: CentroAdapter(settings.centro_dir),
    "rest_bearer_v2": lambda client, settings: SurAdapter(client, settings.sur_url, settings.sur_token),
}


def build_adapters(settings: Settings, client: httpx.AsyncClient) -> List[CajaAdapter]:
    """Arma los adaptadores activos a partir de config/cajas.yaml + entorno. Caja
    Sur solo se incluye si CAJA_SUR_ENABLED=true — asi la cuarta caja se suma por
    configuracion, sin tocar ningun archivo de src/."""
    adapters: List[CajaAdapter] = []
    for declaracion in settings.cajas_declaradas:
        if declaracion.nombre == "sur" and not settings.sur_enabled:
            continue
        adapters.append(_BUILDERS[declaracion.adaptador](client, settings))
    return adapters
