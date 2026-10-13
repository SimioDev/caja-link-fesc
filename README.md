# Caja Link - Cabrera & Peñaranda

<!--
Documentación del software de la pareja (entregable «README: documentación del software», 2 puntos).
Llenen cada sección; conserven los títulos ## tal como están. Los comentarios como este no cuentan
y una sección vacía no suma. La guía del kit está en KIT.md.
-->

## Descripción

Caja Link es el servicio de interoperabilidad entre cuatro cajas de compensación familiar
(Norte, Oriente, Centro y Sur) que permite a cualquiera de ellas validar, antes de otorgar una
tarifa subsidiada o un subsidio, si una persona ya tiene afiliación vigente en otra caja,
sin compartir bases de datos entre sí, sin exponer más datos personales de los estrictamente
necesarios, y sin dar nunca una respuesta falsa cuando alguna caja no responde a tiempo.

## Integrantes

- Nestor Fabian Cabrera Carreño
- William Alexsi Peñaranda Castro

## Requisitos

Docker y el plugin `docker compose` (no se usa `docker-compose` standalone), Git, y acceso a
internet solo para construir las imágenes la primera vez. No hace falta tener Python instalado
en el equipo: todo corre dentro de contenedores.

## Instalación y ejecución

```bash
cp .env.example .env
docker compose up -d --build
docker compose --profile test run --rm tests
```

El primer comando levanta Caja Norte y Caja Oriente simuladas junto con caja-link en el
puerto 8083. El segundo comando corre la suite de pruebas del equipo y deja el reporte en
test-results/results.xml. Caja Sur (la cuarta caja) se enciende aparte con
`docker compose --profile caja-sur up -d`.

## Configuración

Variables de `.env.example`:

- `NORTE_TOKEN`, `ORIENTE_TOKEN`, `CENTRO_TOKEN`, `SUR_TOKEN`: tokens con los que cada caja
  consumidora se autentica contra Caja Link (ejemplo: `cambiar-norte`).
- `ADMIN_TOKEN`: token que exige el endpoint de auditoría (ejemplo: `cambiar-admin`).
- `CAJA_NORTE_URL`: URL donde Caja Link encuentra a Caja Norte (ejemplo: `http://caja-norte:9001`).
- `CAJA_NORTE_API_KEY`: llave que Caja Link usa para autenticarse contra Caja Norte (ejemplo: `norte-key`).
- `CAJA_ORIENTE_URL`: endpoint SOAP de Caja Oriente (ejemplo: `http://caja-oriente:9002/ws/AfiliacionService`).
- `CAJA_ORIENTE_USER`, `CAJA_ORIENTE_PASSWORD`: credenciales SOAP de Caja Oriente (ejemplo: `caja-link` / `oriente-pass`).
- `CAJA_CENTRO_DIR`: directorio donde Caja Link busca el archivo plano diario de Caja Centro (ejemplo: `/data/caja-centro`).
- `CAJA_SUR_URL`: endpoint REST v2 de Caja Sur (ejemplo: `http://caja-sur:9004`).
- `CAJA_SUR_TOKEN`: token Bearer con el que Caja Link se autentica contra Caja Sur (ejemplo: `sur-token`).
- `CAJA_SUR_ENABLED`: en `true` activa el adaptador de Caja Sur sin tocar código (ejemplo: `false`).
- `CAJA_NORTE_PORT`, `CAJA_ORIENTE_PORT`, `CAJA_SUR_PORT`: puertos publicados en el host para cada caja simulada (ejemplo: `9001`, `9002`, `9004`).

## Arquitectura

`docker-compose.yml` define cinco servicios: `caja-norte` y `caja-oriente` (las cajas
simuladas REST y SOAP del kit), `caja-sur` (la cuarta caja, perfil caja-sur), `caja-link`
(nuestro servicio de interoperabilidad en el puerto 8083) y `tests` (perfil test, corre la
suite de pruebas contra caja-link ya levantado y deja el reporte JUnit en test-results/).
caja-link mantiene un adaptador por caja detrás de una interfaz común (`CajaAdapter`) y un
orquestador que agrega los resultados en paralelo con tolerancia a fallas; ver
docs/architecture.md para el detalle completo del flujo y las decisiones descartadas.

## Uso

```bash
curl -H "Authorization: Bearer $CENTRO_TOKEN" \
  "http://localhost:8083/api/v1/affiliations/{document}?purpose=VALIDACION_AFILIACION"

curl -H "Authorization: Bearer $CENTRO_TOKEN" \
  "http://localhost:8083/api/v2/affiliations/{document}?purpose=VALIDACION_AFILIACION"

curl -X POST -H "Authorization: Bearer $NORTE_TOKEN" -H "Idempotency-Key: demo-1" \
  -H "Content-Type: text/csv" --data-binary @data/lote_10000.csv \
  "http://localhost:8083/api/v1/batch-checks"

curl -H "Authorization: Bearer $NORTE_TOKEN" \
  "http://localhost:8083/api/v1/batch-checks/{jobId}"

curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8083/api/v1/audit?limit=10"
```

## Pruebas

La suite (`pytest`, en `tests/unit/` y `tests/contract/`) cubre normalización de documentos,
agregación con adaptadores falsos, autenticación, finalidad, auditoría, lote con idempotencia
y tolerancia a fallas vía `/__chaos`. Se ejecuta con `docker compose --profile test run --rm tests`,
que deja el reporte en test-results/results.xml.

## Documentación

- docs/architecture.md
- docs/adr/
- docs/threat-model.md
- docs/load-test.md
- openapi.yaml
- config/cajas.yaml
- AI_USAGE.md

## Qué resolvimos

Implementamos el contrato completo de interoperabilidad: consulta en línea v1 y v2, cruce
por lote de 10.000 documentos con idempotencia, auditoría con documento enmascarado, y la
cuarta caja activable solo por configuración. La tolerancia a fallas (caja caída o lenta)
nunca degrada a un falso "no afiliado", verificado con pruebas que apagan Caja Norte en
caliente vía /__chaos. En el camino encontramos y corregimos tres fallas reales: el formato
de fecha del encabezado de Caja Centro no era el mismo que el de cada fila, la imagen de
pruebas no copiaba algunos archivos que sus propias pruebas necesitaban, y una condición de
carrera al reiniciar un contenedor recién levantado.

## Limitaciones y pendientes

El estado de los jobs de lote vive en memoria del proceso: un reinicio de caja-link a mitad
de un lote lo pierde (ver ADR-003). No implementamos persistencia de auditoría entre
reinicios tampoco, por la misma razón de alcance.
