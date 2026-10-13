import os
import time
import uuid

import requests

NORTE_URL = os.environ.get("CAJA_NORTE_URL", "http://caja-norte:9001")


def _chaos(mode: str) -> None:
    requests.post(f"{NORTE_URL}/__chaos", json={"mode": mode}, timeout=5)


def test_batch_nunca_responde_no_afiliado_si_una_caja_cayo_a_mitad_del_lote(base_url, known_norte_document):
    headers = {
        "Authorization": "Bearer " + os.environ["CENTRO_TOKEN"],
        "Idempotency-Key": "test-caos-" + uuid.uuid4().hex,
        "Content-Type": "text/csv",
    }
    documentos = [known_norte_document] + [str(9000000000000 + i) for i in range(19)]
    payload = "document\n" + "\n".join(documentos) + "\n"

    _chaos("down")
    try:
        response = requests.post(f"{base_url}/api/v1/batch-checks", headers=headers, data=payload, timeout=30)
        assert response.status_code == 202
        job_id = response.json()["jobId"]

        status = {}
        for _ in range(30):
            status = requests.get(f"{base_url}/api/v1/batch-checks/{job_id}", headers=headers, timeout=10).json()
            if status["status"] == "DONE":
                break
            time.sleep(1)
    finally:
        _chaos("ok")

    assert status["status"] == "DONE"
    assert len(status["results"]) == len(documentos)
    for result in status["results"]:
        assert result["result"] != "NO_AFILIADO" or "NORTE" not in (result.get("unavailable") or [])
        if result["result"] == "INDETERMINADO":
            assert "NORTE" in result["unavailable"]


def test_batch_misma_idempotency_key_mientras_el_lote_sigue_corriendo_no_duplica_el_trabajo(base_url, known_norte_document):
    headers = {
        "Authorization": "Bearer " + os.environ["CENTRO_TOKEN"],
        "Idempotency-Key": "test-running-" + uuid.uuid4().hex,
        "Content-Type": "text/csv",
    }
    documentos = [known_norte_document] + [str(9100000000000 + i) for i in range(29)]
    payload = "document\n" + "\n".join(documentos) + "\n"

    _chaos("slow")
    try:
        first = requests.post(f"{base_url}/api/v1/batch-checks", headers=headers, data=payload, timeout=30)
        assert first.status_code == 202
        first_job_id = first.json()["jobId"]

        # El lote sigue RUNNING (Norte esta "slow"): repetir la misma llave
        # ahora no debe arrancar un segundo proceso.
        second = requests.post(f"{base_url}/api/v1/batch-checks", headers=headers, data=payload, timeout=30)
        assert second.status_code == 202
        assert second.json()["jobId"] == first_job_id

        mid_flight = requests.get(f"{base_url}/api/v1/batch-checks/{first_job_id}", headers=headers, timeout=10).json()
        assert mid_flight["status"] in ("PENDING", "RUNNING")
    finally:
        _chaos("ok")

    status = {}
    for _ in range(30):
        status = requests.get(f"{base_url}/api/v1/batch-checks/{first_job_id}", headers=headers, timeout=10).json()
        if status["status"] == "DONE":
            break
        time.sleep(1)

    assert status["status"] == "DONE"
    assert len(status["results"]) == len(documentos)
