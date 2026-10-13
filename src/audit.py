import asyncio
from datetime import datetime, timezone
from typing import List

from .documents import mask
from .schemas import AuditEntry, ConsultaResultado


class AuditLog:
    """Registro en memoria de quien consulto, con que finalidad y que resultado
    obtuvo. El documento se guarda siempre enmascarado."""

    def __init__(self) -> None:
        self._entries: List[AuditEntry] = []
        self._lock = asyncio.Lock()

    async def registrar(self, requesting_caja: str, purpose: str, result: ConsultaResultado, document: str) -> None:
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            requestingCaja=requesting_caja,
            purpose=purpose,
            result=result,
            documentMasked=mask(document),
        )
        async with self._lock:
            self._entries.append(entry)

    async def recientes(self, limit: int = 100) -> List[AuditEntry]:
        async with self._lock:
            return list(self._entries[-limit:])
