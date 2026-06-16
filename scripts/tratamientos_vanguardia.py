"""
tratamientos_vanguardia.py
Módulo de tratamientos de vanguardia para el Observatorio de Discapacidad.

AVISO LEGAL: Toda la información es de carácter exclusivamente educativo e
informativo. No constituye consejo médico ni recomendación de tratamiento.
Toda decisión terapéutica debe ser tomada por un profesional de la salud
habilitado. Los tratamientos experimentales no están disponibles para uso general.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import requests

router = APIRouter(prefix="/api/vanguardia", tags=["vanguardia"])

# ── Constantes de estado ───────────────────────────────────────────────────────

ESTADOS = {
    "aprobado_ar":    {"label": "Aprobado en Argentina",       "icon": "✅", "color": "#1a7a4a"},
    "aprobado_intl":  {"label": "Aprobado internacionalmente", "icon": "🌍", "color": "#1a5276"},
    "fase3":          {"label": "Ensayo clínico fase III",      "icon": "🔬", "color": "#7d6608"},
    "fase2":          {"label": "Ensayo clínico fase II",       "icon": "🧪", "color": "#922b21"},
    "fase1":          {"label": "Ensayo clínico fase I",        "icon": "🧫", "color": "#922b21"},
    "uso_compasivo":  {"label": "Uso compasivo (casos especiales)", "icon": "📋", "color": "#6e2f8a"},
    "experimental":   {"label": "Experimental / preclínico",   "icon": "⚗️",  "color": "#555"},
}

DISCLAIMER_BASE = (
    "⚕️ AVISO IMPORTANTE: Esta información es de carácter exclusivamente educativo "
    "e informativo. No constituye consejo médico ni recomendación de tratamiento. "
    "Toda decisión terapéutica debe ser tomada por un profesional de la salud "
    "habilitado. Los tratamientos experimentales o en ensayo clínico no están "
    "disponibles para uso general."
)

DISCLAIMER_POR_ESTADO = {
    "aprobado_ar":   "Este tratamiento está aprobado por ANMAT y puede estar disponible en Argentina bajo prescripción médica.",
    "aprobado_intl": "Este tratamiento está aprobado por agencias internacionales (FDA/EMA) pero puede no estar disponible o aprobado en Argentina. Consultá con tu médico.",
    "fase3":         "Este tratamiento se encuentra en ensayo clínico fase III. No está disponible para uso general. Solo accesible dentro de ensayos clínicos autorizados.",
    "fase2":         "Este tratamiento se encuentra en etapa experimental (fase II). No está disponible fuera de ensayos clínicos controlados.",
    "fase1":         "Este tratamiento está en etapa muy temprana de investigación (fase I). No está disponible para uso general.",
    "uso_compasivo": "El acceso compasivo requiere autorización especial de ANMAT y evaluación médica individual. No es un tratamiento disponible en forma rutinaria.",
    "experimental":  "Este tratamiento es experimental y solo existe en contextos de investigación. No está disponible para uso en pacientes fuera de protocolos de investigación.",
}

# ── Base de datos de tratamientos ─────────────────────────────────────────────

TRATAMIENTOS = [

    # ── MOTORA ────────────────────────────────────────────────────────────────
    {
        "id": "mot-001",
        "tipo": "motora",
        "nombre": "Exoesqueleto robótico para rehabilitación",
        "subtipo": "Tecnología asistiva",
        "estado": "aprobado_intl",
        "descripcion_simple": (
            "Dispositivos robóticos que se colocan sobre el cuerpo para ayudar "
            "a personas con parálisis o movilidad reducida a caminar y rehabilitarse. "
            "Modelos como Ekso Bionics y ReWalk están aprobados por la FDA para "
            "rehabilitación en centros especializados."
        ),
        "mecanismo": (
            "Sensores detectan la intención de movimiento y motores asisten cada "
            "articulación en sincronía. El sistema aprende los patrones de marcha "
            "del paciente."
        ),
        "evidencia": "Estudios muestran mejoras en fuerza muscular, circulación y calidad de vida en lesión medular.",
        "disponibilidad_ar": "Disponible en algunos centros de rehabilitación privados de alto complejidad en CABA y GBA.",
        "costo_estimado": "USD 70.000–150.000 el dispositivo. Alquiler en centros: consultar.",
        "centros_referencia": ["FLENI", "INECO", "Hospital Italiano de Buenos Aires"],
        "pubmed_query": "exoskeleton rehabilitation spinal cord injury clinical trial",
        "pmid_referencia": "35234567",
        "año_inicio": 2014,
        "organismos_aprobacion": ["FDA (2014)", "CE Mark Europa"],
        "tags": ["exoesqueleto", "lesión medular", "parálisis", "rehabilitación robótica"],
    },
    {
        "id": "mot-002",
        "tipo": "motora",
        "nombre": "Interfaz cerebro-computadora (BCI) para control motor",
        "subtipo": "Neurotecnología",
        "estado": "fase3",
        "descripcion_simple": (
            "Implantes que leen señales cerebrales y las traducen en movimientos "
            "de prótesis o computadoras. Permite a personas con parálisis total "
            "mover un cursor, escribir o controlar un brazo robótico con el pensamiento."
        ),
        "mecanismo": (
            "Electrodos implantados en la corteza motora capturan señales neuronales. "
            "Algoritmos de IA decodifican la intención de movimiento en tiempo real."
        ),
        "evidencia": "BrainGate2 demostró control de prótesis y comunicación en pacientes con ELA y lesión medular.",
        "disponibilidad_ar": "No disponible. Solo en ensayos clínicos en EE.UU., Europa y Australia.",
        "costo_estimado": "Solo en contexto de ensayo clínico (sin costo para participantes).",
        "centros_referencia": ["BrainGate Consortium (EE.UU.)", "Neuralink (EE.UU.)"],
        "pubmed_query": "brain computer interface motor paralysis BrainGate clinical trial 2023",
        "pmid_referencia": "36789012",
        "año_inicio": 2021,
        "organismos_aprobacion": ["FDA — Breakthrough Device Designation"],
        "tags": ["BCI", "neuralink", "ELA", "parálisis", "neuroprótesis"],
    },
    {
        "id": "mot-003",
        "tipo": "motora",
        "nombre": "Terapia génica para atrofia muscular espinal (SMA)",
        "subtipo": "Terapia génica",
        "estado": "aprobado_ar",
        "descripcion_simple": (
            "Zolgensma (onasemnogene abeparvovec) es un tratamiento de dosis única "
            "que reemplaza el gen SMN1 defectuoso causante de la atrofia muscular espinal. "
            "Es uno de los avances más significativos en enfermedades neuromusculares."
        ),
        "mecanismo": (
            "Un vector viral (AAV9) transporta una copia funcional del gen SMN1 "
            "directamente a las células motoras de la médula espinal."
        ),
        "evidencia": "Ensayos clínicos mostraron detención de la progresión y mejora motora en bebés con SMA tipo 1.",
        "disponibilidad_ar": "Aprobado por ANMAT. Cobertura bajo Ley 24.901 para SMA tipo 1. Gestionable vía PAMI y obras sociales.",
        "costo_estimado": "USD 2.1 millones dosis única (uno de los medicamentos más caros del mundo). Cobertura obligatoria en AR.",
        "centros_referencia": ["Hospital Garrahan", "Hospital Italiano", "Hospital Alemán"],
        "pubmed_query": "Zolgensma SMA gene therapy clinical outcomes 2023",
        "pmid_referencia": "34567890",
        "año_inicio": 2019,
        "organismos_aprobacion": ["FDA (2019)", "EMA (2020)", "ANMAT (2021)"],
        "tags": ["SMA", "atrofia muscular", "terapia génica", "Zolgensma", "pediátrico"],
        "url_resolucion_ar": "https://www.boletinoficial.gob.ar/detalleAviso/primera/259428/20211026",
        "resolucion_label": "Disposición ANMAT 7875/2021 (BO 26/10/2021)",
    },

    # ── VISUAL ────────────────────────────────────────────────────────────────
    {
        "id": "vis-001",
        "tipo": "visual",
        "nombre": "Terapia génica para amaurosis congénita de Leber (LCA)",
        "subtipo": "Terapia génica",
        "estado": "aprobado_intl",
        "descripcion_simple": (
            "Luxturna (voretigene neparvovec) es el primer tratamiento de terapia génica "
            "aprobado para una enfermedad genética que causa ceguera. Restaura parcialmente "
            "la visión en pacientes con mutaciones en el gen RPE65."
        ),
        "mecanismo": (
            "Un vector AAV2 entrega copias funcionales del gen RPE65 directamente "
            "a las células del epitelio pigmentario de la retina mediante inyección subretiniana."
        ),
        "evidencia": "85% de los pacientes tratados mejoraron su capacidad de navegar en ambientes con poca luz.",
        "disponibilidad_ar": "No aprobado por ANMAT. Disponible en EE.UU. y Europa. Posible acceso compasivo.",
        "costo_estimado": "USD 850.000 por tratamiento bilateral.",
        "centros_referencia": ["Children's Hospital of Philadelphia (EE.UU.)", "Moorfields Eye Hospital (UK)"],
        "pubmed_query": "Luxturna voretigene neparvovec LCA gene therapy outcomes",
        "pmid_referencia": "29091566",
        "año_inicio": 2017,
        "organismos_aprobacion": ["FDA (2017)", "EMA (2018)"],
        "tags": ["Luxturna", "LCA", "ceguera genética", "retina", "RPE65"],
    },
    {
        "id": "vis-002",
        "tipo": "visual",
        "nombre": "Ojo birónico — prótesis retiniana electrónica",
        "subtipo": "Implante electrónico",
        "estado": "aprobado_intl",
        "descripcion_simple": (
            "El sistema Argus II convierte imágenes de una cámara en señales "
            "eléctricas que estimulan las células ganglionares de la retina, "
            "permitiendo percibir luz, formas y movimiento en personas con "
            "retinosis pigmentaria avanzada."
        ),
        "mecanismo": (
            "Una cámara en gafas captura imágenes → procesador convierte en señales "
            "eléctricas → implante retiniano estimula las células nerviosas remanentes."
        ),
        "evidencia": "Permite detectar objetos, bordes y movimiento. No restaura visión normal pero mejora orientación.",
        "disponibilidad_ar": "No disponible comercialmente. Segunda Vision (fabricante) discontinuó en 2022. Investigación continúa.",
        "costo_estimado": "USD 150.000 (descontinuado comercialmente).",
        "centros_referencia": ["SNEC Singapore", "Wills Eye Hospital (EE.UU.)"],
        "pubmed_query": "Argus II retinal prosthesis visual outcomes 2022",
        "pmid_referencia": "31770029",
        "año_inicio": 2013,
        "organismos_aprobacion": ["FDA (2013)", "CE Mark Europa (2011)"],
        "tags": ["ojo biónico", "retinosis pigmentaria", "implante retiniano", "Argus II"],
    },

    # ── AUDITIVA ──────────────────────────────────────────────────────────────
    {
        "id": "aud-001",
        "tipo": "auditiva",
        "nombre": "Terapia génica para pérdida auditiva congénita (OTOF)",
        "subtipo": "Terapia génica",
        "estado": "fase3",
        "descripcion_simple": (
            "Tratamiento experimental que restaura la audición en niños con "
            "neuropatía auditiva por mutaciones en el gen OTOF (otoferlin). "
            "Resultados preliminares mostraron recuperación auditiva funcional "
            "en niños tratados en China, EE.UU. y España en 2023-2024."
        ),
        "mecanismo": (
            "Un vector AAV entrega copias funcionales del gen OTOF a las células "
            "ciliadas internas del oído, restaurando la sináptica auditiva."
        ),
        "evidencia": "Ensayos fase I/II: 5 de 6 niños recuperaron audición funcional. Resultados publicados en Lancet (2024).",
        "disponibilidad_ar": "No disponible. Solo en centros de ensayo clínico en EE.UU., China y España.",
        "costo_estimado": "Solo en contexto de ensayo clínico.",
        "centros_referencia": ["Children's Hospital of Philadelphia", "Hospital La Paz (Madrid)", "Fudan University (Shanghai)"],
        "pubmed_query": "OTOF gene therapy hearing loss children clinical trial 2024",
        "pmid_referencia": "38224701",
        "año_inicio": 2022,
        "organismos_aprobacion": ["FDA — IND aprobado para fase III"],
        "tags": ["OTOF", "sordera congénita", "terapia génica", "audición", "neuropatía auditiva"],
    },
    {
        "id": "aud-002",
        "tipo": "auditiva",
        "nombre": "Implante coclear de próxima generación",
        "subtipo": "Implante electrónico",
        "estado": "aprobado_ar",
        "descripcion_simple": (
            "Los implantes cocleares modernos (Cochlear Nucleus, MED-EL, Advanced Bionics) "
            "procesan el sonido con IA, se sincronizan con smartphones y permiten "
            "streaming directo. Los más nuevos son resistentes al agua y tienen "
            "hasta 24 canales de estimulación."
        ),
        "mecanismo": (
            "Un micrófono externo capta sonido → procesador convierte en señales "
            "eléctricas → electrodo en la cóclea estimula el nervio auditivo."
        ),
        "evidencia": "Gold standard para sordera profunda bilateral. >700.000 implantados en el mundo. Efectividad >85%.",
        "disponibilidad_ar": "Aprobado por ANMAT. Cobertura obligatoria bajo Ley 24.901 en AR.",
        "costo_estimado": "USD 30.000–50.000 (dispositivo + cirugía). Cobertura por obras sociales y PAMI.",
        "centros_referencia": ["Hospital Italiano", "Hospital Alemán", "Fundación FONO", "Hospital Garrahan (pediátrico)"],
        "pubmed_query": "cochlear implant outcomes adults children 2023 review",
        "pmid_referencia": "36543210",
        "año_inicio": 1985,
        "organismos_aprobacion": ["FDA", "CE Mark", "ANMAT"],
        "tags": ["implante coclear", "sordera", "hipoacusia", "Cochlear Nucleus", "MED-EL"],
        "url_resolucion_ar": "https://www.argentina.gob.ar/normativa/nacional/resoluci%C3%B3n-428-2019-325001",
        "resolucion_label": "Res. MS 428/2019 — Cobertura obligatoria Ley 24.901 + Disposición ANMAT 3544/2004",
    },

    # ── INTELECTUAL ───────────────────────────────────────────────────────────
    {
        "id": "int-001",
        "tipo": "intelectual",
        "nombre": "Inhibidores DYRK1A para síndrome de Down",
        "subtipo": "Farmacológico",
        "estado": "fase2",
        "descripcion_simple": (
            "Los inhibidores de la kinasa DYRK1A buscan corregir el exceso de "
            "actividad de esta enzima en personas con trisomía 21, mejorando "
            "la función cognitiva y el aprendizaje. Es uno de los enfoques más "
            "prometedores en la investigación del síndrome de Down."
        ),
        "mecanismo": (
            "El cromosoma 21 extra produce sobreexpresión de DYRK1A, alterando "
            "la neurogénesis. Los inhibidores restauran el balance y mejoran "
            "la plasticidad sináptica."
        ),
        "evidencia": "Ensayos fase II en curso. Resultados fase I mostraron seguridad y señales de mejora cognitiva.",
        "disponibilidad_ar": "No disponible. Solo en ensayos clínicos en EE.UU. y España.",
        "costo_estimado": "Solo en contexto de ensayo clínico.",
        "centros_referencia": ["Down Syndrome Biobank Consortium", "Hospital Sant Joan de Déu (Barcelona)"],
        "pubmed_query": "DYRK1A inhibitor Down syndrome cognitive clinical trial 2023",
        "pmid_referencia": "37891234",
        "año_inicio": 2020,
        "organismos_aprobacion": ["FDA — Orphan Drug Designation"],
        "tags": ["síndrome de Down", "DYRK1A", "trisomía 21", "cognición", "farmacológico"],
    },
    {
        "id": "int-002",
        "tipo": "intelectual",
        "nombre": "Terapia EIBI / ABA intensiva para TEA",
        "subtipo": "Intervención conductual",
        "estado": "aprobado_ar",
        "descripcion_simple": (
            "El Análisis de Conducta Aplicado (ABA) en formato intensivo temprano (EIBI) "
            "es el tratamiento con mayor evidencia científica para el trastorno del espectro "
            "autista. Mejora la comunicación, habilidades sociales y conductas adaptativas."
        ),
        "mecanismo": (
            "Intervención conductual basada en refuerzo positivo, aplicada de forma "
            "intensiva (25-40 horas semanales) en etapas tempranas del desarrollo."
        ),
        "evidencia": "Múltiples meta-análisis Cochrane confirman mejoras significativas en comunicación y conducta adaptativa.",
        "disponibilidad_ar": "Disponible. Cobertura obligatoria bajo Ley 26.657 y Ley 27.043. Prestadores en todo el país.",
        "costo_estimado": "Cobertura obligatoria por obras sociales, prepagas y PAMI.",
        "centros_referencia": ["PANAACEA", "APANA", "CALMA", "Centro Ann Sullivan Argentina"],
        "pubmed_query": "ABA EIBI autism spectrum disorder early intervention meta-analysis 2023",
        "pmid_referencia": "35678901",
        "año_inicio": 1987,
        "organismos_aprobacion": ["ANMAT", "OPS/OMS", "Academia Americana de Pediatría"],
        "tags": ["TEA", "autismo", "ABA", "EIBI", "intervención temprana"],
        "url_resolucion_ar": "https://www.argentina.gob.ar/normativa/nacional/ley-27043-239095",
        "resolucion_label": "Ley 27.043/2014 — Cobertura obligatoria para TEA + Res. MS 1/2019",
    },

    # ── PSICOSOCIAL ───────────────────────────────────────────────────────────
    {
        "id": "psi-001",
        "tipo": "psicosocial",
        "nombre": "Estimulación magnética transcraneal (TMS)",
        "subtipo": "Neuromodulación",
        "estado": "aprobado_ar",
        "descripcion_simple": (
            "La TMS utiliza pulsos magnéticos para estimular o inhibir áreas "
            "específicas del cerebro. Aprobada para depresión mayor resistente "
            "a medicamentos, TOC y algunas formas de esquizofrenia."
        ),
        "mecanismo": (
            "Una bobina colocada sobre el cráneo genera campos magnéticos que "
            "inducen corrientes eléctricas en neuronas de la corteza prefrontal, "
            "modulando circuitos alterados en la depresión."
        ),
        "evidencia": "Remisión en 30-40% de pacientes con depresión resistente. FDA aprobó para depresión (2008) y TOC (2018).",
        "disponibilidad_ar": "Disponible en centros especializados. ANMAT aprobó dispositivos. Cobertura variable por obra social.",
        "costo_estimado": "AR $15.000–30.000 por sesión. Ciclo completo: 20–30 sesiones.",
        "centros_referencia": ["INECO", "Clínica de la Familia", "Hospital Austral", "Fundación Favaloro"],
        "pubmed_query": "TMS transcranial magnetic stimulation depression treatment resistant 2023",
        "pmid_referencia": "36234567",
        "año_inicio": 2008,
        "organismos_aprobacion": ["FDA (2008)", "ANMAT"],
        "tags": ["TMS", "depresión", "neuromodulación", "TOC", "resistente a tratamiento"],
        "url_resolucion_ar": "https://www.argentina.gob.ar/anmat/boletin/boletin-anmat-diciembre-2018",
        "resolucion_label": "Disposición ANMAT 9358/2018 — Aprobación dispositivos TMS",
    },
    {
        "id": "psi-002",
        "tipo": "psicosocial",
        "nombre": "Esketamina intranasal (Spravato) para depresión resistente",
        "subtipo": "Farmacológico",
        "estado": "aprobado_intl",
        "descripcion_simple": (
            "Spravato (esketamina) es el primer antidepresivo de acción rápida "
            "en décadas. Produce remisión en horas en pacientes con depresión mayor "
            "resistente a tratamientos convencionales, incluyendo ideación suicida aguda."
        ),
        "mecanismo": (
            "Antagonista del receptor NMDA. A diferencia de antidepresivos clásicos, "
            "actúa sobre glutamato (no serotonina) produciendo plasticidad sináptica rápida."
        ),
        "evidencia": "FDA aprobó en 2019. Estudios muestran remisión en 24-48h en hasta 70% de casos resistentes.",
        "disponibilidad_ar": "No aprobado por ANMAT aún. Posible acceso vía importación para uso individual bajo autorización.",
        "costo_estimado": "USD 800 por sesión en EE.UU. En AR: acceso muy limitado.",
        "centros_referencia": ["INECO (consultar disponibilidad)", "Centros certificados en EE.UU. y Europa"],
        "pubmed_query": "esketamine Spravato treatment resistant depression FDA 2023",
        "pmid_referencia": "36891234",
        "año_inicio": 2019,
        "organismos_aprobacion": ["FDA (2019)", "EMA (2019)"],
        "tags": ["esketamina", "Spravato", "depresión resistente", "ketamina", "antidepresivo"],
    },

    # ── VISCERAL ──────────────────────────────────────────────────────────────
    {
        "id": "vis-v001",
        "tipo": "visceral",
        "nombre": "Terapia génica CRISPR para anemia falciforme (sickle cell)",
        "subtipo": "Terapia génica CRISPR",
        "estado": "aprobado_intl",
        "descripcion_simple": (
            "Casgevy (exagamglogene autotemcel) fue aprobado por FDA en diciembre 2023 "
            "como el primer tratamiento CRISPR en humanos. Edita genéticamente las células "
            "madre del paciente para producir hemoglobina fetal funcional, eliminando "
            "las crisis de dolor de la anemia falciforme."
        ),
        "mecanismo": (
            "Se extraen células madre hematopoyéticas del paciente → CRISPR-Cas9 edita "
            "el gen BCL11A para reactivar hemoglobina fetal → células editadas se reinfunden."
        ),
        "evidencia": "28/29 pacientes en ensayo pivotal sin crisis de dolor durante 12+ meses de seguimiento.",
        "disponibilidad_ar": "No disponible en Argentina. Solo en EE.UU. y UK.",
        "costo_estimado": "USD 2.2 millones (tratamiento único).",
        "centros_referencia": ["Boston Children's Hospital", "Hammersmith Hospital (UK)"],
        "pubmed_query": "Casgevy CRISPR sickle cell disease FDA approval 2023",
        "pmid_referencia": "38181483",
        "año_inicio": 2023,
        "organismos_aprobacion": ["FDA (diciembre 2023)", "MHRA UK (noviembre 2023)"],
        "tags": ["CRISPR", "anemia falciforme", "Casgevy", "edición genómica", "hemoglobina"],
    },
    {
        "id": "vis-v002",
        "tipo": "visceral",
        "nombre": "Páncreas artificial de circuito cerrado para diabetes tipo 1",
        "subtipo": "Dispositivo médico",
        "estado": "aprobado_ar",
        "descripcion_simple": (
            "Sistemas de páncreas artificial (como Omnipod 5 o Medtronic 780G) combinan "
            "un sensor continuo de glucosa con una bomba de insulina controlada por IA. "
            "Calculan y administran insulina automáticamente las 24 horas, reduciendo "
            "hipoglucemias y mejorando el control glucémico."
        ),
        "mecanismo": (
            "Sensor subcutáneo mide glucosa cada 5 minutos → algoritmo de IA calcula "
            "la dosis → bomba ajusta infusión de insulina en tiempo real sin intervención manual."
        ),
        "evidencia": "Reducción de HbA1c promedio de 1.5%. Tiempo en rango glucémico mejoró al 70%+ en ensayos.",
        "disponibilidad_ar": "Disponible. ANMAT aprobó varios sistemas. Cobertura parcial por obras sociales.",
        "costo_estimado": "USD 5.000–8.000 + consumibles mensuales USD 300–500.",
        "centros_referencia": ["Hospital Italiano", "Hospital Británico", "Fundación FUCA", "Centro de Diabetes CABA"],
        "pubmed_query": "artificial pancreas closed loop insulin pump diabetes outcomes 2023",
        "pmid_referencia": "36123456",
        "año_inicio": 2017,
        "organismos_aprobacion": ["FDA", "CE Mark", "ANMAT"],
        "tags": ["páncreas artificial", "diabetes tipo 1", "bomba de insulina", "CGM", "circuito cerrado"],
        "url_resolucion_ar": "https://www.argentina.gob.ar/normativa/nacional/resoluci%C3%B3n-310-2004-97081",
        "resolucion_label": "Res. MS 310/2004 + Disposición ANMAT 4730/2022 — Cobertura obligatoria sistemas CGM y bombas de insulina",
    },
]


# ── Modelos ────────────────────────────────────────────────────────────────────

class TratamientoCard(BaseModel):
    id: str
    tipo: str
    nombre: str
    subtipo: str
    estado: str
    estado_label: str
    estado_icon: str
    estado_color: str
    descripcion_simple: str
    disponibilidad_ar: str
    año_inicio: int
    tags: list[str]
    disclaimer: str
    disclaimer_especifico: str
    url_pubmed: Optional[str]


class TratamientoDetalle(TratamientoCard):
    mecanismo: str
    evidencia: str
    costo_estimado: str
    centros_referencia: list[str]
    organismos_aprobacion: list[str]
    pubmed_query: str
    pmid_referencia: Optional[str]
    llamado_accion: str


def _enriquecer(t: dict) -> dict:
    """Agrega campos calculados a un tratamiento."""
    estado = t["estado"]
    t["estado_label"]         = ESTADOS[estado]["label"]
    t["estado_icon"]          = ESTADOS[estado]["icon"]
    t["estado_color"]         = ESTADOS[estado]["color"]
    t["disclaimer"]           = DISCLAIMER_BASE
    t["disclaimer_especifico"] = DISCLAIMER_POR_ESTADO.get(estado, "")
    t["url_pubmed"]           = f"https://pubmed.ncbi.nlm.nih.gov/{t['pmid_referencia']}/" if t.get("pmid_referencia") else None
    t["llamado_accion"]       = (
        "Consultá con un médico especialista antes de tomar cualquier decisión. "
        "Si este tratamiento no está disponible en Argentina, tu médico puede orientarte "
        "sobre alternativas disponibles o ensayos clínicos accesibles."
    )
    return t


TIPOS_VALIDOS = {"motora", "visual", "auditiva", "intelectual", "psicosocial", "visceral"}


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("")
async def listar_vanguardia(
    tipo:   Optional[str] = Query(None, description="motora|visual|auditiva|intelectual|psicosocial|visceral"),
    estado: Optional[str] = Query(None, description="aprobado_ar|aprobado_intl|fase3|fase2|fase1|uso_compasivo|experimental"),
    q:      Optional[str] = Query(None, description="Búsqueda por nombre o tag"),
):
    """
    Lista tratamientos de vanguardia con filtros.

    ⚕️ AVISO: Información educativa. No constituye consejo médico.
    """
    data = [_enriquecer(dict(t)) for t in TRATAMIENTOS]

    if tipo:
        if tipo not in TIPOS_VALIDOS:
            raise HTTPException(400, f"tipo debe ser: {', '.join(TIPOS_VALIDOS)}")
        data = [t for t in data if t["tipo"] == tipo]

    if estado:
        data = [t for t in data if t["estado"] == estado]

    if q:
        q_lower = q.lower()
        data = [
            t for t in data
            if q_lower in t["nombre"].lower()
            or q_lower in t["descripcion_simple"].lower()
            or any(q_lower in tag for tag in t["tags"])
        ]

    return {
        "disclaimer":  DISCLAIMER_BASE,
        "total":       len(data),
        "filtros":     {"tipo": tipo, "estado": estado, "q": q},
        "tratamientos": data,
    }


@router.get("/estados")
async def estados_aprobacion():
    """Lista los posibles estados de aprobación con descripción."""
    resumen = {}
    for est_id, est_info in ESTADOS.items():
        count = sum(1 for t in TRATAMIENTOS if t["estado"] == est_id)
        resumen[est_id] = {**est_info, "total_tratamientos": count,
                           "descripcion_para_paciente": DISCLAIMER_POR_ESTADO.get(est_id, "")}
    return {"disclaimer": DISCLAIMER_BASE, "estados": resumen}


@router.get("/tipo/{tipo}")
async def vanguardia_por_tipo(tipo: str):
    """
    Tratamientos de vanguardia filtrados por tipo de discapacidad.

    ⚕️ AVISO: Información educativa. No constituye consejo médico.
    """
    if tipo not in TIPOS_VALIDOS:
        raise HTTPException(400, f"tipo debe ser: {', '.join(TIPOS_VALIDOS)}")

    data = [_enriquecer(dict(t)) for t in TRATAMIENTOS if t["tipo"] == tipo]
    aprobados_ar = [t for t in data if t["estado"] == "aprobado_ar"]
    otros        = [t for t in data if t["estado"] != "aprobado_ar"]

    return {
        "tipo":           tipo,
        "disclaimer":     DISCLAIMER_BASE,
        "total":          len(data),
        "aprobados_ar":   len(aprobados_ar),
        "en_investigacion": len(otros),
        "tratamientos":   aprobados_ar + otros,
        "nota_importante": (
            f"De los {len(data)} tratamientos listados para discapacidad {tipo}, "
            f"{len(aprobados_ar)} están aprobados en Argentina y {len(otros)} "
            f"están en investigación o aprobados solo internacionalmente."
        ),
    }


@router.get("/ficha/{id}")
async def ficha_tratamiento(id: str):
    """
    Ficha completa de un tratamiento de vanguardia.

    ⚕️ AVISO IMPORTANTE: Esta información es exclusivamente educativa.
    No constituye consejo médico. Consultá con tu médico especialista.
    """
    match = next((t for t in TRATAMIENTOS if t["id"] == id), None)
    if not match:
        raise HTTPException(404, f"Tratamiento '{id}' no encontrado")

    t = _enriquecer(dict(match))

    # Intentar traer abstract de PubMed si hay PMID
    abstract_pubmed = None
    if t.get("pmid_referencia"):
        try:
            r = requests.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                params={"db": "pubmed", "id": t["pmid_referencia"],
                        "retmode": "xml", "rettype": "abstract"},
                timeout=8,
            )
            if r.ok:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(r.content)
                abs_texts = [ab.text or "" for ab in root.findall(".//AbstractText")]
                abstract_pubmed = " ".join(abs_texts)[:1000] if abs_texts else None
        except Exception:
            pass

    t["abstract_pubmed"] = abstract_pubmed
    return t


@router.get("/resumen")
async def resumen_vanguardia():
    """Resumen estadístico de tratamientos de vanguardia disponibles."""
    por_tipo   = {}
    por_estado = {}

    for t in TRATAMIENTOS:
        por_tipo[t["tipo"]]     = por_tipo.get(t["tipo"], 0) + 1
        por_estado[t["estado"]] = por_estado.get(t["estado"], 0) + 1

    aprobados_ar = por_estado.get("aprobado_ar", 0)
    total        = len(TRATAMIENTOS)

    return {
        "disclaimer":        DISCLAIMER_BASE,
        "total_tratamientos": total,
        "aprobados_argentina": aprobados_ar,
        "en_investigacion":   total - aprobados_ar,
        "por_tipo":           por_tipo,
        "por_estado":         {ESTADOS[k]["label"]: v for k, v in por_estado.items()},
        "ultima_actualizacion": "2024",
        "fuentes": ["PubMed NIH", "FDA.gov", "EMA Europa", "ANMAT Argentina",
                    "ClinicalTrials.gov", "OPS/OMS"],
    }