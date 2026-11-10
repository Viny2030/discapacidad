"""Tests del registro de fuentes y su antigüedad."""
import re
from datetime import date
from pathlib import Path

from scripts import api_fuentes as af

ROOT = Path(__file__).resolve().parent.parent


def test_antiguedad_y_estados():
    hoy = date(2026, 11, 10)
    assert af.antiguedad("2026-11-02", hoy) == {"meses": 0, "estado": "al_dia"}
    assert af.antiguedad("2026-05-01", hoy)["estado"] == "al_dia"        # 6 meses
    assert af.antiguedad("2026-04-01", hoy)["estado"] == "revisar"       # 7 meses
    assert af.antiguedad("2023-11-01", hoy) == {"meses": 36, "estado": "antiguo"}


def test_api_fuentes(client):
    r = client.get("/api/fuentes")
    assert r.status_code == 200
    data = r.json()
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    nav = html[html.index("<nav>"):html.index("</nav>")]
    pestanas = set(re.findall(r'data-panel="([^"]+)"', nav))
    for f in data["fuentes"]:
        assert f["seccion"] and f["fuente"] and f["actualizacion"]
        assert f["pestana"] in pestanas, f["pestana"]
        assert not f["url"] or f["url"].startswith("https://")
        assert f["antiguedad"]["estado"] in {"al_dia", "revisar", "antiguo", "en_vivo"}
        assert f["tipo"] == "en_vivo" or re.fullmatch(r"\d{4}-\d{2}-\d{2}", f["fecha"])
    andis = next(f for f in data["fuentes"] if f["seccion"].startswith("Estadístico (CUD"))
    assert andis["fecha"] == "2023-11-01" and "andis/estadisticas" in andis["url"]   # sale del scraper, no del registro


def test_inicio_y_pie_muestran_las_fuentes():
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    inicio = html[html.index('id="panel-inicio"'):html.index('id="panel-cud"')]
    assert 'id="fuentes"' in inicio and 'id="fuentes-tabla"' in inicio
    assert "fetchJSON('/api/fuentes')" in html and "renderFuentes(data)" in html and "renderAvisoActualizacion(data)" in html
    footer = html[html.index("<footer>"):html.index("</footer>")]
    assert "Fuentes y antig&uuml;edad de los datos" in footer


def test_scripts_inline_sin_errores_de_sintaxis(tmp_path):
    """Un error de sintaxis en un <script> rompe todas las pestañas; pytest solo no lo ve."""
    import shutil
    import subprocess
    import pytest
    if not shutil.which("node"):
        pytest.skip("node no está instalado")
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    bloques = re.findall(r"<script(?![^>]*src)[^>]*>(.*?)</script>", html, re.S)
    assert bloques
    for i, js in enumerate(bloques):
        f = tmp_path / f"bloque{i}.js"
        f.write_text(js, encoding="utf-8")
        r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
        assert r.returncode == 0, f"<script> n.º {i}: {r.stderr[:400]}"


def test_aviso_de_actualizacion_visible_en_todas_las_pestanas(client):
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    # está fuera de los paneles: entre el encabezado y el primer panel, así se ve en cualquier pestaña
    entre = html[html.index("</header>"):html.index('id="panel-inicio"')]
    assert 'id="aviso-actualizacion"' in entre and "Actualizaci&oacute;n de la informaci&oacute;n" in entre
    assert "noviembre de 2023" in entre                       # texto de respaldo si la API no responde
    fuentes = client.get("/api/fuentes").json()["fuentes"]
    origenes = {f.get("origen"): f for f in fuentes}
    assert origenes["andis_oficial"]["valor"] == 1_680_723
    assert origenes["andis_reciente"]["valor"] == 1_900_061
