import logging
import os
import secrets
import time
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from taximetro import autenticacion, config, historial, registro
from taximetro.carrera import Carrera

DURACION_SESION = 8 * 3600
CARPETA_WEB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    registro.configurar_registro()
    logging.info("Programa iniciado (API)")
    yield


app = FastAPI(title="Taxímetro Digital", lifespan=ciclo_de_vida)
app.state.carrera = None
app.state.sesiones = {}

seguridad = HTTPBearer()


def exigir_sesion(credenciales: HTTPAuthorizationCredentials = Depends(seguridad)) -> str:
    token = credenciales.credentials
    caduca = app.state.sesiones.get(token)
    if caduca is None or caduca < time.time():
        app.state.sesiones.pop(token, None)
        raise HTTPException(
            status_code=401,
            detail="Sesión no válida. Inicia sesión de nuevo.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


proteger = [Depends(exigir_sesion)]


class Acceso(BaseModel):
    contrasena: str


class CambioEstado(BaseModel):
    estado: Literal["parado", "movimiento"]


def carrera_en_curso() -> Carrera:
    if app.state.carrera is None:
        raise HTTPException(status_code=404, detail="No hay ninguna carrera en curso.")
    return app.state.carrera


@app.get("/", include_in_schema=False)
def inicio() -> RedirectResponse:
    return RedirectResponse("/panel/")


@app.post("/login")
def iniciar_sesion(acceso: Acceso) -> dict:
    try:
        if not autenticacion.existe_contrasena():
            raise HTTPException(
                status_code=503,
                detail="No hay contraseña creada. Créala con: python main.py --terminal",
            )
        correcta = autenticacion.verificar_contrasena(acceso.contrasena)
    except (OSError, ValueError, KeyError) as error:
        logging.error("Error de autenticación: %s", error)
        raise HTTPException(
            status_code=500, detail="No se pudo comprobar la contraseña."
        ) from error
    if not correcta:
        logging.error("Acceso denegado a la API")
        raise HTTPException(status_code=401, detail="Contraseña incorrecta.")
    token = secrets.token_urlsafe(32)
    app.state.sesiones[token] = time.time() + DURACION_SESION
    logging.info("Sesión iniciada")
    return {"token": token}


@app.post("/logout")
def cerrar_sesion(token: str = Depends(exigir_sesion)) -> dict:
    app.state.sesiones.pop(token, None)
    logging.info("Sesión cerrada")
    return {"cerrada": True}


@app.post("/carrera", status_code=201, dependencies=proteger)
def iniciar_carrera() -> dict:
    if app.state.carrera is not None:
        raise HTTPException(status_code=409, detail="Ya hay una carrera en curso.")
    try:
        tarifas = config.cargar_tarifas()
    except (OSError, ValueError, KeyError) as error:
        logging.error("No se pudieron cargar las tarifas: %s", error)
        raise HTTPException(
            status_code=500, detail="No se pudieron cargar las tarifas."
        ) from error
    app.state.carrera = Carrera(time.time(), tarifas)
    logging.info("Carrera iniciada")
    return {"estado": app.state.carrera.estado}


@app.put("/carrera/estado", dependencies=proteger)
def cambiar_estado(cambio: CambioEstado) -> dict:
    carrera = carrera_en_curso()
    carrera.cambiar_estado(cambio.estado, time.time())
    logging.info("Cambio de estado: %s", cambio.estado)
    return {"estado": carrera.estado, "importe": round(carrera.importe, 2)}


@app.post("/carrera/finalizar", dependencies=proteger)
def finalizar_carrera() -> dict:
    carrera = carrera_en_curso()
    ahora = time.time()
    duracion = ahora - carrera.hora_inicio
    total = carrera.finalizar(ahora)
    app.state.carrera = None
    logging.info("Carrera finalizada: %.0f s, %.2f EUR", duracion, total)
    guardada = True
    try:
        historial.guardar_carrera(carrera.hora_inicio, duracion, total)
    except historial.ErrorHistorial as error:
        logging.error("No se pudo guardar la carrera: %s", error)
        guardada = False
    return {"duracion": round(duracion), "importe": round(total, 2), "guardada": guardada}


@app.get("/historial", dependencies=proteger)
def consultar_historial() -> list[dict]:
    try:
        carreras = historial.leer_historial()
    except historial.ErrorHistorial as error:
        logging.error("No se pudo leer el historial: %s", error)
        raise HTTPException(
            status_code=500, detail="No se pudo leer el historial."
        ) from error
    return [
        {"inicio": inicio, "duracion": duracion, "importe": importe}
        for inicio, duracion, importe in carreras
    ]


app.mount("/panel", StaticFiles(directory=CARPETA_WEB, html=True), name="panel")
