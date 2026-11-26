"""Aviso de servicio/médico personal en EPOF y en el pie (todas las pestañas)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARK = "solo de servicio y orientaci&oacute;n"


def _html():
    return (ROOT / "templates" / "index.html").read_text(encoding="utf-8")


def test_epof_subpestanas_con_aviso():
    html = _html()
    for pid in ("panel-epof-info", "panel-epof-dx", "panel-epof-ley"):
        a = html.index(f'<div class="panel" id="{pid}">')
        p = html[a:html.index('<div class="panel"', a + 1)]
        assert MARK in p and "m&eacute;dico/a personal" in p, pid


def test_pie_con_aviso():
    html = _html()
    footer = html[html.index("<footer>"):html.index("</footer>")]
    assert MARK in footer and "m&eacute;dico/a personal" in footer and "911" in footer
