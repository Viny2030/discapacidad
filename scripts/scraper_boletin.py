"""
scraper_boletin.py — normas sobre discapacidad publicadas en el Boletín Oficial (sección primera).

Fuente: el listado oficial de PDF del Boletín Oficial, https://otslist.boletinoficial.gob.ar/ots/
(cada día publica el PDF de cada sección con su hash y recibo de la Blockchain Federal Argentina).
Se usa este dominio porque www.boletinoficial.gob.ar no responde a los servidores de GitHub
Actions (timeout de conexión, ver issue #1), y otslist sí.

Para cada día hábil:
  1. Busca en el listado el PDF de la sección 1 (primera) de esa fecha y lo descarga (un pedido).
  2. Extrae el texto con pypdf y lo separa en avisos por la marca de cierre de cada uno
     ("e. 03/11/2026 N° 82345/26 v. 03/11/2026").
  3. Se queda con los avisos que mencionan discapacidad, los clasifica (aranceles,
     asignaciones, pensiones, cud, otras) y guarda un resumen del artículo 1°.

NO se guardan los anexos ni el texto completo: solo el resumen y los enlaces oficiales
(la página de la sección del día y el PDF). Si un resumen contiene un número de DNI, se oculta.

Salida: data/processed/boletin_discapacidad.json (último año).

Uso:  python -m scripts.scraper_boletin                  # hoy y los 3 días anteriores
      python -m scripts.scraper_boletin --desde 2026-01-01 [--hasta 2026-10-31]
"""
from __future__ import annotations

import io
import json
import re
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

from scripts.scraper_andis import USER_AGENT

ROOT = Path(__file__).resolve().parent.parent
SALIDA = ROOT / "data" / "processed" / "boletin_discapacidad.json"
BASE = "https://www.boletinoficial.gob.ar"
OTS = "https://otslist.boletinoficial.gob.ar"
PAUSA = 2.0             # segundos entre pedidos
DIAS_GUARDADOS = 400
MAX_PAGINAS_LISTADO = 40   # ~25 días por página: alcanza para más de 3 años

RELEVANTE = re.compile(
    r"discapacidad|certificado [uú]nico de discapacidad|\bCUD\b|24\.901|22\.431|27\.793|27\.711|"
    r"pensi[oó]n(es)? no contributiva|invalidez laboral|prestaciones b[aá]sicas", re.I)
CATEGORIAS = [
    ("aranceles", re.compile(r"arancel|nomenclador|valores? de las prestaciones", re.I)),
    ("asignaciones", re.compile(r"asignaci[oó]n(es)? familiar|asignaci[oó]n universal|Ley N° 24\.714", re.I)),
    ("pensiones", re.compile(r"pensi[oó]n|invalidez|rehabilitaci[oó]n del beneficio", re.I)),
    ("cud", re.compile(r"certificado [uú]nico de discapacidad|\bCUD\b|juntas? evaluadora", re.I)),
]
DNI = re.compile(r"(D\.?\s?N\.?\s?I\.?\s*(N[°º]\s*)?:?\s*)\d{1,2}\.?\d{3}\.?\d{3}", re.I)

FIN_AVISO = re.compile(r"e\.\s*\d{2}/\d{2}/\d{4}\s*N[°º]\s*\d+/\d+\s*v\.\s*\d{2}/\d{2}/\d{4}")
TIPOS = (r"(?:Resolución Conjunta|Resolución Sintetizada|Resolución General|Resolución|Decreto|Disposición Conjunta|"
         r"Disposición|Decisión Administrativa|Ley|Nota Externa|Comunicación\s*“?[A-Z]?”?|Acordada|Instrucción General|Circular)")
# Con código GDE (RESOL-2026-3702-APN-SND#MS) o sin él; el cuerpo empieza con la fecha o con VISTO.
ENCABEZADO = re.compile(r"(?P<norma>" + TIPOS + r"\s+(?:N[°º]\s*)?[\d.]+/\d{4})"
                        r"(?:\s+(?P<codigo>[A-Z]{2,}-\d{4}-[\dA-Z]+-[A-Z0-9#\-]+))?")
CUERPO_INICIO = re.compile(r"Ciudad de Buenos Aires,? \d{2}/\d{2}/\d{4}|VISTO|\d{2}/\d{2}/\d{4} A LAS ")
CABECERA_PAGINA = re.compile(r"BOLET[IÍ]N OFICIAL N[º°] [\d.]+ - Primera Secci[oó]n( \d+)? [A-Za-zéáÁÉ]+ \d+ de [a-z]+ de \d{4}( \d+)?", re.I)
MARCAS = re.compile(r"#[IF]\d+[IF]#")


class BoletinInvalido(ValueError):
    pass


# ── Listado de PDF oficiales ────────────────────────────────────────────────────

def parsear_listado(html: str) -> dict[str, str]:
    """{AAAA-MM-DD: url del PDF de la sección 1} de una página del listado otslist."""
    salida = {}
    for bloque in re.split(r'<h4 class="text-left">', html)[1:]:
        m = re.match(r"(\d{2})-(\d{2})-(\d{4})", bloque)
        if not m:
            continue
        fecha = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        fila = re.search(r"<tr>\s*<td>\s*1\s*</td>.*?href=\"(/ots/download/[0-9a-f]+/0/)\"", bloque, re.S)
        if fila:
            salida[fecha] = OTS + fila.group(1)
    return salida


def pdfs_del_periodo(s: requests.Session, desde: str, hasta: str) -> dict[str, str]:
    """Recorre el listado (de lo más nuevo a lo más viejo) hasta cubrir el período."""
    encontrados: dict[str, str] = {}
    for pagina in range(1, MAX_PAGINAS_LISTADO + 1):
        fechas = parsear_listado(_get(s, f"{OTS}/ots/?page={pagina}").text)
        if not fechas:
            if pagina == 1:
                raise BoletinInvalido("el listado de PDF oficiales vino vacío o cambió de formato")
            break
        encontrados.update({f: u for f, u in fechas.items() if desde <= f <= hasta})
        if min(fechas) < desde:
            break
        time.sleep(PAUSA)
    return encontrados


# ── Texto del PDF ───────────────────────────────────────────────────────────────

def texto_pdf(contenido: bytes) -> str:
    from pypdf import PdfReader
    paginas = PdfReader(io.BytesIO(contenido)).pages
    return re.sub(r"\s+", " ", " ".join(p.extract_text() or "" for p in paginas))


def separar_avisos(texto: str) -> list[dict]:
    """Avisos del PDF de la sección primera: organismo, norma, código y cuerpo."""
    texto = MARCAS.sub(" ", CABECERA_PAGINA.sub(" ", texto))
    avisos = []
    for parte in FIN_AVISO.split(texto)[:-1]:          # lo que sigue a la última marca no es un aviso
        # El encabezado es la ÚLTIMA norma nombrada antes de que empiece el cuerpo ("Ciudad de Buenos
        # Aires, dd/mm", "VISTO" o la fecha de una comunicación). Así se saltea el sumario del día, que
        # precede al primer aviso, y las normas citadas dentro del texto, que vienen después.
        cuerpo = CUERPO_INICIO.search(parte)
        tope = cuerpo.start() if cuerpo else 400
        candidatos = [c for c in ENCABEZADO.finditer(parte, 0, tope + 1) if c.end() <= tope + 1]
        enc = candidatos[-1] if candidatos else None
        if not enc:
            continue      # edictos y avisos oficiales: no son normas y nombran personas; no se guardan
        previo = parte[:enc.start()].strip()
        org = re.search(r"([A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ0-9 ,.\-–()“”\"]{2,200})$", previo)
        avisos.append({"organismo": " ".join((org.group(1) if org else previo[-120:]).split()).strip(" -–"),
                       "norma": " ".join(enc.group("norma").split()), "codigo": enc.group("codigo") or "",
                       "cuerpo": parte[enc.end():].strip()})
    return avisos


def resumir(cuerpo: str) -> str:
    """Artículo 1° (o el comienzo de la parte resolutiva), sin DNI, hasta ~420 caracteres."""
    m = re.search(r"ART[IÍ]CULO 1[°º]?\.?\s*-?\s*(.*?)(?=ART[IÍ]CULO 2|$)", cuerpo, re.S)
    texto = m.group(1) if m else cuerpo
    # art. 1° muy corto o que anuncia un texto ("… por el siguiente: “"): seguir leyendo
    if m and (len(texto) < 160 or texto.rstrip().endswith((":", "“", '"', "«"))):
        texto = cuerpo[m.start(1):]
    texto = DNI.sub(r"\1[omitido]", texto).strip()
    return texto if len(texto) <= 420 else texto[:417].rsplit(" ", 1)[0] + "…"


def categoria(texto: str) -> str:
    for nombre, patron in CATEGORIAS:
        if patron.search(texto):
            return nombre
    return "otras"


def normas_del_dia(fecha: str, pdf_url: str, texto: str) -> list[dict]:
    normas = []
    for i, a in enumerate(separar_avisos(texto)):
        if not (RELEVANTE.search(a["cuerpo"]) or RELEVANTE.search(a["organismo"])):
            continue
        normas.append({"id": f"{fecha.replace('-', '')}-{a['codigo'] or a['norma'].replace(' ', '_')}", "organismo": a["organismo"],
                       "norma": a["norma"], "codigo": a["codigo"], "fecha": fecha,
                       "url": f"{BASE}/seccion/primera/{fecha.replace('-', '')}", "pdf": pdf_url,
                       "resumen": resumir(a["cuerpo"]),
                       "categoria": categoria(a["organismo"] + " " + a["cuerpo"])})   # el texto completo no se guarda
    return normas


# ── Red y almacenamiento ────────────────────────────────────────────────────────

def _get(s: requests.Session, url: str) -> requests.Response:
    """GET con respeto por el servidor: ante 429/503 espera (Retry-After o 30, 60, 120 s) y reintenta."""
    for espera in (30, 60, 120, None):
        r = s.get(url, timeout=90)
        if r.status_code not in (429, 503) or espera is None:
            r.raise_for_status()
            return r
        retry = r.headers.get("Retry-After", "")
        time.sleep(int(retry) if retry.isdigit() else espera)
    raise AssertionError("inalcanzable")


def cargar() -> dict:
    try:
        return json.loads(SALIDA.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"normas": [], "dias_revisados": []}


def guardar(datos: dict, nuevas: dict[str, list[dict]], hoy: date) -> int:
    """Incorpora los días revisados (reemplaza lo que hubiera de esos días). Devuelve normas nuevas."""
    limite = (hoy - timedelta(days=DIAS_GUARDADOS)).isoformat()
    previas = {(n["fecha"], n["codigo"]) for n in datos["normas"]}
    normas = [n for n in datos["normas"] if n["fecha"] not in nuevas and n["fecha"] >= limite]
    for lista in nuevas.values():
        normas.extend(lista)
    normas.sort(key=lambda n: (n["fecha"], n["id"]), reverse=True)
    dias = sorted({*datos.get("dias_revisados", []), *nuevas}, reverse=True)
    dias = [d for d in dias if d >= limite]
    datos.update({"fuente": "Boletín Oficial de la República Argentina — sección primera (PDF oficial)",
                  "fuente_url": f"{OTS}/ots/", "actualizado": hoy.isoformat(),
                  "dias_revisados": dias, "normas": normas})
    SALIDA.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return len([n for n in normas if (n["fecha"], n["codigo"]) not in previas])


def main(argv: list[str]) -> int:
    hoy = date.today()
    hasta = date.fromisoformat(argv[argv.index("--hasta") + 1]) if "--hasta" in argv else hoy
    desde = date.fromisoformat(argv[argv.index("--desde") + 1]) if "--desde" in argv else hasta - timedelta(days=3)
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    pdfs = pdfs_del_periodo(s, desde.isoformat(), hasta.isoformat())
    datos, agregadas = cargar(), 0
    for fecha in sorted(pdfs):
        time.sleep(PAUSA)
        texto = texto_pdf(_get(s, pdfs[fecha]).content)
        avisos = separar_avisos(texto)
        if not avisos:
            raise BoletinInvalido(f"el PDF del {fecha} no tiene avisos reconocibles")
        normas = normas_del_dia(fecha, pdfs[fecha], texto)
        agregadas += guardar(datos, {fecha: normas}, hoy)   # se guarda día por día
        print(f"{fecha}: {len(avisos)} avisos, {len(normas)} sobre discapacidad", flush=True)
    print(f"Boletín Oficial: {len(pdfs)} días revisados, {agregadas} normas nuevas, {len(datos['normas'])} en total")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (BoletinInvalido, requests.RequestException) as e:
        print(f"ERROR: no se actualizó boletin_discapacidad.json — {e}", file=sys.stderr)
        sys.exit(1)
