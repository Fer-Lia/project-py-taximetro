import unittest

from taximetro.tarifas import calcular_tramo

TARIFAS = {"parado": 0.02, "movimiento": 0.05}


class TestCalcularTramo(unittest.TestCase):
    def test_parado_usa_la_tarifa_de_parado(self) -> None:
        self.assertAlmostEqual(calcular_tramo("parado", 10, TARIFAS), 0.20)

    def test_movimiento_usa_la_tarifa_de_movimiento(self) -> None:
        self.assertAlmostEqual(calcular_tramo("movimiento", 10, TARIFAS), 0.50)

    def test_un_tramo_de_cero_segundos_cuesta_cero(self) -> None:
        self.assertEqual(calcular_tramo("movimiento", 0, TARIFAS), 0)

    def test_usa_las_tarifas_que_recibe(self) -> None:
        tarifas = {"parado": 1.0, "movimiento": 2.0}
        self.assertAlmostEqual(calcular_tramo("movimiento", 3, tarifas), 6.0)


if __name__ == "__main__":
    unittest.main()
