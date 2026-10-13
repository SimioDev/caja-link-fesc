import re

_NON_DIGITS = re.compile(r"\D")


def normalize(raw: str) -> str:
    """Forma canónica de un documento: solo dígitos, sin ceros a la izquierda.

    Tolera puntos, espacios y relleno con ceros (Caja Oriente usa 12 dígitos con
    ceros a la izquierda; las demás no), de forma que la misma persona compare
    igual sin importar cómo llegó el documento.
    """
    digits = _NON_DIGITS.sub("", raw or "")
    stripped = digits.lstrip("0")
    return stripped or ("0" if digits else "")


def is_valid(canonical: str) -> bool:
    """Un documento canonico es valido si conserva al menos un digito distinto de
    cero; '' (sin digitos) o '0' (solo ceros) no identifican a ninguna persona."""
    return canonical not in ("", "0")


def to_oriente_format(document: str) -> str:
    """Caja Oriente exige exactamente 12 dígitos con ceros a la izquierda."""
    return document.zfill(12)


def mask(document: str) -> str:
    """Enmascara un documento dejando como máximo los 4 últimos dígitos visibles."""
    if len(document) <= 4:
        return "*" * len(document)
    return "*" * (len(document) - 4) + document[-4:]
