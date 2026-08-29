import requests
from bs4 import BeautifulSoup

CABECERAS = {"User-Agent": "Mozilla/5.0 (compatible; NewsletterArte/1.0)"}


def leer_pagina(url: str, max_caracteres: int = 4000) -> str:
    respuesta = requests.get(url, timeout=10, headers=CABECERAS)
    respuesta.raise_for_status()

    sopa = BeautifulSoup(respuesta.text, "html.parser")
    for etiqueta in sopa(["script", "style", "nav", "header", "footer"]):
        etiqueta.decompose()

    texto = " ".join(sopa.get_text(separator=" ").split())
    return texto[:max_caracteres]
