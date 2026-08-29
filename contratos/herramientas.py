from typing import Any

from pydantic import BaseModel, Field


class DefinicionHerramienta(BaseModel):
    nombre: str
    descripcion: str
    esquema_parametros: dict[str, Any]


class LlamadaHerramienta(BaseModel):
    id: str
    nombre: str
    argumentos: dict[str, Any]


class RespuestaModelo(BaseModel):
    mensaje_bruto: dict[str, Any]
    texto: str | None = None
    llamadas_herramientas: list[LlamadaHerramienta] = Field(default_factory=list)
