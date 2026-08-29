from ddgs import DDGS

from contratos.esquemas import ResultadoBusqueda


def buscar(tema: str, max_resultados: int = 5) -> list[ResultadoBusqueda]:
    resultados_crudos = DDGS().text(tema, max_results=max_resultados)
    return [
        ResultadoBusqueda(
            titulo=r["title"],
            url=r["href"],
            fragmento=r["body"],
        )
        for r in resultados_crudos
    ]
