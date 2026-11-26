"""Subpestaña Deporte adaptado en Derechos y Trámites."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_deporte_adaptado_registrado():
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    assert '<button class="sub-btn" data-sub="dt-deporte">Deporte adaptado*</button>' in html
    assert "'dt-turismo', 'dt-deporte'" in html
    a = html.index('<div class="panel" id="panel-dt-deporte">')
    panel = html[a:html.index('<div class="panel"', a + 1)]
    assert "Contenido pendiente de revisi&oacute;n profesional" in panel
    assert "Ley 27.202" in panel and "2061/2022" in panel
