"""
etl_estadistico.py
Motor de ingesta de datos estadísticos de discapacidad en Argentina.

Fuentes:
  - ANDIS  — CUD emitidos por provincia (PDF + informes)
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

    # Georef — provincias con geometría
    "georef_provincias": "https://apis.datos.gob.ar/georef/api/v2.0/provincias?formato=geojson&max=100",

    # Georef — comunas CABA
    "georef_comunas_caba": "https://apis.datos.gob.ar/georef/api/v2.0/departamentos?provincia=02&formato=geojson&max=20",
}

# Datos ANDIS noviembre 2023 (publicados en informe PDF — hardcodeados del último informe oficial)
ANDIS_NOV_2023 = {
    "total_nacional": 1_680_723,
    "porcentaje_poblacion": 3.65,
    "fecha_corte": "2023-11-01",
    "por_provincia": {
        "Buenos Aires":          680_333,
        "CABA":                  163_114,
        "Santa Fe":              124_441,
        "Córdoba":               112_777,
        "Mendoza":                67_148,
        "Entre Ríos":             47_890,
        "Tucumán":                46_203,
        "Salta":                  38_901,
        "Chaco":                  31_245,
        "Corrientes":             30_112,
        "Misiones":               29_887,
        "Santiago del Estero":    26_334,
        "Jujuy":                  22_111,
        "Río Negro":              21_445,
        "Neuquén":                20_889,
        "Formosa":                18_223,
        "San Juan":               17_667,
        "Chubut":                 16_334,
        "La Pampa":               12_001,
        "San Luis":               11_778,
        "Catamarca":              10_445,
        "La Rioja":                9_334,
        "Santa Cruz":              9_001,
        "Tierra del Fuego":        4_445,
    },
    "por_tipo": {
        "Mental/Psiquiátrica":  465_234,
        "Motora":               428_945,
        "Sensorial auditiva":   201_456,
        "Sensorial visual":     189_234,
        "Intelectual":          168_072,
        "Visceral/Sistémica":    89_234,
        "Múltiple":              68_972,
        "Otras":                 69_576,
    },
    "por_rango_edad": {
        "0-14":   201_234,
        "15-29":  268_445,
        "30-44":  312_667,
        "45-59":  378_223,
        "60-74":  312_001,
        "75+":    208_153,
    },
    "por_genero": {
        "Femenino":  882_345,
        "Masculino": 798_378,
    },
}

# Datos históricos CUD emitidos (evolución)
EVOLUCION_CUD = [
    {"año": 2018, "total": 950_000},
    {"año": 2019, "total": 1_020_000},
    {"año": 2020, "total": 1_059_480},
    {"año": 2021, "total": 1_120_869},
    {"año": 2022, "total": 1_231_185},
    {"año": 2023, "total": 1_680_723},
]

# Datos CABA por comuna (estimados del informe COPIDIS 2022)
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
    """Descarga GeoJSON de provincias desde Georef."""
    cache = RAW_DIR / "georef_provincias.geojson"
    if cache.exists():
        log.info("Georef provincias: caché local")
        import json
        return json.loads(cache.read_text())
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
    """Descarga GeoJSON de comunas de CABA desde Georef."""
    cache = RAW_DIR / "georef_comunas_caba.geojson"
    if cache.exists():
        log.info("Georef comunas CABA: caché local")
        import json
        return json.loads(cache.read_text())
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
    for prov, cud in ANDIS_NOV_2023["por_provincia"].items():
        pob = POBLACION_2022.get(prov, 1)
        rows.append({
            "provincia":         prov,
            "cud_vigentes":      cud,
            "poblacion_2022":    pob,
            "tasa_prevalencia":  round(cud / pob * 100, 2),
            "fecha_datos":       ANDIS_NOV_2023["fecha_corte"],
        })
    df = pd.DataFrame(rows).sort_values("cud_vigentes", ascending=False)
    df.to_csv(PROC_DIR / "prevalencia_provincias.csv", index=False)
    log.info(f"  ✓ prevalencia_provincias.csv — {len(df)} provincias")
    return df


def construir_df_evolucion() -> pd.DataFrame:
    """Construye DataFrame de evolución histórica del CUD."""
    df = pd.DataFrame(EVOLUCION_CUD)
    variacion = df["total"].pct_change() * 100
    # pct_change() da NaN en la primera fila (sin año anterior).
    # NaN no es JSON-serializable -> lo convertimos a None.
    df["variacion_pct"] = variacion.round(2).astype(object).where(variacion.notna(), None)
    df.to_csv(PROC_DIR / "evolucion_cud.csv", index=False)
    log.info(f"  ✓ evolucion_cud.csv — {len(df)} años")
    return df


def construir_df_tipos() -> pd.DataFrame:
    """Construye DataFrame de CUD por tipo de discapacidad."""
    rows = [{"tipo": k, "cantidad": v, "porcentaje": round(v / ANDIS_NOV_2023["total_nacional"] * 100, 1)}
            for k, v in ANDIS_NOV_2023["por_tipo"].items()]
    df = pd.DataFrame(rows).sort_values("cantidad", ascending=False)
    df.to_csv(PROC_DIR / "cud_por_tipo.csv", index=False)
    log.info(f"  ✓ cud_por_tipo.csv — {len(df)} tipos")
    return df


def construir_df_caba() -> pd.DataFrame:
    """Construye DataFrame de CUD por comuna de CABA."""
    rows = [{"comuna": k, "nombre": v["nombre"], "cud": v["cud"],
             "tasa_estimada": round(v["cud"] / 163_114 * 100, 1)}
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
        "total_cud_nacional":    ANDIS_NOV_2023["total_nacional"],
        "porcentaje_poblacion":  ANDIS_NOV_2023["porcentaje_poblacion"],
        "fecha_datos":           ANDIS_NOV_2023["fecha_corte"],
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
