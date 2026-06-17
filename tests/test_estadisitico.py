"""
test_estadistico.py
Tests para el módulo estadístico (/api/resumen, /api/provincias, etc.)
y para el ETL estadístico (construye DataFrames sin conexión externa).
"""
import pytest


# ── /api/resumen ──────────────────────────────────────────────────────────────

def test_resumen(client):
    r = client.get("/api/resumen")
    assert r.status_code == 200
    data = r.json()
    assert data["total_cud_vigentes"] > 0
    assert 0 < data["porcentaje_poblacion"] < 100
    assert "fecha_datos" in data
    assert "fuente" in data


# ── /api/provincias ───────────────────────────────────────────────────────────

def test_provincias(client):
    r = client.get("/api/provincias")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 24
    provincias = [p["provincia"] for p in data["provincias"]]
    assert "Buenos Aires" in provincias
    assert "CABA" in provincias
    assert "Tierra del Fuego" in provincias


def test_provincias_campos_requeridos(client):
    r = client.get("/api/provincias")
    for p in r.json()["provincias"]:
        assert "provincia" in p
        assert "cud_vigentes" in p
        assert "tasa_prevalencia" in p
        assert p["cud_vigentes"] > 0
        assert 0 < p["tasa_prevalencia"] < 100


@pytest.mark.parametrize("orden", ["cud_vigentes", "tasa_prevalencia", "provincia"])
def test_provincias_orden(client, orden):
    r = client.get(f"/api/provincias?orden={orden}")
    assert r.status_code == 200
    data = r.json()
    assert len(data["provincias"]) == 24
    if orden == "cud_vigentes":
        cuds = [p["cud_vigentes"] for p in data["provincias"]]
        assert cuds == sorted(cuds, reverse=True)
    elif orden == "provincia":
        nombres = [p["provincia"] for p in data["provincias"]]
        assert nombres == sorted(nombres)


# ── /api/provincias/{nombre} ──────────────────────────────────────────────────

def test_provincia_detalle(client):
    r = client.get("/api/provincias/CABA")
    assert r.status_code == 200
    data = r.json()
    assert data["provincia"] == "CABA"
    assert data["cud_vigentes"] == 163_114


def test_provincia_detalle_inexistente(client):
    r = client.get("/api/provincias/Atlantida")
    assert r.status_code == 404


# ── /api/evolucion ────────────────────────────────────────────────────────────

def test_evolucion(client):
    r = client.get("/api/evolucion")
    assert r.status_code == 200
    data = r.json()
    assert len(data["series"]) >= 4
    años = [s["año"] for s in data["series"]]
    assert 2018 in años
    assert 2023 in años
    # Evolución debe ser creciente
    totales = [s["total"] for s in data["series"]]
    assert totales == sorted(totales)


# ── /api/tipos ────────────────────────────────────────────────────────────────

def test_tipos(client):
    r = client.get("/api/tipos")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] > 0
    assert len(data["tipos"]) >= 5
    for t in data["tipos"]:
        assert "tipo" in t
        assert "cantidad" in t
        assert "porcentaje" in t
        assert 0 < t["porcentaje"] < 100


# ── /api/caba/comunas ─────────────────────────────────────────────────────────

def test_caba_comunas(client):
    r = client.get("/api/caba/comunas")
    assert r.status_code == 200
    data = r.json()
    assert data["total_caba"] > 0
    assert len(data["comunas"]) == 15
    for c in data["comunas"]:
        assert "comuna" in c
        assert "nombre" in c
        assert "cud" in c
        assert c["cud"] > 0


# ── /api/mapa/provincias ──────────────────────────────────────────────────────

def test_mapa_provincias(client):
    r = client.get("/api/mapa/provincias")
    # Puede devolver error si no hay GeoJSON descargado — aceptamos ambos
    assert r.status_code == 200
    data = r.json()
    # O tiene features (GeoJSON real) o tiene error informativo
    assert "features" in data or "error" in data


def test_mapa_caba(client):
    r = client.get("/api/mapa/caba")
    assert r.status_code == 200
    data = r.json()
    assert "features" in data or "error" in data


# ── ETL estadístico (unit tests sin red) ─────────────────────────────────────

def test_etl_construir_provincias():
    from scripts.etl_estadistico import construir_df_provincias
    df = construir_df_provincias()
    assert len(df) == 24
    assert "tasa_prevalencia" in df.columns
    assert (df["tasa_prevalencia"] > 0).all()
    assert (df["tasa_prevalencia"] < 20).all()   # ninguna provincia > 20%


def test_etl_construir_evolucion():
    from scripts.etl_estadistico import construir_df_evolucion
    df = construir_df_evolucion()
    assert len(df) >= 4
    totales = df["total"].tolist()
    assert totales == sorted(totales)             # siempre creciente
    # variacion_pct: primer valor None, resto numérico
    assert df["variacion_pct"].iloc[0] is None


def test_etl_construir_tipos():
    from scripts.etl_estadistico import construir_df_tipos
    df = construir_df_tipos()
    assert len(df) >= 5
    assert df["porcentaje"].sum() <= 101          # puede sumar ~100%


def test_etl_construir_caba():
    from scripts.etl_estadistico import construir_df_caba
    df = construir_df_caba()
    assert len(df) == 15
    assert (df["cud"] > 0).all()
