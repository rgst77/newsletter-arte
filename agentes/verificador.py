from pydantic import ValidationError

from contratos.esquemas import FlashcardNewsletter, NewsletterVerificado, NotasAutor
from contratos.herramientas import DefinicionHerramienta
from modelos.base import ModeloLLM

MAX_INTENTOS = 3

SYSTEM_PROMPT = (
    "You are a verifier agent, skeptical by nature. You receive a biography already "
    "written for an art newsletter, together with the original research notes. Your "
    "only job is to assess its reliability, NOT to rewrite it or add new "
    "information.\n\n"
    "Check that every claim in the biography is actually backed by the research "
    "notes, not invented or exaggerated. Assign 'fiabilidad' as 'high' (everything "
    "well backed), 'medium' (some minor inaccuracy) or 'low' (claims without clear "
    "backing in the notes). List every concrete problem you find in 'advertencias', "
    "in English — an empty list means you found no problem. Deliver your assessment "
    "by calling 'entregar_verificacion' exactly once."
)

HERRAMIENTA_ENTREGAR_VERIFICACION = DefinicionHerramienta(
    nombre="entregar_verificacion",
    descripcion="Delivers the reliability assessment. Call it exactly once.",
    esquema_parametros={
        "type": "object",
        "properties": {
            "fiabilidad": {"type": "string", "enum": ["high", "medium", "low"]},
            "advertencias": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["fiabilidad", "advertencias"],
    },
)


def verificar(
    flashcard: FlashcardNewsletter, notas: NotasAutor, modelo: ModeloLLM
) -> NewsletterVerificado:
    historial = [
        {
            "role": "user",
            "content": (
                f"Biography to assess (author: {flashcard.nombre}):\n{flashcard.biografia}\n\n"
                f"Original research notes (for cross-checking):\n{notas.notas}"
            ),
        }
    ]

    for _ in range(MAX_INTENTOS):
        respuesta = modelo.conversar(
            historial,
            herramientas=[HERRAMIENTA_ENTREGAR_VERIFICACION],
            system=SYSTEM_PROMPT,
        )
        historial.append(respuesta.mensaje_bruto)

        entrega = next(
            (l for l in respuesta.llamadas_herramientas if l.nombre == "entregar_verificacion"),
            None,
        )
        if entrega:
            try:
                return NewsletterVerificado(flashcard=flashcard, **entrega.argumentos)
            except ValidationError as error:
                historial.append(
                    {
                        "role": "user",
                        "content": [
                            modelo.bloque_resultado_herramienta(
                                entrega.id,
                                f"Error: the assessment does not match the required format: {error}",
                            )
                        ],
                    }
                )
                continue

        historial.append(
            {
                "role": "user",
                "content": "You must deliver your assessment by calling 'entregar_verificacion'.",
            }
        )

    raise RuntimeError("The verificador reached the attempt limit without delivering an assessment")
