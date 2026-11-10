"""Auditoría: los números visibles del sitio coinciden con las fuentes oficiales cargadas."""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
HTML = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")


def test_adultos_mayores_usa_las_participaciones_oficiales():
    df = pd.read_csv(ROOT / "data" / "processed" / "prevalencia_provincias.csv")
    tc, tp = df.cud_vigentes.sum(), df.poblacion_2022.sum()
    bloque = HTML[HTML.index("const AM_CUD = ["):HTML.index("const AM_PROV_NOMBRE")]
    filas = re.findall(r"nombre: '([^']+)', prov: [^,]+, cud: ([\d.]+), pob: ([\d.]+)", bloque)
    nombres = {"Provincia de Buenos Aires": "Buenos Aires"}
    top = []
    for nombre, cud, pob in filas:
        if nombre.startswith("Resto"):
            resto = df[~df.provincia.isin(top)]
            assert float(cud) == round(resto.cud_vigentes.sum() / tc * 100, 1)
            assert float(pob) == round(resto.poblacion_2022.sum() / tp * 100, 1)
            continue
        prov = nombres.get(nombre, nombre)
        top.append(prov)
        r = df[df.provincia == prov].iloc[0]
        assert float(cud) == round(r.cud_vigentes / tc * 100, 1), prov
        assert float(pob) == round(r.poblacion_2022 / tp * 100, 1), prov
    assert "CUD 65+ del país" not in HTML and "% CUD 65+" not in HTML     # no se presenta el total como si fuera 65+


def test_comparador_no_tiene_cupos_escritos_a_mano():
    assert "const CUPO_LABORAL" not in HTML
    assert "function cupoLaboral(prov)" in HTML and "table.il-prov tbody tr" in HTML


def test_juntas_oficiales_coherentes():
    d = json.loads((ROOT / "data" / "processed" / "juntas_oficiales.json").read_text(encoding="utf-8"))
    assert len(d["por_provincia"]) == 24 and d["total"] == sum(len(v) for v in d["por_provincia"].values()) >= 300
    assert d["fuente_pagina"] == "https://www.argentina.gob.ar/andis/juntas-evaluadoras-cud"
    assert not any("<" in j["direccion"] + j["contacto"] for v in d["por_provincia"].values() for j in v)


def test_la_pantalla_no_muestra_los_datos_de_juntas_escritos_a_mano():
    render = HTML[HTML.index("function renderJunta(data)"):HTML.index("function loadJunta()")]
    for campo in ("tiempo_espera_estimado", "nombre_organismo", "data.telefono", "data.sedes"):
        assert campo not in render, campo
