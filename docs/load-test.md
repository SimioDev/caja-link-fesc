# Prueba de carga del lote

herramienta: scripts/load_test.py (Python + requests, POST /api/v1/batch-checks + polling de GET /api/v1/batch-checks/{jobId})
documentos: 10000
duracion_segundos: 63
errores: 0

Ejecutado contra el stack local (`docker compose up -d --build`) con `BatchStore(concurrency=50)`
en `src/main.py`. El cuello de botella es el numero de llamadas HTTP/SOAP concurrentes hacia las
cajas simuladas, no CPU del servicio: subir la concurrencia del semaforo reduce la duracion casi
linealmente hasta el limite de conexiones del cliente httpx compartido (`max_connections=300`).
