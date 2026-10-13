import os
import time
import uuid

import requests


def _headers() -> dict:
    return {
        "Authorization": "Bearer " + os.environ["NORTE_TOKEN"],
        "Idempotency-Key": "test-" + uuid.uuid4().hex,
        "Content-Type": "text/csv",
    }


def test_batch_checks_accepts_a_small_csv_and_reaches_done(base_url, known_norte_document):
    headers = _headers()
    payload = f"document\n{known_norte_document}\n9999999999999\n"
    response = requests.post(f"{base_url}/api/v1/batch-checks", headers=headers, data=payload, timeout=30)
    assert response.status_code == 202
    job_id = response.json()["jobId"]

    status = {}
    for _ in range(30):
        status = requests.get(f"{base_url}/api/v1/batch-checks/{job_id}", headers=headers, timeout=10).json()
        if status["status"] == "DONE":
            break
        time.sleep(1)

    assert status["status"] == "DONE"
    assert {r["document"] for r in status["results"]} == {known_norte_document, "9999999999999"}


def test_batch_checks_same_idempotency_key_returns_the_same_job_id(base_url, known_norte_document):
    headers = _headers()
    payload = f"document\n{known_norte_document}\n"
    first = requests.post(f"{base_url}/api/v1/batch-checks", headers=headers, data=payload, timeout=30)
    second = requests.post(f"{base_url}/api/v1/batch-checks", headers=headers, data=payload, timeout=30)
    assert first.json()["jobId"] == second.json()["jobId"]


def test_batch_checks_unknown_job_id_responds_404(base_url):
    headers = {"Authorization": "Bearer " + os.environ["NORTE_TOKEN"]}
    response = requests.get(f"{base_url}/api/v1/batch-checks/no-existe", headers=headers, timeout=10)
    assert response.status_code == 404
