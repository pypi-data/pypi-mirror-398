import click
import MetaTrader5 as mt5

from .conf import (
    LIMIT,
    PERIOD,
    SORT,
    SYMBOL,
    TICK_SIZE,
)
from .controller import VAPController


@click.command()
@click.version_option(package_name="mtcli-vap")
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
    help="Numero de timeframes a serem lidos.",
)
@click.option(
    "--sort",
    type=click.Choice(["volume", "price"], case_sensitive=False),
    default=SORT,
    show_default=True,
    help="Ordenacao do VAP.",
)
@click.option(
    "--tick-size", "-ts", default=TICK_SIZE, show_default=True, help="Tamanho do tick."
)
def vap(symbol, timeframe, bars, sort, tick_size):
    """Exibe o VAP (Volume At Price) no terminal seguindo o padrão textual do mtcli-market."""
    tf_map = {
        "M1": mt5.TIMEFRAME_M1,
        "M2": mt5.TIMEFRAME_M2,
        "M3": mt5.TIMEFRAME_M3,
        "M4": mt5.TIMEFRAME_M4,
        "M5": mt5.TIMEFRAME_M5,
        "M6": mt5.TIMEFRAME_M6,
        "M10": mt5.TIMEFRAME_M10,
        "M12": mt5.TIMEFRAME_M12,
        "M15": mt5.TIMEFRAME_M15,
        "M20": mt5.TIMEFRAME_M20,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H2": mt5.TIMEFRAME_H2,
        "H3": mt5.TIMEFRAME_H3,
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
        symbol=symbol,
        timeframe=tf_map[timeframe_upper],
        bars=bars,
        sort=sort,
        tick_size=tick_size,
    )

    output = controller.execute()
    click.echo(output)
