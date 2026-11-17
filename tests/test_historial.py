import os
import tempfile
import time
import unittest
from unittest.mock import patch

from taximetro import historial


class TestHistorial(unittest.TestCase):
    def setUp(self) -> None:
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        ruta = os.path.join(carpeta.name, "prueba.db")
        parche_carpeta = patch.object(historial, "CARPETA_DATOS", carpeta.name)
        parche_bd = patch.object(historial, "ARCHIVO_BD", ruta)
        parche_carpeta.start()
        parche_bd.start()
        self.addCleanup(parche_carpeta.stop)
        self.addCleanup(parche_bd.stop)

    def test_sin_carreras_devuelve_una_lista_vacia(self) -> None:
        self.assertEqual(historial.leer_carreras_de_hoy(), [])

    def test_una_carrera_guardada_se_puede_leer(self) -> None:
        historial.guardar_carrera(time.time(), 12.4, 3.45)
        carreras = historial.leer_carreras_de_hoy()
        self.assertEqual(len(carreras), 1)
        self.assertEqual(carreras[0][1], 12)
        self.assertAlmostEqual(carreras[0][2], 3.45)

    def test_el_importe_se_guarda_con_dos_decimales(self) -> None:
        historial.guardar_carrera(time.time(), 10, 2.056440119743347)
        self.assertEqual(historial.leer_carreras_de_hoy()[0][2], 2.06)

    def test_una_carrera_de_otro_dia_no_aparece(self) -> None:
        hace_dos_dias = time.time() - 2 * 24 * 3600
        historial.guardar_carrera(hace_dos_dias, 10, 1.00)
        self.assertEqual(historial.leer_carreras_de_hoy(), [])

    def test_un_importe_negativo_se_rechaza(self) -> None:
        with self.assertRaises(historial.ErrorHistorial):
            historial.guardar_carrera(time.time(), 10, -1.0)

    def test_leer_historial_devuelve_primero_la_carrera_mas_reciente(self) -> None:
        ahora = time.time()
        historial.guardar_carrera(ahora - 2 * 24 * 3600, 10, 1.00)
        historial.guardar_carrera(ahora, 20, 2.00)
        carreras = historial.leer_historial()
        self.assertEqual([carrera[1] for carrera in carreras], [20, 10])


if __name__ == "__main__":
    unittest.main()
