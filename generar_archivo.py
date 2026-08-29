import html
import json
from datetime import datetime
from pathlib import Path

from plantillas.email import DISCIPLINAS_EN, _siglo_a_ordinal

RUTA_ENVIADOS = Path(__file__).resolve().parent / "datos" / "autores_enviados.json"
RUTA_SALIDA = Path(__file__).resolve().parent / "archivo" / "index.html"

# Los envíos de antes de este corte usan una versión anterior de la plantilla
# (fondo blanco / etiquetas en pastillas de color) y no encajarían visualmente
# con el diseño actual. Se excluyen del archivo público en vez de mostrarlos
# inconsistentes; cuando se regeneren con el diseño final, este corte deja de
# hacer falta.
CORTE_DISENO_ACTUAL = datetime(2026, 8, 29, 14, 0, 0)


def _entrada(registro: dict) -> str:
    ruta_html = registro["archivo_html"]
    disciplina = DISCIPLINAS_EN.get(registro.get("disciplina", ""), "")
    siglo = _siglo_a_ordinal(registro["siglo"])
    nombre = html.escape(registro["nombre"])
    corriente = html.escape(registro["corriente"])
    return f"""
    <a href="../{html.escape(ruta_html)}" style="text-decoration:none; display:block; margin-bottom:32px;">
      <div style="height:220px; overflow:hidden; border:1px solid #222222; position:relative; background:#0a0a0a;">
        <iframe src="../{html.escape(ruta_html)}" title="{nombre}"
                style="width:600px; height:900px; border:0; transform:scale(0.4); transform-origin:top left; pointer-events:none;"
                tabindex="-1"></iframe>
      </div>
      <p style="margin:12px 0 0 0; font-family:'Orbitron','Helvetica Neue',Arial,sans-serif; font-size:18px; font-weight:900; color:#f5f5f5;">{nombre}</p>
      <p style="margin:2px 0 0 0; font-family:'Helvetica Neue',Arial,sans-serif; font-size:12px; letter-spacing:0.5px; color:#6b6b6b;">{siglo} CENTURY &nbsp;/&nbsp; {corriente}</p>
    </a>"""


def generar() -> None:
    registros = json.loads(RUTA_ENVIADOS.read_text(encoding="utf-8"))
    incluidos = [
        r for r in registros
        if r.get("archivo_html") and datetime.fromisoformat(r["fecha_envio"]) >= CORTE_DISENO_ACTUAL
    ]
    tarjetas = "".join(_entrada(r) for r in incluidos)

    RUTA_SALIDA.parent.mkdir(exist_ok=True)
    RUTA_SALIDA.write_text(
        f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Archive — curiosARTy</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@800;900&display=swap" rel="stylesheet">
</head>
<body style="margin:0; padding:0; background-color:#0a0a0a;">
  <div style="max-width:760px; margin:0 auto; padding:48px 24px;">
    <span style="font-family:'Helvetica Neue',Arial,sans-serif; font-size:28px; font-weight:900;">
      <span style="color:#f5f5f5;">curios</span><span style="color:#00cc00;">ART</span><span style="color:#f5f5f5;">y</span>
    </span>
    <p style="font-family:'Helvetica Neue',Arial,sans-serif; font-size:13px; letter-spacing:2px; color:#6b6b6b; margin:6px 0 40px 0;">ARCHIVE — EVERY ISSUE SENT</p>
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:24px;">
      {tarjetas}
    </div>
  </div>
</body>
</html>""",
        encoding="utf-8",
    )
    print(f"Archive generated with {len(incluidos)} issues -> {RUTA_SALIDA}")


if __name__ == "__main__":
    generar()
