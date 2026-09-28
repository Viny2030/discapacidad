"""
tests/test_fixes_revision.py
Tests de los arreglos de la revisión (menú, búsquedas médicas, traductor,
enlaces rotos, bloqueo del servidor, lectura en voz alta).
No usan red: las llamadas externas se simulan.
"""
import inspect
import re
from pathlib import Path
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

import main
from scripts import api_medica, datos_cud, etl_medico, tratamientos_vanguardia

ROOT = Path(__file__).resolve().parent.parent
client = TestClient(main.app)


# ── Búsquedas médicas ────────────────────────────────────────────────────────
def test_quitar_anios():
    assert api_medica._quitar_anios("visual impairment treatment 2023 2024") == (
        "visual impairment treatment", True)
    assert api_medica._quitar_anios("autismo") == ("autismo", False)


def test_consultas_originales_no_se_modifican():
    # El arreglo es en tiempo de consulta: las listas curadas quedan como estaban.
    assert api_medica.QUERIES_DEFAULT["motora"].endswith("2023 2024")


def _resp(json_data):
    r = MagicMock()
    r.ok = True
    r.json.return_value = json_data
    r.raise_for_status.return_value = None
    return r


def test_ensayos_usa_query_term_sin_anios():
    with patch.object(api_medica.requests, "get", return_value=_resp({"studies": []})) as g:
        r = client.get("/api/ensayos?tipo=visual")
    assert r.status_code == 200
    params = g.call_args.kwargs["params"]
    assert "query.term" in params and "query.cond" not in params
    assert not re.search(r"\b20\d{2}\b", params["query.term"])


def test_tratamientos_pide_conteo_total():
    with patch.object(api_medica, "_pubmed_search_live", return_value=[]), \
         patch.object(api_medica.requests, "get", return_value=_resp({"totalCount": 42})) as g:
        r = client.get("/api/tratamientos/motora")
    assert r.json()["ensayos_activos"] == 42
    assert g.call_args.kwargs["params"]["countTotal"] == "true"


def test_endpoints_de_red_no_son_async():
    for f in (api_medica.listar_articulos, api_medica.detalle_articulo, api_medica.listar_ensayos,
              api_medica.tratamientos_por_tipo, api_medica.buscar, api_medica.buscar_por_condicion,
              tratamientos_vanguardia.ficha_tratamiento):
        assert not inspect.iscoroutinefunction(f), f.__name__


# ── Traductor ────────────────────────────────────────────────────────────────
def test_etl_medico_sin_mojibake():
    txt = (ROOT / "scripts" / "etl_medico.py").read_text(encoding="utf-8")
    assert "Ã" not in txt and "Â" not in txt
    assert etl_medico._TERMINOS["rehabilitation"] == "rehabilitación"


def test_limpiar_traduccion_descarta_fallback_parcial():
    assert api_medica._limpiar_traduccion("texto [traducciÃÂ³n automÃÂ¡tica parcial]") == ""
    assert api_medica._limpiar_traduccion("texto [traducción automática parcial]") == ""
    assert api_medica._limpiar_traduccion("Resumen en español.") == "Resumen en español."


def test_memo_evita_retraducir():
    etl_medico._TRAD_MEMO["hola mundo de prueba"] = "traducido desde memo"
    with patch.object(etl_medico.requests, "get") as g:
        assert etl_medico.traducir_resumen("hola   mundo de prueba") == "traducido desde memo"
    g.assert_not_called()


# ── Enlaces y videos ─────────────────────────────────────────────────────────
def test_sin_videos_ni_enlaces_rotos_conocidos():
    fuentes = "".join((ROOT / p).read_text(encoding="utf-8") for p in (
        "scripts/datos_cud.py", "scripts/tratamientos_vanguardia.py", "templates/index.html"))
    for roto in ("kQW8Spw744M", "y2hKk-lQ_a4", "G6P8c3W6r4g", "santafe.gov.ar/discapacidad",
                 "boletin-anmat-diciembre-2018", "anac/web/index.php", "asoarteterapia"):
        assert roto not in fuentes, roto


# ── Portada: menú y lectura en voz alta ──────────────────────────────────────
def test_menu_no_esconde_pestanas():
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    regla_nav = html[html.index("    nav{"):]
    regla_nav = regla_nav[:regla_nav.index("}")]
    assert "justify-content:flex-start" in regla_nav
    assert "nav > :first-child{margin-left:auto}" in html


def test_lectura_en_voz_alta_por_fragmentos():
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    assert "function fragmentarTexto(" in html and "function elegirVozEspanol(" in html
    assert "window.speechSynthesis.pause();" not in html
