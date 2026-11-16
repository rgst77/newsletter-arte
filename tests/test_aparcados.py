import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import newsletter
from contratos.esquemas import AutorCatalogo, SolicitudNewsletter
from herramientas import catalogo


def _autor(nombre: str) -> AutorCatalogo:
    return AutorCatalogo(nombre=nombre, disciplina="pintura", siglo="siglo XXI")


class TestAparcados(unittest.TestCase):
    def _archivo(self, entradas: list[dict]) -> Path:
        carpeta = Path(tempfile.mkdtemp())
        ruta = carpeta / "autores_sin_imagen.json"
        ruta.write_text(json.dumps(entradas), encoding="utf-8")
        return ruta

    def test_un_autor_aparcado_recientemente_no_se_vuelve_a_elegir(self):
        ruta = self._archivo([{"nombre": "A", "fecha": datetime.now().isoformat()}])
        with patch.object(catalogo, "RUTA_OMITIDOS", ruta):
            self.assertEqual(catalogo.nombres_aparcados_vigentes(), {"A"})

    def test_pasado_el_plazo_se_vuelve_a_intentar(self):
        vieja = (datetime.now() - timedelta(days=catalogo.DIAS_APARCADO + 1)).isoformat()
        ruta = self._archivo([{"nombre": "A", "fecha": vieja}])
        with patch.object(catalogo, "RUTA_OMITIDOS", ruta):
            self.assertEqual(catalogo.nombres_aparcados_vigentes(), set())

    def test_cuenta_el_aparcado_mas_reciente_de_cada_nombre(self):
        vieja = (datetime.now() - timedelta(days=200)).isoformat()
        ruta = self._archivo(
            [{"nombre": "A", "fecha": vieja}, {"nombre": "A", "fecha": datetime.now().isoformat()}]
        )
        with patch.object(catalogo, "RUTA_OMITIDOS", ruta):
            self.assertEqual(catalogo.nombres_aparcados_vigentes(), {"A"})

    def test_sin_archivo_no_hay_aparcados(self):
        with patch.object(catalogo, "RUTA_OMITIDOS", Path(tempfile.mkdtemp()) / "no_existe.json"):
            self.assertEqual(catalogo.nombres_aparcados_vigentes(), set())


    def test_un_autor_liberado_vuelve_a_la_rotacion_pero_queda_en_el_historial(self):
        ahora = datetime.now()
        ruta = self._archivo(
            [
                {"nombre": "A", "fecha": (ahora - timedelta(days=5)).isoformat(), "estado": "aparcado"},
                {"nombre": "A", "fecha": ahora.isoformat(), "estado": "liberado"},
            ]
        )
        with patch.object(catalogo, "RUTA_OMITIDOS", ruta):
            self.assertEqual(catalogo.nombres_aparcados_vigentes(), set())
            self.assertEqual(catalogo.registros_aparcados()["A"]["estado"], "liberado")
        self.assertEqual(len(json.loads(ruta.read_text())), 2)  # nada se borra

    def test_los_autores_reales_aparcados_siguen_pendientes_en_el_catalogo(self):
        # El archivo real: aparcar nunca debe equivaler a perder al autor.
        publicados = {r.nombre for r in catalogo.cargar_enviados()}
        en_catalogo = {a.nombre for a in catalogo.cargar_catalogo()}
        for nombre in catalogo.registros_aparcados():
            self.assertIn(nombre, en_catalogo)
            self.assertNotIn(nombre, publicados)

    def test_comprobar_libera_solo_a_quien_ya_tiene_imagenes(self):
        import aparcados

        ahora = datetime.now().isoformat()
        ruta = self._archivo(
            [
                {"nombre": "Ya", "disciplina": "pintura", "siglo": "siglo XXI", "fecha": ahora, "estado": "aparcado"},
                {"nombre": "Aun no", "disciplina": "pintura", "siglo": "siglo XXI", "fecha": ahora, "estado": "aparcado"},
            ]
        )
        fake = lambda nombre, *a, **k: [object()] if nombre == "Ya" else []  # noqa: E731
        with patch.object(catalogo, "RUTA_OMITIDOS", ruta), patch.object(aparcados, "RUTA_OMITIDOS", ruta), \
             patch.object(aparcados, "cargar_enviados", return_value=[]), \
             patch("agentes.imagenes.elegir_imagenes", side_effect=fake):
            aparcados.comprobar()
            self.assertEqual(catalogo.nombres_aparcados_vigentes(), {"Aun no"})


class _Parar(Exception):
    pass


class TestComprobacionPrevia(unittest.TestCase):
    @patch.object(newsletter, "_registrar_omitido")
    @patch.object(newsletter, "redactar", side_effect=_Parar)
    @patch.object(newsletter, "investigar")
    @patch.object(newsletter, "elegir_imagenes")
    @patch.object(newsletter, "elegir_autor_pendiente")
    @patch.object(newsletter, "AnthropicAdapter", MagicMock())
    def test_no_se_investiga_a_quien_no_tiene_imagenes(
        self, elegir_autor, elegir_imagenes, investigar, _redactar, registrar
    ):
        sin_imagenes, con_imagenes = _autor("Vivo"), _autor("Viable")
        elegir_autor.side_effect = [sin_imagenes, con_imagenes]
        # 1ª llamada: comprobación previa de "Vivo" (vacía); 2ª: la de "Viable";
        # 3ª: la búsqueda real tras investigar.
        elegir_imagenes.side_effect = [[], [MagicMock()], [MagicMock()]]
        investigar.return_value = MagicMock(nombre="Viable", titulos_obras_conocidas=["x"])

        with self.assertRaises(_Parar):
            newsletter.generar_newsletter(SolicitudNewsletter(siglo="siglo XXI", disciplina="cualquiera"))

        self.assertEqual(investigar.call_count, 1)
        self.assertEqual(investigar.call_args.args[0].nombre, "Viable")
        self.assertEqual(registrar.call_args.args[0], "Vivo")


if __name__ == "__main__":
    unittest.main()
