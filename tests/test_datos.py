"""
test_datos.py
Tests de integridad de los datos estáticos en datos_cud.py.
No requieren levantar la API — validan los datos directamente.
"""
import pytest
from scripts.datos_cud import (
    FORMULARIOS,
    REQUISITOS_GENERALES,
    REQUISITOS_POR_TIPO,
    PASOS_TRAMITE,
    BENEFICIOS,
    JUNTAS_POR_PROVINCIA,
    FAQ,
)


# ── Formularios ───────────────────────────────────────────────────────────────

def test_formularios_no_vacios():
    assert len(FORMULARIOS) >= 1


def test_formularios_tienen_url():
    for f in FORMULARIOS:
        assert f.get("url"), f"Formulario '{f.get('nombre')}' sin URL"
        assert f["url"].startswith("http")


# ── Requisitos ────────────────────────────────────────────────────────────────

def test_requisitos_generales_completos():
    assert len(REQUISITOS_GENERALES) >= 4
    campos = ["documento", "detalle", "obligatorio"]
    for r in REQUISITOS_GENERALES:
        for c in campos:
            assert c in r, f"Requisito sin campo '{c}': {r}"


def test_tipos_discapacidad_completos():
    tipos_esperados = {"motora", "visual", "auditiva", "intelectual", "psicosocial", "visceral"}
    assert tipos_esperados == set(REQUISITOS_POR_TIPO.keys())


def test_cada_tipo_tiene_documentos():
    for tipo, datos in REQUISITOS_POR_TIPO.items():
        assert "documentos_adicionales" in datos, f"Tipo '{tipo}' sin documentos_adicionales"
        assert len(datos["documentos_adicionales"]) >= 2, f"Tipo '{tipo}' con pocos documentos"
        assert "tip" in datos, f"Tipo '{tipo}' sin tip"


# ── Pasos del trámite ─────────────────────────────────────────────────────────

def test_pasos_ordenados():
    nums = [p["paso"] for p in PASOS_TRAMITE]
    assert nums == list(range(1, len(PASOS_TRAMITE) + 1))


def test_pasos_tienen_contenido():
    for p in PASOS_TRAMITE:
        assert p.get("titulo")
        assert p.get("descripcion")
        assert p.get("duracion_estimada")


# ── Beneficios ────────────────────────────────────────────────────────────────

def test_categorias_beneficios():
    cats = {c["categoria"] for c in BENEFICIOS}
    assert "Salud" in cats
    assert "Transporte" in cats
    assert "Trabajo" in cats
    assert "Vivienda" in cats


def test_beneficios_tienen_normativa():
    for cat in BENEFICIOS:
        for b in cat["beneficios"]:
            assert b.get("nombre"), f"Beneficio sin nombre en {cat['categoria']}"
            assert b.get("normativa"), f"Beneficio '{b.get('nombre')}' sin normativa"


def test_transporte_tiene_url_sube():
    transporte = next(c for c in BENEFICIOS if c["categoria"] == "Transporte")
    sube = next((b for b in transporte["beneficios"] if "SUBE" in b.get("detalle", "") or "SUBE" in b.get("nombre", "")), None)
    assert sube is not None, "No se encontró beneficio de SUBE en Transporte"
    assert sube.get("url"), "Beneficio SUBE sin URL"


# ── Juntas por provincia ──────────────────────────────────────────────────────

def test_juntas_24_provincias():
    assert len(JUNTAS_POR_PROVINCIA) == 24


def test_juntas_campos_obligatorios():
    campos = ["nombre_organismo", "url_turno", "telefono", "turno_online",
              "tiempo_espera_estimado", "sedes"]
    for prov, datos in JUNTAS_POR_PROVINCIA.items():
        for c in campos:
            assert c in datos, f"Provincia '{prov}' sin campo '{c}'"


def test_juntas_sedes_no_vacias():
    for prov, datos in JUNTAS_POR_PROVINCIA.items():
        assert len(datos["sedes"]) >= 1, f"Provincia '{prov}' sin sedes"
        for sede in datos["sedes"]:
            assert sede.get("nombre"), f"Sede sin nombre en {prov}"
            assert sede.get("direccion"), f"Sede sin dirección en {prov}"


def test_juntas_tiempo_espera_formato():
    import re
    patron = re.compile(r"\d+-\d+ días")
    for prov, datos in JUNTAS_POR_PROVINCIA.items():
        espera = datos.get("tiempo_espera_estimado", "")
        assert patron.match(espera), f"Formato de tiempo incorrecto en {prov}: '{espera}'"


def test_provincias_con_turno_online():
    con_turno = [p for p, d in JUNTAS_POR_PROVINCIA.items() if d["turno_online"]]
    # Al menos CABA y Buenos Aires deben tener turno online
    assert "CABA" in con_turno
    assert "Buenos Aires" in con_turno


# ── FAQ ───────────────────────────────────────────────────────────────────────

def test_faq_no_vacio():
    assert len(FAQ) >= 5


def test_faq_campos():
    for item in FAQ:
        assert item.get("pregunta"), "FAQ sin pregunta"
        assert item.get("respuesta"), "FAQ sin respuesta"
        assert len(item["respuesta"]) > 20, f"Respuesta muy corta: {item['pregunta']}"


def test_faq_cubre_temas_clave():
    preguntas = " ".join(f["pregunta"].lower() for f in FAQ)
    assert "vence" in preguntas, "FAQ no cubre vencimiento del CUD"
    assert "gratuito" in preguntas, "FAQ no cubre costo del trámite"
    assert "sube" in preguntas, "FAQ no cubre SUBE"


# ── Health del servidor ───────────────────────────────────────────────────────

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"