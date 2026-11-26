"""Menú en dos filas hasta 1120 px y favicon inline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_menu_compacto_y_favicon():
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    assert "@media (min-width:701px) and (max-width:1120px)" in html
    assert '<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,' in html


def test_playwright_mcp_ignorado():
    assert ".playwright-mcp/" in (ROOT / ".gitignore").read_text(encoding="utf-8")
