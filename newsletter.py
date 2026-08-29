import logging
from pathlib import Path

from agentes.imagenes import elegir_imagenes
from agentes.investigador import investigar
from agentes.redactor import redactar
from agentes.verificador import verificar
from contratos.esquemas import RegistroEnvio, SolicitudNewsletter
from costes.registro import resumen_gasto
from herramientas.catalogo import elegir_autor_pendiente, registrar_envio
from modelos.anthropic_adapter import AnthropicAdapter
from plantillas.email import renderizar_html

logger = logging.getLogger(__name__)

RUTA_SALIDA = Path(__file__).resolve().parent / "salida"


def generar_newsletter(solicitud: SolicitudNewsletter):
    autor = elegir_autor_pendiente(solicitud.siglo, solicitud.disciplina)
    if autor is None:
        raise RuntimeError(
            f"No quedan autores pendientes en el catálogo para "
            f"{solicitud.siglo} / {solicitud.disciplina}"
        )
    logger.info(f"Autor elegido: {autor.nombre}")

    modelo_investigador = AnthropicAdapter(etiqueta="investigador")
    modelo_redactor = AnthropicAdapter(etiqueta="redactor")
    modelo_verificador = AnthropicAdapter(etiqueta="verificador")

    notas = investigar(autor, modelo_investigador)
    logger.info(f"Investigación completa: {len(notas.titulos_obras_conocidas)} obras encontradas")

    imagenes = elegir_imagenes(notas.nombre, notas.titulos_obras_conocidas, cantidad=3)
    logger.info(f"Imágenes encontradas: {len(imagenes)}/3")

    flashcard = redactar(notas, imagenes, modelo_redactor)
    resultado = verificar(flashcard, notas, modelo_verificador)

    registrar_envio(
        RegistroEnvio(
            nombre=autor.nombre,
            corriente=flashcard.corriente,
            periodo=flashcard.periodo,
            siglo=solicitud.siglo,
        )
    )

    return resultado


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    solicitud = SolicitudNewsletter(
        siglo=input("¿Qué siglo? (ej. 'siglo XIX'): ") or "siglo XIX",
        disciplina=input("¿Qué disciplina? (escultura/arquitectura/pintura/poesía/cualquiera): ")
        or "cualquiera",
    )

    resultado = generar_newsletter(solicitud)

    print(f"\nFiabilidad: {resultado.fiabilidad}")
    if resultado.advertencias:
        print("Advertencias:")
        for advertencia in resultado.advertencias:
            print(f" - {advertencia}")

    RUTA_SALIDA.mkdir(exist_ok=True)
    nombre_archivo = resultado.flashcard.nombre.lower().replace(" ", "_")
    ruta_html = RUTA_SALIDA / f"{nombre_archivo}.html"
    ruta_html.write_text(renderizar_html(resultado.flashcard), encoding="utf-8")
    print(f"\nNewsletter guardado en: {ruta_html}")

    gasto = resumen_gasto()
    print(
        f"\nGasto acumulado total en esta máquina: ${gasto['coste_total_usd']:.4f} "
        f"({gasto['llamadas']} llamadas) — {gasto['por_etiqueta']}"
    )
