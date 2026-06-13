"""
api_cud.py
Endpoints FastAPI — Módulo Trámite CUD.
Toda la información proviene de fuentes oficiales ANDIS / argentina.gob.ar
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from .datos_cud import (
    FORMULARIOS, REQUISITOS_GENERALES, REQUISITOS_POR_TIPO,
    PASOS_TRAMITE, BENEFICIOS, JUNTAS_POR_PROVINCIA, FAQ,
)

router = APIRouter(prefix="/api/cud", tags=["trámite CUD"])

TIPOS_VALIDOS = {"motora", "visual", "auditiva", "intelectual", "psicosocial", "visceral"}


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("")
async def info_general():
    """Información general sobre el CUD y acceso rápido a los recursos."""
    return {
        "titulo":      "Certificado Único de Discapacidad (CUD)",
        "descripcion": (
            "El CUD es un documento público gratuito que certifica la discapacidad "
            "y permite acceder a derechos y prestaciones del Estado argentino."
        ),
        "normativa_principal": ["Ley 22.431", "Ley 24.901", "Resolución ANDIS 322/2023"],
        "gratuito":            True,
        "tramite_presencial":  True,
        "turno_requerido":     True,
        "url_oficial":         "https://www.argentina.gob.ar/andis",
        "url_turno":           "https://www.argentina.gob.ar/tramites/sacar-turno-cud",
        "telefono_andis":      "0800-333-ANDIS",
        "endpoints": {
            "formularios":   "/api/cud/formularios",
            "requisitos":    "/api/cud/requisitos",
            "pasos":         "/api/cud/pasos",
            "beneficios":    "/api/cud/beneficios",
            "juntas":        "/api/cud/juntas",
            "faq":           "/api/cud/faq",
            "consulta_estado": "/api/cud/consulta-estado",
        },
    }


@router.get("/formularios")
async def formularios():
    """Formularios oficiales para descargar."""
    return {
        "total":       len(FORMULARIOS),
        "fuente":      "ANDIS — argentina.gob.ar/andis",
        "formularios": FORMULARIOS,
        "nota": "Verificá siempre en el sitio oficial que el formulario esté vigente antes de imprimirlo.",
    }


@router.get("/requisitos")
async def requisitos(
    tipo: Optional[str] = Query(None, description="motora|visual|auditiva|intelectual|psicosocial|visceral"),
):
    """
    Requisitos para tramitar el CUD.
    Sin parámetro: requisitos generales.
    Con tipo: requisitos específicos por tipo de discapacidad.
    """
    respuesta = {
        "requisitos_generales": REQUISITOS_GENERALES,
        "fuente": "ANDIS — argentina.gob.ar",
        "nota": "Los requisitos pueden variar según la provincia. Confirmá en la Junta Evaluadora de tu jurisdicción.",
    }

    if tipo:
        if tipo not in TIPOS_VALIDOS:
            raise HTTPException(400, f"tipo debe ser: {', '.join(TIPOS_VALIDOS)}")
        especificos = REQUISITOS_POR_TIPO.get(tipo)
        if especificos:
            respuesta["requisitos_especificos"] = especificos

    return respuesta


@router.get("/pasos")
async def pasos_tramite():
    """Paso a paso del trámite del CUD."""
    return {
        "total_pasos":    len(PASOS_TRAMITE),
        "duracion_total": "30 a 90 días hábiles (varía por provincia)",
        "gratuito":       True,
        "pasos":          PASOS_TRAMITE,
        "url_turno":      "https://www.argentina.gob.ar/tramites/sacar-turno-cud",
        "consulta_estado": "https://www.argentina.gob.ar/andis/consultas-publicas",
    }


@router.get("/beneficios")
async def beneficios(
    categoria: Optional[str] = Query(None, description="Salud|Transporte|Educación|Trabajo|Impuestos y económico|Vivienda"),
):
    """Beneficios y derechos que otorga el CUD."""
    data = BENEFICIOS
    if categoria:
        data = [b for b in BENEFICIOS if categoria.lower() in b["categoria"].lower()]
        if not data:
            raise HTTPException(404, f"Categoría '{categoria}' no encontrada")

    total_beneficios = sum(len(b["beneficios"]) for b in data)

    return {
        "total_categorias": len(data),
        "total_beneficios": total_beneficios,
        "categorias":       data,
        "fuente":           "Leyes 22.431, 24.901, 26.206, 24.714 y normativa complementaria",
        "nota": (
            "Los beneficios pueden variar según provincia, obra social y tipo de discapacidad. "
            "Consultá con ANDIS o con tu obra social para conocer tu situación específica."
        ),
    }


@router.get("/juntas")
async def juntas_evaluadoras(
    provincia: Optional[str] = Query(None, description="Nombre de la provincia (ej: CABA, Córdoba)"),
):
    """Juntas evaluadoras interdisciplinarias por provincia."""
    if provincia:
        match = next(
            ({"provincia": k, **v} for k, v in JUNTAS_POR_PROVINCIA.items()
             if provincia.lower() in k.lower()),
            None,
        )
        if not match:
            raise HTTPException(
                404,
                f"Provincia '{provincia}' no encontrada. Provincias disponibles: {', '.join(JUNTAS_POR_PROVINCIA.keys())}. "
                f"Para otras provincias consultá: https://www.argentina.gob.ar/andis"
            )
        return match

    return {
        "total":    len(JUNTAS_POR_PROVINCIA),
        "nota":     "Para provincias no listadas, consultá en www.argentina.gob.ar/andis o llamá al 0800 de ANDIS.",
        "url_andis": "https://www.argentina.gob.ar/andis",
        "juntas":   [{"provincia": k, **v} for k, v in JUNTAS_POR_PROVINCIA.items()],
    }


@router.get("/faq")
async def preguntas_frecuentes(
    q: Optional[str] = Query(None, description="Buscar en preguntas frecuentes"),
):
    """Preguntas frecuentes sobre el CUD."""
    data = FAQ
    if q:
        q_lower = q.lower()
        data = [
            f for f in FAQ
            if q_lower in f["pregunta"].lower() or q_lower in f["respuesta"].lower()
        ]
    return {
        "total":    len(data),
        "fuente":   "ANDIS — argentina.gob.ar/andis",
        "preguntas": data,
    }


@router.get("/consulta-estado")
async def consulta_estado():
    """Cómo consultar el estado del trámite CUD."""
    return {
        "titulo":  "Consultar estado del trámite CUD",
        "opciones": [
            {
                "canal": "Web oficial ANDIS",
                "url":   "https://www.argentina.gob.ar/andis/consultas-publicas",
                "como":  "Ingresá con tu DNI y número de trámite en el portal oficial.",
            },
            {
                "canal": "App Mi Argentina",
                "url":   "https://mi.argentina.gob.ar",
                "como":  "Descargá la app, ingresá con tu CUIL y contraseña. El CUD aparece en 'Mis documentos' cuando está listo.",
            },
            {
                "canal": "Teléfono ANDIS",
                "url":   None,
                "como":  "Llamá al 0800 de ANDIS de tu provincia con DNI y número de trámite a mano.",
            },
        ],
        "nota": (
            "El CUD digital se activa automáticamente en Mi Argentina cuando es emitido. "
            "No es necesario retirar el físico para empezar a usar los beneficios digitales."
        ),
    }


@router.get("/sube")
async def registrar_en_sube():
    """Cómo registrar el CUD en la tarjeta SUBE para transporte gratuito."""
    return {
        "titulo":      "Registrar CUD en SUBE — Transporte gratuito",
        "beneficio":   "100% de descuento en colectivos, trenes y subtes de todo el país.",
        "normativa":   "Resolución CNRT",
        "opciones": [
            {
                "canal": "Online",
                "url":   "https://www.sube.gob.ar",
                "pasos": [
                    "Ingresá a www.sube.gob.ar",
                    "Seleccioná 'Registrar tarjeta SUBE'",
                    "Completá tus datos y el número de CUD",
                    "El beneficio se activa en 48-72 horas",
                ],
            },
            {
                "canal": "Terminal SUBE",
                "url":   None,
                "pasos": [
                    "Buscá una terminal SUBE habilitada en tu ciudad",
                    "Apoyá la tarjeta y seguí las instrucciones",
                    "Seleccioná la opción 'Discapacidad'",
                    "Ingresá el número de CUD",
                ],
            },
            {
                "canal": "App SUBE",
                "url":   "https://www.sube.gob.ar/app",
                "pasos": [
                    "Descargá la app oficial SUBE",
                    "Registrá la tarjeta con tu CUIL",
                    "Seleccioná 'Tengo CUD' e ingresá el número",
                ],
            },
        ],
        "nota": "El CUD debe estar vigente para mantener el beneficio.",
    }


@router.get("/obras-sociales")
async def derechos_obras_sociales():
    """Derechos ante obras sociales y prepagas con CUD."""
    return {
        "titulo": "Derechos ante obras sociales y prepagas — Ley 24.901",
        "cobertura_obligatoria": [
            "Prestaciones médicas: 100% sin coseguro ni copago",
            "Medicamentos vinculados a la discapacidad: 100%",
            "Rehabilitación: kinesiología, fonoaudiología, terapia ocupacional, psicología",
            "Apoyo escolar y maestra integradora",
            "Estimulación temprana (0-6 años)",
            "Centro de día, hogar y residencia si se necesita",
            "Asistente personal y acompañante terapéutico",
            "Traslado a prestaciones",
            "Órtesis, prótesis y equipamiento",
        ],
        "que_hacer_si_te_niegan": [
            "Pedí el rechazo por escrito a la obra social",
            "Presentá carta documento intimando a cumplir Ley 24.901",
            "Denunciá ante la Superintendencia de Salud: 0800-222-SALUD (72583)",
            "Podés pedir una medida cautelar judicial urgente si es una necesidad inmediata",
        ],
        "superintendencia_salud": {
            "telefono": "0800-222-72583",
            "url":      "https://www.sssalud.gob.ar",
            "email":    "consultas@sssalud.gob.ar",
        },
        "normativa": ["Ley 24.901", "Ley 26.682 (prepagas)", "Resolución 428/99 MS"],
    }
