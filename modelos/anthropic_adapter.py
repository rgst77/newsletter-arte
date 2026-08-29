import os
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from contratos.herramientas import DefinicionHerramienta, LlamadaHerramienta, RespuestaModelo
from costes.registro import registrar_uso
from modelos.base import ModeloLLM

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class AnthropicAdapter(ModeloLLM):
    def __init__(self, modelo: str = "claude-haiku-4-5-20251001", etiqueta: str = "modelo"):
        self._cliente = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self._modelo = modelo
        self._etiqueta = etiqueta

    def generar(self, prompt: str, system: str = "") -> str:
        respuesta = self._cliente.messages.create(
            model=self._modelo,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        registrar_uso(
            self._modelo, self._etiqueta, respuesta.usage.input_tokens, respuesta.usage.output_tokens
        )
        return respuesta.content[0].text

    def conversar(
        self,
        historial: list[dict],
        herramientas: list[DefinicionHerramienta],
        system: str = "",
    ) -> RespuestaModelo:
        respuesta = self._cliente.messages.create(
            model=self._modelo,
            max_tokens=2048,
            system=system,
            messages=historial,
            tools=[
                {
                    "name": h.nombre,
                    "description": h.descripcion,
                    "input_schema": h.esquema_parametros,
                }
                for h in herramientas
            ],
        )
        registrar_uso(
            self._modelo, self._etiqueta, respuesta.usage.input_tokens, respuesta.usage.output_tokens
        )

        texto = None
        llamadas = []
        for bloque in respuesta.content:
            if bloque.type == "text":
                texto = bloque.text
            elif bloque.type == "tool_use":
                llamadas.append(
                    LlamadaHerramienta(id=bloque.id, nombre=bloque.name, argumentos=bloque.input)
                )

        return RespuestaModelo(
            mensaje_bruto={"role": "assistant", "content": respuesta.content},
            texto=texto,
            llamadas_herramientas=llamadas,
        )

    def bloque_resultado_herramienta(self, id_llamada: str, resultado: str) -> dict:
        return {"type": "tool_result", "tool_use_id": id_llamada, "content": resultado}
