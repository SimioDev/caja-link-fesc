import os

import requests


def test_auditoria_sin_token_responde_401(base_url):
    response = requests.get(f"{base_url}/api/v1/audit", timeout=10)
    assert response.status_code == 401


def test_auditoria_con_token_de_caja_responde_403(base_url):
    headers = {"Authorization": "Bearer " + os.environ["NORTE_TOKEN"]}
    response = requests.get(f"{base_url}/api/v1/audit", headers=headers, timeout=10)
    assert response.status_code == 403


def test_auditoria_requiere_admin_token(base_url, known_norte_document):
    requests.get(
        f"{base_url}/api/v1/affiliations/{known_norte_document}",
        headers={"Authorization": "Bearer " + os.environ["CENTRO_TOKEN"]},
        params={"purpose": "VALIDACION_AFILIACION"},
        timeout=10,
    )
    headers = {"Authorization": "Bearer " + os.environ["ADMIN_TOKEN"]}
    response = requests.get(f"{base_url}/api/v1/audit", headers=headers, params={"limit": 5}, timeout=10)
    assert response.status_code == 200
    entries = response.json()
    assert entries
    required = {"timestamp", "requestingCaja", "purpose", "result", "documentMasked"}
    assert required.issubset(entries[0].keys())
    assert len(entries[0]["documentMasked"].replace("*", "")) <= 4
