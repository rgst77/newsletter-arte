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
        params={"select": "email,ultimo_archivo_enviado,fecha_ultimo_envio,token"},
        headers=_cabeceras(),
        timeout=15,
    )
    respuesta.raise_for_status()
    return respuesta.json()


def actualizar_progreso_suscriptor(email: str, archivo_html: str) -> None:
    # Se guarda el archivo del issue recién enviado (no un índice numérico):
    # así la posición de cada suscriptor no depende de que el orden de
    # cargar_incluidos() se mantenga estable para siempre — si algún día se
    # rellena un hueco antiguo del archivo (ej. un issue sin JSON), un índice
    # numérico desincronizaría a todo el mundo de golpe, pero un nombre de
    # archivo sigue apuntando exactamente a lo mismo pase lo que pase.
    respuesta = requests.patch(
        f"{os.environ['SUPABASE_URL']}/rest/v1/suscriptores",
        params={"email": f"eq.{email}"},
        headers={**_cabeceras(), "Content-Type": "application/json", "Prefer": "return=minimal"},
        json={
            "ultimo_archivo_enviado": archivo_html,
            "fecha_ultimo_envio": datetime.now(timezone.utc).isoformat(),
        },
        timeout=15,
    )
    respuesta.raise_for_status()
