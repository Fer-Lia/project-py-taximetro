import logging
import time
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from taximetro import config, historial, registro
from taximetro.carrera import Carrera


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    registro.configurar_registro()
    logging.info("Programa iniciado (API)")
    yield


app = FastAPI(title="Taxímetro Digital", lifespan=ciclo_de_vida)
app.state.carrera = None


class CambioEstado(BaseModel):
    estado: Literal["parado", "movimiento"]


def carrera_en_curso() -> Carrera:
    if app.state.carrera is None:
        raise HTTPException(status_code=404, detail="No hay ninguna carrera en curso.")
    return app.state.carrera


@app.post("/carrera", status_code=201)
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


@app.put("/carrera/estado")
def cambiar_estado(cambio: CambioEstado) -> dict:
    carrera = carrera_en_curso()
    carrera.cambiar_estado(cambio.estado, time.time())
    logging.info("Cambio de estado: %s", cambio.estado)
    return {"estado": carrera.estado, "importe": round(carrera.importe, 2)}


@app.post("/carrera/finalizar")
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


@app.get("/historial")
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
