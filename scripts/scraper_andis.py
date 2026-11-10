"""
scraper_andis.py — lee el último informe estadístico OFICIAL del Registro
Nacional de Personas con Discapacidad (RNPcD) y lo guarda en
data/processed/andis_oficial.json.

Fuente: https://www.argentina.gob.ar/andis/estadisticas/datos-estadisticos
(página pública del Estado nacional; el informe es un PDF público).

Reglas del scraper (uso legal y respetuoso):
  - Solo lee páginas y PDF públicos; no inicia sesión ni toca datos personales.
  - Respeta robots.txt de argentina.gob.ar (Crawl-delay: 10; la ruta
    /sites/default/files/ no está prohibida salvo /infoleg/).
  - Se identifica con un User-Agent propio y hace 2 pedidos por corrida.

Si el informe no se puede leer o los números no cierran (las provincias,
los tipos y los tramos de edad tienen que sumar el total), NO se toca el
JSON guardado y el proceso termina con error para que GitHub Actions avise.

Uso:  python -m scripts.scraper_andis            (descarga y actualiza)
      python -m scripts.scraper_andis --pdf X.pdf (lee un PDF local)
"""
from __future__ import annotations

import io
import json
import re
import sys
import time
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

import requests

ROOT = Path(__file__).resolve().parent.parent
SALIDA = ROOT / "data" / "processed" / "andis_oficial.json"
PAGINA = "https://www.argentina.gob.ar/andis/estadisticas/datos-estadisticos"
USER_AGENT = "ObservatorioDiscapacidad/1.0 (+https://discapacidad.viny2030.com.ar)"
CRAWL_DELAY = 10  # segundos, según robots.txt de argentina.gob.ar

MESES = {m: i for i, m in enumerate(
    ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
     "septiembre", "octubre", "noviembre", "diciembre"], start=1)}

# nombre canónico del sitio -> cómo aparece en la tabla del informe
PROVINCIAS = {
    "Buenos Aires": ["Buenos Aires"], "CABA": ["CABA", "Ciudad Autónoma de Buenos Aires"],
    "Catamarca": ["Catamarca"], "Chaco": ["Chaco"], "Chubut": ["Chubut"], "Córdoba": ["Córdoba"],
    "Corrientes": ["Corrientes"], "Entre Ríos": ["Entre Ríos"], "Formosa": ["Formosa"],
    "Jujuy": ["Jujuy"], "La Pampa": ["La Pampa"], "La Rioja": ["La Rioja"], "Mendoza": ["Mendoza"],
    "Misiones": ["Misiones"], "Neuquén": ["Neuquén"], "Río Negro": ["Río Negro", "Rio Negro"],
    "Salta": ["Salta"], "San Juan": ["San Juan"], "San Luis": ["San Luis"],
    "Santa Cruz": ["Santa Cruz"], "Santa Fe": ["Santa Fe"],
    "Santiago del Estero": ["Santiago del Estero", "Santiago Del Estero"],
    "Tierra del Fuego": ["Tierra del Fuego", "Tierra Del Fuego"], "Tucumán": ["Tucumán", "Tucuman"],
}
TIPOS = {
    "Física motora": ["Física Motora"], "Mental": ["Mental"], "Intelectual": ["Intelectual"],
    "Sensorial auditiva": ["Sensorial Auditiva"], "Física visceral": ["Física Visceral"],
    "Sensorial visual": ["Sensorial Visual"], "Más de un tipo": ["Más de un tipo de deficiencia"],
}
EDADES = {"0 a 14 años": ["De 0 a 14 años"], "15 a 64 años": ["De 15 a 64 años"],
          "65 años y más": ["De 65 años y más"]}

_NUM = r"(\d{1,3}(?:\.\d{3})*)"


class InformeInvalido(ValueError):
    """El PDF no tiene la estructura esperada o sus números no cierran."""


def _entero(s: str) -> int:
    return int(s.replace(".", ""))


def _fila(texto: str, etiquetas: list[str]) -> int:
    """Busca una fila de tabla 'Etiqueta 12.345 6,7%' y devuelve la cantidad."""
    for et in etiquetas:
        m = re.search(rf"(?<![\wÁÉÍÓÚáéíóúñ]){re.escape(et)}\s+{_NUM}\s+\d{{1,3}},\d%", texto)
        if m:
            return _entero(m.group(1))
    raise InformeInvalido(f"no se encontró la fila de tabla «{etiquetas[0]}»")


def _tabla(texto: str, filas: dict[str, list[str]]) -> dict[str, int]:
    return {nombre: _fila(texto, etiquetas) for nombre, etiquetas in filas.items()}


def texto_de_pdf(contenido: bytes) -> str:
    from pypdf import PdfReader
    paginas = PdfReader(io.BytesIO(contenido)).pages
    return re.sub(r"\s+", " ", " ".join(p.extract_text() or "" for p in paginas))


def parsear_informe(texto: str) -> dict:
    """Extrae y valida los datos del informe. Lanza InformeInvalido si algo no cierra."""
    plano = texto.replace("n oviembre", "noviembre")  # pypdf a veces parte una palabra
    m = re.search(r"Datos actualizados a (\w+) de (\d{4})", plano)
    if not m or m.group(1).lower() not in MESES:
        raise InformeInvalido("no se encontró la fecha de corte («Datos actualizados a …»)")
    corte = date(int(m.group(2)), MESES[m.group(1).lower()], 1)

    m = re.search(rf"{_NUM} personas con CUD vigente", plano)
    if not m:
        raise InformeInvalido("no se encontró el total de personas con CUD vigente")
    total = _entero(m.group(1))
    m = re.search(r"Un (\d+,\d+)% de la población nacional", plano)
    porcentaje = float(m.group(1).replace(",", ".")) if m else None

    provincias = _tabla(plano, PROVINCIAS)
    tipos = _tabla(plano, TIPOS)
    edades = _tabla(plano, EDADES)
    for nombre, valores in (("provincias", provincias), ("tipos", tipos), ("edades", edades)):
        suma = sum(valores.values())
        if suma != total:
            raise InformeInvalido(f"las {nombre} suman {suma:,} y el total es {total:,}")

    return {
        "fecha_corte": corte.isoformat(),
        "total_cud_vigentes": total,
        "porcentaje_poblacion": porcentaje,
        "por_provincia": dict(sorted(provincias.items(), key=lambda kv: -kv[1])),
        "por_tipo": dict(sorted(tipos.items(), key=lambda kv: -kv[1])),
        "por_edad": edades,
    }


def buscar_pdf(html: str) -> str:
    """Devuelve la URL del PDF de 'texto plano' (o del primer PDF) de la página oficial."""
    pdfs = re.findall(r'href="([^"]+\.pdf)"', html)
    if not pdfs:
        raise InformeInvalido("la página oficial no tiene ningún PDF enlazado")
    preferido = [p for p in pdfs if "texto_plano" in p] or pdfs
    return urljoin(PAGINA, preferido[0])


def cargar_guardado() -> dict:
    try:
        return json.loads(SALIDA.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def guardar(datos: dict, pdf_url: str) -> bool:
    """Escribe el JSON solo si cambió algo del informe. Devuelve True si escribió."""
    previo = cargar_guardado()
    oficial = {**datos, "fuente": "ANDIS — Registro Nacional de Personas con Discapacidad",
               "fuente_pagina": PAGINA, "fuente_pdf": pdf_url}
    if previo.get("oficial") == oficial:
        return False
    nuevo = {**previo, "oficial": oficial, "fecha_lectura": date.today().isoformat()}
    SALIDA.write_text(json.dumps(nuevo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def main(argv: list[str]) -> int:
    if "--pdf" in argv:
        ruta = Path(argv[argv.index("--pdf") + 1])
        datos, pdf_url = parsear_informe(texto_de_pdf(ruta.read_bytes())), cargar_guardado().get("oficial", {}).get("fuente_pdf", str(ruta))
    else:
        s = requests.Session()
        s.headers["User-Agent"] = USER_AGENT
        r = s.get(PAGINA, timeout=30)
        r.raise_for_status()
        pdf_url = buscar_pdf(r.text)
        time.sleep(CRAWL_DELAY)
        r = s.get(pdf_url, timeout=60)
        r.raise_for_status()
        datos = parsear_informe(texto_de_pdf(r.content))
    cambio = guardar(datos, pdf_url)
    print(f"Informe oficial: corte {datos['fecha_corte']}, {datos['total_cud_vigentes']:,} CUD vigentes "
          f"— {'ACTUALIZADO' if cambio else 'sin cambios'} ({pdf_url})")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (InformeInvalido, requests.RequestException) as e:
        print(f"ERROR: no se actualizó andis_oficial.json — {e}", file=sys.stderr)
        sys.exit(1)
