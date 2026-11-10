"""Tests del lector del informe oficial de ANDIS (sin red)."""
import json
from pathlib import Path

import pytest

from scripts import scraper_andis as s

ROOT = Path(__file__).resolve().parent.parent

# Texto con el mismo formato que devuelve pypdf para el informe de noviembre de 2023
TEXTO = (
    "PRINCIPALES DATOS ESTADÍSTICOS Datos actualizados a n oviembre de 2023 Documento ... "
    "1.680.723 personas con CUD vigente  Un 3,65% de la población nacional tiene un CUD vigente "
    "Física Motora 425.813 25,3% Mental 391.857 23,3% Intelectual 171.196 10,2% "
    "Sensorial Auditiva 153.073 9,1% Física Visceral 122.179 7,3% Sensorial Visual 80.838 4,8% "
    "Más de un tipo de deficiencia 335.767 20,0% Total 1.680.723 100,0% "
    "Buenos Aires 678.237 40,4% CABA 162.522 9,7% De 0 a 14 años 383.125 22,7% "
    "De 15 a 64 años 918.589 54,7% Santa Fe 126.431 7,5% Córdoba 113.005 6,7% Mendoza 80.338 4,8% "
    "Tucumán 63.809 3,8% Salta 57.497 3,4% Entre Ríos 50.164 3,0% Chaco 37.696 2,2% "
    "Rio Negro 33.709 2,0% Misiones 29.117 1,7% San Juan 28.712 1,7% Neuquén 28.299 1,7% "
    "Corrientes 28.182 1,7% Jujuy 28.121 1,7% Santiago Del Estero 23.849 1,4% Chubut 23.206 1,4% "
    "San Luis 16.603 1,0% Catamarca 15.910 0,9% Santa Cruz 14.617 0,9% Formosa 13.030 0,8% "
    "La Rioja 11.535 0,7% La Pampa 10.010 0,6% Tierra Del Fuego 6.124 0,3% Total 1.680.723 100,0% "
    "De 65 años y más 379.009 22,6% Total 1.680.723 100,0%"
)


def test_parsea_el_informe_oficial():
    d = s.parsear_informe(TEXTO)
    assert d["fecha_corte"] == "2023-11-01"
    assert d["total_cud_vigentes"] == 1_680_723 and d["porcentaje_poblacion"] == 3.65
    assert len(d["por_provincia"]) == 24
    assert d["por_provincia"]["Tucumán"] == 63_809
    assert d["por_provincia"]["Río Negro"] == 33_709           # «Rio Negro» en el PDF
    assert d["por_provincia"]["Buenos Aires"] == 678_237       # no confunde con «Ciudad Autónoma de Buenos Aires»
    assert d["por_tipo"]["Sensorial auditiva"] == 153_073
    assert d["por_edad"]["0 a 14 años"] == 383_125              # la tabla, no la errata del texto (383.150)


def test_rechaza_un_informe_cuyas_sumas_no_cierran():
    with pytest.raises(s.InformeInvalido, match="provincias suman"):
        s.parsear_informe(TEXTO.replace("Tucumán 63.809", "Tucumán 63.000"))


def test_rechaza_un_informe_sin_fecha():
    with pytest.raises(s.InformeInvalido, match="fecha de corte"):
        s.parsear_informe(TEXTO.replace("Datos actualizados a n oviembre de 2023", ""))


def test_busca_el_pdf_de_texto_plano():
    html = ('<a href="https://www.argentina.gob.ar/sites/default/files/informe.pdf">Gráficos</a>'
            '<a href="/sites/default/files/texto_plano_del_poster.pdf">Texto plano</a>')
    assert s.buscar_pdf(html) == "https://www.argentina.gob.ar/sites/default/files/texto_plano_del_poster.pdf"


def test_json_guardado_es_coherente_y_con_fuentes():
    d = json.loads((ROOT / "data" / "processed" / "andis_oficial.json").read_text(encoding="utf-8"))
    o = d["oficial"]
    for clave in ("por_provincia", "por_tipo", "por_edad"):
        assert sum(o[clave].values()) == o["total_cud_vigentes"], clave
    assert o["fuente_pagina"].startswith("https://www.argentina.gob.ar/andis/")
    assert d["dato_reciente"]["fuente"] and d["dato_reciente"]["url"].startswith("https://")
    assert {n["dato"] for n in d["no_oficiales"]} >= {"Tasa por provincia", "Distribución en CABA por comuna"}


def test_control_frescura_meses_y_deteccion(monkeypatch):
    from datetime import date
    from scripts import control_frescura as c
    assert c.meses_desde("2023-11-01", date(2026, 11, 10)) == 36

    guardado = json.loads((ROOT / "data" / "processed" / "andis_oficial.json").read_text(encoding="utf-8"))["oficial"]

    class Resp:
        def __init__(self, text="", data=None): self.text, self._data = text, data
        def json(self): return self._data

    def falso_get(self, url, timeout):
        if url == c.PAGINA:
            return Resp(text='<a href="/sites/default/files/texto_plano_informe_2026.pdf">Texto plano</a>')
        return Resp(data={"fecha_datos": guardado["fecha_corte"], "total_cud_vigentes": guardado["total_cud_vigentes"]})

    monkeypatch.setattr(c.requests.Session, "get", falso_get)
    ok, lineas = c.controlar("https://ejemplo.test")
    assert not ok and any("no está cargado" in x for x in lineas)   # informe nuevo publicado y no cargado
