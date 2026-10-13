"""Mide cuanto tarda el lote de 10.000 documentos en terminar. Uso:
   python scripts/load_test.py
Requiere el stack levantado (docker compose up -d --build) y NORTE_TOKEN
definido en el entorno (se puede cargar con `set -a; source .env; set +a`).
"""
import os
import time
import uuid

import requests

BASE_URL = os.environ.get("SERVICE_BASE_URL", "http://localhost:8083")
TOKEN = os.environ["NORTE_TOKEN"]


def main() -> None:
    with open("data/lote_10000.csv", "rb") as handle:
        payload = handle.read()

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Idempotency-Key": "load-test-" + uuid.uuid4().hex,
        "Content-Type": "text/csv",
    }

    started = time.monotonic()
    response = requests.post(f"{BASE_URL}/api/v1/batch-checks", headers=headers, data=payload, timeout=60)
    response.raise_for_status()
    job_id = response.json()["jobId"]

    errors = 0
    while True:
        status = requests.get(f"{BASE_URL}/api/v1/batch-checks/{job_id}", headers=headers, timeout=60).json()
        if status["status"] == "DONE":
            break
        if time.monotonic() - started > 600:
            raise TimeoutError("El lote no termino en 10 minutos")
        time.sleep(2)

    elapsed = time.monotonic() - started
    documentos = len(status["results"])
    print("herramienta: scripts/load_test.py (Python + requests)")
    print(f"documentos: {documentos}")
    print(f"duracion_segundos: {round(elapsed)}")
    print(f"errores: {errors}")


if __name__ == "__main__":
    main()
