"""
api_presupuesto.py
Endpoint FastAPI de auditoría de ejecución presupuestaria (crédito vigente vs.
devengado) de la política de discapacidad.

ESTADO: preparado para Fase 2 (auditoría — Plan de Acción, Fase 2 punto 2).
Este router NO está incluido todavía en main.py: activarlo es, a propósito,
un cambio de una línea de import + una de include_router (ver abajo) que se
hace recién cuando se confirme la URL real de Presupuesto Abierto contra la
documentación oficial (ver scripts/etl_presupuesto.py). Hasta entonces este
archivo es autónomo y no afecta ningún endpoint, test ni ruta existente.

Integración futura en main.py (una vez confirmada la URL oficial):
    from scripts.api_presupuesto import router as router_presupuesto
    # ...
    app.include_router(router_presupuesto)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from scripts.etl_presupuesto import run_etl_presupuesto, calcular_subejecucion

router = APIRouter(prefix="/api/v1/auditoria", tags=["presupuesto"])

BASE_DIR = Path(__file__).resolve().parent.parent
PRESUPUESTO_JSON = BASE_DIR / "data" / "processed" / "presupuesto_andis.json"


# Validación de entrada con Pydantic / Field (cierra la brecha señalada en la
# auditoría, Sección 2: "validación Pydantic solo en la salida").
class PresupuestoQuery(BaseModel):
    anio: int = Field(ge=2016, le=2030, description="Año fiscal a auditar")
    ajustar_ipc: bool = Field(default=False, description="Expresar el devengado a precios constantes (INDEC)")


class PresupuestoOut(BaseModel):
    anio: int
    disponible: bool
    credito_vigente: Optional[float] = None
    devengado: Optional[float] = None
    subejecucion_pct: Optional[float] = None
    fuente: str
    fuente_dataset: str
    fecha_lectura: str
    nota: Optional[str] = None


@router.get("/presupuesto-andis", response_model=PresupuestoOut)
def presupuesto_andis(
    anio: int = Query(2026, ge=2016, le=2030, description="Año fiscal a auditar"),
    ajustar_ipc: bool = Query(False, description="Expresar el devengado a precios constantes"),
):
    """
    Crédito vigente vs. devengado de la función Seguridad Social / Discapacidad
    e índice de subejecución mensual. Si el conector de Presupuesto Abierto no
    está disponible, devuelve disponible=false en vez de simular cifras —
    cumple la regla de veracidad absoluta del proyecto.
    """
    try:
        cache = json.loads(PRESUPUESTO_JSON.read_text(encoding="utf-8"))
        if cache.get("anio") != anio:
            cache = run_etl_presupuesto(anio)
    except (FileNotFoundError, json.JSONDecodeError):
        cache = run_etl_presupuesto(anio)

    if not cache.get("disponible"):
        return PresupuestoOut(
            anio=anio,
            disponible=False,
            fuente=cache["fuente"],
            fuente_dataset=cache["fuente_dataset"],
            fecha_lectura=cache["fecha_lectura"],
            nota="Conector de Presupuesto Abierto aún no verificado contra la documentación oficial — ver scripts/etl_presupuesto.py",
        )

    datos = cache["datos"]
    try:
        indicadores = calcular_subejecucion(
            datos["credito_vigente"], datos["devengado"],
            datos.get("ipc_acumulado") if ajustar_ipc else None,
        )
    except (KeyError, ValueError) as e:
        raise HTTPException(502, f"Esquema de Presupuesto Abierto inesperado: {e}")

    return PresupuestoOut(
        anio=anio, disponible=True, fuente=cache["fuente"],
        fuente_dataset=cache["fuente_dataset"], fecha_lectura=cache["fecha_lectura"],
        **indicadores,
    )
