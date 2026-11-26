"""Subpestaña Sexualidad, ESI y violencia en Derechos y Trámites."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_sexualidad_registrada():
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    assert '<button class="sub-btn" data-sub="dt-sexualidad">Sexualidad, ESI y violencia*</button>' in html
    assert "'dt-deporte', 'dt-sexualidad']" in html
    a = html.index('<div class="panel" id="panel-dt-sexualidad">')
    panel = html[a:html.index('<div class="panel"', a + 1)]
    assert "Contenido pendiente de revisi&oacute;n profesional" in panel
    assert "no atiende emergencias ni recibe denuncias" in panel
    for s in ("144", "137", "27.655", "26.150", "911"):
        assert s in panel
