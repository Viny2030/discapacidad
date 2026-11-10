"""
scraper_juntas.py — descarga el listado OFICIAL de juntas evaluadoras del CUD.

Fuente: la página https://www.argentina.gob.ar/andis/juntas-evaluadoras-cud
muestra una planilla de Google publicada por el Estado (id abajo). Se lee
esa misma planilla en CSV: es un dato público, sin datos personales de
pacientes (nombre de la junta, localidad, dirección y contacto institucional).

Guarda data/processed/juntas_oficiales.json agrupado por provincia, con los
nombres de provincia del sitio (CABA en lugar de "Ciudad Autónoma de
Buenos Aires"). Solo escribe si el listado cambió y si pasa los controles:
columnas esperadas, las 24 jurisdicciones y al menos 300 juntas.

Uso:  python -m scripts.scraper_juntas
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

import requests

from scripts.scraper_andis import USER_AGENT

ROOT = Path(__file__).resolve().parent.parent
SALIDA = ROOT / "data" / "processed" / "juntas_oficiales.json"
PAGINA = "https://www.argentina.gob.ar/andis/juntas-evaluadoras-cud"
ID_PLANILLA = "1pvcQRLcLr8_gvJfb5rij-QhqUHcs5mS3lkJnBnfqyCw"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{ID_PLANILLA}/export?format=csv"
COLUMNAS = ["nombre", "provincia", "localidad", "direccion", "contacto"]
MINIMO_JUNTAS = 300

PROVINCIAS = ["Buenos Aires", "CABA", "Catamarca", "Chaco", "Chubut", "Córdoba", "Corrientes",
              "Entre Ríos", "Formosa", "Jujuy", "La Pampa", "La Rioja", "Mendoza", "Misiones",
              "Neuquén", "Río Negro", "Salta", "San Juan", "San Luis", "Santa Cruz", "Santa Fe",
              "Santiago del Estero", "Tierra del Fuego", "Tucumán"]


class ListadoInvalido(ValueError):
    pass


def _clave(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()


_ALIAS = {_clave(p): p for p in PROVINCIAS}
_ALIAS.update({"ciudad autonoma de buenos aires": "CABA", "ciudad de buenos aires": "CABA",
               "tierra del fuego, antartida e islas del atlantico sur": "Tierra del Fuego"})


def _limpio(s: str) -> str:
    """Sin etiquetas HTML (la planilla trae algunos <a>), sin espacios de más."""
    s = re.sub(r"<[^>]+>", " ", s or "")
    return " ".join(s.split()).strip(" .")


def parsear_csv(texto: str) -> dict[str, list[dict]]:
    filas = list(csv.DictReader(io.StringIO(texto)))
    if not filas or [c.strip().lower() for c in (filas[0].keys())] != COLUMNAS:
        raise ListadoInvalido(f"columnas inesperadas: {list(filas[0].keys()) if filas else 'sin filas'}")
    por_prov: dict[str, list[dict]] = {p: [] for p in PROVINCIAS}
    for f in filas:
        if _clave(f["nombre"]) == "nombre":          # la planilla repite el encabezado
            continue
        prov = _ALIAS.get(_clave(f["provincia"]))
        if not prov:
            raise ListadoInvalido(f"provincia desconocida: {f['provincia']!r}")
        por_prov[prov].append({k: _limpio(f[k]) for k in ("nombre", "localidad", "direccion", "contacto")})
    faltan = [p for p, v in por_prov.items() if not v]
    total = sum(len(v) for v in por_prov.values())
    if faltan:
        raise ListadoInvalido(f"jurisdicciones sin juntas: {faltan}")
    if total < MINIMO_JUNTAS:
        raise ListadoInvalido(f"solo {total} juntas (mínimo esperado {MINIMO_JUNTAS})")
    for v in por_prov.values():
        v.sort(key=lambda j: (j["localidad"], j["nombre"]))
    return por_prov


def cargar() -> dict:
    try:
        return json.loads(SALIDA.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def guardar(por_prov: dict) -> bool:
    previo = cargar()
    if previo.get("por_provincia") == por_prov:
        return False
    datos = {"fuente": "ANDIS — Listado de juntas evaluadoras para CUD", "fuente_pagina": PAGINA,
             "fuente_datos": CSV_URL, "fecha_lectura": date.today().isoformat(),
             "total": sum(len(v) for v in por_prov.values()), "por_provincia": por_prov}
    SALIDA.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return True


def main() -> int:
    r = requests.get(CSV_URL, headers={"User-Agent": USER_AGENT}, timeout=60)
    r.raise_for_status()
    r.encoding = "utf-8"
    por_prov = parsear_csv(r.text)
    cambio = guardar(por_prov)
    total = sum(len(v) for v in por_prov.values())
    print(f"Juntas oficiales: {total} en 24 jurisdicciones — {'ACTUALIZADO' if cambio else 'sin cambios'}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ListadoInvalido, requests.RequestException) as e:
        print(f"ERROR: no se actualizó juntas_oficiales.json — {e}", file=sys.stderr)
        sys.exit(1)
