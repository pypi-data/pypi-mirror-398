import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
from mtcli.mt5_context import mt5_conexao
from mtcli.logger import setup_logger


log = setup_logger()


def calcular_vwap(symbol: str, minutes: int, limit: int):
    with mt5_conexao():
        if not mt5.symbol_select(symbol, True):
            log.error(f"Erro ao selecionar símbolo {symbol}")
            return None

        timeframe = _get_timeframe(minutes)
        utc_from = datetime.now() - timedelta(minutes=limit * minutes)
        rates = mt5.copy_rates_from(symbol, timeframe, utc_from, limit)
        if rates is None or len(rates) == 0:
            return None

    df = pd.DataFrame(rates)
    df["tp"] = (df["high"] + df["low"] + df["close"]) / 3
    df["vwap_num"] = df["tp"] * df["real_volume"]
    df["vwap_den"] = df["real_volume"]
    df["vwap"] = df["vwap_num"].cumsum() / df["vwap_den"].cumsum()

    return df["vwap"].iloc[-1]


def _get_timeframe(minutes):
    return {
        1: mt5.TIMEFRAME_M1,
        2: mt5.TIMEFRAME_M2,
        3: mt5.TIMEFRAME_M3,
        4: mt5.TIMEFRAME_M4,
        5: mt5.TIMEFRAME_M5,
        6: mt5.TIMEFRAME_M6,
        10: mt5.TIMEFRAME_M10,
        12: mt5.TIMEFRAME_M12,
        15: mt5.TIMEFRAME_M15,
        20: mt5.TIMEFRAME_M20,
        30: mt5.TIMEFRAME_M30,
        60: mt5.TIMEFRAME_H1,
        120: mt5.TIMEFRAME_H2,
        180: mt5.TIMEFRAME_H3,
        240: mt5.TIMEFRAME_H4,
    }.get(minutes, mt5.TIMEFRAME_M1)
