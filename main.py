"""
main.py — Observatorio de Discapacidad
API principal que integra los módulos:
  - CUD (trámite y beneficios)        -> scripts/api_cud.py
  - Medico (PubMed / ClinicalTrials)  -> scripts/api_medica.py
  - Estadistico (ANDIS / INDEC)       -> scripts/api_estadistica.py

Tambien arranca el scheduler de actualizacion automatica (cada 15 dias)
definido en scripts/scheduler.py.
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from scripts.api_cud import router as router_cud
from scripts.api_medica import router as router_medica
from scripts.api_estadistica import router as router_estadistica
from scripts.tratamientos_vanguardia import router as router_vanguardia
from scripts.scheduler import create_scheduler

logging.basicConfig(level=logging.INFO, format="[OBSERVATORIO] %(message)s")
log = logging.getLogger(__name__)

scheduler = create_scheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    log.info("Scheduler iniciado - ETL estadistico y medico cada 15 dias")
    yield
    scheduler.shutdown(wait=False)
    log.info("Scheduler detenido")


app = FastAPI(
    title="Observatorio de Discapacidad",
    description="API integral: tramite del CUD, evidencia medica (PubMed/ClinicalTrials) "
                 "y estadisticas oficiales de discapacidad en Argentina (ANDIS/INDEC).",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(router_cud)
app.include_router(router_medica)
app.include_router(router_estadistica)
app.include_router(router_vanguardia)


@app.get("/", response_class=HTMLResponse)
async def landing():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width,initial-scale=1.0">
      <title>Observatorio de Discapacidad</title>
      <style>
        *{box-sizing:border-box;margin:0;padding:0}
        body{font-family:system-ui,sans-serif;background:#f8f9fa;color:#212529}
        header{background:#1a5276;color:white;padding:2rem;text-align:center}
        header h1{font-size:1.8rem;margin-bottom:.5rem}
        .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));
              gap:1.2rem;padding:2rem;max-width:1200px;margin:0 auto}
        .card{background:white;border-radius:10px;padding:1.5rem;
              box-shadow:0 1px 4px rgba(0,0,0,.08)}
        .card h2{color:#1a5276;margin-bottom:1rem;font-size:1rem}
        .ep{display:flex;align-items:center;gap:.5rem;padding:.35rem 0;
            border-bottom:1px solid #eee;font-size:.85rem}
        .ep:last-child{border:none}
        .tag{background:#e8f4fd;color:#1a5276;border-radius:4px;
             padding:2px 6px;font-size:.72rem;font-weight:600}
        .tag-warn{background:#fdf3e0;color:#7d6608;border-radius:4px;
             padding:2px 6px;font-size:.72rem;font-weight:600}
        .disclaimer{background:#fdf3e0;border-left:3px solid #7d6608;
             padding:.6rem .8rem;margin-top:1rem;font-size:.78rem;
             color:#5c4a08;border-radius:4px;line-height:1.4}
        a{color:#1a5276;text-decoration:none}
        a:hover{text-decoration:underline}
        .cta{text-align:center;padding:0 2rem 2rem}
        .btn{padding:.6rem 1.5rem;border-radius:6px;font-size:.9rem;
             display:inline-block;font-weight:600;background:#1a5276;color:white}
        footer{text-align:center;padding:2rem;color:#888;font-size:.82rem}
      </style>
    </head>
    <body>
      <header>
        <h1>Observatorio de Discapacidad</h1>
        <p>CUD - Evidencia medica - Estadisticas oficiales (ANDIS/INDEC)</p>
      </header>

      <div class="grid">
        <div class="card">
          <h2>Modulo CUD</h2>
          <div class="ep"><span class="tag">GET</span><a href="/api/cud">/api/cud</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/cud/requisitos">/api/cud/requisitos</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/cud/pasos">/api/cud/pasos</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/cud/beneficios">/api/cud/beneficios</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/cud/juntas?provincia=CABA">/api/cud/juntas?provincia=CABA</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/cud/faq">/api/cud/faq</a></div>
        </div>
        <div class="card">
          <h2>Modulo Medico</h2>
          <div class="ep"><span class="tag">GET</span><a href="/api/articulos?tipo=motora">/api/articulos?tipo=motora</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/ensayos">/api/ensayos</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/tratamientos/visual">/api/tratamientos/visual</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/buscar?q=rehabilitacion">/api/buscar?q=...</a></div>
        </div>
        <div class="card">
          <h2>Modulo Estadistico</h2>
          <div class="ep"><span class="tag">GET</span><a href="/api/resumen">/api/resumen</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/provincias">/api/provincias</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/evolucion">/api/evolucion</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/tipos">/api/tipos</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/caba/comunas">/api/caba/comunas</a></div>
        </div>
        <div class="card">
          <h2>Modulo Vanguardia</h2>
          <div class="ep"><span class="tag">GET</span><a href="/api/vanguardia">/api/vanguardia</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/vanguardia/tipo/motora">/api/vanguardia/tipo/motora</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/vanguardia/estados">/api/vanguardia/estados</a></div>
          <div class="ep"><span class="tag">GET</span><a href="/api/vanguardia/resumen">/api/vanguardia/resumen</a></div>
          <div class="disclaimer">
            <span class="tag-warn">AVISO</span> Informacion educativa sobre tratamientos
            de vanguardia. No constituye consejo medico. Consulta siempre con un
            profesional de la salud habilitado.
          </div>
        </div>
      </div>

      <div class="cta">
        <a href="/docs" class="btn">API Docs</a>
      </div>

      <footer>
        Informacion oficial basada en normativa ANDIS - Ley 22.431 - Ley 24.901<br>
        Para consultas oficiales: <a href="https://www.argentina.gob.ar/andis">argentina.gob.ar/andis</a>
        - 0800-333-ANDIS
      </footer>
    </body>
    </html>
    """


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "module": "observatorio-discapacidad",
        "version": "1.0.0",
        "scheduler_running": scheduler.running,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8001)), reload=True)
