from pydantic import ValidationError

from contratos.esquemas import FlashcardNewsletter, ImagenObra, NotasAutor
from contratos.herramientas import DefinicionHerramienta
from modelos.base import ModeloLLM

MAX_INTENTOS = 3

SYSTEM_PROMPT = (
    "You are a writer agent specialized in art outreach for a curious, non-expert "
    "audience. You receive research notes already gathered about ONE author and your "
    "only job is to turn them into a short, engaging biography in 'flashcard' "
    "format: 3 to 5 sentences, warm tone, no unnecessary jargon, the kind that makes "
    "someone want to keep reading. You have NO access to any search tool: use only "
    "the information in the notes you were given, never your own knowledge. Write "
    "the biography in English. Deliver the result by calling 'entregar_biografia'."
)

HERRAMIENTA_ENTREGAR_BIOGRAFIA = DefinicionHerramienta(
    nombre="entregar_biografia",
    descripcion="Delivers the flashcard-format biography. Call it exactly once.",
    esquema_parametros={
        "type": "object",
        "properties": {
            "biografia": {
                "type": "string",
                "description": "3 to 5 sentences, warm and accessible tone, in English",
            },
        },
        "required": ["biografia"],
    },
)


def redactar(
    notas: NotasAutor, disciplina: str, siglo: str, imagenes: list[ImagenObra], modelo: ModeloLLM
) -> FlashcardNewsletter:
    fuentes_texto = "\n".join(f"- {f.titulo}: {f.url}" for f in notas.fuentes)
    historial = [
        {
            "role": "user",
            "content": (
                f"Author: {notas.nombre}\nMovement: {notas.corriente}\nPeriod: {notas.periodo}\n\n"
                f"Research notes:\n{notas.notas}\n\nAvailable sources:\n{fuentes_texto}"
            ),
        }
    ]

    for _ in range(MAX_INTENTOS):
        respuesta = modelo.conversar(
            historial,
            herramientas=[HERRAMIENTA_ENTREGAR_BIOGRAFIA],
            system=SYSTEM_PROMPT,
        )
        historial.append(respuesta.mensaje_bruto)

        entrega = next(
            (l for l in respuesta.llamadas_herramientas if l.nombre == "entregar_biografia"),
            None,
        )
        if entrega:
            try:
                # nombre/corriente/periodo/imágenes se pasan directo del pipeline,
                # nunca los regenera el LLM: evita que invente o reescriba URLs.
                return FlashcardNewsletter(
                    nombre=notas.nombre,
                    disciplina=disciplina,
                    siglo=siglo,
                    corriente=notas.corriente,
                    periodo=notas.periodo,
                    biografia=entrega.argumentos["biografia"],
                    imagenes=imagenes,
                )
            except (ValidationError, KeyError) as error:
                historial.append(
                    {
                        "role": "user",
                        "content": [
                            modelo.bloque_resultado_herramienta(
                                entrega.id,
                                f"Error: the biography does not match the required format: {error}",
                            )
                        ],
                    }
                )
                continue

        historial.append(
            {"role": "user", "content": "You must deliver the biography by calling 'entregar_biografia'."}
        )

    raise RuntimeError("The redactor reached the attempt limit without delivering a valid biography")
