import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def obtener_suscriptores() -> list[str]:
    # Usa la clave secreta (bypassa RLS) — nunca la publicable, que por diseño
    # no puede leer la tabla. Esta función solo debe llamarse desde el script
    # de envío automático, nunca desde código expuesto al navegador.
    respuesta = requests.get(
        f"{os.environ['SUPABASE_URL']}/rest/v1/suscriptores",
        params={"select": "email"},
        headers={
            "apikey": os.environ["SUPABASE_SERVICE_KEY"],
            "Authorization": f"Bearer {os.environ['SUPABASE_SERVICE_KEY']}",
        },
        timeout=15,
    )
    respuesta.raise_for_status()
    return [fila["email"] for fila in respuesta.json()]
