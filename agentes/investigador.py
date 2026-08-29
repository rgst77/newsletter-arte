from pydantic import ValidationError

from contratos.esquemas import AutorCatalogo, NotasAutor
from contratos.herramientas import DefinicionHerramienta
from herramientas.buscador import buscar
from herramientas.lector import leer_pagina
from modelos.base import ModeloLLM

MAX_ITERACIONES = 6

SYSTEM_PROMPT = (
    "You are a research agent specialized in art history, sculpture, architecture "
    "and poetry. Your only job is to research ONE specific author you are given, NOT "
    "to write the final newsletter. You have a maximum of 8 searches in total. You "
    "must cover: a short biography, the artistic movement they belonged to (verify "
    "it, do not trust the initial hint without checking), their concrete "
    "period/years of activity, and above all the EXACT TITLES of at least 3 known "
    "works (sculptures, buildings, paintings or poems depending on their "
    "discipline) — this is critical because another bot will use those exact titles "
    "to search for real images of those works.\n\n"
    "IMPORTANT: write ALL your output (biography, movement, period, work titles) in "
    "English, even if the sources you find are in another language.\n\n"
    "If a 'buscar' result's snippet looks relevant but is too short, use "
    "'leer_pagina' on that URL to dig deeper. Once you have enough information, "
    "deliver your findings by calling 'entregar_notas' exactly once.\n\n"
    "CRITICAL RULE: you may only cite in 'fuentes' results that actually came from "
    "'buscar' or 'leer_pagina' in this conversation, and you may only list in "
    "'titulos_obras_conocidas' works you actually saw mentioned in those real "
    "results. If searches repeatedly fail, NEVER invent works, dates or sources "
    "from your internal memory: deliver partial notes explaining what could not be "
    "verified."
)

HERRAMIENTA_BUSCAR = DefinicionHerramienta(
    nombre="buscar",
    descripcion=(
        "Searches the internet for current information on a specific topic. "
        "Can be called multiple times with different, specific queries."
    ),
    esquema_parametros={
        "type": "object",
        "properties": {"consulta": {"type": "string", "description": "Text to search for"}},
        "required": ["consulta"],
    },
)

HERRAMIENTA_LEER = DefinicionHerramienta(
    nombre="leer_pagina",
    descripcion=(
        "Downloads the full text of a specific URL (obtained from a 'buscar' "
        "result), to dig deeper when the short snippet is not enough."
    ),
    esquema_parametros={
        "type": "object",
        "properties": {"url": {"type": "string", "description": "Exact URL to read"}},
        "required": ["url"],
    },
)

HERRAMIENTA_ENTREGAR_NOTAS = DefinicionHerramienta(
    nombre="entregar_notas",
    descripcion="Delivers the findings gathered about the author. Call it exactly once, when done.",
    esquema_parametros={
        "type": "object",
        "properties": {
            "nombre": {"type": "string"},
            "corriente": {"type": "string", "description": "Verified artistic movement, in English"},
            "periodo": {"type": "string", "description": "Concrete years/range of activity"},
            "notas": {"type": "string", "description": "Biography and context, in English"},
            "titulos_obras_conocidas": {
                "type": "array",
                "items": {"type": "string"},
                "description": "EXACT titles of works found in real sources",
            },
            "fuentes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "titulo": {"type": "string"},
                        "url": {"type": "string"},
                    },
                    "required": ["titulo", "url"],
                },
            },
        },
        "required": ["nombre", "corriente", "periodo", "notas", "titulos_obras_conocidas", "fuentes"],
    },
)


def investigar(autor: AutorCatalogo, modelo: ModeloLLM) -> NotasAutor:
    historial = [
        {
            "role": "user",
            "content": (
                f"Research: {autor.nombre} ({autor.disciplina}, {autor.siglo}). "
                f"Initial movement hint (verify it, do not trust it blindly): "
                f"{autor.corriente_orientativa or 'unknown'}."
            ),
        }
    ]

    for _ in range(MAX_ITERACIONES):
        respuesta = modelo.conversar(
            historial,
            herramientas=[HERRAMIENTA_BUSCAR, HERRAMIENTA_LEER, HERRAMIENTA_ENTREGAR_NOTAS],
            system=SYSTEM_PROMPT,
        )
        historial.append(respuesta.mensaje_bruto)

        if not respuesta.llamadas_herramientas:
            historial.append(
                {
                    "role": "user",
                    "content": "You must keep researching or deliver your notes with 'entregar_notas'.",
                }
            )
            continue

        bloques_resultado = []
        for llamada in respuesta.llamadas_herramientas:
            if llamada.nombre == "entregar_notas":
                try:
                    return NotasAutor(**llamada.argumentos)
                except ValidationError as error:
                    texto_resultado = f"Error: notes do not match the required format: {error}"

            elif llamada.nombre == "buscar":
                try:
                    resultados = buscar(llamada.argumentos["consulta"], 5)
                    texto_resultado = "\n\n".join(
                        f"{r.titulo}\n{r.url}\n{r.fragmento}" for r in resultados
                    )
                except Exception as error:
                    texto_resultado = f"Error: search failed ({error}). Try a different query."

            elif llamada.nombre == "leer_pagina":
                try:
                    texto_resultado = leer_pagina(llamada.argumentos["url"])
                except Exception as error:
                    texto_resultado = f"Error: could not read the page ({error})."

            else:
                texto_resultado = f"Error: tool '{llamada.nombre}' does not exist."

            bloques_resultado.append(
                modelo.bloque_resultado_herramienta(llamada.id, texto_resultado)
            )

        historial.append({"role": "user", "content": bloques_resultado})

    raise RuntimeError("The investigador reached the iteration limit without delivering notes")
