from .model import VAPModel
from .view import VAPView


class VAPController:
    """
    Controller no padrão MVC utilizado pelos utilitários mtcli:
    - não contém lógica pesada;
    - orquestra Model -> View;
    - responsável por passar parâmetros e devolver a string pronta.
    """

    def __init__(
        self,
        symbol: str,
        timeframe=None,
        bars: int = None,
        sort: str = "volume",
        tick_size: float = 5,
    ):
        """
        Args:
            symbol: símbolo do ativo (ex: WINZ25).
            timeframe: constante do MetaTrader5.
            bars: quantidade de candles.
            sort: critério de ordenação ("volume" ou "price").
            tick_size: tamanho do tick.
        """
        self.model = VAPModel(
            symbol=symbol, timeframe=timeframe, bars=bars, tick_size=tick_size
        )
        self.view = VAPView(sort=sort)

    def execute(self) -> str:
        vap = self.model.get_vap()
        return self.view.render(vap)
