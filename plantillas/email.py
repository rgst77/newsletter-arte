import html

from contratos.esquemas import FlashcardNewsletter

# HTML de correo != HTML web: los clientes (Gmail, Outlook...) no soportan CSS
# moderno, así que todo el estilo va inline y la maquetación usa tablas. Esta
# función es deliberadamente determinista (sin LLM): nunca debe poder inventar
# una URL ni romper la maqueta.

# Orbitron (la fuente del logo, ver marca/logo.svg) se enlaza vía Google Fonts
# para el nombre del autor, pero el soporte de fuentes web en email es
# irregular: Apple Mail / iOS Mail suelen cargarla, Gmail es inconsistente,
# Outlook de escritorio la ignora siempre. Por eso lleva SIEMPRE un fallback
# en negrita a fuente de sistema — en el peor caso se ve como antes, nunca se
# rompe.
FUENTE_PEQUENA = "'Helvetica Neue', Helvetica, Arial, sans-serif"
FUENTE_TITULO = "'Orbitron', 'Helvetica Neue', Helvetica, Arial, sans-serif"
FUENTE_CUERPO = "Georgia, 'Times New Roman', serif"

NEGRO_MARCA = "#0a0a0a"
PANEL_CONTEXTO = "#232323"  # gris claro de verdad, para que el bloque se note contra el negro
VERDE_MARCA = "#00cc00"
GRIS_TEXTO = "#a3a3a3"
GRIS_TENUE = "#6b6b6b"

DISCIPLINAS_EN = {
    "escultura": "SCULPTURE",
    "arquitectura": "ARCHITECTURE",
    "pintura": "PAINTING",
    "poesía": "POETRY",
}

DISCIPLINAS_EMOJI = {
    "escultura": "\U0001F5FF",  # 🗿
    "arquitectura": "\U0001F3DB️",  # 🏛️
    "pintura": "\U0001F5BC️",  # 🖼️
    "poesía": "✒️",  # ✒️
}

EMOJI_SIGLO = "⌛"  # ⏳
EMOJI_TREND = "\U0001F3A8"  # 🎨

# Cobertura no exhaustiva a propósito: si una nacionalidad no está aquí, el
# campo simplemente se muestra sin bandera en vez de romper el render. Ir
# ampliando según lo pida el catálogo real.
NACIONALIDADES_BANDERA = {
    "french": "\U0001F1EB\U0001F1F7", "italian": "\U0001F1EE\U0001F1F9",
    "spanish": "\U0001F1EA\U0001F1F8", "german": "\U0001F1E9\U0001F1EA",
    "dutch": "\U0001F1F3\U0001F1F1", "flemish": "\U0001F1E7\U0001F1EA",
    "belgian": "\U0001F1E7\U0001F1EA", "english": "\U0001F1EC\U0001F1E7",
    "british": "\U0001F1EC\U0001F1E7", "scottish": "\U0001F1EC\U0001F1E7",
    "irish": "\U0001F1EE\U0001F1EA", "portuguese": "\U0001F1F5\U0001F1F9",
    "austrian": "\U0001F1E6\U0001F1F9", "swiss": "\U0001F1E8\U0001F1ED",
    "russian": "\U0001F1F7\U0001F1FA", "polish": "\U0001F1F5\U0001F1F1",
    "greek": "\U0001F1EC\U0001F1F7", "swedish": "\U0001F1F8\U0001F1EA",
    "norwegian": "\U0001F1F3\U0001F1F4", "danish": "\U0001F1E9\U0001F1F0",
    "american": "\U0001F1FA\U0001F1F8", "mexican": "\U0001F1F2\U0001F1FD",
    "brazilian": "\U0001F1E7\U0001F1F7", "argentine": "\U0001F1E6\U0001F1F7",
    "argentinian": "\U0001F1E6\U0001F1F7", "japanese": "\U0001F1EF\U0001F1F5",
    "chinese": "\U0001F1E8\U0001F1F3", "indian": "\U0001F1EE\U0001F1F3",
    "czech": "\U0001F1E8\U0001F1FF", "hungarian": "\U0001F1ED\U0001F1FA",
    "romanian": "\U0001F1F7\U0001F1F4", "turkish": "\U0001F1F9\U0001F1F7",
    "egyptian": "\U0001F1EA\U0001F1EC", "colombian": "\U0001F1E8\U0001F1F4",
    "cuban": "\U0001F1E8\U0001F1FA", "chilean": "\U0001F1E8\U0001F1F1",
    "peruvian": "\U0001F1F5\U0001F1EA", "canadian": "\U0001F1E8\U0001F1E6",
    "australian": "\U0001F1E6\U0001F1FA", "florentine": "\U0001F1EE\U0001F1F9",
    "venetian": "\U0001F1EE\U0001F1F9", "roman": "\U0001F1EE\U0001F1F9",
    "catalan": "\U0001F1EA\U0001F1F8", "basque": "\U0001F1EA\U0001F1F8",
}

_NUMEROS_ROMANOS = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def _romano_a_entero(romano: str) -> int:
    total, anterior = 0, 0
    for caracter in reversed(romano):
        valor = _NUMEROS_ROMANOS[caracter]
        total += -valor if valor < anterior else valor
        anterior = max(anterior, valor)
    return total


def _ordinal(n: int) -> str:
    sufijo = "TH" if 10 <= n % 100 <= 20 else {1: "ST", 2: "ND", 3: "RD"}.get(n % 10, "TH")
    return f"{n}{sufijo}"


def _siglo_a_ordinal(siglo: str) -> str:
    # Deriva el ordinal a partir del número romano en vez de un diccionario a
    # mano, para que ampliar el catálogo a más siglos nunca requiera acordarse
    # de tocar la plantilla: la coherencia visual queda garantizada por diseño.
    partes = siglo.upper().split()
    if len(partes) == 2 and partes[0] == "SIGLO":
        try:
            return _ordinal(_romano_a_entero(partes[1]))
        except KeyError:
            pass
    return siglo.upper()


def _bandera_nacionalidad(nacionalidad: str) -> str:
    return NACIONALIDADES_BANDERA.get(nacionalidad.strip().lower(), "")


def _campo(etiqueta: str, valor: str, emoji: str = "") -> str:
    prefijo = f"{emoji} " if emoji else ""
    return (
        f'<span style="color:{GRIS_TENUE};">{prefijo}{html.escape(etiqueta)}</span><br/>'
        f'<span style="color:{VERDE_MARCA}; font-weight:700;">{html.escape(valor)}</span>'
    )


def _bloque_imagen(url_imagen: str, titulo_obra: str, creditos: str, url_fuente: str) -> str:
    titulo = html.escape(titulo_obra)
    creditos_txt = html.escape(creditos)
    return f"""
    <tr>
      <td style="padding: 0 0 24px 0;">
        <img src="{html.escape(url_imagen)}" alt="{titulo}"
             style="display:block; width:100%; max-width:560px; height:auto;" />
        <p style="margin:8px 0 0 0; font-family:{FUENTE_PEQUENA}; font-size:12px; color:{GRIS_TENUE};">
          <strong style="color:{GRIS_TEXTO};">{titulo}</strong><br/>
          <a href="{html.escape(url_fuente)}" style="color:{VERDE_MARCA}; text-decoration:none;">{creditos_txt}</a>
        </p>
      </td>
    </tr>"""


def _header() -> str:
    return f"""
    <tr>
      <td style="padding:24px 32px 16px 32px; border-bottom:1px solid #222222;">
        <span style="font-family:'Helvetica Neue', Helvetica, Arial, sans-serif; font-size:26px; font-weight:900; letter-spacing:-0.5px;">
          <span style="color:#f5f5f5;">curios</span><span style="color:{VERDE_MARCA};">ART</span><span style="color:#f5f5f5;">y</span>
        </span>
        <br/>
        <span style="font-family:{FUENTE_PEQUENA}; font-size:11px; letter-spacing:2px; color:{GRIS_TENUE};">ONE ARTIST AT A TIME</span>
      </td>
    </tr>"""


def _footer() -> str:
    return f"""
    <tr>
      <td style="padding:24px 32px; border-top:1px solid #222222;">
        <p style="margin:0 0 8px 0; font-family:{FUENTE_PEQUENA}; font-size:11px; letter-spacing:0.5px; color:{GRIS_TENUE}; line-height:1.6;">
          curiosARTy is generated by an AI research pipeline and illustrated exclusively
          with public-domain and freely-licensed images (The Met Open Access / Wikimedia Commons).
        </p>
        <p style="margin:0; font-family:{FUENTE_PEQUENA}; font-size:11px; letter-spacing:0.5px;">
          <a href="https://github.com/rgst77/newsletter-arte" style="color:{VERDE_MARCA}; text-decoration:none;">Archive on GitHub</a>
          <span style="color:#333333;"> &middot; </span>
          <a href="#" style="color:{GRIS_TENUE}; text-decoration:none;">Unsubscribe</a>
        </p>
      </td>
    </tr>"""


def renderizar_html(flashcard: FlashcardNewsletter) -> str:
    siglo_valor = _siglo_a_ordinal(flashcard.siglo)
    disciplina_valor = DISCIPLINAS_EN.get(flashcard.disciplina, flashcard.disciplina.upper())
    emoji_disciplina = DISCIPLINAS_EMOJI.get(flashcard.disciplina, "")
    emoji_bandera = _bandera_nacionalidad(flashcard.nacionalidad)

    celda = 'style="width:50%; padding:0 12px 14px 0; vertical-align:top;"'
    celda_der = 'style="width:50%; padding:0 0 14px 12px; vertical-align:top;"'
    celda_ult = 'style="width:50%; padding:0 12px 0 0; vertical-align:top;"'
    celda_ult_der = 'style="width:50%; padding:0 0 0 12px; vertical-align:top;"'
    kicker = f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td {celda}>{_campo("CENTURY", siglo_valor, EMOJI_SIGLO)}</td>
          <td {celda_der}>{_campo("DISCIPLINE", disciplina_valor, emoji_disciplina)}</td>
        </tr>
        <tr>
          <td {celda_ult}>{_campo("NATIONALITY", flashcard.nacionalidad.upper(), emoji_bandera)}</td>
          <td {celda_ult_der}>{_campo("TREND", flashcard.corriente.upper(), EMOJI_TREND)}</td>
        </tr>
      </table>"""

    bloques_imagenes = "".join(
        _bloque_imagen(img.url_imagen, img.titulo_obra, img.creditos, img.url_fuente)
        for img in flashcard.imagenes
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(flashcard.nombre)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@800;900&display=swap" rel="stylesheet">
</head>
<body style="margin:0; padding:0; background-color:{NEGRO_MARCA};">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:{NEGRO_MARCA};">
    <tr>
      <td align="center" style="padding: 32px 16px;">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0"
               style="background-color:{NEGRO_MARCA}; max-width:600px; width:100%;">
          {_header()}
          <tr>
            <td style="background-color:{PANEL_CONTEXTO}; padding:18px 32px; border-left:3px solid {VERDE_MARCA}; font-family:{FUENTE_PEQUENA}; font-size:11px; font-weight:700; letter-spacing:1px; line-height:1.6;">
              {kicker}
            </td>
          </tr>
          <tr>
            <td style="padding: 24px 32px 8px 32px;">
              <h1 style="margin:0 0 4px 0; font-family:{FUENTE_TITULO}; font-size:32px; font-weight:900; letter-spacing:0.5px; color:#f5f5f5;">
                {html.escape(flashcard.nombre)}
              </h1>
              <p style="margin:0 0 24px 0; font-family:{FUENTE_PEQUENA}; font-size:12px; letter-spacing:0.5px; color:{GRIS_TENUE};">
                {html.escape(flashcard.periodo)}
              </p>
              <p style="margin:0 0 28px 0; font-family:{FUENTE_CUERPO}; font-size:16px; line-height:1.65; color:{GRIS_TEXTO};">
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
          {_footer()}
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
