import os
import time

import requests
from bs4 import BeautifulSoup

from contratos.esquemas import ImagenObra

MET_BASE = "https://collectionapi.metmuseum.org/public/collection/v1"
WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
SMITHSONIAN_API = "https://api.si.edu/openaccess/api/v1.0/search"
CABECERAS = {"User-Agent": "newsletter-arte-proyecto-aprendizaje/1.0 (uso educativo, sin fines comerciales)"}


def buscar_en_met(nombre_autor: str, max_resultados: int = 3) -> list[ImagenObra]:
    # Nota: "artistOrCulture=true" del Met devuelve 0 resultados con nombres de
    # varias palabras (bug confirmado de su API) — se filtra por autor a mano abajo.
    busqueda = requests.get(
        f"{MET_BASE}/search",
        params={"q": nombre_autor, "hasImages": "true"},
        headers=CABECERAS,
        timeout=10,
    )
    busqueda.raise_for_status()
    ids = busqueda.json().get("objectIDs") or []

    apellido = nombre_autor.split()[-1].lower()
    imagenes: list[ImagenObra] = []
    for object_id in ids[:25]:
        if len(imagenes) >= max_resultados:
            break
        # El Met bloquea con 403 si se hacen demasiadas peticiones seguidas sin
        # pausa (límite de tasa no documentado con claridad); si ocurre, se deja
        # de insistir con el Met para este autor y se completa con Wikimedia.
        time.sleep(0.15)
        detalle = requests.get(f"{MET_BASE}/objects/{object_id}", headers=CABECERAS, timeout=10)
        if detalle.status_code == 403:
            break
        if detalle.status_code != 200:
            continue
        datos = detalle.json()
        if not datos.get("isPublicDomain") or not datos.get("primaryImage"):
            continue
        if apellido not in datos.get("artistDisplayName", "").lower():
            continue
        imagenes.append(
            ImagenObra(
                titulo_obra=datos.get("title") or "Sin título",
                url_imagen=datos["primaryImage"],
                url_fuente=datos.get("objectURL", ""),
                fuente="The Met Open Access",
                creditos="Dominio público — The Metropolitan Museum of Art",
            )
        )
    return imagenes


def _texto_plano(html: str) -> str:
    return BeautifulSoup(html, "html.parser").get_text().strip()


def buscar_en_wikimedia(
    nombre_autor: str,
    max_resultados: int = 3,
    verificar_autor: bool = True,
    requerir_dominio_publico: bool = False,
) -> list[ImagenObra]:
    respuesta = requests.get(
        WIKIMEDIA_API,
        params={
            "action": "query",
            "generator": "search",
            "gsrsearch": nombre_autor,
            "gsrnamespace": 6,
            "gsrlimit": max_resultados,
            "prop": "imageinfo",
            # extmetadata trae autor y licencia: Commons aloja tanto dominio
            # público como CC (CC-BY-SA, etc.), y estas últimas exigen atribución.
            "iiprop": "url|extmetadata",
            "format": "json",
        },
        headers=CABECERAS,
        timeout=10,
    )
    respuesta.raise_for_status()
    paginas = respuesta.json().get("query", {}).get("pages", {})

    # La búsqueda de Commons es por texto libre, no por autor real: un cuadro
    # de otro pintor con tema o título parecido (ej. otro "Dante") puede
    # colarse aunque no sea de quien buscamos. Se descarta si el campo
    # "Artist" real de la imagen no menciona el apellido del autor buscado —
    # más vale una imagen de menos que una mal atribuida en el newsletter.
    apellido = nombre_autor.split()[-1].lower()

    imagenes = []
    for pagina in paginas.values():
        info = pagina.get("imageinfo")
        if not info:
            continue
        titulo = pagina.get("title", "")
        metadatos = info[0].get("extmetadata", {})
        autor = metadatos.get("Artist", {}).get("value", "")
        licencia = metadatos.get("LicenseShortName", {}).get("value", "licencia no especificada")
        autor_limpio = _texto_plano(autor) if autor else "autor no especificado"
        if verificar_autor and autor and apellido not in autor_limpio.lower():
            continue
        if requerir_dominio_publico:
            # OJO: "LicenseShortName: Public domain" NO basta — esa etiqueta
            # también aparece en fotos de obras con copyright vigente donde
            # solo el FOTÓGRAFO liberó los derechos de su fotografía (ej. una
            # foto del Guernica donada por su fotógrafo a la Library of
            # Congress): eso no dice nada sobre si el cuadro en sí es libre,
            # y fue exactamente el fallo real de Picasso. La única señal que
            # sí afirma que la OBRA (no la foto) es de dominio público son
            # las categorías "PD-Art"/"PD-old"/"author died more than X years
            # ago" que Commons aplica cuando la obra representada es libre.
            categorias = metadatos.get("Categories", {}).get("value", "").lower()
            if not any(
                marca in categorias
                for marca in ("pd-art", "pd-old", "author died more than")
            ):
                continue
        imagenes.append(
            ImagenObra(
                titulo_obra=titulo.removeprefix("File:"),
                url_imagen=info[0]["url"],
                url_fuente=f"https://commons.wikimedia.org/wiki/{titulo.replace(' ', '_')}",
                fuente="Wikimedia Commons",
                creditos=f"{autor_limpio} — {licencia} (Wikimedia Commons)",
            )
        )
    return imagenes


def buscar_en_smithsonian(
    nombre_autor: str, max_resultados: int = 3, verificar_autor: bool = True
) -> list[ImagenObra]:
    # Tercera fuente, de ultimo recurso: Met y Wikimedia estan muy sesgados
    # hacia arte europeo/norteamericano, y Smithsonian Open Access tiene
    # museos dedicados a Africa, Asia y pueblos originarios de America que
    # ayudan a cubrir regiones que las otras dos fuentes dejan vacias.
    # Sin SMITHSONIAN_API_KEY usa la DEMO_KEY publica de api.data.gov, que
    # solo permite 10 peticiones/hora - de ahi que solo se use como ultimo
    # recurso y no en cada busqueda.
    clave_api = os.environ.get("SMITHSONIAN_API_KEY") or "DEMO_KEY"
    try:
        respuesta = requests.get(
            SMITHSONIAN_API,
            params={
                "q": f"{nombre_autor} AND online_media_type:Images",
                "api_key": clave_api,
                "rows": 10,
            },
            headers=CABECERAS,
            timeout=10,
        )
    except requests.RequestException:
        return []
    if respuesta.status_code == 429:
        return []
    respuesta.raise_for_status()
    filas = respuesta.json().get("response", {}).get("rows", [])

    apellido = nombre_autor.split()[-1].lower()
    imagenes: list[ImagenObra] = []
    for fila in filas:
        if len(imagenes) >= max_resultados:
            break
        contenido = fila.get("content", {})
        descriptivo = contenido.get("descriptiveNonRepeating", {})
        freetext = contenido.get("freetext", {})

        nombres_asociados = " ".join(
            entrada.get("content", "") for entrada in freetext.get("name", [])
        ).lower()
        if verificar_autor and nombres_asociados and apellido not in nombres_asociados:
            continue

        media = descriptivo.get("online_media", {}).get("media", [])
        imagen_libre = next(
            (m for m in media if m.get("type") == "Images" and m.get("usage", {}).get("access") == "CC0"),
            None,
        )
        if not imagen_libre:
            continue

        url_imagen = next(
            (r["url"] for r in imagen_libre.get("resources", []) if r.get("label") == "High-resolution JPEG"),
            imagen_libre.get("content", ""),
        )
        if not url_imagen:
            continue

        credit_line = freetext.get("creditLine", [{}])[0].get("content", "Smithsonian Institution")
        imagenes.append(
            ImagenObra(
                titulo_obra=fila.get("title") or "Sin titulo",
                url_imagen=url_imagen,
                url_fuente=descriptivo.get("record_link", ""),
                fuente="Smithsonian Open Access",
                creditos=f"Dominio publico (CC0) - {credit_line}",
            )
        )
    return imagenes
