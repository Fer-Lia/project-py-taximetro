import os
import sqlite3
from contextlib import closing
from datetime import datetime

CARPETA_DATOS = "data"
ARCHIVO_BD = "data/taximetro.db"
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"
FORMATO_DIA = "%Y-%m-%d"

CREAR_TABLA = """
CREATE TABLE IF NOT EXISTS carreras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inicio TEXT NOT NULL,
    duracion INTEGER NOT NULL CHECK (duracion >= 0),
    importe REAL NOT NULL CHECK (importe >= 0)
)
"""


class ErrorHistorial(Exception):
    pass


def conectar() -> sqlite3.Connection:
    os.makedirs(CARPETA_DATOS, exist_ok=True)
    conexion = sqlite3.connect(ARCHIVO_BD)
    conexion.execute(CREAR_TABLA)
    return conexion


def guardar_carrera(hora_inicio: float, duracion: float, importe: float) -> None:
    inicio = datetime.fromtimestamp(hora_inicio).strftime(FORMATO_FECHA)
    try:
        with closing(conectar()) as conexion:
            with conexion:
                conexion.execute(
                    "INSERT INTO carreras (inicio, duracion, importe) VALUES (?, ?, ?)",
                    (inicio, round(duracion), round(importe, 2)),
                )
    except (OSError, sqlite3.Error) as error:
        raise ErrorHistorial(error) from error


def leer_carreras_de_hoy() -> list[tuple[str, int, float]]:
    hoy = datetime.now().strftime(FORMATO_DIA)
    try:
        with closing(conectar()) as conexion:
            return conexion.execute(
                "SELECT inicio, duracion, importe FROM carreras "
                "WHERE date(inicio) = ? ORDER BY inicio",
                (hoy,),
            ).fetchall()
    except (OSError, sqlite3.Error) as error:
        raise ErrorHistorial(error) from error


def leer_historial() -> list[tuple[str, int, float]]:
    try:
        with closing(conectar()) as conexion:
            return conexion.execute(
                "SELECT inicio, duracion, importe FROM carreras ORDER BY inicio DESC"
            ).fetchall()
    except (OSError, sqlite3.Error) as error:
        raise ErrorHistorial(error) from error
