import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import yaml

DEFAULT_CONFIG_PATH = Path(os.environ.get("CAJAS_CONFIG_PATH", "config/cajas.yaml"))


@dataclass(frozen=True)
class CajaDeclaration:
    nombre: str
    adaptador: str


@dataclass(frozen=True)
class Settings:
    tokens: Dict[str, str]
    norte_url: str
    norte_api_key: str
    oriente_url: str
    oriente_user: str
    oriente_password: str
    centro_dir: Path
    sur_url: str
    sur_token: str
    sur_enabled: bool
    cajas_declaradas: Tuple[CajaDeclaration, ...]

    @classmethod
    def load(cls, config_path: Path = DEFAULT_CONFIG_PATH) -> "Settings":
        with open(config_path, encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
        declaradas = tuple(CajaDeclaration(**item) for item in raw.get("cajas", []))

        def env(name: str, default: str = "") -> str:
            return os.environ.get(name, default)

        return cls(
            tokens={
                "NORTE": env("NORTE_TOKEN"),
                "ORIENTE": env("ORIENTE_TOKEN"),
                "CENTRO": env("CENTRO_TOKEN"),
                "SUR": env("SUR_TOKEN"),
                "ADMIN": env("ADMIN_TOKEN"),
            },
            norte_url=env("CAJA_NORTE_URL"),
            norte_api_key=env("CAJA_NORTE_API_KEY"),
            oriente_url=env("CAJA_ORIENTE_URL"),
            oriente_user=env("CAJA_ORIENTE_USER"),
            oriente_password=env("CAJA_ORIENTE_PASSWORD"),
            centro_dir=Path(env("CAJA_CENTRO_DIR", "/data/caja-centro")),
            sur_url=env("CAJA_SUR_URL"),
            sur_token=env("CAJA_SUR_TOKEN"),
            sur_enabled=env("CAJA_SUR_ENABLED", "false").lower() == "true",
            cajas_declaradas=declaradas,
        )
