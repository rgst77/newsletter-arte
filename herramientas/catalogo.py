import json
from pathlib import Path

from contratos.esquemas import AutorCatalogo, RegistroEnvio

RUTA_CATALOGO = Path(__file__).resolve().parent.parent / "datos" / "catalogo_autores.json"
RUTA_ENVIADOS = Path(__file__).resolve().parent.parent / "datos" / "autores_enviados.json"


def cargar_catalogo() -> list[AutorCatalogo]:
    with open(RUTA_CATALOGO, encoding="utf-8") as f:
        return [AutorCatalogo(**item) for item in json.load(f)]


def cargar_enviados() -> list[RegistroEnvio]:
    if not RUTA_ENVIADOS.exists():
        return []
    with open(RUTA_ENVIADOS, encoding="utf-8") as f:
        return [RegistroEnvio(**item) for item in json.load(f)]


def elegir_autor_pendiente(siglo: str, disciplina: str = "cualquiera") -> AutorCatalogo | None:
    nombres_enviados = {r.nombre for r in cargar_enviados()}
    candidatos = [
        autor
        for autor in cargar_catalogo()
        if autor.siglo == siglo
        and (disciplina == "cualquiera" or autor.disciplina == disciplina)
        and autor.nombre not in nombres_enviados
    ]
    return candidatos[0] if candidatos else None


def registrar_envio(registro: RegistroEnvio) -> None:
    enviados = cargar_enviados()
    enviados.append(registro)
    RUTA_ENVIADOS.parent.mkdir(exist_ok=True)
    with open(RUTA_ENVIADOS, "w", encoding="utf-8") as f:
        json.dump(
            [r.model_dump(mode="json") for r in enviados], f, ensure_ascii=False, indent=2
        )
