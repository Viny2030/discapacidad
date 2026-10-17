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
        "pmid_referencia": "27042146",
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
        "pmid_referencia": "22596161",
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
        "pmid_referencia": "29091557",
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
        "pmid_referencia": "28712537",
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
        "pmid_referencia": "22244176",
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
        "pmid_referencia": "38280389",
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
        "pmid_referencia": "42525886",
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
        "pmid_referencia": "39422950",
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
        "pmid_referencia": "29742275",
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
        "pmid_referencia": "34711062",
        "año_inicio": 2008,
        "organismos_aprobacion": ["FDA (2008)", "ANMAT"],
        "tags": ["TMS", "depresión", "neuromodulación", "TOC", "resistente a tratamiento"],
        "url_resolucion_ar": "https://www.argentina.gob.ar/anmat",  # FIX: el boletín anterior daba 404
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
        "pmid_referencia": "31109201",
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
        "pmid_referencia": "38661449",
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
        "pmid_referencia": "31618560",
        "año_inicio": 2017,
        "organismos_aprobacion": ["FDA", "CE Mark", "ANMAT"],
        "tags": ["páncreas artificial", "diabetes tipo 1", "bomba de insulina", "CGM", "circuito cerrado"],
        "url_resolucion_ar": "https://www.argentina.gob.ar/normativa/nacional/resoluci%C3%B3n-310-2004-97081",
        "resolucion_label": "Res. MS 310/2004 + Disposición ANMAT 4730/2022 — Cobertura obligatoria sistemas CGM y bombas de insulina",
    },

    # ── Agregados 2026-10 (PMID verificados contra PubMed) ───────────────────
    {
        "id": "mot-004",
        "tipo": "motora",
        "nombre": "Estimulación eléctrica no invasiva de la médula espinal (lesión medular)",
        "subtipo": "Neuromodulación",
        "estado": "aprobado_intl",
        "descripcion_simple": (
            "Electrodos colocados sobre la piel de la nuca envían pulsos eléctricos "
            "programados a la médula espinal mientras la persona hace rehabilitación. "
            "En diciembre de 2024 la FDA autorizó el primer sistema de este tipo (ARC-EX) "
            "para mejorar la fuerza y la función de las manos en lesión medular cervical "
            "crónica e incompleta. La versión implantada para volver a caminar sigue en ensayos."
        ),
        "mecanismo": (
            "La estimulación transcutánea aumenta la excitabilidad de los circuitos "
            "medulares por debajo de la lesión, de modo que las pocas señales que todavía "
            "llegan desde el cerebro alcanzan a activar los músculos."
        ),
        "evidencia": "Ensayo Up-LIFT (Nature Medicine, 2024): 72% de los participantes mejoró la fuerza o la función de brazos y manos.",
        "disponibilidad_ar": "No disponible de forma habitual en Argentina. Aprobado en EE. UU.",
        "costo_estimado": "Sin precio de referencia en Argentina.",
        "centros_referencia": ["ONWARD Medical (Suiza/Países Bajos)", "Centros del ensayo Up-LIFT (EE. UU., Canadá, Europa)"],
        "pubmed_query": "transcutaneous spinal cord stimulation tetraplegia upper extremity",
        "ct_query": "transcutaneous spinal cord stimulation",
        "pmid_referencia": "38769431",
        "año_inicio": 2024,
        "organismos_aprobacion": ["FDA (De Novo, diciembre 2024)"],
        "tags": ["lesión medular", "tetraplejia", "neuromodulación", "estimulación espinal", "ARC-EX"],
    },
    {
        "id": "mot-005",
        "tipo": "motora",
        "nombre": "Terapia génica para distrofia muscular de Duchenne (Elevidys)",
        "subtipo": "Terapia génica",
        "estado": "aprobado_intl",
        "descripcion_simple": (
            "Una única infusión aporta una versión acortada del gen de la distrofina "
            "(microdistrofina) a los músculos. La FDA la aprobó en 2023; en noviembre de "
            "2025 agregó una advertencia de recuadro negro por daño hepático grave, con "
            "muertes en pacientes que ya no caminaban, y limitó su uso a niños de 4 años o "
            "más que todavía caminan."
        ),
        "mecanismo": (
            "Un virus adenoasociado (AAV) modificado lleva el gen de la microdistrofina a "
            "las fibras musculares, que empiezan a producir una proteína funcional parcial."
        ),
        "evidencia": "El ensayo fase 3 EMBARK no alcanzó su objetivo principal; los datos a dos años en pacientes que caminan muestran señales funcionales. Requiere controles hepáticos semanales por al menos tres meses.",
        "disponibilidad_ar": "No aprobado en Argentina. Requiere evaluación de un centro especializado en enfermedades neuromusculares.",
        "costo_estimado": "Alrededor de USD 3,2 millones por dosis única en EE. UU.",
        "centros_referencia": ["FLENI", "Hospital de Pediatría Garrahan (neuromuscular)"],
        "pubmed_query": "delandistrogene moxeparvovec Duchenne muscular dystrophy",
        "ct_query": "Duchenne muscular dystrophy gene therapy",
        "pmid_referencia": "41518520",
        "año_inicio": 2023,
        "organismos_aprobacion": ["FDA (2023; advertencia de recuadro negro y uso limitado, nov. 2025)"],
        "tags": ["Duchenne", "distrofia muscular", "terapia génica", "microdistrofina"],
    },
    {
        "id": "vis-003",
        "tipo": "visual",
        "nombre": "Optogenética para retinosis pigmentaria",
        "subtipo": "Terapia génica + dispositivo",
        "estado": "fase1",
        "descripcion_simple": (
            "Se usa terapia génica para que células de la retina que sobreviven se vuelvan "
            "sensibles a la luz, y unos anteojos especiales proyectan las imágenes con la "
            "longitud de onda adecuada. En 2021 se publicó el primer paciente ciego que "
            "recuperó parte de la visión (reconocer y tocar objetos)."
        ),
        "mecanismo": (
            "Un virus adenoasociado introduce una proteína sensible a la luz (ChrimsonR) "
            "en las células ganglionares de la retina; las gafas convierten la imagen en "
            "pulsos de luz ámbar que esas células pueden captar."
        ),
        "evidencia": "Caso inicial del ensayo PIONEER (Nature Medicine, 2021). Ensayo de fase I/II en curso.",
        "disponibilidad_ar": "No disponible. Solo en ensayos clínicos en Europa y EE. UU.",
        "costo_estimado": "Solo en contexto de ensayo clínico.",
        "centros_referencia": ["Institut de la Vision (París)", "GenSight Biologics"],
        "pubmed_query": "optogenetic therapy retinitis pigmentosa vision",
        "ct_query": "optogenetic retinitis pigmentosa",
        "pmid_referencia": "34031601",
        "año_inicio": 2021,
        "organismos_aprobacion": [],
        "tags": ["optogenética", "retinosis pigmentaria", "ceguera", "terapia génica"],
    },
    {
        "id": "int-003",
        "tipo": "intelectual",
        "nombre": "Trofinetida para síndrome de Rett",
        "subtipo": "Fármaco",
        "estado": "aprobado_intl",
        "descripcion_simple": (
            "Primer medicamento aprobado específicamente para el síndrome de Rett (FDA, "
            "marzo de 2023), para personas de 2 años o más. Se toma por boca dos veces al "
            "día y busca mejorar la comunicación, la conducta y el uso de las manos."
        ),
        "mecanismo": (
            "Es un análogo sintético de un fragmento del factor de crecimiento IGF-1; "
            "reduce la neuroinflamación y favorece la función de las sinapsis."
        ),
        "evidencia": "Ensayo fase 3 LAVENDER (Nature Medicine, 2023), 187 niñas y jóvenes de 5 a 20 años. Efectos adversos frecuentes: diarrea y vómitos.",
        "disponibilidad_ar": "No aprobado en Argentina. Podría gestionarse por importación con autorización de ANMAT.",
        "costo_estimado": "Alto costo; sin precio de referencia en Argentina.",
        "centros_referencia": ["Hospital de Pediatría Garrahan (neurología)", "FLENI"],
        "pubmed_query": "trofinetide Rett syndrome",
        "ct_query": "Rett syndrome",
        "pmid_referencia": "37291210",
        "año_inicio": 2023,
        "organismos_aprobacion": ["FDA (marzo 2023)"],
        "tags": ["Rett", "síndrome de Rett", "trofinetida", "enfermedad poco frecuente"],
    },
    {
        "id": "psi-003",
        "tipo": "psicosocial",
        "nombre": "Psilocibina asistida por psicoterapia para depresión resistente",
        "subtipo": "Fármaco + psicoterapia",
        "estado": "fase3",
        "descripcion_simple": (
            "Una o dos dosis de psilocibina sintética, administradas en un entorno clínico "
            "controlado y con acompañamiento de profesionales. Dos ensayos de fase 3 (2025 y "
            "2026) mostraron mejoría frente a placebo en depresión resistente. Todavía no "
            "está aprobada por la FDA ni por ANMAT."
        ),
        "mecanismo": (
            "Actúa sobre los receptores de serotonina 5-HT2A y aumentaría la plasticidad "
            "cerebral durante unas semanas, lo que potenciaría el trabajo psicoterapéutico."
        ),
        "evidencia": "Ensayo fase 2b (NEJM, 2022) y dos fases 3 con resultado positivo según el fabricante, aún sin publicación revisada por pares.",
        "disponibilidad_ar": "No disponible. Su uso fuera de un ensayo clínico es ilegal y riesgoso.",
        "costo_estimado": "Solo en contexto de ensayo clínico.",
        "centros_referencia": ["Compass Pathways (ensayos COMP005 y COMP006)"],
        "pubmed_query": "psilocybin treatment-resistant depression randomized",
        "ct_query": "psilocybin depression",
        "pmid_referencia": "36322843",
        "año_inicio": 2022,
        "organismos_aprobacion": ["FDA — Breakthrough Therapy Designation"],
        "tags": ["psilocibina", "depresión resistente", "psicodélicos", "salud mental"],
    },
    {
        "id": "vis-v003",
        "tipo": "visceral",
        "nombre": "Teplizumab para retrasar la diabetes tipo 1",
        "subtipo": "Inmunoterapia",
        "estado": "aprobado_intl",
        "descripcion_simple": (
            "Anticuerpo que se aplica por vía intravenosa durante 14 días y puede retrasar "
            "unos años la aparición de la diabetes tipo 1 clínica (etapa 3) en personas de "
            "8 años o más que ya tienen autoanticuerpos y alteraciones de la glucosa (etapa 2). "
            "La FDA lo aprobó en noviembre de 2022."
        ),
        "mecanismo": (
            "Se une a la molécula CD3 de los linfocitos T y frena el ataque autoinmune "
            "contra las células del páncreas que producen insulina."
        ),
        "evidencia": "Ensayo TN-10 (NEJM, 2019): retrasó en una mediana de unos dos años el diagnóstico de diabetes tipo 1 en familiares en riesgo.",
        "disponibilidad_ar": "Sin aprobación de ANMAT confirmada. Consultar con un/a endocrinólogo/a.",
        "costo_estimado": "Alto costo en EE. UU.; sin precio de referencia en Argentina.",
        "centros_referencia": ["TrialNet (red internacional de prevención de diabetes tipo 1)"],
        "pubmed_query": "teplizumab type 1 diabetes delay",
        "ct_query": "teplizumab",
        "pmid_referencia": "31180194",
        "año_inicio": 2022,
        "organismos_aprobacion": ["FDA (noviembre 2022)"],
        "tags": ["diabetes tipo 1", "teplizumab", "prevención", "inmunoterapia"],
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
def ficha_tratamiento(id: str):
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
        "ultima_actualizacion": "2026-10",
        "fuentes": ["PubMed NIH", "FDA.gov", "EMA Europa", "ANMAT Argentina",
                    "ClinicalTrials.gov", "OPS/OMS"],
    }

# ── Evidencia en vivo (PubMed + ClinicalTrials.gov) ───────────────────────────
# Para cada tratamiento consulta las bases en el momento: los artículos más
# recientes de PubMed (NIH) y los ensayos clínicos que reclutan en
# ClinicalTrials.gov, con el título original y su traducción al español (texto
# chico en la página). Caché en memoria de 6 h para no agotar las cuotas.

try:
    from scripts.etl_medico import traducir_resumen as _traducir
except ImportError:
    def _traducir(texto: str, max_chars: int = 600) -> str:
        return ""

_EVIDENCIA_CACHE: dict = {}
_FASES_ES = {"EARLY_PHASE1": "Fase 1 temprana", "PHASE1": "Fase 1", "PHASE2": "Fase 2",
             "PHASE3": "Fase 3", "PHASE4": "Fase 4"}
_EVIDENCIA_TTL = 6 * 3600


def _titulo_es(titulo: str) -> str:
    """Traducción del título; vacía si el traductor solo hizo un reemplazo parcial."""
    es = _traducir(titulo, max_chars=300) if titulo else ""
    return "" if (not es or "parcial]" in es or es.strip() == titulo.strip()) else es


def _pubmed_por_ids(ids: list[str]) -> list[dict]:
    if not ids:
        return []
    res = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi", params={
        "db": "pubmed", "id": ",".join(ids), "retmode": "json",
    }, timeout=10).json().get("result", {})
    out = []
    for pmid in ids:
        a = res.get(pmid, {})
        titulo = a.get("title", "")
        out.append({
            "pmid": pmid,
            "titulo": titulo,
            "titulo_es": _titulo_es(titulo),
            "revista": a.get("source", ""),
            "fecha": a.get("pubdate", ""),
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        })
    return out


def _pubmed_recientes(query: str, n: int = 3) -> list[dict]:
    ids = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", params={
        "db": "pubmed", "term": query, "retmax": n, "sort": "pub_date", "retmode": "json",
    }, timeout=10).json().get("esearchresult", {}).get("idlist", [])
    return _pubmed_por_ids(ids)


def _ensayos_reclutando(query: str, n: int = 4) -> tuple[list[dict], int]:
    r = requests.get("https://clinicaltrials.gov/api/v2/studies", params={
        "query.term": query,
        "filter.overallStatus": "RECRUITING,NOT_YET_RECRUITING",
        "pageSize": n,
        "countTotal": "true",
        "fields": "NCTId,BriefTitle,OverallStatus,Phase,LocationCountry",
    }, timeout=12)
    r.raise_for_status()
    j = r.json()
    out = []
    for s in j.get("studies", []):
        p = s.get("protocolSection", {})
        nct = p.get("identificationModule", {}).get("nctId", "")
        titulo = p.get("identificationModule", {}).get("briefTitle", "")
        paises = sorted({l.get("country", "") for l in p.get("contactsLocationsModule", {}).get("locations", []) if l.get("country")})
        out.append({
            "nct_id": nct,
            "titulo": titulo,
            "titulo_es": _titulo_es(titulo),
            "estado": p.get("statusModule", {}).get("overallStatus", ""),
            "fase": ", ".join(_FASES_ES.get(f, f) for f in (p.get("designModule", {}).get("phases", []) or []) if f != "NA"),
            "en_argentina": "Argentina" in paises,
            "paises": paises[:6],
            "url": f"https://clinicaltrials.gov/study/{nct}",
        })
    return out, j.get("totalCount", len(out))


@router.get("/evidencia/{id}")
def evidencia_en_vivo(id: str):
    """
    Evidencia actualizada de un tratamiento de vanguardia, consultada en vivo:
    artículos recientes de PubMed y ensayos que reclutan en ClinicalTrials.gov,
    con el título original y su traducción al español.

    ⚕️ AVISO: Información educativa. No constituye consejo médico.
    """
    import re
    import time

    match = next((t for t in TRATAMIENTOS if t["id"] == id), None)
    if not match:
        raise HTTPException(404, f"Tratamiento '{id}' no encontrado")

    cache = _EVIDENCIA_CACHE.get(id)
    if cache and time.time() - cache[0] < _EVIDENCIA_TTL:
        return cache[1]

    pm_query = match["pubmed_query"]
    ct_query = match.get("ct_query") or re.sub(r"\b(19|20)\d{2}\b", "", pm_query).strip()

    errores = []
    try:
        ref = _pubmed_por_ids([match["pmid_referencia"]]) if match.get("pmid_referencia") else []
        articulos = [a for a in _pubmed_recientes(pm_query) if a["pmid"] != match.get("pmid_referencia")]
    except Exception:
        ref, articulos, errores = [], [], errores + ["PubMed no respondió"]
    try:
        ensayos, total_ensayos = _ensayos_reclutando(ct_query)
    except Exception:
        ensayos, total_ensayos, errores = [], 0, errores + ["ClinicalTrials.gov no respondió"]

    data = {
        "id": id,
        "nombre": match["nombre"],
        "disclaimer": DISCLAIMER_BASE,
        "fuentes": ["PubMed (NIH, EE. UU.)", "ClinicalTrials.gov (NIH, EE. UU.)"],
        "articulo_referencia": ref[0] if ref else None,
        "articulos_recientes": articulos,
        "ensayos_reclutando": ensayos,
        "total_ensayos_reclutando": total_ensayos,
        "url_busqueda_pubmed": "https://pubmed.ncbi.nlm.nih.gov/?term=" + requests.utils.quote(pm_query),
        "url_busqueda_ensayos": "https://clinicaltrials.gov/search?term=" + requests.utils.quote(ct_query),
        "errores": errores,
        "nota": (
            "Datos consultados en vivo en bases científicas internacionales. Los títulos "
            "traducidos son automáticos y orientativos. Participar en un ensayo requiere "
            "la evaluación de tu médico/a y del equipo del estudio."
        ),
    }
    if not errores:
        _EVIDENCIA_CACHE[id] = (time.time(), data)
    return data
