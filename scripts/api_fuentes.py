"""
api_fuentes.py — GET /api/fuentes: de dónde sale cada dato del sitio y qué antigüedad tiene.

Lee data/fuentes.json (registro editable a mano) y completa las entradas
dinámicas con el dato real:
  - andis_oficial  -> fecha de corte del informe leído por scripts/scraper_andis.py
  - andis_reciente -> fecha del dato reciente cargado en andis_oficial.json
La antigüedad se calcula al momento del pedido.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["fuentes"])

ROOT = Path(__file__).resolve().parent.parent
REGISTRO = ROOT / "data" / "fuentes.json"
ANDIS = ROOT / "data" / "processed" / "andis_oficial.json"
JUNTAS = ROOT / "data" / "processed" / "juntas_oficiales.json"
BOLETIN = ROOT / "data" / "processed" / "boletin_discapacidad.json"


def antiguedad(fecha_iso: str, hoy: date | None = None) -> dict:
    """Meses desde la fecha y un estado legible: al día (<=6), revisar (<=12), antiguo (>12)."""
    hoy = hoy or date.today()
    a, m = int(fecha_iso[:4]), int(fecha_iso[5:7])
    meses = max(0, (hoy.year - a) * 12 + hoy.month - m)
    estado = "al_dia" if meses <= 6 else ("revisar" if meses <= 12 else "antiguo")
    return {"meses": meses, "estado": estado}


def listar_fuentes(hoy: date | None = None) -> list[dict]:
    registro = json.loads(REGISTRO.read_text(encoding="utf-8"))["fuentes"]
    try:
        andis = json.loads(ANDIS.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        andis = {}
    salida = []
    for f in registro:
        f = dict(f)
        dinamico = f.pop("dinamico", None)
        if dinamico:
            f["origen"] = dinamico
        if dinamico == "andis_oficial" and andis.get("oficial"):
            f["fecha"] = andis["oficial"]["fecha_corte"]
            f["valor"] = andis["oficial"]["total_cud_vigentes"]
            f["url"] = andis["oficial"]["fuente_pagina"]
            f["fecha_lectura"] = andis.get("fecha_lectura")
        elif dinamico == "andis_reciente" and andis.get("dato_reciente"):
            f["fecha"] = andis["dato_reciente"]["fecha"] + "-01"
            f["valor"] = andis["dato_reciente"]["total_cud_vigentes"]
            f["url"] = andis["dato_reciente"]["url"]
        elif dinamico == "boletin":
            try:
                bo = json.loads(BOLETIN.read_text(encoding="utf-8"))
                f["fecha"], f["valor"] = bo["dias_revisados"][0], len(bo["normas"])
            except (FileNotFoundError, json.JSONDecodeError, KeyError, IndexError):
                pass
        elif dinamico == "juntas_oficiales":
            try:
                j = json.loads(JUNTAS.read_text(encoding="utf-8"))
                f["fecha"], f["valor"] = j["fecha_lectura"], j["total"]
            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                pass
        if f.get("tipo") == "en_vivo":
            f["antiguedad"] = {"meses": 0, "estado": "en_vivo"}
        elif f.get("fecha"):
            f["antiguedad"] = antiguedad(f["fecha"], hoy)
        salida.append(f)
    return salida


@router.get("/fuentes")
def fuentes():
    """Fuentes de cada sección, fecha de los datos o de la última revisión, y antigüedad."""
    return {
        "fecha_consulta": date.today().isoformat(),
        "criterio": "al día: hasta 6 meses · revisar: 7 a 12 meses · antiguo: más de 12 meses",
        "fuentes": listar_fuentes(),
    }
