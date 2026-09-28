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
    resumen_es: str = ""   # traducción/adaptación al español (Tarea 8)


# ── PubMed ─────────────────────────────────────────────────────────────────────

PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_KEY  = os.getenv("PUBMED_API_KEY", "")  # opcional — 10 req/s con key vs 3 sin key


# ── Traductor científico (resumen_es) ─────────────────────────────────────────

# Diccionario de términos técnicos frecuentes (inglés → español)
_TERMINOS = {
    "randomized controlled trial": "ensayo controlado aleatorizado",
    "systematic review": "revisión sistemática",
    "meta-analysis": "metaanálisis",
    "cochlear implant": "implante coclear",
    "exoskeleton": "exoesqueleto",
    "spinal cord injury": "lesión medular",
    "brain computer interface": "interfaz cerebro-computadora",
    "gene therapy": "terapia génica",
    "stem cell": "célula madre",
    "prosthesis": "prótesis",
    "prosthetic": "protésico",
    "rehabilitation": "rehabilitación",
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
    "clinical trial": "ensayo clínico",
    "adverse events": "eventos adversos",
    "quality of life": "calidad de vida",
    "intervention": "intervención",
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
    "years": "años",
}

# FIX: memoria de traducciones ya hechas. Se precarga desde la caché del ETL
# anterior, así cada resumen se traduce UNA sola vez entre corridas y no se
# agota la cuota diaria gratuita de MyMemory (antes se re-traducía todo cada
# corrida y ~56% terminaba en el fallback parcial).
_MARCA_FALLBACK = "[traducción automática parcial]"
_TRAD_MEMO: dict = {}
_TRAD_PMID: dict = {}   # traducciones guardadas en el repo (data/processed/traducciones_es.json)
_TRAD_MEMO_CARGADA = False
_MYMEMORY_AGOTADO = False


def _clave_trad(texto_en: str) -> str:
    return " ".join((texto_en or "")[:1500].split())


def _precargar_traducciones() -> None:
    global _TRAD_MEMO_CARGADA
    if _TRAD_MEMO_CARGADA:
        return
    _TRAD_MEMO_CARGADA = True
    import json
    from pathlib import Path
    # Traducciones persistentes (versionadas en el repo): sobreviven a cada
    # despliegue de Railway, a diferencia de etl_medico_cache.json.
    try:
        ruta_pmid = Path(__file__).resolve().parent.parent / "data" / "processed" / "traducciones_es.json"
        if ruta_pmid.exists():
            for pmid, es in json.loads(ruta_pmid.read_text(encoding="utf-8")).items():
                if es and "parcial]" not in es:
                    _TRAD_PMID[str(pmid)] = es
    except Exception:
        pass
    try:
        ruta = Path(__file__).resolve().parent.parent / "data" / "processed" / "etl_medico_cache.json"
        if not ruta.exists():
            return
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        for a in datos.get("articulos", []):
            es = a.get("resumen_es") or ""
            if es and "parcial]" not in es and a.get("resumen"):
                _TRAD_MEMO[_clave_trad(a["resumen"])] = es
    except Exception:
        pass


def traduccion_guardada(pmid) -> str:
    """Devuelve la traducción ya guardada para un PMID, o "" si no hay."""
    if not pmid:
        return ""
    _precargar_traducciones()
    return _TRAD_PMID.get(str(pmid), "")


def guardar_traducciones(articulos) -> int:
    """
    Agrega a data/processed/traducciones_es.json las traducciones nuevas y
    válidas (no el fallback parcial). No borra ni reemplaza las existentes.
    Devuelve cuántas se agregaron.
    """
    import json
    from pathlib import Path
    ruta = Path(__file__).resolve().parent.parent / "data" / "processed" / "traducciones_es.json"
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}
    except Exception:
        return 0
    nuevas = 0
    for a in articulos or []:
        d = a if isinstance(a, dict) else getattr(a, "__dict__", {})
        pmid = str(d.get("pmid") or "")
        es = d.get("resumen_es") or ""
        if pmid and es and "parcial]" not in es and pmid not in datos:
            datos[pmid] = es
            _TRAD_PMID[pmid] = es
            nuevas += 1
    if nuevas:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(dict(sorted(datos.items())), ensure_ascii=False, indent=1),
                        encoding="utf-8")
    return nuevas


def traducir_resumen(texto_en: str, max_chars: int = 600) -> str:
    """
    Tarea 8 — Traductor científico para resúmenes PubMed.

    Estrategia por niveles (en orden de disponibilidad):
      1. MyMemory API (gratuita, 5k palabras/día sin key)
      2. LibreTranslate pública (si MyMemory falla)
      3. Sustitución de terminología técnica + resumen acortado

    Siempre devuelve texto en español, nunca lanza excepción.
    """
    if not texto_en or not texto_en.strip():
        return ""

    global _MYMEMORY_AGOTADO
    _precargar_traducciones()
    clave = _clave_trad(texto_en)
    if clave in _TRAD_MEMO:
        return _TRAD_MEMO[clave][:max_chars]

    snippet = texto_en[:1500]  # traducimos hasta 1500 chars para no agotar cuotas

    # Nivel 1 — MyMemory (gratuita, ~5 000 palabras/día)
    try:
        if _MYMEMORY_AGOTADO:
            raise RuntimeError("cuota MyMemory agotada en esta ejecución")
        r = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": snippet[:500], "langpair": "en|es", "de": "observatorio@discapacidad.ar"},
            timeout=8,
        )
        if r.ok:
            j = r.json()
            if j.get("quotaFinished") or str(j.get("responseStatus")) == "429":
                _MYMEMORY_AGOTADO = True
            if j.get("responseStatus") == 200:
                traducido = j["responseData"]["translatedText"]
                if traducido and len(traducido) > 30 and "MYMEMORY WARNING" not in traducido.upper():
                    _TRAD_MEMO[clave] = traducido
                    return traducido[:max_chars]
    except Exception:
        pass

    # Nivel 2 — LibreTranslate pública
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

    # Nivel 3 — sustitución de terminología + recorte (fallback sin red)
    resultado = snippet[:max_chars]
    for en, es in _TERMINOS.items():
        resultado = re.sub(re.escape(en), es, resultado, flags=re.IGNORECASE)
    # Agregar nota al pie para que el lector sepa que es automático
    return resultado + " [traducción automática parcial]"


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

            # Traducción al español (Tarea 8)
            # FIX: primero se usa la traducción guardada en el repo (si existe)
            a.resumen_es = traduccion_guardada(a.pmid) or traducir_resumen(a.resumen)

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
    Corre el ETL completo de fuentes médicas.
    Retorna dict con listas de artículos y ensayos por tipo.
    Persiste el resultado en data/processed/etl_medico_cache.json (Tarea 11).
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

    # ── Tarea 11: Persistencia en disco ──────────────────────────────────────
    _persistir_resultado_etl(resultado)

    return resultado


def _persistir_resultado_etl(resultado: dict) -> None:
    """
    Tarea 11 — Serializa el resultado del ETL a JSON para que api_medica.py
    lo consuma con caché sin volver a llamar a PubMed en cada request.
    """
    import json
    from pathlib import Path
    from dataclasses import asdict

    cache_dir = Path(__file__).resolve().parent.parent / "data" / "processed"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / "etl_medico_cache.json"

    # Convertir dataclasses a dict (los artículos de PubMed son Articulo)
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
        log.info(f"  Cache ETL Médico escrito → {cache_path}")
    except Exception as e:
        log.warning(f"  No se pudo persistir cache ETL Médico: {e}")

    # FIX: conservar las traducciones nuevas en data/processed/traducciones_es.json
    # (el workflow semanal etl_medico.yml lo commitea con `git add data/`).
    try:
        n = guardar_traducciones(resultado.get("articulos", []))
        log.info(f"  Traducciones nuevas guardadas: {n}")
    except Exception as e:
        log.warning(f"  No se pudieron guardar las traducciones: {e}")


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
