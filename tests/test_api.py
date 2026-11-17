import os
import tempfile
import time
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
        app.state.sesiones = {}
        self.anonimo = TestClient(app)
        self.token = self.anonimo.post("/login", json={"contrasena": CONTRASENA}).json()["token"]
        self.cliente = TestClient(app, headers={"Authorization": "Bearer " + self.token})

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

    def test_login_con_la_contrasena_correcta_devuelve_un_token(self) -> None:
        respuesta = self.anonimo.post("/login", json={"contrasena": CONTRASENA})
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.json()["token"])

    def test_login_con_una_contrasena_incorrecta_da_401(self) -> None:
        respuesta = self.anonimo.post("/login", json={"contrasena": "incorrecta"})
        self.assertEqual(respuesta.status_code, 401)

    def test_login_sin_contrasena_creada_da_503(self) -> None:
        os.remove(self.credenciales)
        respuesta = self.anonimo.post("/login", json={"contrasena": CONTRASENA})
        self.assertEqual(respuesta.status_code, 503)

    def test_sin_token_no_se_puede_consultar_el_historial(self) -> None:
        self.assertIn(self.anonimo.get("/historial").status_code, (401, 403))

    def test_un_token_falso_da_401(self) -> None:
        respuesta = self.anonimo.get("/historial", headers={"Authorization": "Bearer falso"})
        self.assertEqual(respuesta.status_code, 401)

    def test_cerrar_sesion_invalida_el_token(self) -> None:
        self.assertEqual(self.cliente.post("/logout").status_code, 200)
        self.assertEqual(self.cliente.get("/historial").status_code, 401)

    def test_una_sesion_caducada_da_401(self) -> None:
        app.state.sesiones[self.token] = time.time() - 1
        self.assertEqual(self.cliente.get("/historial").status_code, 401)

    def test_el_panel_web_se_sirve_sin_sesion(self) -> None:
        respuesta = self.anonimo.get("/panel/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Taxímetro Digital", respuesta.text)

    def test_la_raiz_redirige_al_panel(self) -> None:
        respuesta = self.anonimo.get("/", follow_redirects=False)
        self.assertEqual(respuesta.headers["location"], "/panel/")


if __name__ == "__main__":
    unittest.main()
