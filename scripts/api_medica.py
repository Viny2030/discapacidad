"""
api_medica.py
Endpoints FastAPI para el módulo médico del Observatorio de Discapacidad.
Se monta en el main.py principal como router.

Incluye:
  - /api/articulos        → listado con filtros
  - /api/articulos/{pmid} → detalle
  - /api/ensayos          → ClinicalTrials activos
  - /api/tratamientos     → resumen por tipo + artículos top
  - /api/buscar           → búsqueda en tiempo real vía PubMed
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
import requests
import xml.etree.ElementTree as ET
import html
import os
import json
from pathlib import Path
from datetime import datetime

# Importar traductor del ETL (Tarea 8 — para búsquedas en vivo)
try:
    from scripts.etl_medico import traducir_resumen as _traducir
except ImportError:
    def _traducir(texto: str, max_chars: int = 600) -> str:  # fallback silencioso
        return ""

router = APIRouter(prefix="/api", tags=["médico"])

PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
CT_BASE     = "https://clinicaltrials.gov/api/v2/studies"
PUBMED_KEY  = os.getenv("PUBMED_API_KEY", "")

TIPOS_VALIDOS = {"motora", "visual", "auditiva", "intelectual", "psicosocial", "visceral"}

# ── Caché ETL Médico (Tarea 11) ───────────────────────────────────────────────

_ETL_CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "etl_medico_cache.json"
_ETL_CACHE_TTL_DIAS = 15  # coincide con el scheduler

_etl_cache_mem: dict | None = None      # memoria de la sesión (se resetea al reiniciar)
_etl_cache_ts: float = 0.0              # epoch del último load


def _load_etl_cache(force: bool = False) -> dict | None:
    """
    Carga el cache JSON del ETL.
    - Primero intenta la caché en memoria (válida durante la sesión).
    - Luego lee el archivo JSON escrito por run_etl_medico().
    - Devuelve None si el archivo no existe o es más viejo que TTL.
    """
    global _etl_cache_mem, _etl_cache_ts
    import time

    if not force and _etl_cache_mem is not None:
        return _etl_cache_mem

    if not _ETL_CACHE_PATH.exists():
        return None

    try:
        data = json.loads(_ETL_CACHE_PATH.read_text(encoding="utf-8"))
        fecha_str = data.get("resumen", {}).get("fecha", "")
        if fecha_str:
            from datetime import timedelta
            edad = datetime.now() - datetime.fromisoformat(fecha_str)
            if edad.days > _ETL_CACHE_TTL_DIAS:
                return None  # expirado → que el endpoint llame a PubMed en vivo
        _etl_cache_mem = data
        _etl_cache_ts  = __import__("time").time()
        return _etl_cache_mem
    except Exception:
        return None

# ── Modelos de respuesta ───────────────────────────────────────────────────────

class ArticuloOut(BaseModel):
    pmid: Optional[str]
    titulo: str
    autores: str
    resumen: str
    resumen_es: str = ""   # Tarea 8 — traducción al español
    revista: str
    fecha_pub: Optional[str]
    doi: Optional[str]
    url: str
    tipo_estudio: str
    tipo_discapacidad: str
    mesh_terms: list[str]

class EnsayoOut(BaseModel):
    nct_id: str
    titulo: str
    estado: str
    fase: str
    resumen: str
    condicion: str
    sponsor: str
    fecha_inicio: str
    url: str
    tipo_discapacidad: str

class TratamientoOut(BaseModel):
    tipo: str
    descripcion: str
    nivel_evidencia: str  # A/B/C según fuente
    articulos_top: list[ArticuloOut]
    ensayos_activos: int

# ── Helpers ────────────────────────────────────────────────────────────────────

def _pubmed_search_live(query: str, max_results: int = 10) -> list[dict]:
    """Búsqueda en tiempo real en PubMed — sin caché."""
    params = {
        "db": "pubmed", "term": query,
        "retmax": max_results, "retmode": "json", "sort": "pub_date",
    }
    if PUBMED_KEY:
        params["api_key"] = PUBMED_KEY
    try:
        r = requests.get(f"{PUBMED_BASE}/esearch.fcgi", params=params, timeout=10)
        r.raise_for_status()
        pmids = r.json()["esearchresult"]["idlist"]
        if not pmids:
            return []
        fetch_params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"}
        if PUBMED_KEY:
            fetch_params["api_key"] = PUBMED_KEY
        fr = requests.get(f"{PUBMED_BASE}/efetch.fcgi", params=fetch_params, timeout=20)
        fr.raise_for_status()
        root = ET.fromstring(fr.content)
        results = []
        for art in root.findall(".//PubmedArticle"):
            pmid_el   = art.find(".//PMID")
            titulo_el = art.find(".//ArticleTitle")
            pmid      = pmid_el.text if pmid_el is not None else ""
            titulo    = html.unescape(titulo_el.text or "") if titulo_el is not None else ""
            autores   = []
            for au in art.findall(".//Author"):
                last = au.find("LastName")
                fore = au.find("ForeName")
                if last is not None:
                    autores.append(f"{fore.text} {last.text}" if fore is not None else last.text)
            abstract_texts = [
                (f"{ab.get('Label', '')}: " if ab.get("Label") else "") + (ab.text or "")
                for ab in art.findall(".//AbstractText")
            ]
            revista   = art.findtext(".//Journal/Title") or ""
            year      = art.findtext(".//PubDate/Year")
            month     = art.findtext(".//PubDate/Month") or "01"
            doi       = next(
                (i.text for i in art.findall(".//ArticleId") if i.get("IdType") == "doi"),
                None
            )
            mesh = [m.findtext("DescriptorName") or "" for m in art.findall(".//MeshHeading")]
            pub_types = [pt.text for pt in art.findall(".//PublicationType") if pt.text]
            if any("Randomized" in pt for pt in pub_types):
                tipo_estudio = "RCT"
            elif any("Review" in pt or "Meta-Analysis" in pt for pt in pub_types):
                tipo_estudio = "Review/Meta-analysis"
            elif any("Clinical Trial" in pt for pt in pub_types):
                tipo_estudio = "Clinical Trial"
            else:
                tipo_estudio = "Original"
            resumen_texto = " ".join(abstract_texts)[:1500]
            results.append({
                "pmid": pmid, "titulo": titulo,
                "autores": "; ".join(autores[:5]),
                "resumen": resumen_texto,
                "resumen_es": _traducir(resumen_texto),
                "revista": revista,
                "fecha_pub": f"{year}-{month}" if year else None,
                "doi": doi, "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "tipo_estudio": tipo_estudio, "mesh_terms": mesh,
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"PubMed error: {e}")


QUERIES_DEFAULT = {
    "motora":      "motor disability rehabilitation treatment 2023 2024",
    "visual":      "visual impairment blindness treatment 2023 2024",
    "auditiva":    "hearing loss cochlear implant treatment 2023 2024",
    "intelectual": "intellectual disability intervention ABA 2023 2024",
    "psicosocial": "mental health psychosocial disability treatment 2023 2024",
    "visceral":    "chronic disease organ disability treatment 2023 2024",
}

DESCRIPCIONES = {
    "motora":      "Afecta el sistema neuromuscular y esquelético. Incluye parálisis, amputaciones, ELA, parkinson.",
    "visual":      "Pérdida parcial o total de visión. Incluye ceguera, baja visión, retinosis pigmentaria.",
    "auditiva":    "Pérdida parcial o total de audición. Incluye hipoacusia, sordera profunda.",
    "intelectual": "Alteraciones en la función intelectual. Incluye síndrome de Down, TEA, TDAH.",
    "psicosocial": "Alteraciones en la conducta adaptativa y salud mental. Incluye esquizofrenia, depresión mayor.",
    "visceral":    "Afecta órganos internos. Incluye insuficiencia renal, cardíaca, diabetes, enfermedades raras.",
}

# ── Condiciones específicas (búsqueda curada) ─────────────────────────────────
# Capa ADICIONAL y opcional a los 6 tipos de discapacidad de arriba: permite
# buscar evidencia médica por condición/diagnóstico puntual (más específico
# que "motora" o "intelectual"), incluyendo el síndrome de Tourette. Cada
# condición queda igualmente asociada a uno de los 6 tipos ya existentes
# (mismo campo "tipo" que usan /api/articulos, /api/tratamientos/{tipo}, etc.)
# para no romper esa taxonomía. No modifica QUERIES_DEFAULT ni DESCRIPCIONES.
CONDICIONES_ESPECIFICAS: dict[str, dict] = {
    "tourette": {
        "nombre": "Síndrome de Tourette",
        "tipo": "intelectual",
        "descripcion": "Trastorno del neurodesarrollo caracterizado por tics motores "
                       "y vocales involuntarios, recurrentes y crónicos.",
        "query_pubmed": "Tourette syndrome tic disorder treatment 2023 2024 2025",
    },
    "tdah": {
        "nombre": "TDAH (Trastorno por Déficit de Atención e Hiperactividad)",
        "tipo": "intelectual",
        "descripcion": "Patrón persistente de inatención y/o hiperactividad-impulsividad "
                       "que interfiere con el funcionamiento o desarrollo.",
        "query_pubmed": "ADHD attention deficit hyperactivity disorder treatment 2023 2024 2025",
    },
    "sindrome_down": {
        "nombre": "Síndrome de Down",
        "tipo": "intelectual",
        "descripcion": "Trastorno genético por trisomía del cromosoma 21, con "
                       "discapacidad intelectual y rasgos físicos característicos.",
        "query_pubmed": "Down syndrome trisomy 21 intervention treatment 2023 2024 2025",
    },
    "ela": {
        "nombre": "Esclerosis Lateral Amiotrófica (ELA)",
        "tipo": "motora",
        "descripcion": "Enfermedad neurodegenerativa que afecta las neuronas motoras, "
                       "con pérdida progresiva de la fuerza muscular.",
        "query_pubmed": "amyotrophic lateral sclerosis ALS treatment therapy 2023 2024 2025",
    },
    "esclerosis_multiple": {
        "nombre": "Esclerosis Múltiple",
        "tipo": "motora",
        "descripcion": "Enfermedad autoinmune que afecta el sistema nervioso central "
                       "y puede causar discapacidad motora progresiva.",
        "query_pubmed": "multiple sclerosis treatment disease modifying therapy 2023 2024 2025",
    },
    "parkinson": {
        "nombre": "Enfermedad de Parkinson",
        "tipo": "motora",
        "descripcion": "Trastorno neurodegenerativo que afecta el control motor, "
                       "con temblor, rigidez y bradicinesia.",
        "query_pubmed": "Parkinson disease treatment rehabilitation 2023 2024 2025",
    },
    "paralisis_cerebral": {
        "nombre": "Parálisis Cerebral",
        "tipo": "motora",
        "descripcion": "Grupo de trastornos permanentes del movimiento y la postura "
                       "atribuidos a alteraciones no progresivas del cerebro en desarrollo.",
        "query_pubmed": "cerebral palsy rehabilitation treatment 2023 2024 2025",
    },
    "espectro_autista": {
        "nombre": "Trastorno del Espectro Autista (TEA)",
        "tipo": "intelectual",
        "descripcion": "Condición del neurodesarrollo que afecta la comunicación "
                       "social y presenta patrones restringidos/repetitivos de conducta.",
        "query_pubmed": "autism spectrum disorder intervention treatment 2023 2024 2025",
    },
    "retinosis_pigmentaria": {
        "nombre": "Retinosis Pigmentaria",
        "tipo": "visual",
        "descripcion": "Grupo de enfermedades genéticas de la retina que provocan "
                       "pérdida progresiva de la visión.",
        "query_pubmed": "retinitis pigmentosa treatment gene therapy 2023 2024 2025",
    },
    "glaucoma": {
        "nombre": "Glaucoma",
        "tipo": "visual",
        "descripcion": "Grupo de enfermedades oculares que dañan el nervio óptico, "
                       "asociadas frecuentemente a presión intraocular elevada.",
        "query_pubmed": "glaucoma treatment management 2023 2024 2025",
    },
    "hipoacusia": {
        "nombre": "Hipoacusia / Pérdida auditiva",
        "tipo": "auditiva",
        "descripcion": "Disminución de la capacidad auditiva, de grado y origen variable "
                       "(congénita o adquirida).",
        "query_pubmed": "hearing loss cochlear implant treatment 2023 2024 2025",
    },
    "esquizofrenia": {
        "nombre": "Esquizofrenia",
        "tipo": "psicosocial",
        "descripcion": "Trastorno psiquiátrico grave que afecta el pensamiento, la "
                       "percepción y el comportamiento.",
        "query_pubmed": "schizophrenia treatment antipsychotic 2023 2024 2025",
    },
    "trastorno_bipolar": {
        "nombre": "Trastorno Bipolar",
        "tipo": "psicosocial",
        "descripcion": "Trastorno del estado de ánimo con episodios de manía/hipomanía "
                       "y depresión.",
        "query_pubmed": "bipolar disorder treatment management 2023 2024 2025",
    },
    "toc": {
        "nombre": "Trastorno Obsesivo Compulsivo (TOC)",
        "tipo": "psicosocial",
        "descripcion": "Trastorno de ansiedad caracterizado por obsesiones y/o "
                       "compulsiones recurrentes.",
        "query_pubmed": "obsessive compulsive disorder OCD treatment 2023 2024 2025",
    },
    "diabetes_tipo1": {
        "nombre": "Diabetes tipo 1",
        "tipo": "visceral",
        "descripcion": "Enfermedad autoinmune crónica con destrucción de las células "
                       "beta pancreáticas y dependencia de insulina exógena.",
        "query_pubmed": "type 1 diabetes management treatment 2023 2024 2025",
    },
    "fibrosis_quistica": {
        "nombre": "Fibrosis Quística",
        "tipo": "visceral",
        "descripcion": "Enfermedad genética que afecta principalmente los pulmones y "
                       "el sistema digestivo por producción de moco espeso.",
        "query_pubmed": "cystic fibrosis treatment CFTR modulator 2023 2024 2025",
    },
    "insuficiencia_renal": {
        "nombre": "Insuficiencia Renal Crónica",
        "tipo": "visceral",
        "descripcion": "Pérdida progresiva e irreversible de la función renal.",
        "query_pubmed": "chronic kidney disease treatment dialysis 2023 2024 2025",
    },
}

# ── Especialidades médicas (taxonomía en paralelo) ────────────────────────────
# Segunda capa, independiente de "tipo" y de CONDICIONES_ESPECIFICAS: agrupa
# por especialidad médica (a qué profesional consultar), enlazando hacia las
# condiciones curadas de arriba. Tampoco modifica nada existente.
ESPECIALIDADES_MEDICAS: dict[str, dict] = {
    "neurologia": {
        "nombre": "Neurología",
        "descripcion": "Diagnóstico y tratamiento de enfermedades del sistema "
                       "nervioso central y periférico.",
        "condiciones_relacionadas": [
            "tourette", "ela", "esclerosis_multiple", "parkinson", "paralisis_cerebral",
        ],
    },
    "psiquiatria": {
        "nombre": "Psiquiatría",
        "descripcion": "Diagnóstico y tratamiento de trastornos mentales y de la "
                       "conducta.",
        "condiciones_relacionadas": ["tdah", "toc", "esquizofrenia", "trastorno_bipolar"],
    },
    "genetica": {
        "nombre": "Genética médica",
        "descripcion": "Diagnóstico y asesoramiento sobre condiciones de origen "
                       "genético o cromosómico.",
        "condiciones_relacionadas": ["sindrome_down", "fibrosis_quistica"],
    },
    "fisiatria": {
        "nombre": "Medicina Física y Rehabilitación (Fisiatría)",
        "descripcion": "Rehabilitación funcional de personas con discapacidad "
                       "motora u otras limitaciones físicas.",
        "condiciones_relacionadas": ["ela", "esclerosis_multiple", "parkinson", "paralisis_cerebral"],
    },
    "oftalmologia": {
        "nombre": "Oftalmología",
        "descripcion": "Diagnóstico y tratamiento de enfermedades de los ojos y la "
                       "vía visual.",
        "condiciones_relacionadas": ["retinosis_pigmentaria", "glaucoma"],
    },
    "otorrinolaringologia": {
        "nombre": "Otorrinolaringología",
        "descripcion": "Diagnóstico y tratamiento de enfermedades del oído, nariz "
                       "y garganta.",
        "condiciones_relacionadas": ["hipoacusia"],
    },
    "endocrinologia": {
        "nombre": "Endocrinología",
        "descripcion": "Diagnóstico y tratamiento de enfermedades hormonales y "
                       "metabólicas.",
        "condiciones_relacionadas": ["diabetes_tipo1"],
    },
    "neumologia": {
        "nombre": "Neumología",
        "descripcion": "Diagnóstico y tratamiento de enfermedades del aparato "
                       "respiratorio.",
        "condiciones_relacionadas": ["fibrosis_quistica"],
    },
    "nefrologia": {
        "nombre": "Nefrología",
        "descripcion": "Diagnóstico y tratamiento de enfermedades renales.",
        "condiciones_relacionadas": ["insuficiencia_renal"],
    },
}

# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/articulos")
async def listar_articulos(
    tipo: Optional[str] = Query(None, description="motora|visual|auditiva|intelectual|psicosocial|visceral"),
    q:    Optional[str] = Query(None, description="Búsqueda por keyword"),
    limit: int          = Query(10, ge=1, le=50),
    fuente: Optional[str] = Query(None, description="pubmed|scielo|clinicaltrials"),
):
    """
    Lista artículos médicos.
    Prioriza la caché del ETL (Tarea 11); si no hay caché, consulta PubMed en vivo.
    """
    if tipo and tipo not in TIPOS_VALIDOS:
        raise HTTPException(400, f"tipo debe ser uno de: {', '.join(sorted(TIPOS_VALIDOS))}")

    # ── Tarea 11: intentar servir desde caché ETL ─────────────────────────────
    cache = _load_etl_cache()
    if cache and not q:
        articulos_cache = cache.get("articulos", [])
        if fuente:
            articulos_cache = [a for a in articulos_cache if a.get("fuente") == fuente]
        if tipo:
            articulos_cache = [a for a in articulos_cache if a.get("tipo_discapacidad") == tipo]
        if articulos_cache:
            return {
                "total":  len(articulos_cache[:limit]),
                "tipo":   tipo or "general",
                "fuente_datos": "cache_etl",
                "fecha_cache": cache.get("resumen", {}).get("fecha", ""),
                "articulos": articulos_cache[:limit],
            }

    # ── Fallback: PubMed en vivo ──────────────────────────────────────────────
    if q:
        query = q
        tipo_final = tipo or "general"
    elif tipo:
        query = QUERIES_DEFAULT[tipo]
        tipo_final = tipo
    else:
        query = "disability rehabilitation treatment 2024"
        tipo_final = "general"

    arts = _pubmed_search_live(query, max_results=limit)
    for a in arts:
        a["tipo_discapacidad"] = tipo_final
    return {"total": len(arts), "tipo": tipo_final, "fuente_datos": "pubmed_live", "articulos": arts}


@router.get("/articulos/{pmid}")
async def detalle_articulo(pmid: str):
    """Detalle completo de un artículo por PMID."""
    params = {"db": "pubmed", "id": pmid, "retmode": "xml"}
    if PUBMED_KEY:
        params["api_key"] = PUBMED_KEY
    try:
        r = requests.get(f"{PUBMED_BASE}/efetch.fcgi", params=params, timeout=15)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        art  = root.find(".//PubmedArticle")
        if art is None:
            raise HTTPException(404, f"PMID {pmid} no encontrado")
        titulo = html.unescape(art.findtext(".//ArticleTitle") or "")
        abstract_texts = [
            (f"{ab.get('Label', '')}: " if ab.get("Label") else "") + (ab.text or "")
            for ab in art.findall(".//AbstractText")
        ]
        autores = []
        for au in art.findall(".//Author"):
            last = au.find("LastName")
            fore = au.find("ForeName")
            if last is not None:
                autores.append(f"{fore.text} {last.text}" if fore is not None else last.text)
        doi   = next((i.text for i in art.findall(".//ArticleId") if i.get("IdType") == "doi"), None)
        mesh  = [m.findtext("DescriptorName") or "" for m in art.findall(".//MeshHeading")]
        year  = art.findtext(".//PubDate/Year")
        month = art.findtext(".//PubDate/Month") or "01"
        return {
            "pmid":      pmid,
            "titulo":    titulo,
            "autores":   autores,
            "resumen":   " ".join(abstract_texts),
            "revista":   art.findtext(".//Journal/Title") or "",
            "fecha_pub": f"{year}-{month}" if year else None,
            "doi":       doi,
            "url":       f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "mesh_terms": mesh,
            "url_pmc":   f"https://www.ncbi.nlm.nih.gov/pmc/articles/pmid/{pmid}/" if doi else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"Error PubMed: {e}")


@router.get("/ensayos")
async def listar_ensayos(
    tipo:   Optional[str] = Query(None),
    estado: str           = Query("RECRUITING", description="RECRUITING|COMPLETED|ACTIVE_NOT_RECRUITING"),
    limit:  int           = Query(10, ge=1, le=30),
):
    """Ensayos clínicos activos desde ClinicalTrials.gov."""
    # Tarea 9: mismo chequeo de tipo que /api/articulos
    if tipo and tipo not in TIPOS_VALIDOS:
        raise HTTPException(400, f"tipo debe ser uno de: {', '.join(sorted(TIPOS_VALIDOS))}")

    query = QUERIES_DEFAULT.get(tipo, "disability treatment") if tipo else "disability treatment"
    params = {
        "query.cond":           query,
        "filter.overallStatus": estado,
        "pageSize":             limit,
        "sort":                 "LastUpdatePostDate:desc",
        "fields":               "NCTId,BriefTitle,OverallStatus,Phase,StartDate,"
                                "CompletionDate,BriefSummary,Condition,LeadSponsorName",
    }
    try:
        r = requests.get(CT_BASE, params=params, timeout=15)
        r.raise_for_status()
        studies = r.json().get("studies", [])
        result  = []
        for s in studies:
            p    = s.get("protocolSection", {})
            idm  = p.get("identificationModule", {})
            stm  = p.get("statusModule", {})
            des  = p.get("descriptionModule", {})
            dsn  = p.get("designModule", {})
            spm  = p.get("sponsorCollaboratorsModule", {})
            cnm  = p.get("conditionsModule", {})
            nct  = idm.get("nctId", "")
            result.append({
                "nct_id":    nct,
                "titulo":    idm.get("briefTitle", ""),
                "estado":    stm.get("overallStatus", ""),
                "fase":      dsn.get("phases", [""])[0] if dsn.get("phases") else "",
                "resumen":   des.get("briefSummary", "")[:800],
                "condicion": "; ".join(cnm.get("conditions", [])),
                "sponsor":   spm.get("leadSponsor", {}).get("name", ""),
                "fecha_inicio": stm.get("startDateStruct", {}).get("date", ""),
                "url":       f"https://clinicaltrials.gov/study/{nct}",
                "tipo_discapacidad": tipo or "general",
            })
        return {"total": len(result), "tipo": tipo, "estado": estado, "ensayos": result}
    except Exception as e:
        raise HTTPException(502, f"ClinicalTrials error: {e}")


@router.get("/tratamientos/{tipo}")
async def tratamientos_por_tipo(tipo: str, limit: int = Query(5, ge=1, le=20)):
    """
    Resumen de tratamientos + artículos top + ensayos activos para un tipo.
    """
    if tipo not in TIPOS_VALIDOS:
        raise HTTPException(400, f"tipo debe ser uno de: {', '.join(TIPOS_VALIDOS)}")

    arts    = _pubmed_search_live(QUERIES_DEFAULT[tipo], max_results=limit)
    for a in arts:
        a["tipo_discapacidad"] = tipo

    try:
        r = requests.get(CT_BASE, params={
            "query.cond": QUERIES_DEFAULT[tipo],
            "filter.overallStatus": "RECRUITING",
            "pageSize": 1,
        }, timeout=10)
        n_ensayos = r.json().get("totalCount", 0) if r.ok else 0
    except Exception:
        n_ensayos = 0

    return {
        "tipo":             tipo,
        "descripcion":      DESCRIPCIONES.get(tipo, ""),
        "articulos_top":    arts,
        "ensayos_activos":  n_ensayos,
        "fuentes":          ["PubMed (NIH)", "ClinicalTrials.gov", "SciELO"],
        "ultima_actualizacion": "cada 15 días",
    }


@router.get("/buscar")
async def buscar(
    q:     str = Query(..., min_length=3, description="Término de búsqueda médica"),
    limit: int = Query(10, ge=1, le=30),
):
    """Búsqueda libre en PubMed en tiempo real."""
    arts = _pubmed_search_live(q, max_results=limit)
    return {"query": q, "total": len(arts), "articulos": arts}


# ── Condiciones específicas (búsqueda curada, incluye Tourette) ──────────────

@router.get("/condiciones")
async def listar_condiciones():
    """
    Lista las condiciones/diagnósticos específicos disponibles para búsqueda
    curada (más puntual que los 6 tipos generales de /api/articulos), como el
    síndrome de Tourette, TDAH, síndrome de Down, ELA, esclerosis múltiple,
    Parkinson, entre otras.
    """
    condiciones = [{"id": cid, **datos} for cid, datos in CONDICIONES_ESPECIFICAS.items()]
    return {"total": len(condiciones), "condiciones": condiciones}


@router.get("/condiciones/{condicion}")
async def buscar_por_condicion(condicion: str, limit: int = Query(10, ge=1, le=30)):
    """
    Evidencia médica (PubMed en vivo) para una condición específica curada,
    por ejemplo `/api/condiciones/tourette`. Ver `/api/condiciones` para el
    listado completo de IDs disponibles.
    """
    datos = CONDICIONES_ESPECIFICAS.get(condicion.lower())
    if not datos:
        disponibles = ", ".join(sorted(CONDICIONES_ESPECIFICAS))
        raise HTTPException(404, f"Condición '{condicion}' no encontrada. Disponibles: {disponibles}")

    arts = _pubmed_search_live(datos["query_pubmed"], max_results=limit)
    for a in arts:
        a["tipo_discapacidad"] = datos["tipo"]

    return {
        "condicion": condicion.lower(),
        "nombre": datos["nombre"],
        "tipo_discapacidad": datos["tipo"],
        "descripcion": datos["descripcion"],
        "total": len(arts),
        "articulos": arts,
    }


# ── Especialidades médicas (taxonomía en paralelo a "tipo") ──────────────────

@router.get("/especialidades")
async def listar_especialidades():
    """
    Lista las especialidades médicas relacionadas con los distintos tipos de
    discapacidad (neurología, psiquiatría, genética, fisiatría, oftalmología,
    otorrinolaringología, endocrinología, neumología, nefrología), cada una
    con las condiciones específicas que agrupa.
    """
    especialidades = [{"id": eid, **datos} for eid, datos in ESPECIALIDADES_MEDICAS.items()]
    return {"total": len(especialidades), "especialidades": especialidades}


@router.get("/especialidades/{especialidad}")
async def detalle_especialidad(especialidad: str):
    """
    Detalle de una especialidad médica: descripción y condiciones específicas
    relacionadas (cada una con su propia ficha, ver `/api/condiciones/{id}`).
    """
    datos = ESPECIALIDADES_MEDICAS.get(especialidad.lower())
    if not datos:
        disponibles = ", ".join(sorted(ESPECIALIDADES_MEDICAS))
        raise HTTPException(404, f"Especialidad '{especialidad}' no encontrada. Disponibles: {disponibles}")

    condiciones = [
        {"id": cid, **CONDICIONES_ESPECIFICAS[cid]}
        for cid in datos["condiciones_relacionadas"]
        if cid in CONDICIONES_ESPECIFICAS
    ]

    return {
        "especialidad": especialidad.lower(),
        "nombre": datos["nombre"],
        "descripcion": datos["descripcion"],
        "condiciones": condiciones,
    }