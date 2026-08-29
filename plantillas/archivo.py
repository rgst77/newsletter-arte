import html
import json
from datetime import datetime
from pathlib import Path

from plantillas.email import DISCIPLINAS_EN, _siglo_a_ordinal

RUTA_ENVIADOS = Path(__file__).resolve().parent.parent / "datos" / "autores_enviados.json"

# Los envíos de antes de este corte usan una versión anterior de la plantilla
# (fondo blanco / etiquetas en pastillas de color) y no encajarían visualmente
# con el diseño actual. Se excluyen de las vistas públicas en vez de mostrarlos
# inconsistentes; cuando se regeneren con el diseño final, este corte deja de
# hacer falta.
CORTE_DISENO_ACTUAL = datetime(2026, 8, 29, 14, 0, 0)


def cargar_incluidos() -> list[dict]:
    registros = json.loads(RUTA_ENVIADOS.read_text(encoding="utf-8"))
    return [
        r for r in registros
        if r.get("archivo_html") and datetime.fromisoformat(r["fecha_envio"]) >= CORTE_DISENO_ACTUAL
    ]


def tarjeta_html(registro: dict, prefijo_ruta: str = "") -> str:
    ruta_html = registro["archivo_html"]
    siglo = _siglo_a_ordinal(registro["siglo"])
    corriente = html.escape(registro["corriente"])
    nombre = html.escape(registro["nombre"])
    return f"""
    <a href="{prefijo_ruta}{html.escape(ruta_html)}" style="text-decoration:none; display:block;">
      <div style="height:220px; overflow:hidden; border:1px solid #222222; position:relative; background:#0a0a0a;">
        <iframe src="{prefijo_ruta}{html.escape(ruta_html)}" title="{nombre}"
                style="width:600px; height:900px; border:0; transform:scale(0.4); transform-origin:top left; pointer-events:none;"
                tabindex="-1"></iframe>
      </div>
      <p style="margin:12px 0 0 0; font-family:'Orbitron','Helvetica Neue',Arial,sans-serif; font-size:18px; font-weight:900; color:#f5f5f5;">{nombre}</p>
      <p style="margin:2px 0 0 0; font-family:'Helvetica Neue',Arial,sans-serif; font-size:12px; letter-spacing:0.5px; color:#6b6b6b;">{siglo} CENTURY &nbsp;/&nbsp; {corriente}</p>
    </a>"""
