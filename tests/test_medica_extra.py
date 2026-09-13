"""
test_medica_extra.py
Tests para la búsqueda médica curada por condición específica (incluye
Tourette) y la taxonomía de especialidades médicas (/api/condiciones y
/api/especialidades).

Solo cubre lo que NO requiere conexión externa (listados y validaciones de
datos/404): los endpoints de detalle por condición/especialidad consultan
PubMed en vivo, igual que /api/tratamientos/{tipo} y /api/buscar, que
tampoco se testean contra la red real en este repositorio.
"""
import pytest
from scripts.api_medica import CONDICIONES_ESPECIFICAS, ESPECIALIDADES_MEDICAS

TIPOS_VALIDOS = {"motora", "visual", "auditiva", "intelectual", "psicosocial", "visceral"}


# ── Datos: CONDICIONES_ESPECIFICAS ────────────────────────────────────────────

def test_condiciones_no_vacio():
    assert len(CONDICIONES_ESPECIFICAS) >= 5


def test_condiciones_incluye_tourette():
    assert "tourette" in CONDICIONES_ESPECIFICAS
    assert "Tourette" in CONDICIONES_ESPECIFICAS["tourette"]["nombre"]


def test_condiciones_campos_obligatorios():
    campos = ["nombre", "tipo", "descripcion", "query_pubmed"]
    for cid, datos in CONDICIONES_ESPECIFICAS.items():
        for c in campos:
            assert c in datos, f"Condición '{cid}' sin campo '{c}'"


def test_condiciones_tipo_valido():
    for cid, datos in CONDICIONES_ESPECIFICAS.items():
        assert datos["tipo"] in TIPOS_VALIDOS, f"Condición '{cid}' con tipo inválido: {datos['tipo']}"


# ── Datos: ESPECIALIDADES_MEDICAS ─────────────────────────────────────────────

def test_especialidades_no_vacio():
    assert len(ESPECIALIDADES_MEDICAS) >= 3


def test_especialidades_incluye_neurologia_para_tourette():
    assert "neurologia" in ESPECIALIDADES_MEDICAS
    assert "tourette" in ESPECIALIDADES_MEDICAS["neurologia"]["condiciones_relacionadas"]


def test_especialidades_condiciones_relacionadas_existen():
    for eid, datos in ESPECIALIDADES_MEDICAS.items():
        assert len(datos["condiciones_relacionadas"]) >= 1, f"Especialidad '{eid}' sin condiciones"
        for cid in datos["condiciones_relacionadas"]:
            assert cid in CONDICIONES_ESPECIFICAS, f"Especialidad '{eid}' referencia condición inexistente '{cid}'"


# ── Endpoint /api/condiciones (listado, sin red) ──────────────────────────────

def test_endpoint_listar_condiciones(client):
    r = client.get("/api/condiciones")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == len(CONDICIONES_ESPECIFICAS)
    ids = [c["id"] for c in data["condiciones"]]
    assert "tourette" in ids


def test_endpoint_condicion_inexistente(client):
    r = client.get("/api/condiciones/no-existe-esta-condicion")
    assert r.status_code == 404


# ── Endpoint /api/especialidades (listado + detalle, sin red) ────────────────

def test_endpoint_listar_especialidades(client):
    r = client.get("/api/especialidades")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == len(ESPECIALIDADES_MEDICAS)
    ids = [e["id"] for e in data["especialidades"]]
    assert "neurologia" in ids


def test_endpoint_detalle_especialidad_neurologia(client):
    r = client.get("/api/especialidades/neurologia")
    assert r.status_code == 200
    data = r.json()
    assert data["nombre"] == "Neurología"
    condiciones_ids = [c["id"] for c in data["condiciones"]]
    assert "tourette" in condiciones_ids


def test_endpoint_especialidad_inexistente(client):
    r = client.get("/api/especialidades/no-existe-esta-especialidad")
    assert r.status_code == 404
