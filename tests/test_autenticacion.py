import unittest

from taximetro.autenticacion import comprobar_contrasena, generar_hash

SAL = b"sal-de-prueba-16"


class TestAutenticacion(unittest.TestCase):
    def test_misma_contrasena_y_sal_dan_el_mismo_hash(self) -> None:
        self.assertEqual(generar_hash("secreta", SAL), generar_hash("secreta", SAL))

    def test_otra_sal_da_otro_hash(self) -> None:
        otra_sal = b"otra-sal-1234567"
        self.assertNotEqual(generar_hash("secreta", SAL), generar_hash("secreta", otra_sal))

    def test_contrasena_correcta_se_acepta(self) -> None:
        hash_guardado = generar_hash("secreta", SAL)
        self.assertTrue(comprobar_contrasena("secreta", SAL, hash_guardado))

    def test_contrasena_incorrecta_se_rechaza(self) -> None:
        hash_guardado = generar_hash("secreta", SAL)
        self.assertFalse(comprobar_contrasena("otra", SAL, hash_guardado))


if __name__ == "__main__":
    unittest.main()
