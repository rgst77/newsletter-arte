import unittest
from unittest.mock import patch

from agentes import investigador
from contratos.esquemas import AutorCatalogo
from contratos.herramientas import LlamadaHerramienta, RespuestaModelo
from modelos.base import ModeloLLM

NOTAS = {
    "nombre": "X", "nacionalidad": "British", "corriente": "Contemporary", "periodo": "1950-",
    "notas": "Partial notes.", "titulos_obras_conocidas": ["Obra"], "fuentes": [{"titulo": "t", "url": "u"}],
}


class _ModeloQueSoloBusca(ModeloLLM):
    """Busca en cada turno, salvo que se le avise de que es el último."""

    def __init__(self):
        self.turnos = 0
        self.herramientas_por_turno = []
        self.historiales = []

    def generar(self, prompt, system=""):
        raise NotImplementedError

    def conversar(self, historial, herramientas, system=""):
        self.turnos += 1
        nombres = [h.nombre for h in herramientas]
        self.herramientas_por_turno.append(nombres)
        self.historiales.append(historial[-1])
        nombre = "entregar_notas" if nombres == ["entregar_notas"] else "buscar"
        args = NOTAS if nombre == "entregar_notas" else {"consulta": "q"}
        return RespuestaModelo(
            mensaje_bruto={"role": "assistant", "content": []},
            llamadas_herramientas=[LlamadaHerramienta(id=f"id{self.turnos}", nombre=nombre, argumentos=args)],
        )

    def bloque_resultado_herramienta(self, id_llamada, resultado):
        return {"type": "tool_result", "tool_use_id": id_llamada, "content": resultado}


class TestUltimoTurno(unittest.TestCase):
    @patch.object(investigador, "buscar", return_value=[])
    def test_si_se_agotan_los_turnos_buscando_se_fuerza_la_entrega(self, _buscar):
        modelo = _ModeloQueSoloBusca()
        autor = AutorCatalogo(nombre="X", disciplina="escultura", siglo="siglo XXI")

        notas = investigador.investigar(autor, modelo)

        self.assertEqual(notas.nombre, "X")
        self.assertEqual(modelo.turnos, investigador.MAX_ITERACIONES)
        # Solo el último turno se limita a entregar; los demás pueden buscar.
        self.assertEqual(modelo.herramientas_por_turno[-1], ["entregar_notas"])
        for nombres in modelo.herramientas_por_turno[:-1]:
            self.assertIn("buscar", nombres)
        ultimo_mensaje = modelo.historiales[-1]["content"]
        self.assertIn("LAST turn", str(ultimo_mensaje))

    def test_hay_mas_turnos_que_las_busquedas_permitidas_en_el_prompt(self):
        self.assertGreater(investigador.MAX_ITERACIONES, 8)


if __name__ == "__main__":
    unittest.main()
