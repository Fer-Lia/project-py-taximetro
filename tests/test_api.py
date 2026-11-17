import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from taximetro import autenticacion, historial
from taximetro.interfaces.api import app

CONTRASENA = "secreta"


class TestApi(unittest.TestCase):
    def setUp(self) -> None:
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        base_datos = os.path.join(carpeta.name, "prueba.db")
        self.credenciales = os.path.join(carpeta.name, "credenciales.json")
        parches = [
            patch.object(historial, "CARPETA_DATOS", carpeta.name),
            patch.object(historial, "ARCHIVO_BD", base_datos),
            patch.object(autenticacion, "CARPETA_DATOS", carpeta.name),
            patch.object(autenticacion, "ARCHIVO_CREDENCIALES", self.credenciales),
        ]
        for parche in parches:
            parche.start()
            self.addCleanup(parche.stop)
        autenticacion.guardar_contrasena(CONTRASENA)
        app.state.carrera = None
        self.cliente = TestClient(app)
        self.cliente.auth = ("taxista", CONTRASENA)

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

    def test_sin_contrasena_da_401(self) -> None:
        self.assertEqual(TestClient(app).get("/historial").status_code, 401)

    def test_una_contrasena_incorrecta_da_401(self) -> None:
        respuesta = self.cliente.get("/historial", auth=("taxista", "incorrecta"))
        self.assertEqual(respuesta.status_code, 401)

    def test_sin_contrasena_creada_da_503(self) -> None:
        os.remove(self.credenciales)
        self.assertEqual(self.cliente.get("/historial").status_code, 503)


if __name__ == "__main__":
    unittest.main()