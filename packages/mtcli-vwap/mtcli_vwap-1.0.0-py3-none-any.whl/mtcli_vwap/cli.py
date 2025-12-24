import click
from .controller import obter_vwap
from .view import exibir_vwap
from .conf import (
    SYMBOL,
    MINUTES,
    LIMIT,
)


@click.command()
@click.version_option(package_name="mtcli-vwap")
@click.option(
    "--symbol", "-s", default=SYMBOL, show_default=True, help="Codigo do ativo."
)
@click.option(
    "--minutes",
    "-m",
    default=MINUTES,
    show_default=True,
    help="Timeframe em minutos usado no calculo da VWAP.",
)
@click.option(
    "--limit",
    "-l",
    default=LIMIT,
    show_default=True,
    help="Numero de timeframes da VWAP.",
)
def vwap(symbol, minutes, limit):
    """Calcula o VWAP do ativo SYMBOL no intraday."""
    resultado = obter_vwap(symbol, minutes, limit)
    exibir_vwap(resultado, symbol)
