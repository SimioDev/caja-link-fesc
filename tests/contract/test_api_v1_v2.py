import os

import pytest
import requests


def _token(name: str) -> str:
    return os.environ[name]


def test_consulta_sin_token_responde_401(base_url, known_norte_document):
    response = requests.get(
        f"{base_url}/api/v1/affiliations/{known_norte_document}",
        params={"purpose": "VALIDACION_AFILIACION"},
        timeout=10,
    )
    assert response.status_code == 401


def test_consulta_sin_purpose_responde_400(base_url, known_norte_document):
    headers = {"Authorization": "Bearer " + _token("CENTRO_TOKEN")}
    response = requests.get(f"{base_url}/api/v1/affiliations/{known_norte_document}", headers=headers, timeout=10)
    assert response.status_code == 400


def test_consulta_con_purpose_invalido_responde_400(base_url, known_norte_document):
    headers = {"Authorization": "Bearer " + _token("CENTRO_TOKEN")}
    response = requests.get(
        f"{base_url}/api/v1/affiliations/{known_norte_document}",
        headers=headers,
        params={"purpose": "MERCADEO"},
        timeout=10,
    )
    assert response.status_code == 400


def test_consulta_valida_devuelve_afiliado_otra_caja(base_url, known_norte_document):
    headers = {"Authorization": "Bearer " + _token("CENTRO_TOKEN")}
    response = requests.get(
        f"{base_url}/api/v1/affiliations/{known_norte_document}",
        headers=headers,
        params={"purpose": "VALIDACION_AFILIACION"},
        timeout=10,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["result"] == "AFILIADO_OTRA_CAJA"
    assert any(m["caja"] == "NORTE" for m in body["matches"])


def test_consulta_excluye_a_la_caja_consultante(base_url, known_norte_document):
    headers = {"Authorization": "Bearer " + _token("NORTE_TOKEN")}
    response = requests.get(
        f"{base_url}/api/v1/affiliations/{known_norte_document}",
        headers=headers,
        params={"purpose": "VALIDACION_AFILIACION"},
        timeout=10,
    )
    assert response.status_code == 200
    assert "NORTE" not in [m["caja"] for m in response.json()["matches"]]


def test_consulta_respuesta_no_contiene_campos_prohibidos(base_url, known_norte_document):
    headers = {"Authorization": "Bearer " + _token("CENTRO_TOKEN")}
    response = requests.get(
        f"{base_url}/api/v1/affiliations/{known_norte_document}",
        headers=headers,
        params={"purpose": "VALIDACION_AFILIACION"},
        timeout=10,
    )
    body = response.json()
    forbidden = {"nombre", "direccion", "telefono", "correo", "salario", "beneficiarios", "titular"}
    found = forbidden & {key.lower() for match in body["matches"] for key in match}
    assert not found, f"Campos prohibidos en la respuesta: {found}"


def test_consulta_normaliza_puntos_espacios_y_ceros(base_url, known_norte_document):
    headers = {"Authorization": "Bearer " + _token("CENTRO_TOKEN")}
    variantes = [known_norte_document.zfill(12), f" {known_norte_document} "]
    resultados = set()
    for variante in variantes:
        response = requests.get(
            f"{base_url}/api/v1/affiliations/{variante}",
            headers=headers,
            params={"purpose": "VALIDACION_AFILIACION"},
            timeout=10,
        )
        assert response.status_code == 200
        resultados.add(response.json()["result"])
    assert len(resultados) == 1


def test_v2_agrega_affiliate_type_y_v1_no_cambia(base_url, known_norte_document):
    headers = {"Authorization": "Bearer " + _token("CENTRO_TOKEN")}
    v1 = requests.get(
        f"{base_url}/api/v1/affiliations/{known_norte_document}",
        headers=headers,
        params={"purpose": "VALIDACION_AFILIACION"},
        timeout=10,
    ).json()
    v2 = requests.get(
        f"{base_url}/api/v2/affiliations/{known_norte_document}",
        headers=headers,
        params={"purpose": "VALIDACION_AFILIACION"},
        timeout=10,
    ).json()
    assert "affiliateType" not in v1["matches"][0]
    assert v2["matches"][0]["affiliateType"] in ("DEPENDIENTE", "INDEPENDIENTE", "PENSIONADO")


@pytest.mark.parametrize("version", ["v1", "v2"])
@pytest.mark.parametrize("document", ["abc", "..."])
def test_consulta_con_documento_sin_digitos_responde_400(base_url, version, document):
    headers = {"Authorization": "Bearer " + _token("CENTRO_TOKEN")}
    response = requests.get(
        f"{base_url}/api/{version}/affiliations/{document}",
        headers=headers,
        params={"purpose": "VALIDACION_AFILIACION"},
        timeout=10,
    )
    assert response.status_code == 400


def test_consulta_con_documento_sin_digitos_y_sin_token_responde_401(base_url):
    response = requests.get(
        f"{base_url}/api/v1/affiliations/abc", params={"purpose": "VALIDACION_AFILIACION"}, timeout=10
    )
    assert response.status_code == 401
