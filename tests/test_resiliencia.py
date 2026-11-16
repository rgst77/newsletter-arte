import unittest
from unittest.mock import MagicMock, patch

import enviar_automatico
from herramientas import imagenes_publicas


def _resp(status: int, retry_after: str | None = None) -> MagicMock:
    r = MagicMock()
    r.status_code = status
    r.headers = {"Retry-After": retry_after} if retry_after else {}
    return r


class TestReintentosWikimedia(unittest.TestCase):
    @patch("herramientas.imagenes_publicas.time.sleep")
    @patch("herramientas.imagenes_publicas.requests.get")
    def test_recupera_tras_429_transitorio(self, get, sleep):
        get.side_effect = [_resp(429, "2"), _resp(429), _resp(200)]
        resultado = imagenes_publicas._get_con_reintentos("u", {})
        self.assertEqual(resultado.status_code, 200)
        self.assertEqual(get.call_count, 3)
        self.assertEqual(sleep.call_args_list[0].args[0], 2.0)  # respeta Retry-After

    @patch("herramientas.imagenes_publicas.time.sleep")
    @patch("herramientas.imagenes_publicas.requests.get")
    def test_429_persistente_devuelve_el_error_al_final(self, get, sleep):
        get.return_value = _resp(429)
        resultado = imagenes_publicas._get_con_reintentos("u", {}, intentos=3)
        self.assertEqual(resultado.status_code, 429)
        self.assertEqual(get.call_count, 3)

    @patch("herramientas.imagenes_publicas.requests.get")
    def test_respuesta_buena_no_reintenta(self, get):
        get.return_value = _resp(200)
        imagenes_publicas._get_con_reintentos("u", {})
        self.assertEqual(get.call_count, 1)

    @patch("herramientas.imagenes_publicas.time.sleep")
    @patch("herramientas.imagenes_publicas.requests.get")
    def test_recupera_tras_error_5xx(self, get, sleep):
        get.side_effect = [_resp(503), _resp(200)]
        self.assertEqual(imagenes_publicas._get_con_reintentos("u", {}).status_code, 200)
        self.assertEqual(get.call_count, 2)

    @patch("herramientas.imagenes_publicas.time.sleep")
    @patch("herramientas.imagenes_publicas.requests.get")
    def test_recupera_tras_timeout(self, get, sleep):
        import requests as rq
        get.side_effect = [rq.Timeout("lento"), rq.ConnectionError("cortado"), _resp(200)]
        self.assertEqual(imagenes_publicas._get_con_reintentos("u", {}).status_code, 200)
        self.assertEqual(get.call_count, 3)

    @patch("herramientas.imagenes_publicas.time.sleep")
    @patch("herramientas.imagenes_publicas.requests.get")
    def test_timeout_persistente_acaba_fallando_en_voz_alta(self, get, sleep):
        import requests as rq
        get.side_effect = rq.Timeout("lento")
        with self.assertRaises(rq.Timeout):
            imagenes_publicas._get_con_reintentos("u", {}, intentos=3)
        self.assertEqual(get.call_count, 3)

    @patch("herramientas.imagenes_publicas.requests.get")
    def test_error_4xx_distinto_de_429_no_se_reintenta(self, get):
        get.return_value = _resp(404)
        self.assertEqual(imagenes_publicas._get_con_reintentos("u", {}).status_code, 404)
        self.assertEqual(get.call_count, 1)


class TestGenerarNoBloqueaEnviar(unittest.TestCase):
    @patch.object(enviar_automatico, "enviar_pendientes")
    @patch.object(enviar_automatico, "generar_landing")
    @patch.object(enviar_automatico, "generar_archivo")
    @patch.object(enviar_automatico, "generar_issue_del_dia", side_effect=RuntimeError("429"))
    def test_si_falla_generar_igualmente_se_envia_y_el_run_sigue_en_rojo(
        self, _generar, _archivo, _landing, enviar
    ):
        with self.assertRaises(RuntimeError):
            enviar_automatico.main()
        enviar.assert_called_once()


if __name__ == "__main__":
    unittest.main()
