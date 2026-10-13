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


def test_no_env_example_value_is_a_real_looking_secret():
    env_example = (_SRC.parent / ".env.example").read_text(encoding="utf-8")
    for line in env_example.splitlines():
        if "TOKEN" in line or "PASSWORD" in line or "API_KEY" in line:
            if "=" in line:
                value = line.split("=", 1)[1].strip()
                assert value.startswith("cambiar-") or value in ("norte-key", "oriente-pass", "sur-token"), (
                    f"Valor sospechoso en .env.example: {line}"
                )
