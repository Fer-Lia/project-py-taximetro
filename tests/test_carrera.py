import unittest

from taximetro.carrera import Carrera

TARIFAS = {"parado": 0.02, "movimiento": 0.05}


class TestCarrera(unittest.TestCase):
    def test_una_carrera_sin_cambios_de_estado_cobra_como_parado(self) -> None:
        carrera = Carrera(0, TARIFAS)
        self.assertAlmostEqual(carrera.finalizar(10), 0.20)

    def test_el_importe_se_acumula_por_tramos(self) -> None:
        carrera = Carrera(0, TARIFAS)
        carrera.cambiar_estado("movimiento", 10)
        carrera.cambiar_estado("parado", 30)
        self.assertAlmostEqual(carrera.finalizar(40), 1.40)

    def test_importe_actual_incluye_el_tramo_en_curso(self) -> None:
        carrera = Carrera(0, TARIFAS)
        carrera.cambiar_estado("movimiento", 10)
        self.assertAlmostEqual(carrera.importe_actual(20), 0.70)

    def test_importe_actual_no_cierra_el_tramo(self) -> None:
        carrera = Carrera(0, TARIFAS)
        carrera.importe_actual(10)
        self.assertAlmostEqual(carrera.finalizar(20), 0.40)


if __name__ == "__main__":
    unittest.main()
