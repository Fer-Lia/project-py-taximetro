import time

from taximetro.carrera import Carrera


def mostrar_instrucciones() -> None:
    print("=== TAXIMETRO DIGITAL ===")
    print("Comandos:")
    print("  i -> iniciar una carrera")
    print("  s -> salir del programa")


def pedir_comando() -> str:
    return input("> ").strip().lower()


def iniciar_carrera() -> Carrera:
    carrera = Carrera(time.time())
    print("Carrera iniciada.")
    return carrera


def ejecutar() -> None:
    mostrar_instrucciones()

    carrera = None

    while True:
        comando = pedir_comando()

        if comando == "i":
            if carrera is None:
                carrera = iniciar_carrera()
            else:
                print("Ya hay una carrera en curso.")

        elif comando == "s":
            print("Hasta luego.")
            break

        else:
            print("Comando no reconocido. Escribe i o s.")