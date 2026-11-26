"""Turismo Social con datos confirmados y turismo accesible en CABA."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_turismo_social_y_caba():
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    a = html.index('<div class="panel" id="panel-dt-turismo">')
    p = html[a:html.index('<div class="panel"', a + 1)]
    assert "4% de las plazas" in p and "(11) 15-4026-4232" in p
    assert "preguntas-frecuentes-de-turismo-social" in p
    assert "turismo.buenosaires.gob.ar/es/article/turismo-accesible" in p
    assert "no estaba disponible" not in p
