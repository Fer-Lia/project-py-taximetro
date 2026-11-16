from taximetro import registro
from taximetro.interfaces import cli


if __name__ == "__main__":
    registro.configurar_registro()
    cli.ejecutar()
