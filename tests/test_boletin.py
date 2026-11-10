"""Tests del lector del Boletín Oficial y del buscador (sin red)."""
import json
import re
from pathlib import Path

from scripts import scraper_boletin as sb

ROOT = Path(__file__).resolve().parent.parent

SECCION = """
<a href="/detalleAviso/primera/349970/20261103" onclick="x">
  <div class="linea-aviso"><p class="item">MINISTERIO DE SALUD - SECRETARÍA NACIONAL DE DISCAPACIDAD </p>
  <p class="item-detalle"><small>Resolución 3702/2026</small></p>
  <p class="item-detalle" ><small>RESOL-2026-3702-APN-SND#MS</small></p></div></a>
<a href="/detalleAviso/primera/349900/20261103" onclick="x">
  <div class="linea-aviso"><p class="item">MINISTERIO DE ECONOMÍA</p>
  <p class="item-detalle"><small>Resolución 1/2026</small></p></div></a>
"""


def test_parsea_la_seccion_y_elige_candidatos():
    avisos = sb.parsear_seccion(SECCION, "2026-11-03")
    assert [a["id"] for a in avisos] == ["349970", "349900"]
    assert avisos[0]["norma"] == "Resolución 3702/2026" and avisos[0]["codigo"].startswith("RESOL-2026-3702")
    assert [sb.es_candidato(a) for a in avisos] == [True, False]


def test_resumen_oculta_dni_y_categoriza():
    cuerpo = ("VISTO ... RESUELVE: ARTÍCULO 1°.- Rehabilítase la pensión no contributiva por invalidez de Juan Pérez, "
              "DNI N° 12.345.678, a partir del mes siguiente. ARTÍCULO 2°.- Comuníquese.")
    r = sb.resumir(cuerpo)
    assert "12.345.678" not in r and "[omitido]" in r
    assert sb.categoria(cuerpo) == "pensiones"
    assert sb.categoria("Apruébanse los aranceles del Sistema de Prestaciones Básicas") == "aranceles"
    assert sb.categoria("Certificado Único de Discapacidad: prorróganse") == "cud"
    assert sb.categoria("asignaciones familiares previstas en la Ley N° 24.714") == "asignaciones"


def test_resumen_sigue_leyendo_si_el_articulo_1_es_corto():
    cuerpo = ("ARTÍCULO 1°.- Sustitúyese el artículo 2° de la Resolución N° 3695, por el siguiente: “ARTÍCULO 2°.- "
              "Hágase saber a las personas titulares que podrán solicitar su rehabilitación en un plazo de SESENTA (60) días corridos.”")
    assert "SESENTA (60) días" in sb.resumir(cuerpo)


def test_api_boletin_busca_y_filtra(client):
    d = client.get("/api/boletin").json()
    assert set(d["por_categoria"]) == {"aranceles", "pensiones", "cud", "asignaciones", "otras"}
    assert d["total"] == len(d["normas"]) or d["total"] > len(d["normas"])
    fechas = [n["fecha"] for n in d["normas"]]
    assert fechas == sorted(fechas, reverse=True)
    for n in d["normas"]:
        assert n["url"].startswith("https://www.boletinoficial.gob.ar/detalleAviso/primera/")
        assert not re.search(r"DNI[^\[]{0,8}\d{1,2}\.?\d{3}\.?\d{3}", n["resumen"])   # ningún DNI publicado
    if d["normas"]:
        n = d["normas"][0]
        assert client.get("/api/boletin", params={"q": n["norma"]}).json()["total"] >= 1
        cat = client.get("/api/boletin", params={"categoria": n["categoria"]}).json()
        assert all(x["categoria"] == n["categoria"] for x in cat["normas"])
    assert client.get("/api/boletin/novedades").status_code == 200


def test_pestana_normativa_en_menu_y_cartel():
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    nav = html[html.index("<nav>"):html.index("</nav>")]
    assert 'data-panel="normativa"' in nav and 'id="panel-normativa"' in html
    assert "if (name === 'normativa') initNormativa();" in html
    assert "fetchJSON('/api/boletin/novedades')" in html


def test_json_del_boletin_sin_anexos_ni_texto_completo():
    d = json.loads((ROOT / "data" / "processed" / "boletin_discapacidad.json").read_text(encoding="utf-8"))
    for n in d["normas"]:
        assert set(n) == {"id", "organismo", "norma", "codigo", "fecha", "url", "resumen", "categoria"}
        assert len(n["resumen"]) <= 420


def test_resumen_sigue_si_el_articulo_1_anuncia_un_texto():
    cuerpo = ("ARTÍCULO 1°.- Sustitúyese el artículo 2° de la Resolución N° 3695 del 27 de octubre de 2026 de la SECRETARÍA "
              "NACIONAL DE DISCAPACIDAD DEL MINISTERIO DE SALUD, por el siguiente: “ARTÍCULO 2°.- Hágase saber que podrán "
              "solicitar su rehabilitación en un plazo de SESENTA (60) días corridos.” ARTÍCULO 2°.- Publíquese.")
    assert "rehabilitación" in sb.resumir(cuerpo)
