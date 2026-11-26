"""Toda sección marcada con * recuerda consultar al médico personal."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEY = "<strong>* Contenido pendiente de revisi&oacute;n profesional.</strong>"
MARK = "solo de servicio y orientaci&oacute;n"


def test_avisos_con_medico_personal():
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    pos, n = 0, 0
    while (i := html.find(KEY, pos)) >= 0:
        end = html.index("</div>", i)
        aviso = html[i:end]
        assert MARK in aviso and "m&eacute;dico/a personal" in aviso, html[i:i + 120]
        n, pos = n + 1, end
    assert n >= 21
    assert "Por ahora se listan agrupadas por categor&iacute;a. <strong>Consult&aacute; siempre con tu m&eacute;dico/a personal" in html
