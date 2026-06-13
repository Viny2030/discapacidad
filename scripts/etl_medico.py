"""
etl_medico.py
Motor de ingesta de artículos médicos y ensayos clínicos sobre discapacidad.

Fuentes:
  - PubMed (NIH) — 35M papers, API gratuita sin key
  - SciELO — ciencia latinoamericana, OAI-PMH
  - ClinicalTrials.gov — ensayos clínicos activos, API v2 gratuita

Salida: tabla articulos_medicos en PostgreSQL
Scheduler: cada 15 días via APScheduler
"""

import os
import time
import logging
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional
import html

logging.basicConfig(level=logging.INFO, format="[ETL-MED] %(message)s")
log = logging.getLogger(__name__)

# ── Queries por tipo de discapacidad ──────────────────────────────────────────

QUERIES_PUBMED = {
    "motora": [
        "motor disability rehabilitation treatment",
        "spinal cord injury therapy advances",
        "exoskeleton rehabilitation paraplegia",
        "prosthetics bionics upper limb",
        "brain computer interface motor disability",
    ],
    "visual": [
        "visual impairment rehabilitation treatment",
        "retinal prosthesis blindness therapy",
        "gene therapy retinal dystrophy",
        "low vision assistive technology",
    ],
    "auditiva": [
        "hearing loss cochlear implant outcomes",
        "auditory brainstem implant",
        "gene therapy hearing loss inner ear",
        "sign language deaf rehabilitation",
    ],
    "intelectual": [
        "intellectual disability intervention treatment",
        "down syndrome therapy advances",
        "autism spectrum disorder ABA therapy",
        "neurofeedback intellectual disability",
        "DYRK1A inhibitor down syndrome clinical trial",
    ],
    "psicosocial": [
        "psychosocial disability rehabilitation",
        "TMS transcranial magnetic stimulation depression",
        "esketamine treatment resistant depression",
        "psilocybin therapy mental health",
        "cognitive behavioral therapy psychosis",
    ],
    "visceral": [
        "chronic disease disability management",
        "artificial pancreas type 1 diabetes disability",
        "bioartificial organ disability",
        "CRISPR gene therapy sickle cell disease",
        "organ transplant disability quality life",
    ],
}

QUERIES_CLINICALTRIALS = {
    "motora":      "motor disability rehabilitation",
    "visual":      "visual impairment treatment",
    "auditiva":    "hearing loss treatment",
    "intelectual": "intellectual disability intervention",
    "psicosocial": "mental health disability treatment",
    "visceral":    "chronic disease organ failure disability",
}


# ── Dataclass artículo ─────────────────────────────────────────────────────────

@dataclass
class Articulo:
    fuente: str
    tipo_discapacidad: str
    pmid: Optional[str] = None
    titulo: str = ""
    autores: str = ""
    resumen: str = ""
    revista: str = ""
    fecha_pub: Optional[str] = None
    doi: Optional[str] = None
    url: str = ""
    es_open_access: bool = False
    tipo_estudio: str = ""  # RCT, review, case study, etc.
    pais: str = ""
    mesh_terms: list = field(default_factory=list)
    fecha_ingesta: str = field(default_factory=lambda: datetime.now().isoformat())


# ── PubMed ─────────────────────────────────────────────────────────────────────

PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_KEY  = os.getenv("PUBMED_API_KEY", "")  # opcional — 10 req/s con key vs 3 sin key


def pubmed_search(query: str, max_results: int = 20) -> list[str]:
    """Devuelve lista de PMIDs para una query."""
    params = {
        "db":      "pubmed",
        "term":    query,
        "retmax":  max_results,
        "retmode": "json",
        "sort":    "pub_date",
        "datetype": "pdat",
        "reldate": 730,  # últimos 2 años
    }
    if PUBMED_KEY:
        params["api_key"] = PUBMED_KEY

    try:
        r = requests.get(f"{PUBMED_BASE}/esearch.fcgi", params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        return data["esearchresult"]["idlist"]
    except Exception as e:
        log.warning(f"PubMed search error '{query}': {e}")
        return []


def pubmed_fetch(pmids: list[str], tipo: str) -> list[Articulo]:
    """Descarga metadatos de una lista de PMIDs."""
    if not pmids:
        return []

    params = {
        "db":      "pubmed",
        "id":      ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract",
    }
    if PUBMED_KEY:
        params["api_key"] = PUBMED_KEY

    try:
        r = requests.get(f"{PUBMED_BASE}/efetch.fcgi", params=params, timeout=30)
        r.raise_for_status()
        root = ET.fromstring(r.content)
    except Exception as e:
        log.warning(f"PubMed fetch error: {e}")
        return []

    articulos = []
    for art in root.findall(".//PubmedArticle"):
        try:
            a = Articulo(fuente="pubmed", tipo_discapacidad=tipo)

            # PMID
            pmid_el = art.find(".//PMID")
            a.pmid = pmid_el.text if pmid_el is not None else ""
            a.url  = f"https://pubmed.ncbi.nlm.nih.gov/{a.pmid}/" if a.pmid else ""

            # Título
            titulo_el = art.find(".//ArticleTitle")
            a.titulo = html.unescape(titulo_el.text or "") if titulo_el is not None else ""

            # Autores
            autores = []
            for au in art.findall(".//Author"):
                last = au.find("LastName")
                fore = au.find("ForeName")
                if last is not None:
                    nombre = f"{fore.text} {last.text}" if fore is not None else last.text
                    autores.append(nombre)
            a.autores = "; ".join(autores[:5])  # máximo 5

            # Abstract
            abstract_texts = []
            for ab in art.findall(".//AbstractText"):
                label = ab.get("Label", "")
                text  = ab.text or ""
                abstract_texts.append(f"{label}: {text}" if label else text)
            a.resumen = " ".join(abstract_texts)[:2000]  # máximo 2000 chars

            # Revista
            journal_el = art.find(".//Journal/Title")
            a.revista = journal_el.text if journal_el is not None else ""

            # Fecha
            year  = art.findtext(".//PubDate/Year")
            month = art.findtext(".//PubDate/Month") or "01"
            a.fecha_pub = f"{year}-{month}" if year else None

            # DOI
            for id_el in art.findall(".//ArticleId"):
                if id_el.get("IdType") == "doi":
                    a.doi = id_el.text

            # MeSH terms
            a.mesh_terms = [
                m.findtext("DescriptorName") or ""
                for m in art.findall(".//MeshHeading")
            ]

            # Tipo de estudio
            pub_types = [pt.text for pt in art.findall(".//PublicationType") if pt.text]
            if any("Randomized" in pt for pt in pub_types):
                a.tipo_estudio = "RCT"
            elif any("Review" in pt or "Meta-Analysis" in pt for pt in pub_types):
                a.tipo_estudio = "Review/Meta-analysis"
            elif any("Clinical Trial" in pt for pt in pub_types):
                a.tipo_estudio = "Clinical Trial"
            else:
                a.tipo_estudio = "Original"

            articulos.append(a)
        except Exception as e:
            log.debug(f"Parse error PMID: {e}")
            continue

    return articulos


# ── ClinicalTrials.gov ─────────────────────────────────────────────────────────

CT_BASE = "https://clinicaltrials.gov/api/v2/studies"


def fetch_clinical_trials(tipo: str, query: str, max_results: int = 10) -> list[dict]:
    """Devuelve ensayos clínicos activos o recientes."""
    params = {
        "query.cond":        query,
        "filter.overallStatus": "RECRUITING,ACTIVE_NOT_RECRUITING,COMPLETED",
        "pageSize":          max_results,
        "sort":              "LastUpdatePostDate:desc",
        "fields":            "NCTId,BriefTitle,OfficialTitle,OverallStatus,Phase,StartDate,"
                             "CompletionDate,BriefSummary,Condition,LeadSponsorName,LocationCountry",
    }
    try:
        r = requests.get(CT_BASE, params=params, timeout=15)
        r.raise_for_status()
        studies = r.json().get("studies", [])
        result = []
        for s in studies:
            proto = s.get("protocolSection", {})
            id_mod    = proto.get("identificationModule", {})
            desc_mod  = proto.get("descriptionModule", {})
            status_mod = proto.get("statusModule", {})
            design_mod = proto.get("designModule", {})
            sponsor_mod = proto.get("sponsorCollaboratorsModule", {})
            cond_mod  = proto.get("conditionsModule", {})
            locs_mod  = proto.get("contactsLocationsModule", {})

            nct_id = id_mod.get("nctId", "")
            result.append({
                "fuente":             "clinicaltrials",
                "tipo_discapacidad":  tipo,
                "nct_id":             nct_id,
                "titulo":             id_mod.get("briefTitle", ""),
                "titulo_oficial":     id_mod.get("officialTitle", ""),
                "estado":             status_mod.get("overallStatus", ""),
                "fase":               design_mod.get("phases", [""])[0] if design_mod.get("phases") else "",
                "resumen":            desc_mod.get("briefSummary", "")[:1000],
                "condicion":          "; ".join(cond_mod.get("conditions", [])),
                "sponsor":            sponsor_mod.get("leadSponsor", {}).get("name", ""),
                "fecha_inicio":       status_mod.get("startDateStruct", {}).get("date", ""),
                "fecha_completado":   status_mod.get("completionDateStruct", {}).get("date", ""),
                "url":                f"https://clinicaltrials.gov/study/{nct_id}",
                "fecha_ingesta":      datetime.now().isoformat(),
            })
        return result
    except Exception as e:
        log.warning(f"ClinicalTrials error '{query}': {e}")
        return []


# ── SciELO (OAI-PMH) ──────────────────────────────────────────────────────────

SCIELO_BASE = "https://www.scielo.org/oai/scielo-oai.php"


def fetch_scielo(tipo: str, query: str, max_results: int = 10) -> list[dict]:
    """Busca artículos en SciELO Argentina via OAI-PMH."""
    params = {
        "verb":            "ListRecords",
        "metadataPrefix":  "oai_dc",
        "set":             "oai:scielo:arg",  # Argentina
    }
    try:
        r = requests.get(SCIELO_BASE, params=params, timeout=20)
        r.raise_for_status()
        ns = {"oai": "http://www.openarchives.org/OAI/2.0/",
              "dc":  "http://purl.org/dc/elements/1.1/"}
        root    = ET.fromstring(r.content)
        records = root.findall(".//oai:record", ns)
        result  = []
        query_words = set(query.lower().split())

        for rec in records[:100]:
            try:
                meta = rec.find(".//oai:metadata", ns)
                if meta is None:
                    continue
                titulo  = meta.findtext(".//dc:title", namespaces=ns) or ""
                subject = meta.findtext(".//dc:subject", namespaces=ns) or ""
                desc    = meta.findtext(".//dc:description", namespaces=ns) or ""
                texto   = (titulo + " " + subject + " " + desc).lower()

                if not any(w in texto for w in query_words):
                    continue

                result.append({
                    "fuente":            "scielo",
                    "tipo_discapacidad": tipo,
                    "titulo":            titulo,
                    "autores":           meta.findtext(".//dc:creator", namespaces=ns) or "",
                    "resumen":           desc[:1000],
                    "revista":           meta.findtext(".//dc:source", namespaces=ns) or "",
                    "fecha_pub":         meta.findtext(".//dc:date", namespaces=ns) or "",
                    "url":               meta.findtext(".//dc:identifier", namespaces=ns) or "",
                    "fecha_ingesta":     datetime.now().isoformat(),
                })

                if len(result) >= max_results:
                    break
            except Exception:
                continue
        return result
    except Exception as e:
        log.warning(f"SciELO error '{query}': {e}")
        return []


# ── Motor principal ────────────────────────────────────────────────────────────

def run_etl_medico(max_por_query: int = 10) -> dict:
    """
    Corre el ETL completo de fuentes médicas.
    Retorna dict con listas de artículos y ensayos por tipo.
    """
    log.info("=" * 55)
    log.info("ETL MÉDICO — Inicio")
    log.info("=" * 55)

    resultado = {
        "articulos":        [],
        "ensayos_clinicos": [],
        "scielo":           [],
        "resumen": {},
    }

    # 1. PubMed
    for tipo, queries in QUERIES_PUBMED.items():
        total_tipo = []
        for q in queries:
            pmids = pubmed_search(q, max_results=max_por_query)
            arts  = pubmed_fetch(pmids, tipo)
            total_tipo.extend(arts)
            time.sleep(0.35)  # respetar rate limit

        resultado["articulos"].extend(total_tipo)
        log.info(f"  PubMed {tipo}: {len(total_tipo)} artículos")

    # 2. ClinicalTrials.gov
    for tipo, query in QUERIES_CLINICALTRIALS.items():
        ensayos = fetch_clinical_trials(tipo, query, max_results=5)
        resultado["ensayos_clinicos"].extend(ensayos)
        log.info(f"  ClinicalTrials {tipo}: {len(ensayos)} ensayos")
        time.sleep(0.5)

    # 3. SciELO Argentina
    for tipo, queries in QUERIES_PUBMED.items():
        arts = fetch_scielo(tipo, queries[0], max_results=5)
        resultado["scielo"].extend(arts)
        time.sleep(1)

    # Resumen
    resultado["resumen"] = {
        "total_articulos":   len(resultado["articulos"]),
        "total_ensayos":     len(resultado["ensayos_clinicos"]),
        "total_scielo":      len(resultado["scielo"]),
        "fecha":             datetime.now().isoformat(),
    }

    log.info(f"ETL Médico OK — {resultado['resumen']}")
    return resultado


# ── Endpoints FastAPI ──────────────────────────────────────────────────────────

"""
Endpoints sugeridos para api/main.py:

GET /api/articulos
    ?tipo=motora|visual|auditiva|intelectual|psicosocial|visceral
    ?fuente=pubmed|scielo|clinicaltrials
    ?q=keyword
    ?limit=20&offset=0

GET /api/articulos/{pmid}           → detalle completo
GET /api/ensayos                    → ensayos clínicos activos
    ?tipo=motora&estado=RECRUITING
GET /api/tratamientos/{tipo}        → resumen de tratamientos + artículos top
GET /api/buscar?q=exoesqueleto      → búsqueda full-text en resúmenes

Caché Redis: TTL 15 días para listas, 30 días para artículos individuales
"""


if __name__ == "__main__":
    import json
    resultado = run_etl_medico(max_por_query=5)
    print(json.dumps(resultado["resumen"], indent=2, ensure_ascii=False))

    # Muestra primeros 3 artículos
    for art in resultado["articulos"][:3]:
        print(f"\n[{art.tipo_discapacidad.upper()}] {art.titulo[:80]}")
        print(f"  Fuente: {art.fuente} | Tipo: {art.tipo_estudio}")
        print(f"  URL: {art.url}")
