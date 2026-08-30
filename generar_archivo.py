from pathlib import Path

from plantillas.archivo import agrupar_por_disciplina, cargar_incluidos, tarjeta_html

RUTA_SALIDA = Path(__file__).resolve().parent / "archivo" / "index.html"


def _seccion_html(disciplina: str, entradas: list[dict]) -> str:
    tarjetas = "".join(tarjeta_html(r, prefijo_ruta="../") for r in entradas)
    return f"""
    <p style="font-family:'Helvetica Neue',Arial,sans-serif; font-size:13px; font-weight:700; letter-spacing:2px; color:#00cc00; margin:48px 0 20px 0; border-bottom:1px solid #222222; padding-bottom:12px;">{disciplina}</p>
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:24px;">
      {tarjetas}
    </div>"""


def generar() -> None:
    incluidos = cargar_incluidos()
    secciones = "".join(
        _seccion_html(disciplina, entradas) for disciplina, entradas in agrupar_por_disciplina(incluidos)
    )

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
    <a href="../index.html" style="text-decoration:none; font-family:'Helvetica Neue',Arial,sans-serif; font-size:28px; font-weight:900;">
      <span style="color:#f5f5f5;">curios</span><span style="color:#00cc00;">ART</span><span style="color:#f5f5f5;">y</span>
    </a>
    <p style="font-family:'Helvetica Neue',Arial,sans-serif; font-size:13px; letter-spacing:2px; color:#6b6b6b; margin:6px 0 0 0;">ARCHIVE — EVERY ISSUE SENT</p>
    {secciones}
  </div>
</body>
</html>""",
        encoding="utf-8",
    )
    print(f"Archive generated with {len(incluidos)} issues -> {RUTA_SALIDA}")


if __name__ == "__main__":
    generar()
