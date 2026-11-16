ESTADO_PARADO = "parado"

ESTADO_MOVIMIENTO = "movimiento"


def calcular_tramo(estado: str, segundos: float, tarifas: dict) -> float:
    if estado == ESTADO_MOVIMIENTO:
        return segundos * tarifas["movimiento"]
    return segundos * tarifas["parado"]
