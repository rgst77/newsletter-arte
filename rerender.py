from pathlib import Path

from contratos.esquemas import FlashcardNewsletter
from plantillas.email import renderizar_html

RUTA_SALIDA = Path(__file__).resolve().parent / "salida"


def rerenderizar_todo() -> None:
    rutas_json = sorted(RUTA_SALIDA.rglob("*.json"))
    for ruta_json in rutas_json:
        flashcard = FlashcardNewsletter.model_validate_json(ruta_json.read_text(encoding="utf-8"))
        ruta_html = ruta_json.with_suffix(".html")
        ruta_html.write_text(renderizar_html(flashcard), encoding="utf-8")
        print(f"Re-rendered: {ruta_html.relative_to(RUTA_SALIDA.parent)}")

    print(f"\n{len(rutas_json)} issue(s) re-rendered with the current template — no API calls made.")


if __name__ == "__main__":
    rerenderizar_todo()
