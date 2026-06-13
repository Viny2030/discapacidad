"""
main.py
Observatorio de Discapacidad Argentina — FastAPI principal.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from scripts.api_estadistica        import router as router_est
from scripts.api_medica             import router as router_med
from scripts.tratamientos_vanguardia import router as router_van
from scripts.scheduler              import create_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [OBS-DIS] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Iniciando Observatorio de Discapacidad...")
    scheduler = create_scheduler()
    scheduler.start()
    log.info("Scheduler APScheduler activo — actualización cada 15 días")

    from pathlib import Path
    if not Path("data/processed/prevalencia_provincias.csv").exists():
        log.info("Primera ejecución — corriendo ETL inicial...")
        from scripts.etl_estadistico import run_etl_estadistico
        from scripts.etl_medico      import run_etl_medico
        run_etl_estadistico()
        run_etl_medico(max_por_query=5)

    yield
    scheduler.shutdown()
    log.info("Scheduler detenido")


app = FastAPI(
    title="Observatorio de Discapacidad Argentina",
    description="""
API del Observatorio de Discapacidad — datos estadísticos, médicos y tratamientos de vanguardia.

⚕️ **AVISO**: Toda la información médica es de carácter exclusivamente educativo e informativo.
No constituye consejo médico ni recomendación de tratamiento.

**Módulo Estadístico**: CUD por provincia, CABA por comunas, evolución histórica, mapas GeoJSON.

**Módulo Médico**: Artículos PubMed, ensayos clínicos, tratamientos por tipo.

**Módulo Vanguardia**: Tratamientos de avanzada con estado de aprobación (ANMAT/FDA/ensayo).

Datos: ANDIS · INDEC · Georef · PubMed (NIH) · ClinicalTrials.gov · SciELO
    """,
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(router_est)
app.include_router(router_med)
app.include_router(router_van)


@app.get("/", response_class=HTMLResponse)
async def landing():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width,initial-scale=1.0">
      <title>Observatorio de Discapacidad Argentina</title>
      <style>
        *{box-sizing:border-box;margin:0;padding:0}
        body{font-family:system-ui,sans-serif;background:#f8f9fa;color:#212529}
        header{background:#1a5276;color:white;padding:2rem;text-align:center}
        header h1{font-size:1.8rem;margin-bottom:.5rem}
        header p{opacity:.85}
        .disclaimer{background:#fff3cd;border-left:4px solid #e6ac00;padding:1rem 2rem;
                    font-size:.88rem;color:#555;max-width:1100px;margin:1.5rem auto 0}
        .kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
                  gap:1rem;padding:1.5rem 2rem;max-width:1100px;margin:0 auto}
        .kpi{background:white;border-radius:10px;padding:1.2rem;text-align:center;
             box-shadow:0 1px 4px rgba(0,0,0,.08)}
        .kpi .num{font-size:1.8rem;font-weight:700;color:#1a5276}
        .kpi .desc{font-size:.8rem;color:#666;margin-top:.3rem}
        .modules{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));
                 gap:1.5rem;padding:0 2rem 2rem;max-width:1100px;margin:0 auto}
        .module{background:white;border-radius:10px;padding:1.5rem;
                box-shadow:0 1px 4px rgba(0,0,0,.08)}
        .module h2{color:#1a5276;margin-bottom:1rem;font-size:1rem}
        .endpoint{display:flex;align-items:center;gap:.5rem;padding:.35rem 0;
                  border-bottom:1px solid #eee;font-size:.85rem}
        .endpoint:last-child{border:none}
        .tag{background:#e8f4fd;color:#1a5276;border-radius:4px;
             padding:2px 6px;font-size:.72rem;font-weight:600}
        .tag-van{background:#fdebd0;color:#784212}
        a{color:#1a5276;text-decoration:none}
        a:hover{text-decoration:underline}
        .cta{text-align:center;padding:0 2rem 2rem}
        .btn{background:#1a5276;color:white;padding:.6rem 1.5rem;
             border-radius:6px;font-size:.9rem;display:inline-block}
        footer{text-align:center;padding:2rem;color:#888;font-size:.82rem}
      </style>
    </head>
    <body>
      <header>
        <h1>🦽 Observatorio de Discapacidad Argentina</h1>
        <p>Estadísticas · Investigación médica · Tratamientos de vanguardia</p>
      </header>

      <div class="disclaimer">
        ⚕️ <strong>Aviso importante:</strong> Toda la información médica de este sitio es
        de carácter exclusivamente educativo e informativo. No constituye consejo médico
        ni recomendación de tratamiento. Consultá siempre con un profesional de la salud habilitado.
      </div>

      <div class="kpi-grid">
        <div class="kpi"><div class="num">1.68M</div><div class="desc">Personas con CUD vigente</div></div>
        <div class="kpi"><div class="num">3.65%</div><div class="desc">De la población nacional</div></div>
        <div class="kpi"><div class="num">24</div><div class="desc">Provincias</div></div>
        <div class="kpi"><div class="num">15</div><div class="desc">Comunas CABA</div></div>
        <div class="kpi"><div class="num">12</div><div class="desc">Tratamientos vanguardia</div></div>
        <div class="kpi"><div class="num">35M+</div><div class="desc">Papers PubMed</div></div>
      </div>

      <div class="modules">
        <div class="module">
          <h2>📊 Estadístico</h2>
          <div class="endpoint"><span class="tag">GET</span><a href="/api/resumen">/api/resumen</a></div>
          <div class="endpoint"><span class="tag">GET</span><a href="/api/provincias">/api/provincias</a></div>
          <div class="endpoint"><span class="tag">GET</span><a href="/api/evolucion">/api/evolucion</a></div>
          <div class="endpoint"><span class="tag">GET</span><a href="/api/tipos">/api/tipos</a></div>
          <div class="endpoint"><span class="tag">GET</span><a href="/api/caba/comunas">/api/caba/comunas</a></div>
          <div class="endpoint"><span class="tag">GET</span><a href="/api/mapa/provincias">/api/mapa/provincias</a></div>
        </div>
        <div class="module">
          <h2>🔬 Médico e Investigación</h2>
          <div class="endpoint"><span class="tag">GET</span><a href="/api/articulos?tipo=motora">/api/articulos?tipo=motora</a></div>
          <div class="endpoint"><span class="tag">GET</span><a href="/api/ensayos?tipo=visual">/api/ensayos?tipo=visual</a></div>
          <div class="endpoint"><span class="tag">GET</span><a href="/api/tratamientos/intelectual">/api/tratamientos/intelectual</a></div>
          <div class="endpoint"><span class="tag">GET</span><a href="/api/buscar?q=exoesqueleto">/api/buscar?q=exoesqueleto</a></div>
        </div>
        <div class="module">
          <h2>🚀 Tratamientos de Vanguardia</h2>
          <div class="endpoint"><span class="tag tag-van">GET</span><a href="/api/vanguardia">/api/vanguardia</a></div>
          <div class="endpoint"><span class="tag tag-van">GET</span><a href="/api/vanguardia/tipo/motora">/api/vanguardia/tipo/motora</a></div>
          <div class="endpoint"><span class="tag tag-van">GET</span><a href="/api/vanguardia/ficha/mot-001">/api/vanguardia/ficha/mot-001</a></div>
          <div class="endpoint"><span class="tag tag-van">GET</span><a href="/api/vanguardia/estados">/api/vanguardia/estados</a></div>
          <div class="endpoint"><span class="tag tag-van">GET</span><a href="/api/vanguardia/resumen">/api/vanguardia/resumen</a></div>
        </div>
      </div>

      <div class="cta">
        <a href="/docs" class="btn">📡 Documentación API (Swagger)</a>
      </div>

      <footer>
        Observatorio de Discapacidad Argentina · Ph.D. Vicente Humberto Monteverde ·
        Datos: ANDIS · INDEC · PubMed NIH · ClinicalTrials.gov · Georef AR<br>
        Actualización automática cada 15 días ·
        <strong>Información exclusivamente educativa — no reemplaza la consulta médica</strong>
      </footer>
    </body>
    </html>
    """


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
