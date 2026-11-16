import logging
import os

CARPETA_LOGS = "logs"
ARCHIVO_LOG = "logs/taximetro.log"
FORMATO_LOG = "%(asctime)s | %(levelname)s | %(message)s"


def configurar_registro() -> None:
    os.makedirs(CARPETA_LOGS, exist_ok=True)
    logging.basicConfig(
        filename=ARCHIVO_LOG,
        level=logging.INFO,
        format=FORMATO_LOG,
        encoding="utf-8",
    )
