from .model import calcular_vwap


def obter_vwap(symbol: str, minutes: int, limit: int):
    return calcular_vwap(symbol, minutes, limit)
