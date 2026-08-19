"""
scripts/api_encuesta.py — Observatorio de Discapacidad
Recibe las respuestas del formulario "Encuesta en Discapacidad. Comuna 7 -
Papa Francisco" (pestaña Comuna_07) y las envia por email via Gmail SMTP,
usando la misma cuenta configurada para el formulario de contacto.

Variables de entorno requeridas (ya cargadas en Railway):
  GMAIL_USER          -> cuenta de gmail que envia el correo
  GMAIL_APP_PASSWORD  -> contrasena de aplicacion de 16 caracteres

El correo de destino de las respuestas de esta encuesta esta fijo
(viny01958@gmail.com), a diferencia del formulario de contacto general que
usa CONTACT_EMAIL_TO.
"""
import os
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/encuesta-comuna07", tags=["encuesta-comuna07"])

DESTINO_ENCUESTA = "viny01958@gmail.com"


class RespuestaEncuesta(BaseModel):
    nombre_apellido: str = Field(..., min_length=1, max_length=200)
    correo: Optional[str] = Field("", max_length=200)
    respuestas: Dict[str, str] = Field(default_factory=dict)


@router.post("")
async def enviar_encuesta(datos: RespuestaEncuesta):
    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_user or not gmail_password:
        log.error("Faltan variables de entorno GMAIL_USER / GMAIL_APP_PASSWORD")
        raise HTTPException(status_code=500, detail="El servicio de encuestas no esta configurado.")

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    lineas = [
        f"Nueva respuesta - Encuesta en Discapacidad. Comuna 7 - Papa Francisco",
        f"Fecha y hora: {fecha}",
        f"Nombre y apellido: {datos.nombre_apellido}",
    ]
    if datos.correo:
        lineas.append(f"Correo de contacto: {datos.correo}")
    lineas.append("")
    lineas.append("Respuestas:")
    lineas.append("-" * 40)

    for pregunta, respuesta in datos.respuestas.items():
        respuesta = (respuesta or "").strip()
        if respuesta:
            lineas.append(f"\n{pregunta}\n{respuesta}")

    cuerpo = "\n".join(lineas)

    msg = MIMEText(cuerpo, "plain", "utf-8")
    msg["Subject"] = f"[Encuesta Comuna 7] Nueva respuesta de {datos.nombre_apellido}"
    msg["From"] = formataddr(("Observatorio de Discapacidad", gmail_user))
    msg["To"] = DESTINO_ENCUESTA
    if datos.correo:
        msg["Reply-To"] = datos.correo

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, [DESTINO_ENCUESTA], msg.as_string())
        log.info("Respuesta de encuesta Comuna 7 enviada correctamente (nombre=%s)", datos.nombre_apellido)
    except Exception as e:
        log.error("Error enviando email de encuesta Comuna 7: %s", e)
        raise HTTPException(status_code=502, detail="No se pudo enviar la encuesta. Intenta nuevamente.")

    return {"status": "ok", "detail": "Encuesta enviada correctamente."}
