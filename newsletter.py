import json
import logging
from datetime import datetime
from pathlib import Path

from agentes.imagenes import elegir_imagenes
from agentes.investigador import investigar
from agentes.redactor import redactar
from agentes.verificador import verificar
from contratos.esquemas import RegistroEnvio, SolicitudNewsletter
from costes.registro import resumen_gasto
from herramientas.catalogo import elegir_autor_pendiente, registrar_envio
from modelos.anthropic_adapter import AnthropicAdapter
from plantillas.email import DISCIPLINAS_EN, _siglo_a_ordinal, renderizar_html

logger = logging.getLogger(__name__)

RUTA_SALIDA = Path(__file__).resolve().parent / "salida"
RUTA_OMITIDOS = Path(__file__).resolve().parent / "datos" / "autores_sin_imagen.json"


def _registrar_omitido(nombre: str, disciplina: str, siglo: str) -> None:
    # No se marca como "enviado" (para no perderlo del catálogo para siempre),
    # pero sin dejar constancia en algún sitio se perdería igual: quedaría
    # pendiente en el catálogo pero nadie sabría por qué el pipeline lo salta
    # una y otra vez. Este archivo es esa constancia — para revisarlo a mano
    # más adelante (ej. buscarle una foto suya en vez de su obra).
    omitidos = json.loads(RUTA_OMITIDOS.read_text(encoding="utf-8")) if RUTA_OMITIDOS.exists() else []
    omitidos.append(
        {
            "nombre": nombre,
            "disciplina": disciplina,
            "siglo": siglo,
            "motivo": "sin imágenes libres encontradas (ni de la obra ni de la persona)",
            "fecha": datetime.now().isoformat(),
        }
    )
    RUTA_OMITIDOS.parent.mkdir(exist_ok=True)
    RUTA_OMITIDOS.write_text(json.dumps(omitidos, ensure_ascii=False, indent=2), encoding="utf-8")


def generar_newsletter(solicitud: SolicitudNewsletter):
    intentados: set[str] = set()
    autor = elegir_autor_pendiente(solicitud.siglo, solicitud.disciplina, excluir=intentados)
    if autor is None:
        raise RuntimeError(
            f"No quedan autores pendientes en el catálogo para "
            f"{solicitud.siglo} / {solicitud.disciplina}"
        )

    modelo_investigador = AnthropicAdapter(etiqueta="investigador")
    modelo_redactor = AnthropicAdapter(etiqueta="redactor")
    modelo_verificador = AnthropicAdapter(etiqueta="verificador")

    while True:
        logger.info(f"Autor elegido: {autor.nombre}")
        notas = investigar(autor, modelo_investigador)
        logger.info(f"Investigación completa: {len(notas.titulos_obras_conocidas)} obras encontradas")

        imagenes = elegir_imagenes(notas.nombre, autor.disciplina, notas.titulos_obras_conocidas, cantidad=3)
        logger.info(f"Imágenes encontradas: {len(imagenes)}/3")

        if imagenes:
            break

        logger.warning(f"Sin imágenes libres para {autor.nombre} — se omite y se prueba el siguiente")
        _registrar_omitido(autor.nombre, autor.disciplina, autor.siglo)
        intentados.add(autor.nombre)
        autor = elegir_autor_pendiente(solicitud.siglo, solicitud.disciplina, excluir=intentados)
        if autor is None:
            raise RuntimeError(
                f"Ningún autor pendiente en {solicitud.siglo} / {solicitud.disciplina} "
                f"tiene imágenes libres disponibles — revisa datos/autores_sin_imagen.json"
            )

    flashcard = redactar(notas, autor.disciplina, autor.siglo, imagenes, modelo_redactor)
    resultado = verificar(flashcard, notas, modelo_verificador)

    # Carpeta por siglo y disciplina (ej. salida/19th-century/sculpture/) para
    # que la base de HTML quede organizada y navegable, no todo en un cajón.
    carpeta_siglo = f"{_siglo_a_ordinal(autor.siglo).lower()}-century"
    carpeta_disciplina = DISCIPLINAS_EN.get(autor.disciplina, autor.disciplina).lower()
    carpeta_destino = RUTA_SALIDA / carpeta_siglo / carpeta_disciplina
    carpeta_destino.mkdir(parents=True, exist_ok=True)

    nombre_archivo = resultado.flashcard.nombre.lower().replace(" ", "_")
    ruta_html = carpeta_destino / f"{nombre_archivo}.html"
    ruta_html.write_text(renderizar_html(resultado.flashcard), encoding="utf-8")

    # Se guarda también el flashcard en bruto (no solo el HTML final) para
    # poder re-renderizar gratis cuando cambie el diseño, sin volver a pagar
    # por investigar/redactar/verificar el mismo autor otra vez.
    ruta_json = ruta_html.with_suffix(".json")
    ruta_json.write_text(resultado.flashcard.model_dump_json(indent=2), encoding="utf-8")

    # Se guarda la ruta relativa (no absoluta de esta máquina) porque el HTML
    # vive en el propio repo público: es el archivo histórico, sin base de
    # datos aparte.
    registrar_envio(
        RegistroEnvio(
            nombre=autor.nombre,
            disciplina=autor.disciplina,
            corriente=flashcard.corriente,
            periodo=flashcard.periodo,
            siglo=solicitud.siglo,
            archivo_html=str(ruta_html.relative_to(Path(__file__).resolve().parent)),
        )
    )

    return resultado, ruta_html


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    solicitud = SolicitudNewsletter(
        siglo=input("¿Qué siglo? (ej. 'siglo XIX'): ") or "siglo XIX",
        disciplina=input("¿Qué disciplina? (escultura/arquitectura/pintura/poesía/cualquiera): ")
        or "cualquiera",
    )

    resultado, ruta_html = generar_newsletter(solicitud)

    print(f"\nFiabilidad: {resultado.fiabilidad}")
    if resultado.advertencias:
        print("Advertencias:")
        for advertencia in resultado.advertencias:
            print(f" - {advertencia}")

    print(f"\nNewsletter guardado en: {ruta_html}")

    gasto = resumen_gasto()
    print(
        f"\nGasto acumulado total en esta máquina: ${gasto['coste_total_usd']:.4f} "
        f"({gasto['llamadas']} llamadas) — {gasto['por_etiqueta']}"
    )
