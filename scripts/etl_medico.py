"""
etl_medico.py
Motor de ingesta de artÃÂ­culos mÃÂ©dicos y ensayos clÃÂ­nicos sobre discapacidad.

Fuentes:
  - PubMed (NIH) Ã¢â¬â 35M papers, API gratuita sin key
  - SciELO Ã¢â¬â ciencia latinoamericana, OAI-PMH
  - ClinicalTrials.gov Ã¢â¬â ensayos clÃÂ­nicos activos, API v2 gratuita

Salida: tabla articulos_medicos en PostgreSQL
Scheduler: cada 15 dÃÂ­as via APScheduler
"""

import os
import re
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

# Ã¢ââ¬Ã¢ââ¬ Queries por tipo de discapacidad Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬

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


# Ã¢ââ¬Ã¢ââ¬ Dataclass artÃÂ­culo Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬

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
    resumen_es: str = ""   # traducciÃÂ³n/adaptaciÃÂ³n al espaÃÂ±ol (Tarea 8)


# Ã¢ââ¬Ã¢ââ¬ PubMed Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬

PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_KEY  = os.getenv("PUBMED_API_KEY", "")  # opcional Ã¢â¬â 10 req/s con key vs 3 sin key


# Ã¢ââ¬Ã¢ââ¬ Traductor cientÃÂ­fico (resumen_es) Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬

# Diccionario de tÃÂ©rminos tÃÂ©cnicos frecuentes (inglÃÂ©s Ã¢â â espaÃÂ±ol)
_TERMINOS = {
    "randomized controlled trial": "ensayo controlado aleatorizado",
    "systematic review": "revisiÃÂ³n sistemÃÂ¡tica",
    "meta-analysis": "metaanÃÂ¡lisis",
    "cochlear implant": "implante coclear",
    "exoskeleton": "exoesqueleto",
    "spinal cord injury": "lesiÃÂ³n medular",
    "brain computer interface": "interfaz cerebro-computadora",
    "gene therapy": "terapia gÃÂ©nica",
    "stem cell": "cÃÂ©lula madre",
    "prosthesis": "prÃÂ³tesis",
    "prosthetic": "protÃÂ©sico",
    "rehabilitation": "rehabilitaciÃÂ³n",
    "disability": "discapacidad",
    "impairment": "deficiencia",
    "motor": "motora",
    "visual": "visual",
    "auditory": "auditivo",
    "intellectual": "intelectual",
    "psychosocial": "psicosocial",
    "treatment": "tratamiento",
    "therapy": "terapia",
    "outcomes": "resultados",
    "patients": "pacientes",
    "clinical trial": "ensayo clÃÂ­nico",
    "adverse events": "eventos adversos",
    "quality of life": "calidad de vida",
    "intervention": "intervenciÃÂ³n",
    "placebo": "placebo",
    "randomized": "aleatorizado",
    "double-blind": "doble ciego",
    "efficacy": "eficacia",
    "safety": "seguridad",
    "significant": "significativo",
    "participants": "participantes",
    "median": "mediana",
    "compared": "comparado",
    "versus": "versus",
    "weeks": "semanas",
    "months": "meses",
    "years": "aÃÂ±os",
}

def traducir_resumen(texto_en: str, max_chars: int = 600) -> str:
    """
    Tarea 8 Ã¢â¬â Traductor cientÃÂ­fico para resÃÂºmenes PubMed.

    Estrategia por niveles (en orden de disponibilidad):
      1. MyMemory API (gratuita, 5k palabras/dÃÂ­a sin key)
      2. LibreTranslate pÃÂºblica (si MyMemory falla)
      3. SustituciÃÂ³n de terminologÃÂ­a tÃÂ©cnica + resumen acortado

    Siempre devuelve texto en espaÃÂ±ol, nunca lanza excepciÃÂ³n.
    """
    if not texto_en or not texto_en.strip():
        return ""

    snippet = texto_en[:1500]  # traducimos hasta 1500 chars para no agotar cuotas

    # Nivel 1 Ã¢â¬â MyMemory (gratuita, ~5 000 palabras/dÃÂ­a)
    try:
        r = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": snippet[:500], "langpair": "en|es", "de": "observatorio@discapacidad.ar"},
            timeout=8,
        )
        if r.ok:
            j = r.json()
            if j.get("responseStatus") == 200:
                traducido = j["responseData"]["translatedText"]
                if traducido and len(traducido) > 30:
                    return traducido[:max_chars]
    except Exception:
        pass

    # Nivel 2 Ã¢â¬â LibreTranslate pÃÂºblica
    try:
        r2 = requests.post(
            "https://libretranslate.com/translate",
            json={"q": snippet[:500], "source": "en", "target": "es"},
            timeout=8,
        )
        if r2.ok:
            data2 = r2.json()
            traducido2 = data2.get("translatedText", "")
            if traducido2 and len(traducido2) > 30:
                return traducido2[:max_chars]
    except Exception:
        pass

    # Nivel 3 Ã¢â¬â sustituciÃÂ³n de terminologÃÂ­a + recorte (fallback sin red)
    resultado = snippet[:max_chars]
    for en, es in _TERMINOS.items():
        resultado = re.sub(re.escape(en), es, resultado, flags=re.IGNORECASE)
    # Agregar nota al pie para que el lector sepa que es automÃÂ¡tico
    return resultado + " [traducciÃÂ³n automÃÂ¡tica parcial]"


def pubmed_search(query: str, max_results: int = 20) -> list[str]:
    """Devuelve lista de PMIDs para una query."""
    params = {
        "db":      "pubmed",
        "term":    query,
        "retmax":  max_results,
        "retmode": "json",
        "sort":    "pub_date",
        "datetype": "pdat",
        "reldate": 730,  # ÃÂºltimos 2 aÃÂ±os
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

            # TÃÂ­tulo
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
            a.autores = "; ".join(autores[:5])  # mÃÂ¡ximo 5

            # Abstract
            abstract_texts = []
            for ab in art.findall(".//AbstractText"):
                label = ab.get("Label", "")
                text  = ab.text or ""
                abstract_texts.append(f"{label}: {text}" if label else text)
            a.resumen = " ".join(abstract_texts)[:2000]  # mÃÂ¡ximo 2000 chars

            # TraducciÃÂ³n al espaÃÂ±ol (Tarea 8)
            a.resumen_es = traducir_resumen(a.resumen)

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


# Ã¢ââ¬Ã¢ââ¬ ClinicalTrials.gov Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬

CT_BASE = "https://clinicaltrials.gov/api/v2/studies"


def fetch_clinical_trials(tipo: str, query: str, max_results: int = 10) -> list[dict]:
    """Devuelve ensayos clÃÂ­nicos activos o recientes."""
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


# Ã¢ââ¬Ã¢ââ¬ SciELO (OAI-PMH) Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬

SCIELO_BASE = "https://www.scielo.org/oai/scielo-oai.php"




def fetch_scielo(tipo: str, query: str, max_results: int = 10) -> list[dict]:
    """SciELO Argentina OAI-PMH devuelve 404 desde 2024 - deshabilitado."""
    log.info("SciELO deshabilitado - omitiendo")
    return []


def _fetch_scielo_original(tipo: str, query: str, max_results: int = 10) -> list[dict]:
    """Codigo original conservado."""
    params = {
        "verb":            "ListRecords",
        "metadataPrefix":  "oai_dc",
        "set":             "oai:scielo:arg",
    }
    try:
        r = requests.get(SCIELO_BASE, params=params, timeout=20)
        r.raise_for_status()
        return []
    except Exception as e:
        log.warning(f"SciELO error '{query}': {e}")
        return []


def run_etl_medico(max_por_query: int = 10) -> dict:
    """
    Corre el ETL completo de fuentes mÃÂ©dicas.
    Retorna dict con listas de artÃÂ­culos y ensayos por tipo.
    Persiste el resultado en data/processed/etl_medico_cache.json (Tarea 11).
    """
    log.info("=" * 55)
    log.info("ETL MÃâ°DICO Ã¢â¬â Inicio")
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
        log.info(f"  PubMed {tipo}: {len(total_tipo)} artÃÂ­culos")

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

    log.info(f"ETL MÃÂ©dico OK Ã¢â¬â {resultado['resumen']}")

    # Ã¢ââ¬Ã¢ââ¬ Tarea 11: Persistencia en disco Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬
    _persistir_resultado_etl(resultado)

    return resultado


def _persistir_resultado_etl(resultado: dict) -> None:
    """
    Tarea 11 Ã¢â¬â Serializa el resultado del ETL a JSON para que api_medica.py
    lo consuma con cachÃÂ© sin volver a llamar a PubMed en cada request.
    """
    import json
    from pathlib import Path
    from dataclasses import asdict

    cache_dir = Path(__file__).resolve().parent.parent / "data" / "processed"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / "etl_medico_cache.json"

    # Convertir dataclasses a dict (los artÃÂ­culos de PubMed son Articulo)
    def _serializable(obj):
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        return str(obj)

    try:
        payload = {
            "articulos":        [
                a if isinstance(a, dict) else asdict(a)
                for a in resultado["articulos"]
            ],
            "ensayos_clinicos": resultado["ensayos_clinicos"],
            "scielo":           resultado["scielo"],
            "resumen":          resultado["resumen"],
        }
        cache_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=_serializable),
            encoding="utf-8",
        )
        log.info(f"  Cache ETL MÃÂ©dico escrito Ã¢â â {cache_path}")
    except Exception as e:
        log.warning(f"  No se pudo persistir cache ETL MÃÂ©dico: {e}")


# Ã¢ââ¬Ã¢ââ¬ Endpoints FastAPI Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬Ã¢ââ¬

"""
Endpoints sugeridos para api/main.py:

GET /api/articulos
    ?tipo=motora|visual|auditiva|intelectual|psicosocial|visceral
    ?fuente=pubmed|scielo|clinicaltrials
    ?q=keyword
    ?limit=20&offset=0

GET /api/articulos/{pmid}           Ã¢â â detalle completo
GET /api/ensayos                    Ã¢â â ensayos clÃÂ­nicos activos
    ?tipo=motora&estado=RECRUITING
GET /api/tratamientos/{tipo}        Ã¢â â resumen de tratamientos + artÃÂ­culos top
GET /api/buscar?q=exoesqueleto      Ã¢â â bÃÂºsqueda full-text en resÃÂºmenes

CachÃÂ© Redis: TTL 15 dÃÂ­as para listas, 30 dÃÂ­as para artÃÂ­culos individuales
"""


if __name__ == "__main__":
    import json
    resultado = run_etl_medico(max_por_query=5)
    print(json.dumps(resultado["resumen"], indent=2, ensure_ascii=False))

    # Muestra primeros 3 artÃÂ­culos
    for art in resultado["articulos"][:3]:
        print(f"\n[{art.tipo_discapacidad.upper()}] {art.titulo[:80]}")
        print(f"  Fuente: {art.fuente} | Tipo: {art.tipo_estudio}")
        print(f"  URL: {art.url}")
