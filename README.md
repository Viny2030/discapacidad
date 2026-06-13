# Módulo CUD — Trámite y Beneficios

Guía completa del Certificado Único de Discapacidad (Argentina).

## Endpoints

```
GET /api/cud                          → info general
GET /api/cud/formularios              → formularios para descargar
GET /api/cud/requisitos               → requisitos generales
GET /api/cud/requisitos?tipo=motora   → requisitos por tipo
GET /api/cud/pasos                    → paso a paso del trámite
GET /api/cud/beneficios               → todos los beneficios
GET /api/cud/juntas                   → juntas evaluadoras por provincia
GET /api/cud/juntas?provincia=CABA    → junta específica
GET /api/cud/faq                      → preguntas frecuentes
GET /api/cud/consulta-estado          → cómo consultar el estado
GET /api/cud/sube                     → registrar CUD en SUBE
GET /api/cud/obras-sociales           → derechos ante obras sociales
```

## Correr

```bash
pip install -r requirements.txt
python main.py
# http://localhost:8001
```

## Integrar al Observatorio principal

```python
from cud_tramite.scripts.api_cud import router as router_cud
app.include_router(router_cud)
```

Fuente oficial: ANDIS · argentina.gob.ar/andis · Ley 22.431 · Ley 24.901
