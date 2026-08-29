from pathlib import Path

from plantillas.archivo import cargar_incluidos, tarjeta_html

RUTA_SALIDA = Path(__file__).resolve().parent / "index.html"

# El formulario NO está conectado a nada todavía (no hay Supabase montado):
# solo confirma visualmente y avisa de que las suscripciones aún no están
# abiertas. Nunca debe fingir que guarda un email que en realidad se pierde.
SCRIPT_FORMULARIO = """
<script>
  document.getElementById('form-suscripcion').addEventListener('submit', function (e) {
    e.preventDefault();
    document.getElementById('mensaje-formulario').textContent =
      "Thanks for the interest — sign-ups aren't open yet. Check back soon.";
  });
</script>
"""


def generar() -> None:
    destacados = cargar_incluidos()[:3]
    tarjetas = "".join(tarjeta_html(r, prefijo_ruta="") for r in destacados)

    RUTA_SALIDA.write_text(
        f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>curiosARTy</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@800;900&display=swap" rel="stylesheet">
</head>
<body style="margin:0; padding:0; background-color:#0a0a0a;">
  <div style="max-width:760px; margin:0 auto; padding:64px 24px;">

    <span style="font-family:'Helvetica Neue',Arial,sans-serif; font-size:28px; font-weight:900;">
      <span style="color:#f5f5f5;">curios</span><span style="color:#00cc00;">ART</span><span style="color:#f5f5f5;">y</span>
    </span>
    <p style="font-family:'Helvetica Neue',Arial,sans-serif; font-size:13px; letter-spacing:2px; color:#6b6b6b; margin:6px 0 48px 0;">ONE ARTIST AT A TIME</p>

    <h1 style="font-family:'Orbitron','Helvetica Neue',Arial,sans-serif; font-size:36px; font-weight:900; line-height:1.25; color:#f5f5f5; margin:0 0 20px 0;">
      Discover art history,<br/>one flashcard at a time.
    </h1>
    <p style="font-family:Georgia,'Times New Roman',serif; font-size:17px; line-height:1.65; color:#a3a3a3; max-width:560px; margin:0 0 32px 0;">
      Every few days curiosARTy researches one real sculptor, architect, painter, or poet,
      fact-checks its own work, and illustrates it exclusively with public-domain art.
      No stock content, no filler — just one artist, done properly.
    </p>

    <form id="form-suscripcion" style="display:flex; gap:0; max-width:420px; margin-bottom:8px;">
      <input type="email" required placeholder="you@email.com"
             style="flex:1; font-family:'Helvetica Neue',Arial,sans-serif; font-size:14px; padding:14px 16px; background:#111111; border:1px solid #333333; color:#f5f5f5;" />
      <button type="submit"
              style="font-family:'Helvetica Neue',Arial,sans-serif; font-size:13px; font-weight:700; letter-spacing:1px; color:#0a0a0a; background-color:#00cc00; border:none; padding:0 24px; cursor:pointer;">
        SUBSCRIBE
      </button>
    </form>
    <p id="mensaje-formulario" style="font-family:'Helvetica Neue',Arial,sans-serif; font-size:12px; color:#6b6b6b; margin:0 0 64px 0;">
      Launching soon — no spam, unsubscribe anytime.
    </p>

    <p style="font-family:'Helvetica Neue',Arial,sans-serif; font-size:13px; font-weight:700; letter-spacing:2px; color:#6b6b6b; margin:0 0 24px 0;">SEE A REAL ISSUE</p>
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:24px; margin-bottom:32px;">
      {tarjetas}
    </div>
    <a href="archivo/index.html" style="font-family:'Helvetica Neue',Arial,sans-serif; font-size:13px; font-weight:700; letter-spacing:0.5px; color:#00cc00; text-decoration:none;">
      Browse the full archive &rarr;
    </a>

    <p style="font-family:'Helvetica Neue',Arial,sans-serif; font-size:12px; color:#444444; margin-top:80px;">
      Built in the open — <a href="https://github.com/rgst77/newsletter-arte" style="color:#6b6b6b;">source on GitHub</a>
    </p>
  </div>
  {SCRIPT_FORMULARIO}
</body>
</html>""",
        encoding="utf-8",
    )
    print(f"Landing generated with {len(destacados)} featured issues -> {RUTA_SALIDA}")


if __name__ == "__main__":
    generar()
