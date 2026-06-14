"""
api_cud.py
Endpoints FastAPI para el módulo CUD (Certificado Único de Discapacidad)
del Observatorio de Discapacidad.

Fuente de datos: scripts/datos_cud.py (ANDIS — argentina.gob.ar/andis,
Ley 22.431, Ley 24.901, Resolución ANDIS 322/2023).
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from scripts.datos_cud import (
    FORMULARIOS,
    REQUISITOS_GENERALES,
    REQUISITOS_POR_TIPO,
    PASOS_TRAMITE,
    BENEFICIOS,
    JUNTAS_POR_PROVINCIA,
    FAQ,
)

router = APIRouter(prefix="/api/cud", tags=["CUD"])


# ── Helpers ────────────────────────────────────────────────────────────────────

def _buscar_faq(palabra_clave: str) -> Optional[dict]:
    """Busca la primera entrada de FAQ cuya pregunta contenga la palabra clave."""
    pk = palabra_clave.lower()
    return next((f for f in FAQ if pk in f["pregunta"].lower()), None)


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("")
async def info_general():
    """Información general del trámite CUD."""
    return {
        "nombre": "Certificado Único de Discapacidad (CUD)",
        "gratuito": True,
        "vence": False,
        "normativa_vencimiento": "Resolución ANDIS 322/2023",
        "tipos_discapacidad": list(REQUISITOS_POR_TIPO.keys()),
        "total_provincias_con_junta": len(JUNTAS_POR_PROVINCIA),
        "normativa_base": ["Ley 22.431", "Ley 24.901", "Resolución ANDIS 322/2023"],
        "fuente": "ANDIS — argentina.gob.ar/andis",
        "endpoints_disponibles": [
            "/api/cud",
            "/api/cud/formularios",
            "/api/cud/requisitos",
            "/api/cud/requisitos?tipo=motora",
            "/api/cud/pasos",
            "/api/cud/beneficios",
            "/api/cud/juntas",
            "/api/cud/juntas?provincia=CABA",
            "/api/cud/faq",
            "/api/cud/faq?q=vence",
            "/api/cud/consulta-estado",
            "/api/cud/sube",
            "/api/cud/obras-sociales",
        ],
    }


@router.get("/formularios")
async def formularios():
    """Formularios oficiales para descargar (solicitud, declaración jurada, autorización a terceros)."""
    return {"total": len(FORMULARIOS), "formularios": FORMULARIOS}


@router.get("/requisitos")
async def requisitos(
    tipo: Optional[str] = Query(
        None,
        description="motora|visual|auditiva|intelectual|psicosocial|visceral",
    ),
):
    """Requisitos generales del trámite, o requisitos específicos por tipo de discapacidad."""
    if tipo:
        if tipo not in REQUISITOS_POR_TIPO:
            raise HTTPException(
                400,
                f"tipo debe ser uno de: {', '.join(REQUISITOS_POR_TIPO.keys())}",
            )
        return {"tipo": tipo, **REQUISITOS_POR_TIPO[tipo]}

    return {
        "generales": REQUISITOS_GENERALES,
        "tipos_disponibles": list(REQUISITOS_POR_TIPO.keys()),
    }


@router.get("/pasos")
async def pasos():
    """Paso a paso del trámite, desde reunir documentación hasta descargar el CUD digital."""
    return {"total": len(PASOS_TRAMITE), "pasos": PASOS_TRAMITE}


@router.get("/beneficios")
async def beneficios(
    categoria: Optional[str] = Query(
        None,
        description="Salud|Transporte|Educación|Trabajo|Impuestos y económico|Vivienda",
    ),
):
    """Beneficios del CUD, opcionalmente filtrados por categoría."""
    if categoria:
        match = next(
            (c for c in BENEFICIOS if c["categoria"].lower() == categoria.lower()),
            None,
        )
        if not match:
            categorias = ", ".join(c["categoria"] for c in BENEFICIOS)
            raise HTTPException(404, f"Categoría '{categoria}' no encontrada. Disponibles: {categorias}")
        return match

    return {"total_categorias": len(BENEFICIOS), "categorias": BENEFICIOS}


@router.get("/juntas")
async def juntas(
    provincia: Optional[str] = Query(None, description="Nombre de la provincia, ej: CABA"),
):
    """Listado de juntas evaluadoras por provincia, o el detalle de una provincia puntual."""
    if provincia:
        match = next(
            (k for k in JUNTAS_POR_PROVINCIA if k.lower() == provincia.lower()),
            None,
        )
        if not match:
            raise HTTPException(404, f"Provincia '{provincia}' no encontrada")
        return {"provincia": match, **JUNTAS_POR_PROVINCIA[match]}

    return {
        "total_provincias": len(JUNTAS_POR_PROVINCIA),
        "provincias": list(JUNTAS_POR_PROVINCIA.keys()),
    }


@router.get("/faq")
async def faq(
    q: Optional[str] = Query(None, description="Buscar por palabra clave en preguntas y respuestas"),
):
    """Preguntas frecuentes sobre el CUD, con búsqueda opcional por palabra clave."""
    if q:
        ql = q.lower()
        resultados = [
            f for f in FAQ
            if ql in f["pregunta"].lower() or ql in f["respuesta"].lower()
        ]
        return {"query": q, "total": len(resultados), "resultados": resultados}

    return {"total": len(FAQ), "preguntas": FAQ}


@router.get("/consulta-estado")
async def consulta_estado():
    """Cómo consultar el estado del trámite y si el CUD vence."""
    faq_vence = _buscar_faq("vence")
    paso_resolucion = next(
        (p for p in PASOS_TRAMITE if "Resolución" in p["titulo"] or "esolución" in p["titulo"]),
        None,
    )
    return {
        "como_consultar": "Podés consultar el estado de tu trámite en "
                          "argentina.gob.ar/andis/consultas-publicas ingresando tu DNI.",
        "url_consulta": "https://www.argentina.gob.ar/andis",
        "plazo_estimado": paso_resolucion["duracion_estimada"] if paso_resolucion else None,
        "cud_vence": False,
        "detalle_vencimiento": faq_vence["respuesta"] if faq_vence else None,
    }


@router.get("/sube")
async def sube():
    """Cómo registrar el CUD en la tarjeta SUBE para transporte gratuito."""
    transporte = next((c for c in BENEFICIOS if c["categoria"] == "Transporte"), None)
    beneficio_transporte = None
    if transporte:
        beneficio_transporte = next(
            (b for b in transporte["beneficios"] if "Transporte público" in b["nombre"]),
            transporte["beneficios"][0] if transporte["beneficios"] else None,
        )
    faq_sube = _buscar_faq("SUBE")

    return {
        "beneficio": beneficio_transporte,
        "como_registrar": faq_sube["respuesta"] if faq_sube else None,
        "url_registro": "https://www.argentina.gob.ar/servicio/registrar-certificado-unico-de-discapacidad-cud-en-la-sube",
    }


@router.get("/obras-sociales")
async def obras_sociales():
    """Derechos del CUD frente a obras sociales y prepagas (Ley 24.901)."""
    salud = next((c for c in BENEFICIOS if c["categoria"] == "Salud"), None)
    faq_os = _buscar_faq("obra social")

    return {
        "normativa": "Ley 24.901",
        "cobertura": "100% de las prestaciones de rehabilitación vinculadas a la discapacidad",
        "beneficios": salud["beneficios"] if salud else [],
        "derechos": faq_os["respuesta"] if faq_os else None,
        "denuncias": {
            "organismo": "Superintendencia de Servicios de Salud",
            "telefono": "0800-222-72583",
        },
    }