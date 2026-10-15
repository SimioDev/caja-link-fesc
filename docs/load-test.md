# Prueba de carga del lote

herramienta: scripts/load_test.py (Python + requests, POST /api/v1/batch-checks + polling de GET /api/v1/batch-checks/{jobId})
documentos: 10000
duracion_segundos: 24
errores: 0

Ejecutado contra el stack local (`docker compose up -d --build`) con `BatchStore(concurrency=50)`
en `src/main.py`, en dos corridas consecutivas con el mismo resultado (24 s, 0 errores).

La primera medicion fue de 63 s: el adaptador de Caja Centro releia y recorria el archivo plano
completo en cada consulta. Desde que el archivo se parsea una sola vez y se indexa por documento
(se recarga solo si cambia), 10.000 consultas a Centro pasaron de ~17 s a ~0,4 s y el lote completo
bajo a 24 s. El cuello de botella restante es el numero de llamadas HTTP/SOAP concurrentes hacia las
cajas simuladas, no CPU del servicio: subir la concurrencia del semaforo reduce la duracion casi
linealmente hasta el limite de conexiones del cliente httpx compartido (`max_connections=300`).
