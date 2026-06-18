"""
test_cud.py
Tests para todos los endpoints del módulo CUD (/api/cud/...).
Datos estáticos de datos_cud.py — no requieren conexión externa.
"""
import pytest


# ── /api/cud ──────────────────────────────────────────────────────────────────

def test_cud_info_general(client):
    r = client.get("/api/cud")
    assert r.status_code == 200
    data = r.json()
    assert data["gratuito"] is True
    assert data["vence"] is False
    assert "tipos_discapacidad" in data
    assert len(data["tipos_discapacidad"]) >= 5
    assert data["total_provincias_con_junta"] == 24


# ── /api/cud/formularios ──────────────────────────────────────────────────────

def test_formularios(client):
    r = client.get("/api/cud/formularios")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    for f in data["formularios"]:
        assert "nombre" in f
        assert "url" in f


# ── /api/cud/requisitos ───────────────────────────────────────────────────────

def test_requisitos_generales(client):
    r = client.get("/api/cud/requisitos")
    assert r.status_code == 200
    data = r.json()
    assert "generales" in data
    assert len(data["generales"]) >= 4
    assert "tipos_disponibles" in data


@pytest.mark.parametrize("tipo", ["motora", "visual", "auditiva", "intelectual", "psicosocial", "visceral"])
def test_requisitos_por_tipo(client, tipo):
    r = client.get(f"/api/cud/requisitos?tipo={tipo}")
    assert r.status_code == 200
    data = r.json()
    assert data["tipo"] == tipo
    assert "documentos_adicionales" in data
    assert len(data["documentos_adicionales"]) >= 1


def test_requisitos_tipo_invalido(client):
    r = client.get("/api/cud/requisitos?tipo=inexistente")
    assert r.status_code == 400


# ── /api/cud/pasos ────────────────────────────────────────────────────────────

def test_pasos(client):
    r = client.get("/api/cud/pasos")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 4
    for p in data["pasos"]:
        assert "titulo" in p
        assert "descripcion" in p


# ── /api/cud/beneficios ───────────────────────────────────────────────────────

def test_beneficios(client):
    r = client.get("/api/cud/beneficios")
    assert r.status_code == 200
    data = r.json()
    assert data["total_categorias"] >= 4
    categorias = [c["categoria"] for c in data["categorias"]]
    assert "Salud" in categorias
    assert "Transporte" in categorias
    assert "Trabajo" in categorias


@pytest.mark.parametrize("cat", ["Salud", "Transporte", "Educación", "Trabajo"])
def test_beneficios_por_categoria(client, cat):
    r = client.get(f"/api/cud/beneficios?categoria={cat}")
    assert r.status_code == 200
    data = r.json()
    assert data["categoria"] == cat
    assert len(data["beneficios"]) >= 1


def test_beneficios_categoria_invalida(client):
    r = client.get("/api/cud/beneficios?categoria=Inexistente")
    assert r.status_code == 404


# ── /api/cud/juntas ───────────────────────────────────────────────────────────

def test_juntas_listado(client):
    r = client.get("/api/cud/juntas")
    assert r.status_code == 200
    data = r.json()
    assert data["total_provincias"] == 24
    assert "Buenos Aires" in data["provincias"]
    assert "CABA" in data["provincias"]


@pytest.mark.parametrize("provincia", [
    "CABA", "Buenos Aires", "Córdoba", "Santa Fe", "Mendoza", "Tucumán"
])
def test_juntas_por_provincia(client, provincia):
    r = client.get(f"/api/cud/juntas?provincia={provincia}")
    assert r.status_code == 200
    data = r.json()
    assert data["provincia"] == provincia
    assert "nombre_organismo" in data
    assert "sedes" in data
    assert len(data["sedes"]) >= 1
    assert "url_turno" in data


def test_juntas_provincia_inexistente(client):
    r = client.get("/api/cud/juntas?provincia=Atlantida")
    assert r.status_code == 404


def test_juntas_case_insensitive(client):
    r = client.get("/api/cud/juntas?provincia=caba")
    assert r.status_code == 200


# ── /api/cud/faq ─────────────────────────────────────────────────────────────

def test_faq(client):
    r = client.get("/api/cud/faq")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 5
    for item in data["preguntas"]:
        assert "pregunta" in item
        assert "respuesta" in item


def test_faq_busqueda(client):
    r = client.get("/api/cud/faq?q=vence")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert data["query"] == "vence"


def test_faq_busqueda_sin_resultados(client):
    r = client.get("/api/cud/faq?q=xyzabc123")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0


# ── /api/cud/consulta-estado, /sube, /obras-sociales ─────────────────────────

def test_consulta_estado(client):
    r = client.get("/api/cud/consulta-estado")
    assert r.status_code == 200
    data = r.json()
    assert data["cud_vence"] is False
    assert "url_consulta" in data


def test_sube(client):
    r = client.get("/api/cud/sube")
    assert r.status_code == 200
    data = r.json()
    # estructura SUBE_INFO completa
    assert "beneficio" in data
    assert "canales" in data
    assert "requisitos" in data
    assert "activacion" in data
    assert "contacto" in data
    # al menos 3 canales de registro
    assert len(data["canales"]) >= 3
    # descuento 100%
    assert data["beneficio"]["descuento"] == "100%"
    # algún canal tiene URL de sube o argentina.gob.ar
    urls = [c.get("url", "") or "" for c in data["canales"]]
    assert any("sube.gob.ar" in u or "argentina.gob.ar" in u for u in urls)
    # contacto telefónico
    assert data["contacto"]["telefono"] == "0800-777-7823"


def test_sube_canal_filtrado(client):
    r = client.get("/api/cud/sube?canal=online")
    assert r.status_code == 200
    data = r.json()
    assert len(data["canales"]) == 1
    canal = data["canales"][0]["canal"].lower()
    assert "sube.gob.ar" in canal or "online" in canal


def test_sube_canal_invalido(client):
    r = client.get("/api/cud/sube?canal=invalido")
    assert r.status_code == 400


def test_obras_sociales(client):
    r = client.get("/api/cud/obras-sociales")
    assert r.status_code == 200
    data = r.json()
    assert data["normativa"] == "Ley 24.901"
    assert "denuncias" in data
    assert data["denuncias"]["telefono"] == "0800-222-72583"