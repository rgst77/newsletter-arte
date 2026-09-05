import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BREVO_API = "https://api.brevo.com/v3/smtp/email"

# Sin dominio propio verificado, Brevo sustituye el dominio de envío por el
# suyo compartido por debajo (para cumplir las reglas de Gmail/Yahoo), pero
# a diferencia de Resend SÍ deja mandar a cualquier destinatario real, no
# solo al email de la cuenta — por eso lo elegimos.
REMITENTE_NOMBRE = "curiosARTy"
REMITENTE_EMAIL = "rodrigo-gst@hotmail.es"


def asunto_para(nombre_autor: str) -> str:
    return f"✨ Here is your new Art inspiration, today {nombre_autor}. Enjoy it!"


def enviar_email(destinatario: str, asunto: str, html: str) -> dict:
    respuesta = requests.post(
        BREVO_API,
        headers={
            "api-key": os.environ["BREVO_API_KEY"],
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={
            "sender": {"name": REMITENTE_NOMBRE, "email": REMITENTE_EMAIL},
            "to": [{"email": destinatario}],
            "subject": asunto,
            "htmlContent": html,
        },
        timeout=15,
    )
    respuesta.raise_for_status()
    return respuesta.json()


def enviar_a_lista(destinatarios: list[str], asunto: str, html: str) -> list[dict]:
    # Uno por destinatario (no un solo "to" con todos) para que nadie vea el
    # email de los demás suscriptores. Un fallo puntual (ej. bounce, límite de
    # la cuenta) no debe tumbar el resto del envío.
    resultados = []
    for destinatario in destinatarios:
        try:
            resultados.append(enviar_email(destinatario, asunto, html))
        except requests.HTTPError as error:
            resultados.append({"destinatario": destinatario, "error": str(error)})
    return resultados
