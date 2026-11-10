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
    df = pd.read_csv(path)
    # NaN no es JSON-serializable -> lo convertimos a None antes de exportar.
    df = df.astype(object).where(pd.notna(df), None)
    return df.to_dict("records")


def _load_json(nombre: str) -> dict:
    path = RAW_DIR / nombre
    if not path.exists():
        # Auto-reparación en runtime: si el GeoJSON no vino en el deploy
        # (p. ej. falló el ETL durante el build de Railway), lo descargamos
        # y cacheamos acá mismo en el primer pedido, en vez de devolver
        # {"error": ...} para siempre.
        try:
            if nombre == "georef_comunas_caba.geojson":
                from scripts.etl_estadistico import descargar_georef_comunas
                data = descargar_georef_comunas()
                if data:
                    return data
            elif nombre == "georef_provincias.geojson":
                from scripts.etl_estadistico import descargar_georef_provincias
                data = descargar_georef_provincias()
                if data:
                    return data
        except Exception:
            pass
        return {}
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    return json.loads(text)


def _andis() -> dict:
    """Informe oficial leído por scripts/scraper_andis.py, más el dato reciente y las aclaraciones."""
    return json.loads((PROC_DIR / "andis_oficial.json").read_text(encoding="utf-8"))


def _fuente_oficial(d: dict) -> dict:
    o = d["oficial"]
    return {"fuente": o["fuente"], "fuente_url": o["fuente_pagina"], "fuente_pdf": o["fuente_pdf"],
            "fecha_datos": o["fecha_corte"], "fecha_lectura": d.get("fecha_lectura")}


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/resumen")
async def resumen_nacional():
    """KPIs nacionales del Observatorio."""
    d = _andis()
    o = d["oficial"]
    prov = max(o["por_provincia"].items(), key=lambda kv: kv[1])[0]
    tipo = max(o["por_tipo"].items(), key=lambda kv: kv[1])[0]
    return {
        "total_cud_vigentes":   o["total_cud_vigentes"],
        "porcentaje_poblacion": o["porcentaje_poblacion"],
        "provincia_mayor":      prov,
        "tipo_mas_frecuente":   tipo,
        "total_provincias":     len(o["por_provincia"]),
        **_fuente_oficial(d),
        "dato_reciente":        d.get("dato_reciente"),
        "no_oficiales":         d.get("no_oficiales", []),
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
    return {"total": len(data), "orden": orden, "provincias": data, **_fuente_oficial(_andis()),
            "nota": "La tasa es un cálculo propio sobre la población estimada 2022 (INDEC)."}


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
    """Totales nacionales con fuente (no hay serie anual oficial publicada)."""
    data = _load_csv("evolucion_cud.csv")
    if not data:
        from scripts.etl_estadistico import construir_df_evolucion
        data = construir_df_evolucion().to_dict("records")
    return {"fuente": "ANDIS y dato informado al Congreso", "series": data}


@router.get("/tipos")
async def tipos_discapacidad():
    """Distribución de CUD por tipo de discapacidad."""
    data = _load_csv("cud_por_tipo.csv")
    if not data:
        from scripts.etl_estadistico import construir_df_tipos
        data = construir_df_tipos().to_dict("records")
    return {"total": sum(d["cantidad"] for d in data), "tipos": data, **_fuente_oficial(_andis())}


@router.get("/caba/comunas")
async def caba_comunas():
    """CUD por comuna de CABA."""
    data = _load_csv("caba_por_comuna.csv")
    if not data:
        from scripts.etl_estadistico import construir_df_caba
        data = construir_df_caba().to_dict("records")
    return {
        "total_caba":    _andis()["oficial"]["por_provincia"]["CABA"],
        "comunas":       data,
        "oficial":       False,
        "fuente":        "Estimación propia por comuna (no oficial); el total de CABA es del informe oficial de ANDIS",
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
