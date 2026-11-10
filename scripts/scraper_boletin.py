"""
scraper_boletin.py — normas sobre discapacidad publicadas en el Boletín Oficial (sección primera).

Para cada día hábil:
  1. Lee https://www.boletinoficial.gob.ar/seccion/primera/AAAAMMDD (lista de avisos).
  2. Abre solo los avisos candidatos: organismos vinculados (Secretaría Nacional de
     Discapacidad, ANSES, Superintendencia de Servicios de Salud, PAMI, Ministerio de
     Salud) y todos los decretos y leyes.
  3. Se queda con los que mencionan discapacidad en su texto, los clasifica
     (aranceles, pensiones, cud, otras) y guarda un resumen del artículo 1°.

Uso legal y respetuoso: robots.txt del Boletín Oficial solo prohíbe la sección segunda;
se hace una pausa entre pedidos y se identifica el cliente. NO se guardan los anexos
(suelen traer listas de personas con nombre y DNI) ni el texto completo: solo el
resumen y el enlace oficial. Si un resumen contiene un número de DNI, se oculta.

Salida: data/processed/boletin_discapacidad.json (último año).

Uso:  python -m scripts.scraper_boletin                  # hoy y los 3 días anteriores
      python -m scripts.scraper_boletin --desde 2026-09-01 [--hasta 2026-11-10]
"""
from __future__ import annotations

import html
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
PAUSA = 3.0            # segundos entre pedidos (con 1,5 s el Boletín Oficial respondió 429)
DIAS_GUARDADOS = 400

ORGANISMOS = re.compile(
    r"DISCAPACIDAD|SEGURIDAD SOCIAL|ANSES|SERVICIOS DE SALUD|JUBILADOS Y PENSIONADOS|PAMI|MINISTERIO DE SALUD", re.I)
NORMAS_GENERALES = re.compile(r"^(Decreto|Ley|Decisión Administrativa|DNU)\b", re.I)
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


class BoletinInvalido(ValueError):
    pass


def _texto(fragmento: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragmento)).split())


def parsear_seccion(pagina: str, fecha: str) -> list[dict]:
    """Avisos de la página de la sección primera de un día: id, organismo, norma, código."""
    fecha_raw = fecha.replace("-", "")
    avisos = []
    for m in re.finditer(r'href="/detalleAviso/primera/(\d+)/' + fecha_raw + r'"(.*?)</a>', pagina, re.S):
        bloque = m.group(2)
        item = re.search(r'<p class="item">(.*?)</p>', bloque, re.S)
        detalles = [_texto(x) for x in re.findall(r"<small>(.*?)</small>", bloque, re.S)]
        avisos.append({"id": m.group(1), "organismo": _texto(item.group(1)) if item else "",
                       "norma": detalles[0] if detalles else "", "codigo": detalles[1] if len(detalles) > 1 else ""})
    return avisos


def es_candidato(aviso: dict) -> bool:
    return bool(ORGANISMOS.search(aviso["organismo"]) or NORMAS_GENERALES.search(aviso["norma"])
                or RELEVANTE.search(aviso["organismo"]))


def cuerpo_aviso(pagina: str) -> str:
    m = re.search(r'id="cuerpoDetalleAviso"(.*?)(<div[^>]*id="anexos|</section>|<footer)', pagina, re.S)
    if not m:
        raise BoletinInvalido("el aviso no tiene el bloque cuerpoDetalleAviso")
    return _texto(m.group(1))


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


def _get(s: requests.Session, url: str) -> requests.Response:
    """GET con respeto por el servidor: ante 429/503 espera (Retry-After o 30, 60, 120 s) y reintenta."""
    for espera in (30, 60, 120, None):
        r = s.get(url, timeout=40)
        if r.status_code not in (429, 503) or espera is None:
            r.raise_for_status()
            return r
        retry = r.headers.get("Retry-After", "")
        time.sleep(int(retry) if retry.isdigit() else espera)
    raise AssertionError("inalcanzable")


def revisar_dia(s: requests.Session, fecha: str) -> list[dict] | None:
    """Normas relevantes de un día. None si ese día no hubo edición (feriado o fin de semana)."""
    r = _get(s, f"{BASE}/seccion/primera/{fecha.replace('-', '')}")
    avisos = parsear_seccion(r.text, fecha)
    if not avisos:
        return None
    normas = []
    for a in filter(es_candidato, avisos):
        time.sleep(PAUSA)
        url = f"{BASE}/detalleAviso/primera/{a['id']}/{fecha.replace('-', '')}"
        cuerpo = cuerpo_aviso(_get(s, url).text)
        if not (RELEVANTE.search(cuerpo) or RELEVANTE.search(a["organismo"])):
            continue
        normas.append({**a, "fecha": fecha, "url": url, "resumen": resumir(cuerpo),
                       "categoria": categoria(a["organismo"] + " " + cuerpo)})   # el texto completo no se guarda
    return normas


def cargar() -> dict:
    try:
        return json.loads(SALIDA.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"normas": [], "dias_revisados": []}


def guardar(datos: dict, nuevas: dict[str, list[dict]], hoy: date) -> int:
    """Incorpora los días revisados (reemplaza lo que hubiera de esos días). Devuelve normas nuevas."""
    limite = (hoy - timedelta(days=DIAS_GUARDADOS)).isoformat()
    previas = {n["id"] for n in datos["normas"]}
    normas = [n for n in datos["normas"] if n["fecha"] not in nuevas and n["fecha"] >= limite]
    for lista in nuevas.values():
        normas.extend(lista)
    normas.sort(key=lambda n: (n["fecha"], n["id"]), reverse=True)
    dias = sorted({*datos.get("dias_revisados", []), *nuevas}, reverse=True)
    dias = [d for d in dias if d >= limite]
    datos.update({"fuente": "Boletín Oficial de la República Argentina — sección primera",
                  "fuente_url": f"{BASE}/seccion/primera", "actualizado": hoy.isoformat(),
                  "dias_revisados": dias, "normas": normas})
    SALIDA.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return len([n for n in normas if n["id"] not in previas])


def main(argv: list[str]) -> int:
    hoy = date.today()
    hasta = date.fromisoformat(argv[argv.index("--hasta") + 1]) if "--hasta" in argv else hoy
    desde = date.fromisoformat(argv[argv.index("--desde") + 1]) if "--desde" in argv else hasta - timedelta(days=3)
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    datos, revisados, agregadas, sin_edicion = cargar(), 0, 0, 0
    dia = desde
    while dia <= hasta:
        if dia.weekday() < 5:
            normas = revisar_dia(s, dia.isoformat())
            if normas is None:
                sin_edicion += 1
            else:
                agregadas += guardar(datos, {dia.isoformat(): normas}, hoy)   # se guarda día por día
                revisados += 1
                print(f"{dia}: {len(normas)} normas sobre discapacidad", flush=True)
            time.sleep(PAUSA)
        dia += timedelta(days=1)
    print(f"Boletín Oficial: {revisados} días revisados ({sin_edicion} sin edición), {agregadas} normas nuevas, "
          f"{len(datos['normas'])} en total")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (BoletinInvalido, requests.RequestException) as e:
        print(f"ERROR: no se actualizó boletin_discapacidad.json — {e}", file=sys.stderr)
        sys.exit(1)
