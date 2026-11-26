"""Directrices de Accesibilidad (Turismo) y enlaces oficiales SUBE (Transporte)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _panel(html, pid):
    a = html.index(f'<div class="panel" id="{pid}">')
    return html[a:html.index('<div class="panel"', a + 1)]


def test_turismo_directrices():
    p = _panel((ROOT / "templates" / "index.html").read_text(encoding="utf-8"), "panel-dt-turismo")
    assert "Directrices de Accesibilidad" in p and "Decreto 914/97" in p
    assert "programas-de-calidad/directrices-de-accesibilidad" in p


def test_transporte_sube():
    p = _panel((ROOT / "templates" / "index.html").read_text(encoding="utf-8"), "panel-dt-transporte")
    assert "beneficio-para-personas-con-cud" in p
    assert "10 d&iacute;gitos del CUD" in p
