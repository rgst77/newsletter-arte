import html

from contratos.esquemas import FlashcardNewsletter

# HTML de correo != HTML web: los clientes (Gmail, Outlook...) no soportan CSS
# moderno ni fuentes web propias, así que todo el estilo va inline, la
# maquetación usa tablas, y el aspecto "moderno" se consigue con peso
# tipográfico/tracking en fuentes de sistema, no con una fuente exótica. Esta
# función es deliberadamente determinista (sin LLM): nunca debe poder inventar
# una URL ni romper la maqueta.

FUENTE_TAG = "'Courier New', Courier, monospace"
FUENTE_TITULO = "'Helvetica Neue', Helvetica, Arial, sans-serif"
FUENTE_CUERPO = "Georgia, 'Times New Roman', serif"

SIGLOS_EN = {
    "siglo XV": "15TH CENTURY",
    "siglo XVI": "16TH CENTURY",
    "siglo XVII": "17TH CENTURY",
    "siglo XVIII": "18TH CENTURY",
    "siglo XIX": "19TH CENTURY",
    "siglo XX": "20TH CENTURY",
    "siglo XXI": "21ST CENTURY",
}

DISCIPLINAS_EN = {
    "escultura": "SCULPTURE",
    "arquitectura": "ARCHITECTURE",
    "pintura": "PAINTING",
    "poesía": "POETRY",
}


def _tag(texto: str, fondo: str, color_texto: str, borde: str = "") -> str:
    estilo_borde = f"border:1px solid {borde};" if borde else ""
    return f"""<td style="padding:0 8px 8px 0;">
      <table role="presentation" cellpadding="0" cellspacing="0"><tr>
        <td style="background-color:{fondo}; {estilo_borde} padding:6px 12px;">
          <span style="font-family:{FUENTE_TAG}; font-size:11px; font-weight:700; letter-spacing:1.5px; color:{color_texto};">{html.escape(texto)}</span>
        </td>
      </tr></table>
    </td>"""


def _bloque_imagen(url_imagen: str, titulo_obra: str, creditos: str, url_fuente: str) -> str:
    titulo = html.escape(titulo_obra)
    creditos_txt = html.escape(creditos)
    return f"""
    <tr>
      <td style="padding: 0 0 24px 0;">
        <img src="{html.escape(url_imagen)}" alt="{titulo}"
             style="display:block; width:100%; max-width:560px; height:auto;" />
        <p style="margin:8px 0 0 0; font-family:{FUENTE_TAG}; font-size:12px; color:#8a8a8a;">
          <strong style="color:#444444;">{titulo}</strong><br/>
          <a href="{html.escape(url_fuente)}" style="color:#0a7d5c; text-decoration:none;">{creditos_txt}</a>
        </p>
      </td>
    </tr>"""


def renderizar_html(flashcard: FlashcardNewsletter) -> str:
    siglo_tag = SIGLOS_EN.get(flashcard.siglo, flashcard.siglo.upper())
    disciplina_tag = DISCIPLINAS_EN.get(flashcard.disciplina, flashcard.disciplina.upper())

    fila_tags = (
        _tag(siglo_tag, "#111111", "#ffffff")
        + _tag(disciplina_tag, "#0a7d5c", "#ffffff")
        + _tag(flashcard.corriente.upper(), "#ffffff", "#111111", borde="#cccccc")
    )

    bloques_imagenes = "".join(
        _bloque_imagen(img.url_imagen, img.titulo_obra, img.creditos, img.url_fuente)
        for img in flashcard.imagenes
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>{html.escape(flashcard.nombre)}</title></head>
<body style="margin:0; padding:0; background-color:#f4f1ea;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f1ea;">
    <tr>
      <td align="center" style="padding: 32px 16px;">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0"
               style="background-color:#ffffff; max-width:600px; width:100%;">
          <tr>
            <td style="padding: 32px 32px 8px 32px;">
              <table role="presentation" cellpadding="0" cellspacing="0"><tr>{fila_tags}</tr></table>
              <h1 style="margin:16px 0 4px 0; font-family:{FUENTE_TITULO}; font-size:34px; font-weight:700; letter-spacing:-0.5px; color:#111111;">
                {html.escape(flashcard.nombre)}
              </h1>
              <p style="margin:0 0 24px 0; font-family:{FUENTE_TAG}; font-size:12px; letter-spacing:1px; color:#8a8a8a;">
                {html.escape(flashcard.periodo)}
              </p>
              <p style="margin:0 0 28px 0; font-family:{FUENTE_CUERPO}; font-size:16px; line-height:1.65; color:#2a2a2a;">
                {html.escape(flashcard.biografia)}
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding: 0 32px 32px 32px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                {bloques_imagenes}
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
