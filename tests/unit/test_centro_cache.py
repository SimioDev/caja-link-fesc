import asyncio
import os
from datetime import date

import pytest

from src.adapters import centro
from src.adapters.centro import CentroAdapter
from src.adapters.models import AffiliateType, Membership

_HEADER = "TIPO_DOC|NUMERO_DOCUMENTO|FECHA_INICIO|FECHA_FIN|TIPO_AFILIADO|NOMBRE|SALARIO\n"


def _write(path, fecha_corte, rows):
    path.write_text(f"FECHA_CORTE|{fecha_corte}\n" + _HEADER + "".join(r + "\n" for r in rows), encoding="utf-8")


@pytest.fixture
def parse_counter(monkeypatch):
    calls = []
    original = centro._parse_file

    def counting(path, file_key):
        calls.append(path.name)
        return original(path, file_key)

    monkeypatch.setattr(centro, "_parse_file", counting)
    return calls


@pytest.mark.asyncio
async def test_centro_no_relee_el_archivo_si_no_cambio(tmp_path, parse_counter):
    _write(tmp_path / "centro_afiliados_20261003.txt", "2026-10-03", ["CC|1098765432|20200101||DEP|ANA|100"])
    adapter = CentroAdapter(tmp_path)

    for _ in range(5):
        lookup = await adapter.lookup("1098765432")
        assert lookup.memberships

    assert parse_counter == ["centro_afiliados_20261003.txt"]


@pytest.mark.asyncio
async def test_centro_recarga_cuando_el_archivo_cambia(tmp_path, parse_counter):
    path = tmp_path / "centro_afiliados_20261003.txt"
    _write(path, "2026-10-03", ["CC|1098765432|20200101||DEP|ANA|100"])
    adapter = CentroAdapter(tmp_path)
    assert (await adapter.lookup("555")).memberships == ()

    _write(path, "2026-10-03", ["CC|1098765432|20200101||DEP|ANA|100", "CC|555|20210101||IND|LUIS|200"])
    stat = path.stat()
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))

    assert (await adapter.lookup("555")).memberships
    assert len(parse_counter) == 2


@pytest.mark.asyncio
async def test_centro_usa_el_archivo_diario_mas_reciente(tmp_path, parse_counter):
    _write(tmp_path / "centro_afiliados_20261003.txt", "2026-10-03", ["CC|111|20200101||DEP|A|1"])
    adapter = CentroAdapter(tmp_path)
    assert (await adapter.lookup("111")).as_of == date(2026, 10, 3)

    _write(tmp_path / "centro_afiliados_20261004.txt", "2026-10-04", ["CC|222|20200101||DEP|B|1"])
    lookup = await adapter.lookup("222")

    assert lookup.as_of == date(2026, 10, 4)
    assert lookup.memberships
    assert (await adapter.lookup("111")).memberships == ()


@pytest.mark.asyncio
async def test_centro_conserva_todas_las_filas_de_un_documento(tmp_path):
    _write(
        tmp_path / "centro_afiliados_20261003.txt",
        "2026-10-03",
        ["CC|00555|20150101|20180101|DEP|X|1", "CC|555|20200101||PEN|X|1"],
    )
    lookup = await CentroAdapter(tmp_path).lookup("555")

    assert [m.affiliate_type for m in lookup.memberships] == [AffiliateType.DEPENDIENTE, AffiliateType.PENSIONADO]
    assert any(m.is_active(date(2026, 10, 3)) for m in lookup.memberships)


@pytest.mark.asyncio
async def test_centro_consultas_concurrentes_parsean_una_sola_vez(tmp_path, parse_counter):
    _write(tmp_path / "centro_afiliados_20261003.txt", "2026-10-03", ["CC|1098765432|20200101||DEP|ANA|100"])
    adapter = CentroAdapter(tmp_path)

    await asyncio.gather(*(adapter.lookup("1098765432") for _ in range(50)))

    assert len(parse_counter) == 1


@pytest.mark.asyncio
async def test_centro_no_guarda_nombre_ni_salario_en_memoria(tmp_path):
    _write(tmp_path / "centro_afiliados_20261003.txt", "2026-10-03", ["CC|1098765432|20200101||DEP|ANA PEREZ|7311000"])
    adapter = CentroAdapter(tmp_path)
    await adapter.lookup("1098765432")

    cached = repr(adapter._snapshot.memberships)
    assert "ANA PEREZ" not in cached
    assert "7311000" not in cached
    assert set(Membership.__dataclass_fields__) == {"valid_from", "valid_to", "affiliate_type"}
