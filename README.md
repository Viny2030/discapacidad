# 🟣 Observatorio de Discapacidad — Argentina

**Versión 1.0 · 2026**

API integral sobre discapacidad en Argentina: trámite del CUD (incluida la vinculación obligatoria con la tarjeta SUBE para transporte gratuito), evidencia médica actualizada desde PubMed y ClinicalTrials, estadísticas oficiales de ANDIS/INDEC, y tratamientos de vanguardia con disclaimers clínicos.

Deployado en [Railway](https://railway.app). Frontend incluido como Single Page Application en `templates/index.html`.

---

## 📁 Estructura del repositorio

```
discapacidad/
│
├── main.py                         # App FastAPI principal — integra los 4 módulos
├── requirements.txt
├── Dockerfile
├── railway.toml
├── .env.example                    # Variables de entorno necesarias
│
├── templates/
│   └── index.html                  # SPA — todas las pestañas del Observatorio
│
├── scripts/
│   ├── __init__.py
│   ├── datos_cud.py                # Base de datos estática: formularios, requisitos,
│   │                               #   beneficios, juntas por provincia (24), FAQ,
│   │                               #   SUBE_INFO (4 canales de registro CUD→SUBE)
│   ├── api_cud.py                  # Router /api/cud — 13 endpoints
│   ├── api_estadistica.py          # Router /api — estadísticas ANDIS/INDEC
│   ├── api_medica.py               # Router /api/medico — PubMed / ClinicalTrials
│   ├── tratamientos_vanguardia.py  # Router /api/vanguardia — 12 tratamientos
│   ├── etl_estadistico.py          # ETL: descarga y procesa datos ANDIS + Georef
│   ├── etl_medico.py               # ETL: artículos PubMed + ensayos ClinicalTrials
│   └── scheduler.py                # APScheduler — ETL cada 15 días
│
├── data/
│   ├── raw/
│   │   ├── georef_provincias.geojson
│   │   └── georef_comunas_caba.geojson
│   └── processed/
│       ├── prevalencia_provincias.csv
│       ├── evolucion_cud.csv
│       ├── cud_por_tipo.csv
│       └── caba_por_comuna.csv
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_cud.py
│   ├── test_datos.py
│   └── test_estadisitico.py
│
└── .github/
    └── workflows/
        ├── ci.yml                  # Tests en cada push a main
        ├── etl_estadistico.yml     # ETL estadístico — lunes 06:00 UTC
        ├── etl_medico.yml          # ETL médico — miércoles 06:00 UTC
        └── heatlh_ckeck.yml        # Health check diario — 10:00 UTC
```

---

## 🧩 Módulos

### 1. CUD — Certificado Único de Discapacidad (`/api/cud`)

Fuente estática curada desde ANDIS, Ley 22.431, Ley 24.901 y Resolución ANDIS 322/2023.

| Endpoint | Descripción |
|---|---|
| `GET /api/cud` | Info general del trámite (gratuito, no vence, normativa) |
| `GET /api/cud/formularios` | Formularios oficiales ANDIS para descargar |
| `GET /api/cud/requisitos` | Requisitos generales |
| `GET /api/cud/requisitos?tipo=motora` | Requisitos por tipo de discapacidad |
| `GET /api/cud/pasos` | 6 pasos del trámite con tiempos estimados |
| `GET /api/cud/beneficios` | Beneficios por categoría (salud, transporte, trabajo…) |
| `GET /api/cud/juntas` | Juntas evaluadoras en las 24 provincias |
| `GET /api/cud/juntas?provincia=CABA` | Junta de una provincia específica |
| `GET /api/cud/faq` | FAQ completo |
| `GET /api/cud/faq?q=vence` | Búsqueda en FAQ por palabra clave |
| `GET /api/cud/consulta-estado` | Cómo consultar el estado del trámite |
| `GET /api/cud/sube` | **Guía completa CUD → SUBE (4 canales, requisitos, FAQ)** |
| `GET /api/cud/sube?canal=online` | Pasos para el canal específico: `online` / `terminal` / `andis` |
| `GET /api/cud/obras-sociales` | Derechos frente a obras sociales (Ley 24.901) |

---

### 🚌 CUD → SUBE: trámite obligatorio de transporte

> El registro del CUD en la tarjeta SUBE es **obligatorio e independiente** del CUD. Sin este paso el descuento del 100% en transporte público **no se activa** aunque ya tengas el CUD.

**Normativa:** Ley 22.431 art. 22 / Resolución CNRT 1018/2018

**Beneficio:** 100% de descuento en colectivos, trenes y subte de todo el país. El acompañante también viaja sin cargo cuando la discapacidad lo requiere.

**4 canales de registro:**

| Canal | Cómo | Activación |
|---|---|---|
| Online | [sube.gob.ar](https://www.sube.gob.ar) | 24-48 hs |
| Trámite oficial | [argentina.gob.ar/servicio/registrar-cud-en-la-sube](https://www.argentina.gob.ar/servicio/registrar-certificado-unico-de-discapacidad-cud-en-la-sube) | 24-48 hs |
| Terminal SUBE | Kioscos, supermercados, Correo Argentino | Inmediata |
| Centro ANDIS | Con turno previo | Inmediata |

**Requisito previo:** la SUBE debe estar registrada a nombre del titular (una SUBE anónima no puede recibir el beneficio).

**Consultas:** 0800-777-7823 (gratuito, lun-vie 8-20 hs)

El endpoint `GET /api/cud/sube` devuelve la guía completa con pasos por canal, requisitos, tiempos de activación, qué hacer ante pérdida/robo de la SUBE y FAQ específica.

---

### 2. Estadístico — ANDIS / INDEC (`/api`)

ETL automático que descarga datos de ANDIS y Georef (API del Estado).

| Endpoint | Descripción |
|---|---|
| `GET /api/resumen` | Totales nacionales (CUD vigentes, tipos, cobertura) |
| `GET /api/provincias` | Datos de todas las provincias |
| `GET /api/provincias/{nombre}` | Detalle de una provincia |
| `GET /api/evolucion` | Serie temporal de CUD emitidos |
| `GET /api/tipos` | Distribución por tipo de discapacidad |
| `GET /api/caba/comunas` | Datos por comuna de CABA |
| `GET /api/mapa/provincias` | GeoJSON para mapa de prevalencia provincial |
| `GET /api/mapa/caba` | GeoJSON para mapa de comunas CABA |

---

### 3. Médico — PubMed / ClinicalTrials (`/api/medico`)

ETL que consulta PubMed y ClinicalTrials.gov con queries por tipo de discapacidad.

| Endpoint | Descripción |
|---|---|
| `GET /api/medico/articulos` | Artículos científicos recientes |
| `GET /api/medico/articulos/{pmid}` | Detalle de un artículo por PMID |
| `GET /api/medico/ensayos` | Ensayos clínicos activos |
| `GET /api/medico/tratamientos/{tipo}` | Tratamientos por tipo de discapacidad |
| `GET /api/medico/buscar` | Búsqueda libre en artículos y ensayos |

---

### 4. Vanguardia (`/api/vanguardia`)

12 tratamientos de vanguardia con fichas clínicas, estado de aprobación y disclaimers.

| Endpoint | Descripción |
|---|---|
| `GET /api/vanguardia` | Lista todos los tratamientos |
| `GET /api/vanguardia/estados` | Categorías por estado (aprobado / experimental) |
| `GET /api/vanguardia/tipo/{tipo}` | Tratamientos por tipo de discapacidad |
| `GET /api/vanguardia/ficha/{id}` | Ficha completa de un tratamiento |
| `GET /api/vanguardia/resumen` | Resumen estadístico |

---

## 🚀 Correr en local

### 1. Clonar y crear entorno

```bash
git clone https://github.com/Viny2030/discapacidad.git
cd discapacidad
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env si necesitás la API key de PubMed
```

### 3. Levantar el servidor

```bash
uvicorn main:app --reload --port 8001
```

- **Sitio:** `http://localhost:8001`
- **Docs interactivas (Swagger):** `http://localhost:8001/docs`
- **Health check:** `http://localhost:8001/health`

### 4. Correr tests

```bash
pytest tests/ -v
```

---

## 🔑 Variables de entorno

| Variable | Requerida | Descripción |
|---|---|---|
| `PORT` | No (default `8001`) | Puerto del servidor |
| `PUBMED_API_KEY` | No | API key de NCBI — aumenta el rate limit de 3 a 10 req/s. Gratis en [ncbi.nlm.nih.gov/account](https://www.ncbi.nlm.nih.gov/account/) |
| `ENVIRONMENT` | No (default `production`) | `production` o `development` |
| `RAILWAY_URL` | Solo en producción | URL pública para el health check automático (secret en GitHub Actions) |

---

## ⚙️ Workflows — GitHub Actions

| Workflow | Archivo | Frecuencia | Qué hace |
|---|---|---|---|
| **CI** | `ci.yml` | Cada push a `main` | Instala dependencias, corre pytest, verifica imports críticos |
| **ETL Estadístico** | `etl_estadistico.yml` | Lunes 06:00 UTC | Descarga datos ANDIS + Georef, genera CSVs, hace commit automático a `data/` |
| **ETL Médico** | `etl_medico.yml` | Miércoles 06:00 UTC | Descarga artículos PubMed y ensayos ClinicalTrials, hace commit automático |
| **Health Check** | `heatlh_ckeck.yml` | Diario 10:00 UTC | Verifica `/health` y 5 endpoints críticos en producción |

Los workflows de ETL también se pueden disparar manualmente desde la pestaña **Actions** de GitHub (`workflow_dispatch`).

Para el health check, configurar el secret `RAILWAY_URL` en **Settings → Secrets → Actions**.

---

## 🔧 Deploy en Railway

El repositorio incluye `railway.toml` con la configuración necesaria. El `Dockerfile` corre el ETL estadístico durante el build para que los datos estén disponibles desde el primer request.

---

## 📄 Normativa y fuentes

- Ley 22.431 — Sistema de Protección Integral de los Discapacitados
- Ley 24.901 — Sistema de Prestaciones Básicas
- Resolución ANDIS 322/2023 — CUD sin vencimiento
- Resolución CNRT 1018/2018 — Beneficio SUBE para personas con discapacidad
- [ANDIS](https://www.argentina.gob.ar/andis) — datos estadísticos y tramitación
- [SUBE](https://www.sube.gob.ar) — registro del beneficio de transporte
- [PubMed](https://pubmed.ncbi.nlm.nih.gov) / [ClinicalTrials.gov](https://clinicaltrials.gov) — evidencia médica
- [API Georef](https://georef-ar-api.readthedocs.io) — polígonos provinciales

---

## 👤 Autor

**Vicente Humberto Monteverde**
Investigador en políticas públicas y transparencia — Argentina

---

*Proyecto de acceso libre. Los datos médicos son informativos y no reemplazan consulta profesional.*
