import logging
import os
from datetime import datetime, timedelta

from contratos.esquemas import SolicitudNewsletter
from generar_archivo import generar as generar_archivo
from generar_landing import generar as generar_landing
from herramientas.catalogo import cargar_enviados, elegir_siguiente_siglo_disciplina
from herramientas.envio import asunto_para, enviar_a_lista
from herramientas.suscriptores import obtener_suscriptores
from newsletter import generar_newsletter

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

DIAS_ENTRE_ENVIOS = 3


def _toca_enviar_hoy() -> bool:
    enviados = cargar_enviados()
    if not enviados:
        return True
    ultimo = max(r.fecha_envio for r in enviados)
    return datetime.now() - ultimo >= timedelta(days=DIAS_ENTRE_ENVIOS)


def main() -> None:
    forzado = os.environ.get("FORZAR_ENVIO", "").lower() == "true"
    if not forzado and not _toca_enviar_hoy():
        logger.info(f"Todavía no toca enviar (cadencia: cada {DIAS_ENTRE_ENVIOS} días). Saliendo sin hacer nada.")
        return
    if forzado:
        logger.info("Envío forzado manualmente: se ignora la cadencia de 3 días.")

    siglo, disciplina = elegir_siguiente_siglo_disciplina()
    logger.info(f"Siguiente en la rotación: {siglo} / {disciplina}")

    resultado, ruta_html = generar_newsletter(SolicitudNewsletter(siglo=siglo, disciplina=disciplina))
    logger.info(f"Newsletter generado: {resultado.flashcard.nombre} (fiabilidad: {resultado.fiabilidad})")

    generar_archivo()
    generar_landing()

    suscriptores = obtener_suscriptores()
    if not suscriptores:
        logger.info("No hay suscriptores todavía — newsletter generado y archivado, pero no se envía nada.")
        return

    asunto = asunto_para(resultado.flashcard.nombre)
    html = ruta_html.read_text(encoding="utf-8")
    envios = enviar_a_lista(suscriptores, asunto, html)
    fallos = [e for e in envios if "error" in e]
    logger.info(f"Enviado a {len(envios) - len(fallos)}/{len(envios)} suscriptor(es).")
    for fallo in fallos:
        logger.warning(f"Fallo al enviar a {fallo['destinatario']}: {fallo['error']}")


if __name__ == "__main__":
    main()
