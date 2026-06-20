"""
scripts/api_contacto.py — Observatorio de Discapacidad
Recibe mensajes del formulario de contacto (sugerencias, errores, consultas)
y los envia por email via Gmail SMTP usando una contrasena de aplicacion.

Variables de entorno requeridas (ya cargadas en Railway):
  GMAIL_USER          -> cuenta de gmail que envia el correo
  GMAIL_APP_PASSWORD  -> contrasena de aplicacion de 16 caracteres
  CONTACT_EMAIL_TO    -> direccion que recibe las consultas
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.utils import formataddr

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/contacto", tags=["contacto"])


class MensajeContacto(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    tipo: str = Field(..., min_length=1, max_length=50)
    mensaje: str = Field(..., min_length=1, max_length=5000)


@router.post("")
async def enviar_contacto(datos: MensajeContacto):
    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    destino = os.getenv("CONTACT_EMAIL_TO")

    if not gmail_user or not gmail_password or not destino:
        log.error("Faltan variables de entorno GMAIL_USER / GMAIL_APP_PASSWORD / CONTACT_EMAIL_TO")
        raise HTTPException(status_code=500, detail="El servicio de contacto no esta configurado.")

    asunto = f"[Observatorio Discapacidad] {datos.tipo} de {datos.nombre}"
    cuerpo = (
        f"Nombre y apellido: {datos.nombre}\n"
        f"Email de contacto: {datos.email}\n"
        f"Tipo: {datos.tipo}\n\n"
        f"Mensaje:\n{datos.mensaje}"
    )

    msg = MIMEText(cuerpo, "plain", "utf-8")
    msg["Subject"] = asunto
    msg["From"] = formataddr(("Observatorio de Discapacidad", gmail_user))
    msg["To"] = destino
    msg["Reply-To"] = datos.email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, [destino], msg.as_string())
        log.info("Mensaje de contacto enviado correctamente (tipo=%s)", datos.tipo)
    except Exception as e:
        log.error("Error enviando email de contacto: %s", e)
        raise HTTPException(status_code=502, detail="No se pudo enviar el mensaje. Intenta nuevamente.")

    return {"status": "ok", "detail": "Mensaje enviado correctamente."}
