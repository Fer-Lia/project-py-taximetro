import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from taximetro import historial
from taximetro.interfaces.api import app


class TestApi(unittest.TestCase):
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
        app.state.carrera = None
        self.cliente = TestClient(app)

    def test_iniciar_una_carrera(self) -> None:
        respuesta = self.cliente.post("/carrera")
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json(), {"estado": "parado"})

    def test_no_se_pueden_iniciar_dos_carreras(self) -> None:
        self.cliente.post("/carrera")
        self.assertEqual(self.cliente.post("/carrera").status_code, 409)

    def test_cambiar_estado_sin_carrera_da_404(self) -> None:
        respuesta = self.cliente.put("/carrera/estado", json={"estado": "movimiento"})
        self.assertEqual(respuesta.status_code, 404)

    def test_un_estado_no_valido_da_422(self) -> None:
        self.cliente.post("/carrera")
        respuesta = self.cliente.put("/carrera/estado", json={"estado": "volando"})
        self.assertEqual(respuesta.status_code, 422)

    def test_finalizar_sin_carrera_da_404(self) -> None:
        self.assertEqual(self.cliente.post("/carrera/finalizar").status_code, 404)

    def test_una_carrera_completa_queda_en_el_historial(self) -> None:
        self.cliente.post("/carrera")
        self.cliente.put("/carrera/estado", json={"estado": "movimiento"})
        respuesta = self.cliente.post("/carrera/finalizar")
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.json()["guardada"])
        self.assertEqual(len(self.cliente.get("/historial").json()), 1)


if __name__ == "__main__":
    unittest.main()
