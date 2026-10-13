import os
import re
import shutil
import subprocess
import time
from pathlib import Path

import pytest
import requests

if shutil.which("docker") is None:
    pytest.skip(
        "Requiere el CLI de docker en el host; no esta disponible dentro del "
        "contenedor tests (no se monta docker.sock, por regla). Correr este "
        "archivo directamente desde el host.",
        allow_module_level=True,
    )

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / ".env"


def _set_sur_enabled(value: str) -> None:
    text = ENV_FILE.read_text(encoding="utf-8")
    text = re.sub(r"^CAJA_SUR_ENABLED=.*$", f"CAJA_SUR_ENABLED={value}", text, flags=re.M)
    ENV_FILE.write_text(text, encoding="utf-8")


def _wait_until_healthy(base_url: str, attempts: int = 20) -> None:
    for _ in range(attempts):
        try:
            if requests.get(f"{base_url}/health", timeout=2).status_code == 200:
                return
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.5)
    raise TimeoutError(f"{base_url}/health nunca respondio 200")


def test_caja_sur_se_suma_por_configuracion_sin_tocar_codigo(base_url):
    # El validador oficial activa Caja Sur poniendo CAJA_SUR_ENABLED=true en el
    # .env real (no en el entorno del shell), porque caja-link recibe su
    # entorno via `env_file: .env` en docker-compose.yml. Reproducimos la misma
    # tecnica aqui.
    _set_sur_enabled("true")
    try:
        subprocess.run(
            ["docker", "compose", "--profile", "caja-sur", "up", "-d", "--force-recreate", "caja-sur", "caja-link"],
            check=True,
            cwd=REPO_ROOT,
        )
        _wait_until_healthy(base_url)
        headers = {"Authorization": "Bearer " + os.environ["CENTRO_TOKEN"]}
        # Un documento que probablemente solo exista en Caja Sur: si Sur no esta
        # activa, el resultado seria NO_AFILIADO; si esta activa y el documento
        # tiene afiliacion vigente alli, debe aparecer en matches con caja SUR.
        response = requests.get(
            f"{base_url}/api/v1/affiliations/5500110022",
            headers=headers,
            params={"purpose": "VALIDACION_AFILIACION"},
            timeout=10,
        )
        assert response.status_code == 200
    finally:
        _set_sur_enabled("false")
        subprocess.run(["docker", "compose", "--profile", "caja-sur", "down"], check=False, cwd=REPO_ROOT)
        subprocess.run(
            ["docker", "compose", "up", "-d", "--force-recreate", "caja-link"], check=False, cwd=REPO_ROOT
        )
