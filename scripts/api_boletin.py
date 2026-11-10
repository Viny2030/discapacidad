"""
api_boletin.py — buscador de normas sobre discapacidad del Boletín Oficial.

Lee data/processed/boletin_discapacidad.json (lo actualiza scripts/scraper_boletin.py
todos los días hábiles). Solo hay resúmenes y enlaces oficiales: los anexos con
datos de personas no se copian.
"""
from __future__ import annotations

import json
import unicodedata
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/boletin", tags=["boletín oficial"])

ARCHIVO = Path(__file__).resolve().parent.parent / "data" / "processed" / "boletin_discapacidad.json"
CATEGORIAS = ("aranceles", "pensiones", "cud", "asignaciones", "otras")
IMPORTANTES = ("aranceles", "pensiones", "cud")


def _datos() -> dict:
    try:
        return json.loads(ARCHIVO.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"normas": [], "dias_revisados": []}


def _plano(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def _meta(d: dict) -> dict:
    dias = d.get("dias_revisados", [])
    return {"fuente": d.get("fuente", "Boletín Oficial"), "fuente_url": d.get("fuente_url"),
            "actualizado": d.get("actualizado"), "ultimo_dia_revisado": dias[0] if dias else None,
            "primer_dia_revisado": dias[-1] if dias else None, "dias_revisados": len(dias)}


@router.get("")
def buscar(
    q: Optional[str] = Query(None, description="Texto a buscar en organismo, norma y resumen"),
    categoria: Optional[str] = Query(None, description="|".join(CATEGORIAS)),
    desde: Optional[str] = Query(None, description="AAAA-MM-DD"),
    hasta: Optional[str] = Query(None, description="AAAA-MM-DD"),
    limite: int = Query(50, ge=1, le=500),
):
    """Normas sobre discapacidad publicadas en el Boletín Oficial, de la más nueva a la más vieja."""
    d = _datos()
    normas = d["normas"]
    if categoria in CATEGORIAS:
        normas = [n for n in normas if n["categoria"] == categoria]
    if desde:
        normas = [n for n in normas if n["fecha"] >= desde]
    if hasta:
        normas = [n for n in normas if n["fecha"] <= hasta]
    if q:
        terminos = _plano(q).split()
        normas = [n for n in normas
                  if all(t in _plano(" ".join((n["organismo"], n["norma"], n["codigo"], n["resumen"]))) for t in terminos)]
    por_cat = {c: sum(1 for n in d["normas"] if n["categoria"] == c) for c in CATEGORIAS}
    return {**_meta(d), "total": len(normas), "por_categoria": por_cat, "normas": normas[:limite]}


@router.get("/novedades")
def novedades(dias: int = Query(15, ge=1, le=60)):
    """Normas importantes (aranceles, pensiones, CUD) de los últimos días, para el cartel del sitio."""
    d = _datos()
    corte = (date.today() - timedelta(days=dias)).isoformat()
    recientes = [n for n in d["normas"] if n["fecha"] >= corte and n["categoria"] in IMPORTANTES]
    return {**_meta(d), "dias": dias, "normas": recientes[:3]}
