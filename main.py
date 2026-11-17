import sys

from taximetro import registro


def main() -> None:
    if "--api" in sys.argv:
        import uvicorn

        uvicorn.run("taximetro.interfaces.api:app", host="0.0.0.0", port=8000)
        return
    registro.configurar_registro()
    if "--terminal" in sys.argv:
        from taximetro.interfaces import cli

        cli.ejecutar()
    else:
        from taximetro.interfaces import gui

        gui.ejecutar()


if __name__ == "__main__":
    main()
