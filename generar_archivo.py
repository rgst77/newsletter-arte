from pathlib import Path

from plantillas.archivo import agrupar_por_disciplina, cargar_incluidos, disciplina_info, tarjeta_html

RUTA_ARCHIVO = Path(__file__).resolve().parent / "archivo"

CABECERA_FUENTES = '<link rel="preconnect" href="https://fonts.googleapis.com">\n  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@800;900&display=swap" rel="stylesheet">'


def _logo(prefijo_ruta: str) -> str:
    return f"""<a href="{prefijo_ruta}index.html" style="text-decoration:none; font-family:'Helvetica Neue',Arial,sans-serif; font-size:28px; font-weight:900;">
      <span style="color:#f5f5f5;">curios</span><span style="color:#00cc00;">ART</span><span style="color:#f5f5f5;">y</span>
    </a>"""


def _portada_html(disciplina: str, entradas: list[dict]) -> str:
    info = disciplina_info(disciplina)
    return f"""
    <a href="{info['slug']}/index.html" style="text-decoration:none; display:block; border:1px solid #222222; background:#141414; padding:32px 24px; text-align:center;">
      <div style="font-size:40px; margin-bottom:12px;">{info['emoji']}</div>
      <p style="margin:0; font-family:'Helvetica Neue',Arial,sans-serif; font-size:16px; font-weight:700; letter-spacing:1px; color:#f5f5f5;">{info['etiqueta']}</p>
      <p style="margin:6px 0 0 0; font-family:'Helvetica Neue',Arial,sans-serif; font-size:12px; color:#6b6b6b;">{len(entradas)} issue{'s' if len(entradas) != 1 else ''}</p>
    </a>"""


def _pagina(titulo: str, prefijo_ruta: str, cuerpo: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{titulo} — curiosARTy</title>
  {CABECERA_FUENTES}
</head>
<body style="margin:0; padding:0; background-color:#0a0a0a;">
  <div style="max-width:760px; margin:0 auto; padding:48px 24px;">
    {_logo(prefijo_ruta)}
    {cuerpo}
  </div>
</body>
</html>"""


def generar() -> None:
    incluidos = cargar_incluidos()
    grupos = agrupar_por_disciplina(incluidos)

    # Portada del archivo: una ficha por disciplina, no todo apilado.
    portadas = "".join(_portada_html(disciplina, entradas) for disciplina, entradas in grupos)
    cuerpo_indice = f"""
    <p style="font-family:'Helvetica Neue',Arial,sans-serif; font-size:13px; letter-spacing:2px; color:#6b6b6b; margin:6px 0 40px 0;">ARCHIVE — BROWSE BY DISCIPLINE</p>
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(160px, 1fr)); gap:16px;">
      {portadas}
    </div>"""
    RUTA_ARCHIVO.mkdir(exist_ok=True)
    (RUTA_ARCHIVO / "index.html").write_text(_pagina("Archive", "../", cuerpo_indice), encoding="utf-8")

    # Una página por disciplina, con sus issues ordenados por siglo.
    for disciplina, entradas in grupos:
        info = disciplina_info(disciplina)
        tarjetas = "".join(tarjeta_html(r, prefijo_ruta="../../") for r in entradas)
        cuerpo_disciplina = f"""
    <p style="font-family:'Helvetica Neue',Arial,sans-serif; font-size:13px; letter-spacing:2px; color:#6b6b6b; margin:6px 0 8px 0;">
      <a href="../index.html" style="color:#6b6b6b; text-decoration:none;">ARCHIVE</a> / {info['etiqueta']}
    </p>
    <h1 style="font-family:'Orbitron','Helvetica Neue',Arial,sans-serif; font-size:32px; font-weight:900; color:#f5f5f5; margin:0 0 32px 0;">
      {info['emoji']} {info['etiqueta']}
    </h1>
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:24px;">
      {tarjetas}
    </div>"""
        carpeta_disciplina = RUTA_ARCHIVO / info["slug"]
        carpeta_disciplina.mkdir(exist_ok=True)
        (carpeta_disciplina / "index.html").write_text(
            _pagina(info["etiqueta"].title(), "../../", cuerpo_disciplina), encoding="utf-8"
        )

    print(f"Archive generated: {len(incluidos)} issue(s) across {len(grupos)} discipline page(s)")


if __name__ == "__main__":
    generar()
