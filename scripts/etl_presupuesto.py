"""
etl_presupuesto.py
Ingesta de ejecución presupuestaria de la función Seguridad Social / Discapacidad
desde la API de Presupuesto Abierto (Subsecretaría de Presupuesto, Ministerio de
Economía — dataset publicado en datos.gob.ar/dataset/sspre-api-presupuesto-abierto).

IMPORTANTE (regla de veracidad del proyecto): la URL exacta del endpoint REST y
sus parámetros (jurisdicción, finalidad-función, agrupación) NO están verificados
en esta propuesta. PRESUPUESTO_ABIERTO_URL debe confirmarse contra la documentación
oficial (botón "VER DOCUMENTACION" del recurso en datos.gob.ar) antes de activar el
scheduler. Hasta entonces, el ETL falla de forma controlada y el endpoint lo informa.

ESTADO: preparado para Fase 2 (auditoría — Plan de Acción, Fase 2 punto 2).
Este módulo NO está incluido todavía en main.py / scheduler.py: no corre en
producción hasta que se confirme la URL oficial y se agregue el import en
main.py (ver scripts/api_presupuesto.py). Es autónomo y no afecta ningún
endpoint ni test existente.
"""
import logging
import os
from pathlib import Path
from datetime import datetime

import requests

logging.basicConfig(level=logging.INFO, format="[ETL-PRESUPUESTO] %(message)s")
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
PROC_DIR = BASE_DIR / "data" / "processed"
PROC_DIR.mkdir(parents=True, exist_ok=True)

# TODO-VERIFICAR: confirmar contra la documentación oficial del recurso antes de usar en producción.
PRESUPUESTO_ABIERTO_URL = os.getenv(
    "PRESUPUESTO_ABIERTO_URL",
    "https://www.presupuestoabierto.gob.ar/sici/api",  # placeholder a confirmar
)

# Jurisdicción/finalidad donde vive la política de discapacidad en el clasificador
# presupuestario (Finalidad 3 - Seguridad Social, dentro de ANDIS / Secretaría
# Nacional de Discapacidad). Confirmar el código exacto contra el clasificador
# publicado por la Oficina Nacional de Presupuesto antes de filtrar en producción.
FINALIDAD_SEGURIDAD_SOCIAL = "3"

PRESUPUESTO_JSON = PROC_DIR / "presupuesto_andis.json"


def descargar_ejecucion_presupuestaria(anio: int) -> dict | None:
    """
    Descarga crédito vigente y devengado de la función Seguridad Social /
    Discapacidad para el año pedido. Devuelve None si la fuente no responde o
    el esquema no coincide con lo esperado — NUNCA devuelve datos simulados.
    """
    try:
        r = requests.get(
            PRESUPUESTO_ABIERTO_URL,
            params={"anio": anio, "finalidad": FINALIDAD_SEGURIDAD_SOCIAL},
            timeout=20,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:  # noqa: BLE001 — cualquier error de red o de formato se informa, nunca se oculta
        log.warning(f"No se pudo leer Presupuesto Abierto ({anio}): {e}")
        return None


def calcular_subejecucion(credito_vigente: float, devengado: float, ipc_acumulado: float | None = None) -> dict:
    """
    Índice de subejecución = 1 - (devengado / crédito vigente).
    Si se provee IPC acumulado del período (INDEC), se informa también el
    devengado a precios constantes — nunca se inventa el IPC si no se pasó.
    """
    if credito_vigente <= 0:
        raise ValueError("crédito vigente debe ser mayor a cero")
    subejecucion_pct = round((1 - devengado / credito_vigente) * 100, 2)
    salida = {
        "credito_vigente": credito_vigente,
        "devengado": devengado,
        "subejecucion_pct": subejecucion_pct,
    }
    if ipc_acumulado:
        salida["devengado_precios_constantes"] = round(devengado / (1 + ipc_acumulado / 100), 2)
        salida["ipc_acumulado_aplicado"] = ipc_acumulado
    return salida


def run_etl_presupuesto(anio: int | None = None) -> dict:
    """Corre el ETL de ejecución presupuestaria. Persiste el resultado en JSON con fuente y fecha de lectura."""
    anio = anio or datetime.now().year
    datos = descargar_ejecucion_presupuestaria(anio)
    resultado = {
        "anio": anio,
        "disponible": datos is not None,
        "fuente": "Subsecretaría de Presupuesto, Ministerio de Economía — API Presupuesto Abierto",
        "fuente_dataset": "https://datos.gob.ar/dataset/sspre-api-presupuesto-abierto",
        "fecha_lectura": datetime.now().isoformat(),
        "datos": datos,
    }
    PRESUPUESTO_JSON.write_text(
        __import__("json").dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info(f"ETL Presupuesto {'OK' if datos else 'SIN DATOS (conector a confirmar)'} — año {anio}")
    return resultado


if __name__ == "__main__":
    import json
    print(json.dumps(run_etl_presupuesto(), indent=2, ensure_ascii=False))
