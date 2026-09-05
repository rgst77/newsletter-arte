from contratos.esquemas import ImagenObra
from herramientas.imagenes_publicas import buscar_en_met, buscar_en_wikimedia


# En Wikimedia el campo "Artist" solo identifica de forma fiable al creador
# real de la obra para pintura/escultura; en arquitectura (y poesía) suele
# ser el fotógrafo que tomó la foto del edificio, no el autor que buscamos —
# aplicar el filtro ahí descartaría fotos correctas por error.
DISCIPLINAS_CON_AUTOR_VERIFICABLE = {"pintura", "escultura"}


def _buscar_generico(consulta: str, cantidad: int, verificar_autor: bool) -> list[ImagenObra]:
    try:
        imagenes = buscar_en_met(consulta, cantidad)
    except Exception:
        # La API del Met tiene un límite de peticiones no documentado y puede
        # devolver 403 de forma intermitente: nunca debe tumbar el pipeline.
        imagenes = []

    if len(imagenes) < cantidad:
        imagenes += buscar_en_wikimedia(consulta, cantidad - len(imagenes), verificar_autor)

    return imagenes


def elegir_imagenes(
    nombre_autor: str, disciplina: str, titulos_obras: list[str] | None = None, cantidad: int = 3
) -> list[ImagenObra]:
    verificar_autor = disciplina in DISCIPLINAS_CON_AUTOR_VERIFICABLE
    imagenes: list[ImagenObra] = []
    vistas: set[str] = set()

    for titulo in (titulos_obras or [])[:cantidad]:
        encontradas = _buscar_generico(f"{nombre_autor} {titulo}", 1, verificar_autor)
        for imagen in encontradas:
            if imagen.url_imagen not in vistas:
                imagenes.append(imagen)
                vistas.add(imagen.url_imagen)
                break
        if len(imagenes) >= cantidad:
            return imagenes

    faltan = cantidad - len(imagenes)
    if faltan > 0:
        for imagen in _buscar_generico(nombre_autor, faltan + len(vistas), verificar_autor):
            if imagen.url_imagen not in vistas:
                imagenes.append(imagen)
                vistas.add(imagen.url_imagen)
            if len(imagenes) >= cantidad:
                break

    return imagenes[:cantidad]
