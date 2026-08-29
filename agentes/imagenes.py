from contratos.esquemas import ImagenObra
from herramientas.imagenes_publicas import buscar_en_met, buscar_en_wikimedia


def _buscar_generico(consulta: str, cantidad: int) -> list[ImagenObra]:
    try:
        imagenes = buscar_en_met(consulta, cantidad)
    except Exception:
        # La API del Met tiene un límite de peticiones no documentado y puede
        # devolver 403 de forma intermitente: nunca debe tumbar el pipeline.
        imagenes = []

    if len(imagenes) < cantidad:
        imagenes += buscar_en_wikimedia(consulta, cantidad - len(imagenes))

    return imagenes


def elegir_imagenes(
    nombre_autor: str, titulos_obras: list[str] | None = None, cantidad: int = 3
) -> list[ImagenObra]:
    imagenes: list[ImagenObra] = []
    vistas: set[str] = set()

    for titulo in (titulos_obras or [])[:cantidad]:
        encontradas = _buscar_generico(f"{nombre_autor} {titulo}", 1)
        for imagen in encontradas:
            if imagen.url_imagen not in vistas:
                imagenes.append(imagen)
                vistas.add(imagen.url_imagen)
                break
        if len(imagenes) >= cantidad:
            return imagenes

    faltan = cantidad - len(imagenes)
    if faltan > 0:
        for imagen in _buscar_generico(nombre_autor, faltan + len(vistas)):
            if imagen.url_imagen not in vistas:
                imagenes.append(imagen)
                vistas.add(imagen.url_imagen)
            if len(imagenes) >= cantidad:
                break

    return imagenes[:cantidad]
