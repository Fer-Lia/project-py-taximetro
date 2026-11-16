import logging
import time

from taximetro import historial
from taximetro.carrera import Carrera
from taximetro.tarifas import ESTADO_MOVIMIENTO, ESTADO_PARADO


def mostrar_instrucciones() -> None:
    print("=== TAXIMETRO DIGITAL ===")
    print("Comandos:")
    print("  i -> iniciar una carrera")
    print("  p -> pasar a parado")
    print("  m -> pasar a movimiento")
    print("  f -> finalizar la carrera")
    print("  h -> ver las carreras de hoy")
    print("  s -> salir del programa")


def pedir_comando() -> str:
    return input("> ").strip().lower()


def iniciar_carrera() -> Carrera:
    carrera = Carrera(time.time())
    logging.info("Carrera iniciada")
    print("Carrera iniciada.")
    return carrera


def cambiar_estado(carrera: Carrera, estado: str) -> None:
    carrera.cambiar_estado(estado, time.time())
    logging.info("Cambio de estado: %s", estado)
    print("Estado: " + estado)


def finalizar_carrera(carrera: Carrera) -> None:
    ahora = time.time()
    duracion = ahora - carrera.hora_inicio
    total = carrera.finalizar(ahora)
    print(f"Total a cobrar: {total:.2f} €")
    logging.info("Carrera finalizada: %.0f s, %.2f EUR", duracion, total)
    try:
        historial.guardar_carrera(carrera.hora_inicio, duracion, total)
    except OSError as error:
        logging.error("No se pudo guardar la carrera: %s", error)
        print("Aviso: no se pudo guardar la carrera en el historial.")


def mostrar_historial() -> None:
    try:
        carreras = historial.leer_carreras_de_hoy()
    except OSError as error:
        logging.error("No se pudo leer el historial: %s", error)
        print("No se pudo leer el historial.")
        return
    if len(carreras) == 0:
        print("Hoy no hay carreras.")
    else:
        for fecha, duracion, importe in carreras:
            print(f"{fecha} | {duracion} s | {importe} €")


def ejecutar() -> None:
    logging.info("Programa iniciado")
    mostrar_instrucciones()

    carrera = None

    while True:
        comando = pedir_comando()

        if comando == "i":
            if carrera is None:
                carrera = iniciar_carrera()
            else:
                print("Ya hay una carrera en curso.")

        elif comando == "p":
            if carrera is None:
                print("No hay ninguna carrera en curso.")
            else:
                cambiar_estado(carrera, ESTADO_PARADO)

        elif comando == "m":
            if carrera is None:
                print("No hay ninguna carrera en curso.")
            else:
                cambiar_estado(carrera, ESTADO_MOVIMIENTO)

        elif comando == "f":
            if carrera is None:
                print("No hay ninguna carrera en curso.")
            else:
                finalizar_carrera(carrera)
                carrera = None

        elif comando == "h":
            mostrar_historial()

        elif comando == "s":
            logging.info("Programa cerrado")
            print("Hasta luego.")
            break

        else:
            print("Comando no reconocido. Escribe i, p, m, f, h o s.")
