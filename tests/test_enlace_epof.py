"""Enlaces cruzados entre Condiciones > Poco frecuentes y la pestaña EPOF."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _panel(html, pid):
    a = html.index(f'<div class="panel" id="{pid}">')
    return html[a:html.index('<div class="panel"', a + 1)]


def test_epf_y_epof_se_enlazan_en_ambos_sentidos():
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    assert "switchTab('epof-info')\">Ver m&aacute;s" in _panel(html, "panel-epf")
    assert "switchTab('epf')\">Ver m&aacute;s" in _panel(html, "panel-epof-info")
