import html

from contratos.esquemas import FlashcardNewsletter

# HTML de correo != HTML web: los clientes (Gmail, Outlook...) no soportan CSS
# moderno, así que todo el estilo va inline y la maquetación usa tablas. Esta
# función es deliberadamente determinista (sin LLM): nunca debe poder inventar
# una URL ni romper la maqueta.


def _bloque_imagen(url_imagen: str, titulo_obra: str, creditos: str, url_fuente: str) -> str:
    titulo = html.escape(titulo_obra)
    creditos_txt = html.escape(creditos)
    return f"""
    <tr>
      <td style="padding: 0 0 24px 0;">
        <img src="{html.escape(url_imagen)}" alt="{titulo}"
             style="display:block; width:100%; max-width:560px; height:auto; border-radius:6px;" />
        <p style="margin:8px 0 0 0; font-family:Georgia,serif; font-size:13px; color:#666666;">
          <strong>{titulo}</strong><br/>
          <a href="{html.escape(url_fuente)}" style="color:#8a6d3b; text-decoration:none;">{creditos_txt}</a>
        </p>
      </td>
    </tr>"""


def renderizar_html(flashcard: FlashcardNewsletter) -> str:
    bloques_imagenes = "".join(
        _bloque_imagen(img.url_imagen, img.titulo_obra, img.creditos, img.url_fuente)
        for img in flashcard.imagenes
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><title>{html.escape(flashcard.nombre)}</title></head>
<body style="margin:0; padding:0; background-color:#f4f1ea;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f1ea;">
    <tr>
      <td align="center" style="padding: 32px 16px;">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0"
               style="background-color:#ffffff; max-width:600px; width:100%;">
          <tr>
            <td style="padding: 32px 32px 8px 32px; font-family:Georgia,serif;">
              <p style="margin:0; font-size:12px; letter-spacing:1px; text-transform:uppercase; color:#8a6d3b;">
                {html.escape(flashcard.corriente)} &middot; {html.escape(flashcard.periodo)}
              </p>
              <h1 style="margin:8px 0 24px 0; font-size:28px; color:#1a1a1a;">
                {html.escape(flashcard.nombre)}
              </h1>
              <p style="margin:0 0 28px 0; font-size:16px; line-height:1.6; color:#333333;">
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
