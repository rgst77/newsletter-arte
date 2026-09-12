import logging
import os
import time
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


def _siguiente_issue(suscriptor: dict, issues: list[dict]) -> dict | None:
    ultimo_archivo = suscriptor.get("ultimo_archivo_enviado")
    if not ultimo_archivo:
        return issues[0] if issues else None

    # Se busca por nombre de archivo, no por índice numérico: así la
    # posición de cada suscriptor no depende de que cargar_incluidos()
    # mantenga siempre el mismo orden — si algún día se completa un issue
    # antiguo que ahora falta (ej. le falta el .json), un índice numérico
    # desincronizaría a todo el mundo de golpe; un nombre de archivo sigue
    # apuntando a lo mismo pase lo que pase.
    posiciones = {issue["archivo_html"]: i for i, issue in enumerate(issues)}
    posicion_actual = posiciones.get(ultimo_archivo)
    if posicion_actual is None:
        logger.warning(
            f"'{ultimo_archivo}' (último enviado a un suscriptor) ya no aparece en el archivo público "
            "— se le trata como al día en vez de arriesgarse a reenviarle todo desde cero."
        )
        return None

    siguiente = posicion_actual + 1
    return issues[siguiente] if siguiente < len(issues) else None


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
        issue = _siguiente_issue(suscriptor, issues)
        if issue is None:
            al_dia += 1
            continue
        if not _le_toca_a(suscriptor, forzado):
            no_toca += 1
            continue

        ruta_html = RUTA_PROYECTO / issue["archivo_html"]
        # El HTML guardado es el mismo para todos; el enlace de baja se
        # inyecta aquí, por destinatario, con su token único — así nadie
        # puede dar de baja a otro suscriptor sabiendo solo su email.
        html_personalizado = ruta_html.read_text(encoding="utf-8").replace(
            "__UNSUBSCRIBE_URL__", URL_BAJA_BASE + suscriptor["token"]
        )
        try:
            enviar_email(suscriptor["email"], asunto_para(issue["nombre"]), html_personalizado)
        except Exception as error:
            logger.warning(f"Fallo al enviar '{issue['nombre']}' a {suscriptor['email']}: {error}")
            fallos += 1
            continue

        # El email ya ha salido — a partir de aquí NO se puede reintentar
        # enviar_email si algo falla (duplicaría el correo al suscriptor), así
        # que se reintenta solo actualizar_progreso_suscriptor unas veces
        # antes de rendirse. Sin este reintento, un fallo transitorio de
        # Supabase justo aquí dejaría fecha_ultimo_envio sin avanzar, y el
        # próximo envío automático le mandaría el mismo issue otra vez.
        for intento in range(3):
            try:
                actualizar_progreso_suscriptor(suscriptor["email"], issue["archivo_html"])
                enviados += 1
                break
            except Exception as error:
                if intento == 2:
                    logger.error(
                        f"CRÍTICO: se envió '{issue['nombre']}' a {suscriptor['email']} pero no se "
                        f"pudo actualizar su progreso tras 3 intentos ({error}) — recibirá el mismo "
                        f"issue otra vez en el próximo envío automático."
                    )
                    fallos += 1
                else:
                    time.sleep(2)

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
