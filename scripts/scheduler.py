"""
scheduler.py
Motor de actualización automática cada 15 días.
Usa APScheduler. Se inicia junto con FastAPI.
"""

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

log = logging.getLogger(__name__)


def job_etl_estadistico():
    log.info(f"[SCHEDULER] ETL Estadístico iniciado — {datetime.now()}")
    try:
        from scripts.etl_estadistico import run_etl_estadistico
        run_etl_estadistico()
        log.info("[SCHEDULER] ETL Estadístico OK")
    except Exception as e:
        log.error(f"[SCHEDULER] ETL Estadístico ERROR: {e}")


def job_etl_medico():
    log.info(f"[SCHEDULER] ETL Médico iniciado — {datetime.now()}")
    try:
        from scripts.etl_medico import run_etl_medico
        run_etl_medico(max_por_query=10)
        log.info("[SCHEDULER] ETL Médico OK")
    except Exception as e:
        log.error(f"[SCHEDULER] ETL Médico ERROR: {e}")


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="America/Argentina/Buenos_Aires")

    # ETL estadístico — cada 15 días
    scheduler.add_job(
        job_etl_estadistico,
        trigger=IntervalTrigger(days=15),
        id="etl_estadistico",
        name="ETL Estadístico ANDIS/INDEC",
        replace_existing=True,
    )

    # ETL médico — cada 15 días (con 1 día de offset)
    scheduler.add_job(
        job_etl_medico,
        trigger=IntervalTrigger(days=15),
        id="etl_medico",
        name="ETL Médico PubMed/ClinicalTrials",
        replace_existing=True,
    )

    return scheduler
