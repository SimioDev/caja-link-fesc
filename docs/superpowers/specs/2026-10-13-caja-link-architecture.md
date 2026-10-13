# Caja Link — Decisiones de arquitectura (spec interna)

> El contrato funcional completo y obligatorio es el de los organizadores: `RETO.md` §6, `KIT.md` y `RUBRICA.md` (sección "Nivel Profesional"). Este documento fija únicamente las decisiones de diseño que esos archivos dejan libres, para que el plan de implementación tenga un punto de partida único.

## Patrón de integración

**Hub central.** Un único servicio (`caja-link`) expone el contrato en `:8083` y habla con cada caja a través de un adaptador propio. Se descarta federado (cada caja resolviendo parte de la consulta) e híbrido por complejidad innecesaria a 4 cajas con un contrato ya fijo; hub central es lo más simple que cumple todos los requisitos y es defendible en ADR-001.

## Stack

- **Python 3.12 + FastAPI** (async nativo, necesario para llamar a 3-4 cajas en paralelo con presupuesto de 5s).
- **httpx.AsyncClient** para REST (Norte, Sur) y para construir/enviar el sobre SOAP de Oriente (el SOAP del mock es XML plano, no hace falta `zeep`).
- **Pydantic v2** para los modelos de respuesta: se construyen campo por campo (nunca "spread" del JSON crudo de una caja), así el dato mínimo (P06) es una propiedad del esquema, no una lista de exclusión que alguien puede olvidar.
- **PyYAML** para `config/cajas.yaml`.
- **pytest + requests** para las pruebas de caja negra (corren en un contenedor aparte, contra el servicio ya levantado, igual que lo hará el calificador oficial).

## Documento canónico interno

Todo documento se normaliza internamente a **solo dígitos, sin ceros a la izquierda** (`normalize()` en `src/documents.py`). Para llamar a Caja Oriente se re-rellena a 12 dígitos (`to_oriente_format()`); para las demás se usa el valor canónico tal cual.

## Resultado de una consulta

- `AFILIADO_OTRA_CAJA`: al menos una caja (≠ la consultante) respondió con afiliación vigente.
- `NO_AFILIADO`: todas las cajas (≠ la consultante) respondieron, ninguna tiene afiliación vigente.
- `INDETERMINADO`: alguna caja no respondió a tiempo/falló Y no hay coincidencia vigente en las demás.

Timeout por adaptador: 2.5s (margen contra el presupuesto total de 5s, ejecutando las llamadas en paralelo con `asyncio.gather`).

## Config-driven cuarta caja

`config/cajas.yaml` declara las 4 cajas (nombre + tipo de adaptador + si está habilitada). Las URLs/tokens siguen en variables de entorno (nunca en código ni en el YAML). `src/adapters/registry.py` arma la lista de adaptadores activos leyendo ese YAML + entorno; ningún otro archivo de `src/` menciona nombres ni puertos de cajas.
