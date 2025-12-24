"""Plugin VWAP para o mtcli."""

from .cli import vwap


def register(cli):
    cli.add_command(vwap, name="vwap")
