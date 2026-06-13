# Observatorio de Discapacidad Argentina

API FastAPI con datos estadísticos y médicos sobre discapacidad en Argentina.

## Módulos

- **Estadístico**: CUD por provincia, CABA por comunas, evolución histórica, mapas GeoJSON
- **Médico**: Artículos PubMed, ensayos clínicos (ClinicalTrials.gov), tratamientos por tipo

## Fuentes

| Fuente | Dato | Acceso |
|--------|------|--------|
| ANDIS | CUD vigentes por provincia | Informes PDF |
| INDEC | Estudio Nacional 2018 + Censo 2022 | CSV directo |
| Georef AR | Provincias y comunas CABA | API REST gratuita |
| PubMed (NIH) | 35M+ papers médicos | API E-utilities gratuita |
| ClinicalTrials.gov | Ensayos clínicos activos | API v2 gratuita |
| SciELO Argentina | Ciencia latinoamericana | OAI-PMH gratuito |

## Correr local

```bash
pip install -r requirements.txt
cp .env.example .env
python main.py
# http://localhost:8000
# http://localhost:8000/docs
```

## Deploy Railway

1. Push al repo GitHub
2. Railway → nuevo proyecto → conectar repo
3. Railway detecta el Dockerfile automáticamente
4. Variables de entorno: `DATABASE_URL`, `PUBMED_API_KEY` (opcional)

## Endpoints principales

```
GET /api/resumen                    → KPIs nacionales
GET /api/provincias                 → CUD por provincia
GET /api/evolucion                  → Evolución histórica
GET /api/tipos                      → CUD por tipo de discapacidad
GET /api/caba/comunas               → CABA por comunas
GET /api/mapa/provincias            → GeoJSON para mapa coroplético
GET /api/articulos?tipo=motora      → Artículos PubMed por tipo
GET /api/ensayos?tipo=visual        → Ensayos clínicos activos
GET /api/tratamientos/intelectual   → Resumen + artículos + ensayos
GET /api/buscar?q=exoesqueleto      → Búsqueda libre en PubMed
```

## Actualización automática

APScheduler ejecuta los ETL cada 15 días automáticamente.
Como fallback, configurar GitHub Actions con cron `0 6 1,15 * *`.

## Autor

Ph.D. Vicente Humberto Monteverde · vhmonte@retina.ar
