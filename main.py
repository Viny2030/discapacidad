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
from fastapi.responses import HTMLResponse, FileResponse

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
    return FileResponse("templates/index.html")


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