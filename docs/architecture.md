# Arquitectura

## Contexto

Caja Link resuelve la interoperabilidad entre cuatro cajas de compensacion que
hoy se validan afiliaciones por archivos mensuales o integraciones punto a
punto. El servicio centraliza esa validacion detras de un unico contrato HTTP
en el puerto 8083, consumido por cada caja con su propio token Bearer, de forma
que agregar una quinta caja en el futuro no implique cambiar las integraciones
existentes de las demas.

## Componentes

`src/adapters/` contiene un adaptador por caja (Norte REST, Oriente SOAP,
Centro archivo plano, Sur REST v2), todos implementando `CajaAdapter.lookup`.
`src/orchestrator.py` llama en paralelo a los adaptadores relevantes (todos
menos el de la caja consultante) y agrega el resultado. `src/security.py`
resuelve el token Bearer a la caja que pregunta y valida la finalidad.
`src/batch.py` reutiliza el mismo orquestador para procesar un CSV completo de
forma concurrente y acotada. `src/audit.py` registra cada consulta con el
documento enmascarado. `src/main.py` expone todo como rutas FastAPI.

## Flujo de consulta

Una caja llama `GET /api/v1/affiliations/{documento}?purpose=...` con su token.
El documento se normaliza (sin puntos, espacios ni ceros a la izquierda) y el
orquestador llama en paralelo, con timeout de 2.5 segundos cada uno, a los
adaptadores de las demas cajas. Cada adaptador devuelve sus afiliaciones o
marca la caja como no disponible; el orquestador decide AFILIADO_OTRA_CAJA si
alguna coincidencia esta vigente, NO_AFILIADO si todas respondieron sin
coincidencia, o INDETERMINADO si alguna caja fallo y no hay coincidencia en
las demas. La respuesta se construye campo por campo en un modelo propio, nunca
reenviando el JSON/XML crudo de una caja.

## Manejo de fallas

Ningun adaptador propaga una excepcion hacia el orquestador: un timeout, un
error de red o una respuesta inesperada se traducen siempre en
CajaLookup(available=False, ...), y el orquestador nunca interpreta "no se
pudo consultar" como "no afiliado". El presupuesto de 5 segundos del contrato
se cumple ejecutando las llamadas en paralelo con un timeout individual menor
(2.5s), de forma que incluso con una caja lenta o caida el tiempo total de
respuesta no depende de cuantas cajas haya, solo del timeout mas alto alcanzado.

## Alternativas descartadas

- Patron federado (cada caja resuelve su parte y las combina el cliente):
  descartado porque exigiria que las cajas simuladas del kit implementen un
  protocolo de coordinacion que no existe y que el reto no pide.
- Cola de mensajes (Redis/RabbitMQ) para el procesamiento por lote: descartada
  por agregar infraestructura sin necesidad real a la escala de 10.000
  documentos del reto; un semaforo de concurrencia en memoria basta (63
  segundos medidos en pruebas reales) y es mucho mas simple de operar y
  depurar durante el hackathon.
