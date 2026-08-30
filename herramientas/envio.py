import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

RESEND_API = "https://api.resend.com/emails"

# Sin dominio propio verificado en Resend, "onboarding@resend.dev" solo puede
# mandar al email con el que te diste de alta en Resend — es su forma de
# evitar abuso. Para mandar a suscriptores externos reales hará falta
# verificar un dominio propio más adelante.
REMITENTE_PRUEBA = "curiosARTy <onboarding@resend.dev>"


def enviar_email(destinatario: str, asunto: str, html: str) -> dict:
    respuesta = requests.post(
        RESEND_API,
        headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}"},
        json={
            "from": REMITENTE_PRUEBA,
            "to": [destinatario],
            "subject": asunto,
            "html": html,
        },
        timeout=15,
    )
    respuesta.raise_for_status()
    return respuesta.json()
