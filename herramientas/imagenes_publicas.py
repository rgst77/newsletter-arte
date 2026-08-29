import time

import requests
from bs4 import BeautifulSoup

from contratos.esquemas import ImagenObra

MET_BASE = "https://collectionapi.metmuseum.org/public/collection/v1"
WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
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


def buscar_en_wikimedia(nombre_autor: str, max_resultados: int = 3) -> list[ImagenObra]:
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
