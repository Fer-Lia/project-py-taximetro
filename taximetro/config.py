import json

ARCHIVO_TARIFAS = "config/tarifas.json"


def cargar_tarifas() -> dict:
    with open(ARCHIVO_TARIFAS, encoding="utf-8") as archivo:
        tarifas = json.load(archivo)
    return {"parado": tarifas["parado"], "movimiento": tarifas["movimiento"]}
