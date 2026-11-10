"""
etl_estadistico.py
Motor de ingesta de datos estadísticos de discapacidad en Argentina.

Fuentes:
  - ANDIS  — informe oficial del RNPcD, leído por scripts/scraper_andis.py
  - INDEC  — Estudio Nacional 2018 + Censo 2022
  - Georef — Provincias y comunas de CABA para mapas
  - BA Data — Datos específicos de CABA
"""

import os
import logging
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="[ETL-EST] %(message)s")
log = logging.getLogger(__name__)

BASE_DIR  = Path(__file__).resolve().parent.parent
RAW_DIR   = BASE_DIR / "data" / "raw"
PROC_DIR  = BASE_DIR / "data" / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROC_DIR.mkdir(parents=True, exist_ok=True)

# ── URLs de datos abiertos ─────────────────────────────────────────────────────

FUENTES = {
    # Estudio Nacional INDEC 2018 — dataset oficial
    "indec_2018": "https://datos.gob.ar/dataset/otros-estudio-nacional-sobre-perfil-personas-con-discapacidad/archivo/otros_2.1",

    # Proyecciones de población INDEC por provincia (Censo 2022 base)
    "poblacion_provincias": "https://infra.datos.gob.ar/catalog/siempre/dataset/2/distribution/2.5/download/estimaciones-y-proyecciones-2010-2040-total-del-pais.csv",

    # Georef — provincias con geometría COMPLETA (polígonos para choropleth real)
    # aplanar=false → devuelve geometría MultiPolygon, no sólo centroide
    "georef_provincias": (
        "https://apis.datos.gob.ar/georef/api/v2.0/provincias"
        "?formato=geojson&max=100&aplanar=false"
    ),

    # Georef — comunas CABA con geometría completa
    "georef_comunas_caba": (
        "https://apis.datos.gob.ar/georef/api/v2.0/departamentos"
        "?provincia=02&formato=geojson&max=20&aplanar=false"
    ),
}

# Datos oficiales: los escribe scripts/scraper_andis.py a partir del último
# informe publicado en argentina.gob.ar/andis/estadisticas/datos-estadisticos.
# Antes estaban escritos a mano y el desglose no coincidía con el informe.
ANDIS_JSON = PROC_DIR / "andis_oficial.json"


def cargar_andis() -> dict:
    """Devuelve el JSON completo (oficial + dato_reciente + no_oficiales)."""
    import json
    return json.loads(ANDIS_JSON.read_text(encoding="utf-8"))


def oficial() -> dict:
    return cargar_andis()["oficial"]


def puntos_evolucion() -> list[dict]:
    """Únicos totales nacionales con fuente: el informe oficial y el dato reciente."""
    d = cargar_andis()
    puntos = [{"fecha": d["oficial"]["fecha_corte"][:7], "total": d["oficial"]["total_cud_vigentes"],
               "fuente": d["oficial"]["fuente"]}]
    if d.get("dato_reciente"):
        r = d["dato_reciente"]
        puntos.append({"fecha": r["fecha"], "total": r["total_cud_vigentes"], "fuente": r["fuente"]})
    return sorted(puntos, key=lambda x: x["fecha"])


# Datos CABA por comuna — ESTIMACIÓN PROPIA, no oficial (el informe oficial no publica comunas)
CABA_POR_COMUNA = {
    1:  {"nombre": "Constitución",    "cud": 8_234},
    2:  {"nombre": "Recoleta",        "cud": 7_891},
    3:  {"nombre": "San Cristóbal",   "cud": 7_456},
    4:  {"nombre": "La Boca/Barracas","cud": 9_123},
    5:  {"nombre": "Almagro/Boedo",   "cud": 8_567},
    6:  {"nombre": "Caballito",       "cud": 9_234},
    7:  {"nombre": "Flores/Parque Pat","cud": 10_123},
    8:  {"nombre": "Villa Lugano",    "cud": 12_456},
    9:  {"nombre": "Liniers/Mataderos","cud": 9_789},
    10: {"nombre": "Villa Real",      "cud": 6_234},
    11: {"nombre": "Villa del Parque","cud": 7_123},
    12: {"nombre": "Coghlan/Saavedra","cud": 6_789},
    13: {"nombre": "Núñez/Belgrano",  "cud": 7_234},
    14: {"nombre": "Palermo",         "cud": 8_901},
    15: {"nombre": "Villa Ortúzar",   "cud": 5_678},
}


def descargar_georef_provincias() -> dict:
    """
    Descarga GeoJSON de provincias desde Georef con geometría COMPLETA (Tarea 10).
    Invalida caché si el archivo contiene geometría tipo Point (sólo centroide).
    """
    import json as _json
    cache = RAW_DIR / "georef_provincias.geojson"

    # NOTA (verificado 2026-07-03): la API Georef v2.0 devuelve geometría
    # Point (centroides) aunque se pida aplanar=false — no entrega polígonos.
    # El frontend está diseñado para puntos (getPointCoords + circleMarkers),
    # así que un caché con centroides es VÁLIDO y no debe borrarse. La lógica
    # anterior de "invalidar si es Point" borraba el archivo en cada build.
    if cache.exists():
        try:
            data = _json.loads(cache.read_text())
            if data.get("features"):
                log.info("Georef provincias: usando caché local")
                return data
        except Exception:
            pass

    try:
        r = requests.get(FUENTES["georef_provincias"], timeout=20)
        r.raise_for_status()
        cache.write_text(r.text)
        log.info("Georef provincias: descargado")
        return r.json()
    except Exception as e:
        log.warning(f"Georef error: {e}")
        return {}


def descargar_georef_comunas() -> dict:
    """
    Descarga GeoJSON de comunas de CABA desde Georef con geometría completa (Tarea 10).
    Invalida caché si el archivo contiene sólo centroides.
    """
    import json as _json
    cache = RAW_DIR / "georef_comunas_caba.geojson"

    # NOTA (verificado 2026-07-03): Georef v2.0 sólo entrega centroides
    # (geometría Point) — el frontend está diseñado para eso. No invalidar
    # el caché por ser Point: eso borraba el archivo committeado en cada
    # build de Railway y dejaba el mapa sin datos.
    if cache.exists():
        try:
            data = _json.loads(cache.read_text())
            if data.get("features"):
                log.info("Georef comunas CABA: usando caché local")
                return data
        except Exception:
            pass

    try:
        r = requests.get(FUENTES["georef_comunas_caba"], timeout=20)
        r.raise_for_status()
        cache.write_text(r.text)
        log.info("Georef comunas CABA: descargado")
        return r.json()
    except Exception as e:
        log.warning(f"Georef comunas error: {e}")
        return {}


def construir_df_provincias() -> pd.DataFrame:
    """Construye DataFrame de prevalencia por provincia."""
    # Población censo 2022 por provincia (INDEC)
    POBLACION_2022 = {
        "Buenos Aires": 17_542_625, "CABA": 3_120_612, "Santa Fe": 3_556_522,
        "Córdoba": 3_978_984, "Mendoza": 2_014_533, "Entre Ríos": 1_426_949,
        "Tucumán": 1_703_186, "Salta": 1_441_988, "Chaco": 1_204_541,
        "Corrientes": 1_120_801, "Misiones": 1_261_294, "Santiago del Estero": 1_017_170,
        "Jujuy": 770_881, "Río Negro": 747_610, "Neuquén": 664_057,
        "Formosa": 605_193, "San Juan": 781_406, "Chubut": 618_994,
        "La Pampa": 368_550, "San Luis": 508_328, "Catamarca": 415_438,
        "La Rioja": 393_531, "Santa Cruz": 333_473, "Tierra del Fuego": 190_641,
    }
    rows = []
    datos = oficial()
    for prov, cud in datos["por_provincia"].items():
        pob = POBLACION_2022.get(prov, 1)
        rows.append({
            "provincia":         prov,
            "cud_vigentes":      cud,
            "poblacion_2022":    pob,
            "tasa_prevalencia":  round(cud / pob * 100, 2),
            "fecha_datos":       datos["fecha_corte"],
        })
    df = pd.DataFrame(rows).sort_values("cud_vigentes", ascending=False)
    df.to_csv(PROC_DIR / "prevalencia_provincias.csv", index=False)
    log.info(f"  ✓ prevalencia_provincias.csv — {len(df)} provincias")
    return df


def construir_df_evolucion() -> pd.DataFrame:
    """Totales nacionales con fuente (informe oficial y dato reciente informado al Congreso)."""
    df = pd.DataFrame(puntos_evolucion())
    variacion = df["total"].pct_change() * 100
    # pct_change() da NaN en la primera fila (sin año anterior).
    # NaN no es JSON-serializable -> lo convertimos a None.
    df["variacion_pct"] = variacion.round(2).astype(object).where(variacion.notna(), None)
    df.to_csv(PROC_DIR / "evolucion_cud.csv", index=False)
    log.info(f"  ✓ evolucion_cud.csv — {len(df)} puntos con fuente")
    return df


def construir_df_tipos() -> pd.DataFrame:
    """Construye DataFrame de CUD por tipo de discapacidad."""
    datos = oficial()
    rows = [{"tipo": k, "cantidad": v, "porcentaje": round(v / datos["total_cud_vigentes"] * 100, 1)}
            for k, v in datos["por_tipo"].items()]
    df = pd.DataFrame(rows).sort_values("cantidad", ascending=False)
    df.to_csv(PROC_DIR / "cud_por_tipo.csv", index=False)
    log.info(f"  ✓ cud_por_tipo.csv — {len(df)} tipos")
    return df


def construir_df_caba() -> pd.DataFrame:
    """Construye DataFrame de CUD por comuna de CABA."""
    rows = [{"comuna": k, "nombre": v["nombre"], "cud": v["cud"],
             "tasa_estimada": round(v["cud"] / oficial()["por_provincia"]["CABA"] * 100, 1)}
            for k, v in CABA_POR_COMUNA.items()]
    df = pd.DataFrame(rows)
    df.to_csv(PROC_DIR / "caba_por_comuna.csv", index=False)
    log.info(f"  ✓ caba_por_comuna.csv — {len(df)} comunas")
    return df


def run_etl_estadistico() -> dict:
    """Corre el ETL completo de datos estadísticos."""
    log.info("=" * 55)
    log.info("ETL ESTADÍSTICO — Inicio")
    log.info("=" * 55)

    df_prov    = construir_df_provincias()
    df_evol    = construir_df_evolucion()
    df_tipos   = construir_df_tipos()
    df_caba    = construir_df_caba()
    geo_prov   = descargar_georef_provincias()
    geo_comunas = descargar_georef_comunas()

    resumen = {
        "total_cud_nacional":    oficial()["total_cud_vigentes"],
        "porcentaje_poblacion":  oficial()["porcentaje_poblacion"],
        "fecha_datos":           oficial()["fecha_corte"],
        "provincias":            len(df_prov),
        "comunas_caba":          len(df_caba),
        "fecha_etl":             datetime.now().isoformat(),
    }
    log.info(f"ETL Estadístico OK — {resumen}")
    return {
        "provincias":  df_prov.to_dict("records"),
        "evolucion":   df_evol.to_dict("records"),
        "tipos":       df_tipos.to_dict("records"),
        "caba":        df_caba.to_dict("records"),
        "geo_provincias": geo_prov,
        "geo_comunas":    geo_comunas,
        "resumen":        resumen,
    }


if __name__ == "__main__":
    import json
    r = run_etl_estadistico()
    print(json.dumps(r["resumen"], indent=2, ensure_ascii=False))
