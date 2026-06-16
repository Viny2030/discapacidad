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