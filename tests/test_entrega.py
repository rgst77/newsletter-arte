import unittest
from datetime import datetime, timedelta, timezone

from enviar_automatico import DIAS_ENTRE_ENVIOS, _le_toca_a, _siguiente_issue

# Estos tests no tocan Supabase ni generan nada real: simulan el paso del
# tiempo sobre datos sintéticos para demostrar que el ritmo de 3 días es
# idéntico para cualquier suscriptor, sin importar cuándo se apuntó ni en
# qué orden llegue el contenido nuevo.

ISSUES = [
    {"nombre": "Autor A", "archivo_html": "a.html"},
    {"nombre": "Autor B", "archivo_html": "b.html"},
    {"nombre": "Autor C", "archivo_html": "c.html"},
]


def hace(dias: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()


class TestRitmoDeEntrega(unittest.TestCase):
    def test_suscriptor_nuevo_recibe_el_primero_inmediatamente(self):
        suscriptor = {"ultimo_archivo_enviado": None, "fecha_ultimo_envio": None}
        self.assertTrue(_le_toca_a(suscriptor, forzado=False))
        self.assertEqual(_siguiente_issue(suscriptor, ISSUES)["archivo_html"], "a.html")

    def test_dos_suscriptores_en_dias_distintos_no_se_afectan(self):
        # Uno lleva 1 día esperando, otro lleva 4 — cada uno debe evaluarse
        # solo contra su propia fecha, nunca contra la del otro.
        reciente = {"ultimo_archivo_enviado": "a.html", "fecha_ultimo_envio": hace(1)}
        antiguo = {"ultimo_archivo_enviado": "a.html", "fecha_ultimo_envio": hace(4)}
        self.assertFalse(_le_toca_a(reciente, forzado=False))
        self.assertTrue(_le_toca_a(antiguo, forzado=False))

    def test_justo_en_el_limite_de_3_dias_le_toca(self):
        limite = {"ultimo_archivo_enviado": "a.html", "fecha_ultimo_envio": hace(DIAS_ENTRE_ENVIOS)}
        self.assertTrue(_le_toca_a(limite, forzado=False))

    def test_justo_antes_del_limite_no_le_toca(self):
        casi = {"ultimo_archivo_enviado": "a.html", "fecha_ultimo_envio": hace(DIAS_ENTRE_ENVIOS - 0.01)}
        self.assertFalse(_le_toca_a(casi, forzado=False))

    def test_alcanzar_el_frente_del_contenido_no_adelanta_el_ritmo(self):
        # Suscriptor ya al día (recibió el último issue existente) hace solo
        # 1 día. Aunque se genere contenido nuevo ahora mismo, debe seguir
        # esperando a que se cumplan sus propios 3 días, no recibirlo ya
        # por el simple hecho de que ha aparecido.
        al_dia_reciente = {"ultimo_archivo_enviado": "c.html", "fecha_ultimo_envio": hace(1)}
        issues_con_nuevo = ISSUES + [{"nombre": "Autor D", "archivo_html": "d.html"}]
        self.assertIsNotNone(_siguiente_issue(al_dia_reciente, issues_con_nuevo))
        self.assertFalse(_le_toca_a(al_dia_reciente, forzado=False))

    def test_backfill_antes_de_su_posicion_no_desincroniza_a_nadie(self):
        # El caso real que motivó el cambio de índice numérico a nombre de
        # archivo: si se rellena un hueco antiguo (ej. Quevedo) que queda
        # ANTES de donde ya va un suscriptor, insertarlo no debe cambiar cuál
        # es su siguiente issue — solo el nombre de archivo importa, no la
        # posición numérica, que sí se habría desplazado con el sistema viejo.
        suscriptor = {"ultimo_archivo_enviado": "c.html", "fecha_ultimo_envio": hace(5)}
        issues_con_d = ISSUES + [{"nombre": "Autor D", "archivo_html": "d.html"}]
        siguiente_antes = _siguiente_issue(suscriptor, issues_con_d)["archivo_html"]

        issues_con_backfill = [ISSUES[0], {"nombre": "Relleno", "archivo_html": "relleno.html"}] + issues_con_d[1:]
        siguiente_despues = _siguiente_issue(suscriptor, issues_con_backfill)["archivo_html"]

        self.assertEqual(siguiente_antes, "d.html")
        self.assertEqual(siguiente_despues, "d.html")

    def test_backfill_justo_despues_de_su_posicion_se_lo_ofrece_a_continuacion(self):
        # Caso complementario (deseado, no un bug): si el hueco que se rellena
        # queda justo después de donde va alguien, sí debe recibirlo — es
        # exactamente lo que pasó con Erik y Quevedo en producción.
        suscriptor = {"ultimo_archivo_enviado": "a.html", "fecha_ultimo_envio": hace(5)}
        issues_con_backfill = [ISSUES[0], {"nombre": "Relleno", "archivo_html": "relleno.html"}] + ISSUES[1:]
        self.assertEqual(_siguiente_issue(suscriptor, issues_con_backfill)["archivo_html"], "relleno.html")

    def test_suscriptor_al_dia_no_tiene_siguiente(self):
        al_dia = {"ultimo_archivo_enviado": "c.html", "fecha_ultimo_envio": hace(10)}
        self.assertIsNone(_siguiente_issue(al_dia, ISSUES))

    def test_forzado_ignora_la_cadencia_pero_no_el_orden(self):
        suscriptor = {"ultimo_archivo_enviado": "a.html", "fecha_ultimo_envio": hace(0.01)}
        self.assertFalse(_le_toca_a(suscriptor, forzado=False))
        self.assertTrue(_le_toca_a(suscriptor, forzado=True))
        self.assertEqual(_siguiente_issue(suscriptor, ISSUES)["archivo_html"], "b.html")


if __name__ == "__main__":
    unittest.main()
