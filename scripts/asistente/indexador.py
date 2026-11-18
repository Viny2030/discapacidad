"""
indexador.py — construye el índice vectorial local (chromadb, sin servicios
externos) a partir ÚNICAMENTE de fuentes ya verificadas del repositorio.
Se corre junto al ETL existente (scheduler cada 15 días) para mantenerse
sincronizado con datos_cud.py y el boletín oficial.

ESTADO: preparado para Fase 3 (auditoría — Anexo 5.1, Asistente de consulta
normativa). Requiere agregar `chromadb` a requirements.txt (no incluido
todavía a propósito, para no afectar el build actual) y aún no tiene:
  - scripts/asistente/consulta.py (resolución de la pregunta contra el índice)
  - scripts/api_asistente.py (router FastAPI con POST /api/v1/asistente/consulta-normativa)
Ninguno de los dos se especificó con código completo en la auditoría (solo el
contrato de API), así que no se inventan aquí — quedan como siguiente paso.
Este archivo no se importa desde main.py ni desde ningún test: es autónomo.
"""
from __future__ import annotations

import json
from pathlib import Path

import chromadb

from scripts.datos_cud import (
    REQUISITOS_GENERALES, REQUISITOS_POR_TIPO, FORMULARIOS, FAQ,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
INDICE_DIR = BASE_DIR / "data" / "processed" / "indice_normativo"
BOLETIN_JSON = BASE_DIR / "data" / "processed" / "boletin_discapacidad.json"


def _documentos_desde_datos_cud() -> list[dict]:
    """Aplana las estructuras de datos_cud.py en documentos indexables con su fuente."""
    docs = []
    for item in FAQ:
        docs.append({"texto": f"{item['pregunta']} {item['respuesta']}",
                     "fuente": "datos_cud.FAQ", "url": item.get("url", "")})
    for req in REQUISITOS_GENERALES:
        docs.append({"texto": f"{req['documento']}: {req['detalle']}",
                     "fuente": "datos_cud.REQUISITOS_GENERALES", "url": req.get("url", "")})
    for tipo, info in REQUISITOS_POR_TIPO.items():
        docs.append({"texto": f"Discapacidad {tipo}: {info['descripcion']} "
                               f"Documentos adicionales: {', '.join(info['documentos_adicionales'])}",
                     "fuente": f"datos_cud.REQUISITOS_POR_TIPO.{tipo}", "url": ""})
    for form in FORMULARIOS:
        docs.append({"texto": f"{form['nombre']}: {form['descripcion']}",
                     "fuente": "datos_cud.FORMULARIOS", "url": form.get("url", "")})
    return docs


def _documentos_desde_boletin() -> list[dict]:
    """Normas del Boletín Oficial ya scrapeadas (scraper_boletin.py)."""
    if not BOLETIN_JSON.exists():
        return []
    data = json.loads(BOLETIN_JSON.read_text(encoding="utf-8"))
    return [{"texto": n["titulo"] + " " + n.get("resumen", ""),
             "fuente": "boletin_oficial", "url": n.get("url", "")}
            for n in data.get("normas", [])]


def construir_indice() -> int:
    """Reconstruye el índice completo. Devuelve la cantidad de documentos indexados."""
    cliente = chromadb.PersistentClient(path=str(INDICE_DIR))
    coleccion = cliente.get_or_create_collection("normativa_discapacidad")
    documentos = _documentos_desde_datos_cud() + _documentos_desde_boletin()
    if not documentos:
        return 0
    coleccion.upsert(
        ids=[f"doc-{i}" for i in range(len(documentos))],
        documents=[d["texto"] for d in documentos],
        metadatas=[{"fuente": d["fuente"], "url": d["url"]} for d in documentos],
    )
    return len(documentos)


if __name__ == "__main__":
    print(f"Documentos indexados: {construir_indice()}")
