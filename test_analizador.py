"""
Pruebas automáticas del analizador de logs.
Los valores esperados se calcularon A MANO leyendo cada archivo de logs_prueba/
aplicando las reglas del estudiante, antes de ejecutar el script.

Ejecutar:  python -m unittest -v
"""
import io
import os
import unittest
from contextlib import redirect_stdout
from unittest import mock

import analizador_logs as al

BASE = os.path.join(os.path.dirname(__file__), "logs_prueba")


def run(name):
    return al.analyze(al.read_lines(os.path.join(BASE, name)))


class TestArchivosDePrueba(unittest.TestCase):
    def test_log_bueno(self):
        s = run("log_bueno.txt")
        self.assertEqual(s.lines_read, 10)
        self.assertEqual(s.events, 10)
        self.assertEqual(s.by_level, {"INFO": 5, "WARNING": 2, "ERROR": 3})
        self.assertEqual(len(s.malformed), 0)
        self.assertEqual(s.blank_lines, 0)

    def test_log_con_errores(self):
        s = run("log_con_errores.txt")
        self.assertEqual(s.lines_read, 13)
        self.assertEqual(s.blank_lines, 1)
        self.assertEqual(s.events, 5)
        self.assertEqual(s.by_level, {"INFO": 2, "WARNING": 2, "ERROR": 1})
        self.assertEqual(len(s.malformed), 8)
        self.assertEqual(s.malformed_and_event, 1)      # solo [WARNING] sin fecha
        self.assertEqual(s.events_without_date, 1)
        self.assertEqual([p.number for p in s.malformed], [3, 4, 6, 7, 8, 9, 11, 12])

    def test_log_casos_borde(self):
        s = run("log_casos_borde.txt")
        self.assertEqual(s.lines_read, 14)
        self.assertEqual(s.blank_lines, 1)
        # Decisión 8 (regla de fecha más estricta): "1.2.3" ya no parece fecha, así que
        # la línea 6 cuenta como evento sin fecha (antes se descartaba como fecha inválida).
        self.assertEqual(s.events, 10)
        self.assertEqual(s.by_level, {"INFO": 6, "WARNING": 1, "ERROR": 3})
        self.assertEqual(len(s.malformed), 5)
        self.assertEqual(s.malformed_and_event, 2)      # líneas 6 ("1.2.3") y 7 ("404")
        self.assertEqual(s.events_without_date, 2)
        self.assertEqual([p.number for p in s.malformed], [3, 6, 7, 11, 13])

    def test_log_vacio(self):
        self.assertEqual(al.read_lines(os.path.join(BASE, "log_vacio.txt")), [])


class TestReglasDelEstudiante(unittest.TestCase):
    def test_decision1_sin_fecha_es_evento_y_mal_formateada(self):
        p = al.parse_line(1, "[WARNING] Invalid password attempt")
        self.assertTrue(p.is_event and p.is_malformed)
        self.assertEqual(p.date_status, "missing")

    def test_decision2_nivel_invalido_no_es_evento(self):
        for text in ("[DEBUG] 2025-01-10 algo", "texto suelto", "[info] 2025-01-10 x", "[] 2025-01-10 x"):
            p = al.parse_line(1, text)
            self.assertTrue(p.is_malformed, text)
            self.assertFalse(p.is_event, text)
            self.assertIsNone(p.level, text)

    def test_decision3_fecha_invalida_toda_la_linea_mal(self):
        for text in ("[INFO] 2025-13-45 x", "[INFO] 2025-02-30 x", "[INFO] 2025-1-5 x",
                     "[INFO] 2025/01/10 x", "[INFO] 10-01-2025 x"):
            p = al.parse_line(1, text)
            self.assertEqual(p.date_status, "invalid", text)
            self.assertTrue(p.is_malformed and not p.is_event, text)

    def test_decision8_versiones_y_numeros_no_son_fechas(self):
        # Una versión o una IP al inicio del mensaje NO es una fecha mal escrita:
        # la línea simplemente no tiene fecha (evento + mal formateada, decisión 1).
        for text in ("[INFO] 1.2.3 released", "[INFO] 192.168.1.1 connected",
                     "[INFO] 404 pages not found", "[INFO] 3.11 installed"):
            p = al.parse_line(1, text)
            self.assertEqual(p.date_status, "missing", text)
            self.assertTrue(p.is_event and p.is_malformed, text)
            self.assertEqual(p.problems, ["sin fecha"], text)

    def test_decision8_fechas_con_anio_de_4_digitos_siguen_siendo_fechas_mal_escritas(self):
        for text in ("[INFO] 10-01-2025 x", "[INFO] 2025/01/10 x", "[INFO] 2025-01-10T10:00:00 x",
                     "[INFO] 2025.13.45 x"):
            p = al.parse_line(1, text)
            self.assertEqual(p.date_status, "invalid", text)
            self.assertTrue(p.is_malformed and not p.is_event, text)

    def test_linea_vacia_se_ignora(self):
        self.assertIsNone(al.parse_line(1, ""))
        self.assertIsNone(al.parse_line(1, "     "))

    def test_linea_bien_formada(self):
        p = al.parse_line(7, "[ERROR] 2025-01-10 Failed to connect to database")
        self.assertEqual((p.level, p.date_status, p.message), ("ERROR", "valid", "Failed to connect to database"))
        self.assertTrue(p.is_event and not p.is_malformed)

    def test_las_decisiones_se_pueden_cambiar_con_las_constantes(self):
        with mock.patch.object(al, "COUNT_EVENT_IF_NO_DATE", False):
            p = al.parse_line(1, "[WARNING] Invalid password attempt")
            self.assertTrue(p.is_malformed and not p.is_event)
        with mock.patch.object(al, "COUNT_EVENT_IF_INVALID_DATE", True):
            p = al.parse_line(1, "[INFO] 2025-13-45 x")
            self.assertTrue(p.is_malformed and p.is_event)


class TestEntradaSalida(unittest.TestCase):
    def _main_con(self, ruta):
        buf = io.StringIO()
        with mock.patch("sys.argv", ["analizador_logs.py", ruta]), redirect_stdout(buf):
            code = al.main()
        return code, buf.getvalue()

    def test_archivo_inexistente(self):
        code, out = self._main_con("no_existe.txt")
        self.assertEqual(code, 1)
        self.assertIn("no existe", out)

    def test_carpeta_en_lugar_de_archivo(self):
        code, out = self._main_con(BASE)
        self.assertEqual(code, 1)

    def test_archivo_vacio(self):
        code, out = self._main_con(os.path.join(BASE, "log_vacio.txt"))
        self.assertEqual(code, 0)
        self.assertIn("vacío", out)

    def test_reporte_muestra_resumen(self):
        code, out = self._main_con(os.path.join(BASE, "log_con_errores.txt"))
        self.assertEqual(code, 0)
        self.assertIn("Total de eventos", out)
        self.assertIn("Líneas mal formateadas", out)


if __name__ == "__main__":
    unittest.main()
