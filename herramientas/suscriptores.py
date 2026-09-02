import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Todas las funciones de este módulo usan la clave secreta (bypassa RLS) —
# nunca la publicable, que por diseño no puede leer ni actualizar la tabla.
# Solo debe llamarse desde el script de envío automático, nunca desde código
# expuesto al navegador.


def _cabeceras() -> dict:
    clave = os.environ["SUPABASE_SERVICE_KEY"]
    return {"apikey": clave, "Authorization": f"Bearer {clave}"}


def obtener_suscriptores() -> list[dict]:
    respuesta = requests.get(
        f"{os.environ['SUPABASE_URL']}/rest/v1/suscriptores",
        params={"select": "email,siguiente_indice,fecha_ultimo_envio"},
        headers=_cabeceras(),
        timeout=15,
    )
    respuesta.raise_for_status()
    return respuesta.json()


def actualizar_progreso_suscriptor(email: str, nuevo_indice: int) -> None:
    respuesta = requests.patch(
        f"{os.environ['SUPABASE_URL']}/rest/v1/suscriptores",
        params={"email": f"eq.{email}"},
        headers={**_cabeceras(), "Content-Type": "application/json", "Prefer": "return=minimal"},
        json={
            "siguiente_indice": nuevo_indice,
            "fecha_ultimo_envio": datetime.now(timezone.utc).isoformat(),
        },
        timeout=15,
    )
    respuesta.raise_for_status()
