import html
import json
from pathlib import Path

from plantillas.email import DISCIPLINAS_EN, _romano_a_entero, _siglo_a_ordinal

RUTA_PROYECTO = Path(__file__).resolve().parent.parent
RUTA_ENVIADOS = RUTA_PROYECTO / "datos" / "autores_enviados.json"


def cargar_incluidos() -> list[dict]:
    # Solo se muestran públicamente los envíos que tienen su flashcard en
    # bruto guardado (.json junto al .html): eso garantiza que se pueden
    # re-renderizar con `rerender.py` y por tanto SIEMPRE coinciden con el
    # diseño actual — nunca hay que acordarse de excluir nada a mano.
    registros = json.loads(RUTA_ENVIADOS.read_text(encoding="utf-8"))
    return [
        r for r in registros
        if r.get("archivo_html")
        and (RUTA_PROYECTO / r["archivo_html"]).with_suffix(".json").exists()
    ]


def _siglo_numero(siglo: str) -> int:
    partes = siglo.upper().split()
    if len(partes) == 2 and partes[0] == "SIGLO":
        try:
            return _romano_a_entero(partes[1])
        except KeyError:
            pass
    return 0


def agrupar_por_disciplina(incluidos: list[dict]) -> list[tuple[str, list[dict]]]:
    # Secciones por disciplina (orden alfabético del nombre en inglés), y
    # dentro de cada una ordenado por siglo — así el archivo se puede recorrer
    # como una progresión histórica dentro de cada tipo de arte, en vez de
    # una lista suelta en orden de envío.
    grupos: dict[str, list[dict]] = {}
    for registro in incluidos:
        etiqueta = DISCIPLINAS_EN.get(registro.get("disciplina", ""), registro.get("disciplina", "OTHER").upper())
        grupos.setdefault(etiqueta, []).append(registro)

    for entradas in grupos.values():
        entradas.sort(key=lambda r: _siglo_numero(r["siglo"]))

    return sorted(grupos.items())


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
