"""Tests del lector del Boletín Oficial (PDF oficial vía otslist) y del buscador, sin red."""
import json
import re
from pathlib import Path

from scripts import scraper_boletin as sb

ROOT = Path(__file__).resolve().parent.parent

LISTADO = """
<h4 class="text-left">03-11-2026</h4><table><tbody>
<tr><td>1</td><td class="txtlargo">2e3b</td><td><a href="/ots/download/2e3b54c0/0/">x</a></td><td><a href="/ots/download/2e3b54c0/2/">r</a></td></tr>
<tr><td>2</td><td class="txtlargo">aaaa</td><td><a href="/ots/download/aaaa/0/">x</a></td></tr>
</tbody></table>
<h4 class="text-left">02-11-2026</h4><table><tbody>
<tr><td>1</td><td>bbbb</td><td><a href="/ots/download/bbbb/0/">x</a></td></tr></tbody></table>
"""

# Texto con el formato que devuelve pypdf: sumario, dos normas, un edicto y la cola del PDF
PDF = (
    "BOLETÍN OFICIAL Nº 36.026 - Primera Sección Martes 3 de noviembre de 2026 Sumario Decretos MINISTERIO DE DEFENSA "
    "Decreto 1324/2026 DECTO-2026-1324-APN-PTE - Desígnase ...... 3 Resoluciones MINISTERIO DE SALUD SECRETARÍA NACIONAL "
    "DE DISCAPACIDAD Resolución 3702/2026 RESOL-2026-3702-APN-SND#MS ...... 20 #I7833001I# Decretos MINISTERIO DE DEFENSA "
    "Decreto 1324/2026 DECTO-2026-1324-APN-PTE - Desígnase Director. Ciudad de Buenos Aires, 02/11/2026 VISTO el Decreto "
    "Nº 659/1947, Por ello, ARTÍCULO 1°.- Desígnase al coronel. ARTÍCULO 2°.- Comuníquese. #F7833001F# "
    "e. 03/11/2026 N° 82300/26 v. 03/11/2026 "
    "#I7833002I# MINISTERIO DE SALUD SECRETARÍA NACIONAL DE DISCAPACIDAD Resolución 3702/2026 RESOL-2026-3702-APN-SND#MS "
    "Ciudad de Buenos Aires, 02/11/2026 VISTO la Ley N° 13.478 y el Decreto N° 432/97, EL SECRETARIO NACIONAL DE DISCAPACIDAD "
    "RESUELVE: ARTÍCULO 1°.- Déjase sin efecto la Resolución N° 13.901/25 de la ex AGENCIA NACIONAL DE DISCAPACIDAD respecto "
    "de las pensiones no contributivas por invalidez laboral de las personas del Anexo I, entre ellas Juan Pérez, DNI N° "
    "12.345.678, que podrán pedir su rehabilitación. ARTÍCULO 2°.- Comuníquese. e. 03/11/2026 N° 82345/26 v. 03/11/2026 "
    "BOLETÍN OFICIAL Nº 36.026 - Primera Sección 58 Martes 3 de noviembre de 2026 Avisos Oficiales BANCO CENTRAL DE LA "
    "REPÚBLICA ARGENTINA EDICTO El Banco Central cita a Pedro Gómez (DNI 20.111.222), persona con discapacidad, a "
    "comparecer. e. 03/11/2026 N° 82400/26 v. 05/11/2026 Fin del PDF"
)


def test_listado_de_pdf_oficiales():
    pdfs = sb.parsear_listado(LISTADO)
    assert pdfs == {"2026-11-03": sb.OTS + "/ots/download/2e3b54c0/0/",     # solo la sección 1
                    "2026-11-02": sb.OTS + "/ots/download/bbbb/0/"}


def test_separa_avisos_saltea_sumario_y_edictos():
    avisos = sb.separar_avisos(PDF)
    assert [(a["norma"], a["codigo"]) for a in avisos] == [
        ("Decreto 1324/2026", "DECTO-2026-1324-APN-PTE"),                    # no la cita "Decreto Nº 659/1947"
        ("Resolución 3702/2026", "RESOL-2026-3702-APN-SND#MS")]              # el edicto no se guarda
    assert avisos[1]["organismo"] == "MINISTERIO DE SALUD SECRETARÍA NACIONAL DE DISCAPACIDAD"


def test_normas_del_dia_filtra_resume_y_oculta_dni():
    normas = sb.normas_del_dia("2026-11-03", "https://otslist.boletinoficial.gob.ar/ots/download/x/0/", PDF)
    assert [n["norma"] for n in normas] == ["Resolución 3702/2026"]
    n = normas[0]
    assert n["categoria"] == "pensiones" and "12.345.678" not in n["resumen"] and "[omitido]" in n["resumen"]
    assert n["url"] == "https://www.boletinoficial.gob.ar/seccion/primera/20261103" and n["pdf"].startswith(sb.OTS)
    assert n["id"] == "20261103-RESOL-2026-3702-APN-SND#MS"


def test_resumen_sigue_si_el_articulo_1_anuncia_un_texto():
    cuerpo = ("ARTÍCULO 1°.- Sustitúyese el artículo 2° de la Resolución N° 3695 del 27 de octubre de 2026 de la SECRETARÍA "
              "NACIONAL DE DISCAPACIDAD DEL MINISTERIO DE SALUD, por el siguiente: “ARTÍCULO 2°.- Hágase saber que podrán "
              "solicitar su rehabilitación en un plazo de SESENTA (60) días corridos.” ARTÍCULO 2°.- Publíquese.")
    assert "rehabilitación" in sb.resumir(cuerpo)


def test_categorias():
    assert sb.categoria("Apruébanse los aranceles del Sistema de Prestaciones Básicas") == "aranceles"
    assert sb.categoria("Certificado Único de Discapacidad: prorróganse") == "cud"
    assert sb.categoria("asignaciones familiares previstas en la Ley N° 24.714") == "asignaciones"


def test_api_boletin_busca_y_filtra(client):
    d = client.get("/api/boletin").json()
    assert set(d["por_categoria"]) == {"aranceles", "pensiones", "cud", "asignaciones", "otras"}
    fechas = [n["fecha"] for n in d["normas"]]
    assert fechas == sorted(fechas, reverse=True)
    for n in d["normas"]:
        assert n["url"].startswith("https://www.boletinoficial.gob.ar/")
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
        assert set(n) <= {"id", "organismo", "norma", "codigo", "fecha", "url", "pdf", "resumen", "categoria"}
        assert len(n["resumen"]) <= 420


def test_reintenta_ante_corte_de_conexion(monkeypatch):
    import requests
    llamadas = []

    class Resp:
        status_code, headers = 200, {}
        def raise_for_status(self): pass

    def get(url, timeout):
        llamadas.append(url)
        if len(llamadas) == 1:
            raise requests.ConnectionError("Remote end closed connection without response")
        return Resp()

    s = requests.Session()
    monkeypatch.setattr(s, "get", get)
    monkeypatch.setattr(sb.time, "sleep", lambda _: None)
    assert sb._get(s, "https://otslist.boletinoficial.gob.ar/x").status_code == 200 and len(llamadas) == 2
