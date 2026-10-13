from abc import ABC, abstractmethod

from .models import CajaLookup


class CajaAdapter(ABC):
    """Interfaz comun a las cuatro cajas. Un adaptador nunca lanza por una falla
    esperada (timeout, 404, caja caida): devuelve CajaLookup(available=False, ...)."""

    name: str

    @abstractmethod
    async def lookup(self, document: str) -> CajaLookup:
        raise NotImplementedError
