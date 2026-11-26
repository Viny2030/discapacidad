"""Subpestaña Turismo accesible en Derechos y Trámites."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_turismo_accesible_registrada():
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    assert '<button class="sub-btn" data-sub="dt-turismo">Turismo accesible*</button>' in html
    assert '<div class="panel" id="panel-dt-turismo">' in html
    assert "'dt-anses', 'dt-turismo']" in html
    a = html.index('<div class="panel" id="panel-dt-turismo">')
    panel = html[a:html.index('<div class="panel"', a + 1)]
    assert "Contenido pendiente de revisi&oacute;n profesional" in panel
    assert "Ley 25.643" in panel and "CUD" in panel
