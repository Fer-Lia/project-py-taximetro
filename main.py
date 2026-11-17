import sys

from taximetro import registro
from taximetro.interfaces import cli, gui


if __name__ == "__main__":
    registro.configurar_registro()
    if "--terminal" in sys.argv:
        cli.ejecutar()
    else:
        gui.ejecutar()
