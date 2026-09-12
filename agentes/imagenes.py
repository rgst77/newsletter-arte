from contratos.esquemas import ImagenObra
from herramientas.imagenes_publicas import buscar_en_met, buscar_en_smithsonian, buscar_en_wikimedia


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

    if len(imagenes) < cantidad:
        # Ultimo recurso: Smithsonian cubre regiones (Africa, Asia, pueblos
        # originarios) donde Met y Wikimedia suelen no tener nada. Se deja
        # para el final porque la DEMO_KEY sin clave propia solo permite
        # 10 peticiones/hora.
        try:
            imagenes += buscar_en_smithsonian(consulta, cantidad - len(imagenes), verificar_autor)
        except Exception:
            pass

    return imagenes


def elegir_imagenes(
    nombre_autor: str, disciplina: str, titulos_obras: list[str] | None = None, cantidad: int = 3
) -> list[ImagenObra]:
    verificar_autor = disciplina in DISCIPLINAS_CON_AUTOR_VERIFICABLE
    imagenes: list[ImagenObra] = []
    vistas: set[str] = set()

    def _agregar(candidatas: list[ImagenObra]) -> None:
        for imagen in candidatas:
            if len(imagenes) >= cantidad:
                return
            if imagen.url_imagen not in vistas:
                imagenes.append(imagen)
                vistas.add(imagen.url_imagen)

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
        _agregar(_buscar_generico(nombre_autor, faltan + len(vistas), verificar_autor))
    if len(imagenes) >= cantidad:
        return imagenes[:cantidad]

    # A partir de aquí, la búsqueda normal (con autor verificado) no ha
    # encontrado suficientes imágenes — el caso típico es un autor del s.XX-XXI
    # cuya obra sigue con copyright vigente, así que no existe ninguna
    # reproducción libre correctamente atribuida a él (ver caso Picasso).
    if verificar_autor:
        # Nivel 2: se relaja la coincidencia de autor, pero solo se aceptan
        # imágenes que Commons marca como "Public domain" de la propia obra
        # (no solo con licencia CC del fotógrafo/subida) — esto rescata
        # reproducciones antiguas correctas cuyo campo "Artist" no cita el
        # nombre exacto, sin reabrir el fallo original de aceptar cualquier
        # foto con licencia libre aunque la obra en sí no lo sea.
        for titulo in (titulos_obras or [])[:cantidad]:
            if len(imagenes) >= cantidad:
                break
            try:
                _agregar(
                    buscar_en_wikimedia(
                        f"{nombre_autor} {titulo}",
                        cantidad - len(imagenes),
                        verificar_autor=False,
                        requerir_dominio_publico=True,
                    )
                )
            except Exception:
                pass

        # Nivel 3: último recurso — foto de la propia persona en vez de su
        # obra. Aquí sí basta con la licencia normal del fotógrafo, porque no
        # hay una segunda capa de copyright sobre una fotografía biográfica.
        if len(imagenes) < cantidad:
            try:
                _agregar(
                    buscar_en_wikimedia(
                        f"{nombre_autor} portrait photograph",
                        cantidad - len(imagenes),
                        verificar_autor=False,
                    )
                )
            except Exception:
                pass

    return imagenes[:cantidad]
