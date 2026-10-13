import os
import time

import requests

NORTE_URL = os.environ.get("CAJA_NORTE_URL", "http://caja-norte:9001")


def _chaos(mode: str) -> None:
    requests.post(f"{NORTE_URL}/__chaos", json={"mode": mode}, timeout=5)


def test_consulta_nunca_responde_no_afiliado_si_una_caja_no_respondio(base_url, known_norte_document):
    _chaos("down")
    try:
        headers = {"Authorization": "Bearer " + os.environ["CENTRO_TOKEN"]}
        response = requests.get(
            f"{base_url}/api/v1/affiliations/{known_norte_document}",
            headers=headers,
            params={"purpose": "VALIDACION_AFILIACION"},
            timeout=10,
        )
        body = response.json()
        assert body["result"] != "NO_AFILIADO"
        assert body["result"] == "AFILIADO_OTRA_CAJA" or "NORTE" in body["unavailable"]
    finally:
        _chaos("ok")


def test_consulta_responde_en_menos_de_cinco_segundos_con_una_caja_lenta(base_url, known_norte_document):
    _chaos("slow")
    try:
        headers = {"Authorization": "Bearer " + os.environ["CENTRO_TOKEN"]}
        started = time.monotonic()
        response = requests.get(
            f"{base_url}/api/v1/affiliations/{known_norte_document}",
            headers=headers,
            params={"purpose": "VALIDACION_AFILIACION"},
            timeout=10,
        )
        elapsed = time.monotonic() - started
        assert response.status_code == 200
        assert elapsed < 5
    finally:
        _chaos("ok")
