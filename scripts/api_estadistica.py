"""
api_estadistica.py
Endpoints FastAPI para el módulo estadístico del Observatorio de Discapacidad.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import pandas as pd
from pathlib import Path
import json

router = APIRouter(prefix="/api", tags=["estadístico"])

BASE_DIR = Path(__file__).resolve().parent.parent
PROC_DIR = BASE_DIR / "data" / "processed"
RAW_DIR  = BASE_DIR / "data" / "raw"


def _load_csv(nombre: str) -> list[dict]:
    path = PROC_DIR / nombre
    if not path.exists():
        return []
    return pd.read_csv(path).to_dict("records")


def _load_json(nombre: str) -> dict:
    path = RAW_DIR / nombre
    if not path.exists():
        return {}
    return json.loads(path.read_text())


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/resumen")
async def resumen_nacional():
    """KPIs nacionales del Observatorio."""
    prov = _load_csv("prevalencia_provincias.csv")
    tipos = _load_csv("cud_por_tipo.csv")
    evol  = _load_csv("evolucion_cud.csv")
    return {
        "total_cud_vigentes":   1_680_723,
        "porcentaje_poblacion": 3.65,
        "fecha_datos":          "2023-11-01",
        "provincia_mayor":      prov[0]["provincia"] if prov else "",
        "tipo_mas_frecuente":   tipos[0]["tipo"] if tipos else "",
        "variacion_anual_pct":  evol[-1]["variacion_pct"] if evol else 0,
        "total_provincias":     len(prov),
        "fuente":               "ANDIS — Registro Nacional de Personas con Discapacidad",
    }


@router.get("/provincias")
async def provincias(
    orden: str = Query("cud_vigentes", description="cud_vigentes|tasa_prevalencia|provincia"),
):
    """CUD y tasa de prevalencia por provincia."""
    data = _load_csv("prevalencia_provincias.csv")
    if not data:
        from scripts.etl_estadistico import construir_df_provincias
        df   = construir_df_provincias()
        data = df.to_dict("records")
    if orden in ("cud_vigentes", "tasa_prevalencia"):
        data.sort(key=lambda x: x.get(orden, 0), reverse=True)
    elif orden == "provincia":
        data.sort(key=lambda x: x.get("provincia", ""))
    return {"total": len(data), "orden": orden, "provincias": data}


@router.get("/provincias/{nombre}")
async def provincia_detalle(nombre: str):
    """Detalle de una provincia."""
    data = _load_csv("prevalencia_provincias.csv")
    match = [p for p in data if p["provincia"].lower() == nombre.lower()]
    if not match:
        raise HTTPException(404, f"Provincia '{nombre}' no encontrada")
    return match[0]


@router.get("/evolucion")
async def evolucion_historica():
    """Evolución histórica del CUD 2018–2023."""
    data = _load_csv("evolucion_cud.csv")
    if not data:
        from scripts.etl_estadistico import construir_df_evolucion
        data = construir_df_evolucion().to_dict("records")
    return {"fuente": "ANDIS", "series": data}


@router.get("/tipos")
async def tipos_discapacidad():
    """Distribución de CUD por tipo de discapacidad."""
    data = _load_csv("cud_por_tipo.csv")
    if not data:
        from scripts.etl_estadistico import construir_df_tipos
        data = construir_df_tipos().to_dict("records")
    return {"total": sum(d["cantidad"] for d in data), "tipos": data}


@router.get("/caba/comunas")
async def caba_comunas():
    """CUD por comuna de CABA."""
    data = _load_csv("caba_por_comuna.csv")
    if not data:
        from scripts.etl_estadistico import construir_df_caba
        data = construir_df_caba().to_dict("records")
    return {
        "total_caba":    163_114,
        "porcentaje_ar": 9.7,
        "comunas":       data,
        "fuente":        "COPIDIS — Gobierno de CABA",
    }


@router.get("/mapa/provincias")
async def mapa_provincias():
    """GeoJSON de provincias con datos de prevalencia para mapa coroplético."""
    geo  = _load_json("georef_provincias.geojson")
    prov = {p["provincia"]: p for p in _load_csv("prevalencia_provincias.csv")}

    if geo and "features" in geo:
        for feat in geo["features"]:
            nombre = feat.get("properties", {}).get("nombre", "")
            if nombre in prov:
                feat["properties"].update(prov[nombre])
    return geo if geo else {"error": "GeoJSON no disponible — correr ETL primero"}


@router.get("/mapa/caba")
async def mapa_caba():
    """GeoJSON de comunas de CABA con datos de CUD."""
    geo   = _load_json("georef_comunas_caba.geojson")
    caba  = {str(c["comuna"]): c for c in _load_csv("caba_por_comuna.csv")}

    if geo and "features" in geo:
        for feat in geo["features"]:
            nombre = feat.get("properties", {}).get("nombre", "")
            num    = nombre.replace("Comuna ", "").strip()
            if num in caba:
                feat["properties"].update(caba[num])
    return geo if geo else {"error": "GeoJSON no disponible — correr ETL primero"}
