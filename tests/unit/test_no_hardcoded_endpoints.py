import re
from pathlib import Path

_FORBIDDEN = re.compile(r"(?<![\w-])caja-(norte|oriente|sur)(?![\w-])|:900[124](?!\d)", re.IGNORECASE)
_SRC = Path(__file__).resolve().parents[2] / "src"


def test_no_source_file_hardcodes_a_caja_address_or_port():
    offenders = []
    for path in _SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if _FORBIDDEN.search(text):
            offenders.append(str(path))
    assert not offenders, f"Direcciones de caja hardcodeadas en: {offenders}"


# Archivos tal como los trajo el kit de los organizadores (no son "del equipo":
# ya traian estos valores de ejemplo antes de que tocaramos nada del repo).
_KIT_PATHS = {
    ".env.example", "RETO.md", "KIT.md", "RUBRICA.md", "COMO-ENTREGAR.md",
    ".validator.json", ".entregables.py", "validator", "reset.sh",
}
_KIT_DIRS = ("mocks", "docs/cajas", "data", "caja-centro")


def test_no_repo_file_repeats_an_env_example_secret_value():
    """Ningun archivo escrito por el equipo repite en claro el valor de un
    token/clave/contraseña de .env.example, salvo los placeholders
    "cambiar-..." (la regla de la rubrica solo exime esos). Los archivos que
    ya traia el kit de los organizadores no cuentan: no los escribimos."""
    repo_root = _SRC.parent
    env_example = (repo_root / ".env.example").read_text(encoding="utf-8")
    secret_values = []
    for line in env_example.splitlines():
        if "=" not in line or line.strip().startswith("#"):
            continue
        name, _, value = line.partition("=")
        value = value.strip()
        if any(marker in name for marker in ("TOKEN", "PASSWORD", "API_KEY")) and not value.startswith("cambiar-"):
            secret_values.append(value)

    offenders = []
    for path in repo_root.rglob("*"):
        if not path.is_file() or ".git" in path.parts or ".superpowers" in path.parts:
            continue
        relative = path.relative_to(repo_root)
        if str(relative) in _KIT_PATHS or str(relative).startswith(_KIT_DIRS):
            continue
        if path.suffix not in {".py", ".md", ".yaml", ".yml", ".json", ".sh"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(value and value in text for value in secret_values):
            offenders.append(str(relative))

    assert not offenders, f"Valores de .env.example repetidos en: {offenders}"
