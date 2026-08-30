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


def asunto_para(nombre_autor: str) -> str:
    return f"✨ Here is your new Art inspiration, today {nombre_autor}. Enjoy it!"


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


def enviar_a_lista(destinatarios: list[str], asunto: str, html: str) -> list[dict]:
    # Uno por destinatario (no un solo "to" con todos) para que nadie vea el
    # email de los demás suscriptores.
    return [enviar_email(destinatario, asunto, html) for destinatario in destinatarios]
