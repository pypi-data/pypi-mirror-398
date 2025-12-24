import click
from .conf import DIGITOS


def exibir_vwap(valor, symbol):
    if valor is None:
        click.echo("Nenhuma barra encontrada para calcular o VWAP.")
    else:
        click.echo(f"\nVWAP {symbol} {valor:.{DIGITOS}f}\n")
