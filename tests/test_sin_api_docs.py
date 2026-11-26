"""La documentación interactiva de la API no se publica y el sitio no la enlaza."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_docs_apagadas(client):
    for ruta in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(ruta).status_code == 404, ruta


def test_sitio_no_enlaza_docs():
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    assert 'href="/docs"' not in html
    assert "window.open('/docs'" not in html
    assert "API Docs" not in html
