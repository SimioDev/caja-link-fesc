# ADR 003: Lote en memoria, sin cola externa

## Contexto

El lote debe procesar 10.000 documentos en 5 minutos o menos, con idempotencia
por `Idempotency-Key`. El reto no exige que los jobs sobrevivan a un reinicio
del servicio, y el equipo tiene tiempo acotado para el hackathon.

## Decision

El estado de los jobs de lote (`BatchStore` en `src/batch.py`) vive en memoria
del propio proceso de `caja-link`, con un `asyncio.Semaphore` acotando la
concurrencia de llamadas a las cajas.

## Alternativas

- Redis + cola de trabajos (RQ/Celery): descartado por agregar una pieza de
  infraestructura adicional (y otro servicio en `docker-compose.yml`) sin
  necesidad real a esta escala: 10.000 documentos caben comodamente en memoria
  y se procesan en menos de un minuto en pruebas reales.
- Base de datos relacional para persistir jobs: descartado por la misma razon;
  ademas el reto no pide sobrevivir a reinicios, solo terminar en 5 minutos.

## Consecuencias

Mucho menos codigo e infraestructura que mantener. El costo es que si
caja-link se reinicia a mitad de un lote, ese job se pierde; aceptable para
el alcance del reto y documentado aqui como limitacion conocida.
