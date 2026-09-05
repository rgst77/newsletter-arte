import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from contratos.esquemas import SolicitudNewsletter
from generar_archivo import generar as generar_archivo
from generar_landing import generar as generar_landing
from herramientas.catalogo import cargar_enviados, elegir_siguiente_siglo_disciplina
from herramientas.envio import asunto_para, enviar_email
from herramientas.suscriptores import actualizar_progreso_suscriptor, obtener_suscriptores
from newsletter import generar_newsletter
from plantillas.archivo import cargar_incluidos

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

DIAS_ENTRE_ENVIOS = 3
RUTA_PROYECTO = Path(__file__).resolve().parent
URL_BAJA_BASE = "https://rgst77.github.io/newsletter-arte/unsubscribe.html?token="

# Modelo de goteo: el contenido se genera a su propio ritmo (rotación por
# siglos, cada 3 días), pero cada suscriptor recibe los issues empezando por
# el #1, a su propio ritmo de 3 días desde que se apuntó — no todos reciben
# lo mismo el mismo día. `cargar_incluidos()` da el orden cronológico de
# generación, que hace de "lista de reproducción" estable para todos.


def _toca_generar_contenido_hoy() -> bool:
    enviados = cargar_enviados()
    if not enviados:
        return True
    ultimo = max(r.fecha_envio for r in enviados)
    return datetime.now() - ultimo >= timedelta(days=DIAS_ENTRE_ENVIOS)


def generar_issue_del_dia(forzado: bool) -> None:
    if not forzado and not _toca_generar_contenido_hoy():
        logger.info(f"Todavía no toca generar contenido nuevo (cadencia: cada {DIAS_ENTRE_ENVIOS} días).")
        return

    siglo, disciplina = elegir_siguiente_siglo_disciplina()
    logger.info(f"Siguiente en la rotación: {siglo} / {disciplina}")
    resultado, _ = generar_newsletter(SolicitudNewsletter(siglo=siglo, disciplina=disciplina))
    logger.info(f"Newsletter generado: {resultado.flashcard.nombre} (fiabilidad: {resultado.fiabilidad})")


def _le_toca_a(suscriptor: dict, forzado: bool) -> bool:
    ultimo = suscriptor.get("fecha_ultimo_envio")
    if not ultimo:
        return True  # nunca ha recibido nada: le toca el #1 ya
    if forzado:
        return True
    return datetime.now(timezone.utc) - datetime.fromisoformat(ultimo) >= timedelta(days=DIAS_ENTRE_ENVIOS)


def enviar_pendientes(forzado: bool) -> None:
    issues = cargar_incluidos()
    if not issues:
        logger.info("Todavía no hay ningún issue generado — nada que enviar.")
        return

    suscriptores = obtener_suscriptores()
    if not suscriptores:
        logger.info("No hay suscriptores todavía.")
        return

    enviados = al_dia = no_toca = fallos = 0
    for suscriptor in suscriptores:
        indice = suscriptor["siguiente_indice"]
        if indice >= len(issues):
            al_dia += 1
            continue
        if not _le_toca_a(suscriptor, forzado):
            no_toca += 1
            continue

        issue = issues[indice]
        ruta_html = RUTA_PROYECTO / issue["archivo_html"]
        # El HTML guardado es el mismo para todos; el enlace de baja se
        # inyecta aquí, por destinatario, con su token único — así nadie
        # puede dar de baja a otro suscriptor sabiendo solo su email.
        html_personalizado = ruta_html.read_text(encoding="utf-8").replace(
            "__UNSUBSCRIBE_URL__", URL_BAJA_BASE + suscriptor["token"]
        )
        try:
            enviar_email(suscriptor["email"], asunto_para(issue["nombre"]), html_personalizado)
            actualizar_progreso_suscriptor(suscriptor["email"], indice + 1)
            enviados += 1
        except Exception as error:
            logger.warning(f"Fallo al enviar issue #{indice + 1} a {suscriptor['email']}: {error}")
            fallos += 1

    logger.info(
        f"Goteo: {enviados} enviado(s), {al_dia} al día, {no_toca} todavía no les toca, {fallos} fallo(s)."
    )


def main() -> None:
    forzado = os.environ.get("FORZAR_ENVIO", "").lower() == "true"
    if forzado:
        logger.info("Modo forzado: se ignora la cadencia de 3 días tanto para generar como para enviar.")

    generar_issue_del_dia(forzado)
    generar_archivo()
    generar_landing()
    enviar_pendientes(forzado)


if __name__ == "__main__":
    main()
