import click
import MetaTrader5 as mt5

from .conf import (
    LIMIT,
    PERIOD,
    SYMBOL,
)
from .controller import VAPController


@click.command()
@click.option(
    "--symbol",
    "-s",
    required=True,
    default=SYMBOL,
    show_default=True,
    help="Codigo do ativo.",
)
@click.option(
    "--period",
    "-p",
    "timeframe",
    default=PERIOD,
    show_default=True,
    help="Timeframe do VAP.",
)
@click.option(
    "--limit",
    "-l",
    "bars",
    default=LIMIT,
    show_default=True,
    help="Número de candles a serem lidos.",
)
@click.option(
    "--sort",
    type=click.Choice(["volume", "price"], case_sensitive=False),
    default="volume",
    show_default=True,
    help="Ordenacao do VAP: por volume (padrão) ou por preço.",
)
def vap(symbol, timeframe, bars, sort):
    """Exibe o VAP (Volume At Price) no terminal seguindo o padrão textual do mtcli-market."""
    tf_map = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
    }

    timeframe_upper = timeframe.upper()
    if timeframe_upper not in tf_map:
        raise click.ClickException(
            f"Timeframe inválido: {timeframe}. "
            f"Use uma das chaves: {', '.join(tf_map.keys())}"
        )

    controller = VAPController(
        symbol=symbol, timeframe=tf_map[timeframe_upper], bars=bars, sort=sort
    )

    output = controller.execute()
    click.echo(output)
