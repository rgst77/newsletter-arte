from abc import ABC, abstractmethod

from contratos.herramientas import DefinicionHerramienta, RespuestaModelo


class ModeloLLM(ABC):
    @abstractmethod
    def generar(self, prompt: str, system: str = "") -> str:
        ...

    @abstractmethod
    def conversar(
        self,
        historial: list[dict],
        herramientas: list[DefinicionHerramienta],
        system: str = "",
    ) -> RespuestaModelo:
        ...

    @abstractmethod
    def bloque_resultado_herramienta(self, id_llamada: str, resultado: str) -> dict:
        ...
