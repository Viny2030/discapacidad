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
    # el menu envuelve en dos (o mas) filas: ninguna pestaña queda fuera de pantalla
    assert "flex-wrap:wrap" in regla_nav
    assert "overflow-x:auto" not in regla_nav
    assert 'class="nav-break"' in html
    # API Docs queda al final del menu y el alto real del menu se usa como padding
    nav = html[html.index("<nav>"):html.index("</nav>")]
    assert nav.rstrip().endswith('API Docs</a>')
    assert "--nav-h" in html and "function ajustarAltoMenu(" in html


def test_pestana_condiciones_con_subpestanas():
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    nav = html[html.index("<nav>"):html.index("</nav>")]
    assert 'data-panel="condiciones"' in nav
    assert 'data-panel="tea"' not in nav and 'data-panel="tdl"' not in nav
    for sub in ("tea", "tdl", "dea", "hipoacusia", "epilepsia", "epf", "saludmental"):
        assert f'data-sub="{sub}"' in html and f'id="panel-{sub}"' in html
    assert "const CONDICIONES = ['tea', 'tdl', 'dea', 'hipoacusia', 'epilepsia', 'epf', 'saludmental'];" in html


def _panel(html, pid):
    i = html.index(f'id="panel-{pid}"')
    return html[i:html.index('<div class="panel"', i + 1)]


def test_secciones_nuevas_con_aviso_de_revision():
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    assert "Lenguaje (TDL)*" in html
    tdl = _panel(html, "tdl")
    assert "fonoaudi&oacute;logo/a matriculado/a" in tdl
    assert "PROMPT" in tdl and "/api/condiciones/tdl" in tdl
    assert "psicopedagogo/a o fonoaudi&oacute;logo/a matriculado/a" in _panel(html, "dea")
    assert "Ley 27.306" in _panel(html, "dea")
    assert "otorrinolaring&oacute;logo/a matriculado/a" in _panel(html, "hipoacusia")
    assert "Ley 25.415" in _panel(html, "hipoacusia")
    assert "neur&oacute;logo/a matriculado/a" in _panel(html, "epilepsia")
    assert "Ley 25.404" in _panel(html, "epilepsia")
    assert "Ley 26.689" in _panel(html, "epf") and "m&eacute;dico/a matriculado/a" in _panel(html, "epf")
    sm = _panel(html, "saludmental")
    assert "Ley 26.657" in sm and "psiquiatra matriculado/a" in sm
    assert "0800-999-0091" in sm      # línea nacional de salud mental, verificada en argentina.gob.ar


def test_lectura_en_voz_alta_por_fragmentos():
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    assert "function fragmentarTexto(" in html and "function elegirVozEspanol(" in html
    assert "window.speechSynthesis.pause();" not in html


# ── Traducciones persistentes (data/processed/traducciones_es.json) ──────────
def test_archivo_de_traducciones_valido():
    import json
    datos = json.loads((ROOT / "data" / "processed" / "traducciones_es.json").read_text(encoding="utf-8"))
    assert len(datos) >= 200
    for pmid, es in datos.items():
        assert pmid.isdigit()
        assert es and "parcial]" not in es and "Ã" not in es


def test_traduccion_guardada_por_pmid():
    etl_medico._TRAD_PMID["999999001"] = "Traducción guardada de prueba"
    assert etl_medico.traduccion_guardada("999999001") == "Traducción guardada de prueba"
    assert etl_medico.traduccion_guardada(None) == ""


def test_guardar_traducciones_agrega_sin_pisar(tmp_path, monkeypatch):
    import json
    falso = tmp_path / "scripts" / "etl_medico.py"
    falso.parent.mkdir()
    (tmp_path / "data" / "processed").mkdir(parents=True)
    ruta = tmp_path / "data" / "processed" / "traducciones_es.json"
    ruta.write_text(json.dumps({"1": "existente"}), encoding="utf-8")
    monkeypatch.setattr(etl_medico, "__file__", str(falso))
    n = etl_medico.guardar_traducciones([
        {"pmid": "1", "resumen_es": "no debe pisar"},
        {"pmid": "2", "resumen_es": "nueva"},
        {"pmid": "3", "resumen_es": "texto [traducción automática parcial]"},
        {"pmid": "4", "resumen_es": ""},
    ])
    assert n == 1
    assert json.loads(ruta.read_text(encoding="utf-8")) == {"1": "existente", "2": "nueva"}


def test_etl_inicial_si_falta_cache(monkeypatch, tmp_path):
    from scripts import scheduler as sc
    falso = tmp_path / "scripts" / "scheduler.py"
    falso.parent.mkdir()
    monkeypatch.setattr(sc, "__file__", str(falso))  # data/processed/ vacío -> sin caché
    s = sc.create_scheduler()
    assert s.get_job("etl_medico_inicial") is not None


def test_lectura_en_voz_alta_salta_emojis():
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    assert "function limpiarParaVoz(" in html and "function tieneContenido(" in html
    assert "fragmentarTexto(limpiarParaVoz(texto), 220).filter(tieneContenido)" in html


def test_condiciones_adicionales_con_su_ley():
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    assert "CONDICIONES.push('visual', 'diabetes', 'celiaquia', 'fq', 'oncoped', 'trasplante');" in html
    leyes = {
        "visual": ("Ley 25.682", "Ley 26.858"),
        "diabetes": ("Ley 23.753", "Ley 26.914"),
        "celiaquia": ("Ley 26.588", "Ley 27.196"),
        "fq": ("Ley 27.552",),
        "oncoped": ("Ley 27.674",),
        "trasplante": ("Ley 26.928", "Ley 27.447"),
    }
    for sub, nums in leyes.items():
        assert f'data-sub="{sub}"' in html
        panel = _panel(html, sub)
        assert "Contenido pendiente de revisi&oacute;n profesional" in panel
        assert "matriculado/a" in panel and "Evidencia m&eacute;dica reciente" in panel
        for ley in nums:
            assert ley in panel, (sub, ley)


def test_tratamientos_experimentales_con_aviso():
    r = client.get("/api/cud/tratamientos-experimentales")
    assert r.status_code == 200
    data = r.json()
    nombres = [t["nombre"] for t in data["tratamientos"]]
    assert any("Cannabis" in n for n in nombres) and any("células madre" in n for n in nombres)
    assert all(t.get("estado") for t in data["tratamientos"])
    assert "EXPERIMENTALES" in data["nota"] and "profesional" in data["nota"]
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    assert 'data-trat="experimentales"' in html and 'id="trat-experimentales"' in html
    assert "/api/cud/tratamientos-experimentales" in html
    assert "Consult&aacute; siempre con tu m&eacute;dico/a o profesional tratante" in _panel(html, "tratamientos")


def test_vanguardia_pmid_verificados_y_nuevos():
    pmids = {t["pmid_referencia"] for t in tratamientos_vanguardia.TRATAMIENTOS if t.get("pmid_referencia")}
    # PMID inventados que apuntaban a artículos ajenos (Sherlock Holmes, tráfico, etc.)
    for malo in ("35234567", "36789012", "34567890", "29091566", "31770029", "38224701",
                 "36543210", "37891234", "35678901", "36234567", "36891234", "38181483", "36123456"):
        assert malo not in pmids, malo
    ids = {t["id"] for t in tratamientos_vanguardia.TRATAMIENTOS}
    assert {"mot-004", "mot-005", "vis-003", "int-003", "psi-003", "vis-v003"} <= ids
    assert len(ids) == len(tratamientos_vanguardia.TRATAMIENTOS)
    for t in tratamientos_vanguardia.TRATAMIENTOS:
        assert t["estado"] in tratamientos_vanguardia.ESTADOS


def test_vanguardia_evidencia_en_vivo_traduce_titulos():
    assert not inspect.iscoroutinefunction(tratamientos_vanguardia.evidencia_en_vivo)

    def falso_get(url, params=None, timeout=None):
        if "esearch" in url:
            return _resp({"esearchresult": {"idlist": ["111"]}})
        if "esummary" in url:
            ids = params["id"].split(",")
            return _resp({"result": {i: {"title": "Gene therapy trial " + i, "source": "Lancet", "pubdate": "2026"} for i in ids}})
        return _resp({"totalCount": 7, "studies": [{"protocolSection": {
            "identificationModule": {"nctId": "NCT01", "briefTitle": "Spinal cord stimulation study"},
            "statusModule": {"overallStatus": "RECRUITING"}, "designModule": {"phases": ["PHASE2"]},
            "contactsLocationsModule": {"locations": [{"country": "Argentina"}]}}}]})

    tratamientos_vanguardia._EVIDENCIA_CACHE.clear()
    with patch.object(tratamientos_vanguardia.requests, "get", side_effect=falso_get), \
         patch.object(tratamientos_vanguardia, "_traducir", side_effect=lambda t, max_chars=300: "ES: " + t):
        d = client.get("/api/vanguardia/evidencia/mot-004").json()
    assert d["articulo_referencia"]["pmid"] == "38769431"
    assert d["articulo_referencia"]["titulo_es"].startswith("ES: ")
    assert d["articulos_recientes"][0]["titulo_es"] == "ES: Gene therapy trial 111"
    assert d["total_ensayos_reclutando"] == 7 and d["ensayos_reclutando"][0]["en_argentina"]
    assert d["ensayos_reclutando"][0]["fase"] == "Fase 2"
    assert d["ensayos_reclutando"][0]["titulo_es"] == "ES: Spinal cord stimulation study"
    assert client.get("/api/vanguardia/evidencia/no-existe").status_code == 404
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    assert "/api/vanguardia/evidencia/" in html and "function renderEvidenciaVanguardia(" in html
