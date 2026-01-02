"""
VAP Model

Responsável por:
- Buscar candles no MetaTrader5;
- Construir o Volume At Price (VAP);
- Distribuir o volume ao longo do range do candle,
  aproximando o comportamento do Volume At Price do Profit.

Observações importantes:
- O MT5 retorna um numpy structured array (numpy.void).
- O acesso aos campos deve ser feito via r["campo"].
- O volume é distribuído igualmente entre os níveis de preço do candle.
"""

from collections import defaultdict

import MetaTrader5 as mt5

from .conf import DIGITOS as D


class VAPModel:
    """
    Model do plugin mtcli-vap.

    Responsável exclusivamente por:
    - coleta de dados no MT5;
    - processamento do VAP;
    - retorno de dados brutos para a View.

    Não contém lógica de exibição.
    """

    def __init__(
        self,
        symbol: str,
        timeframe=mt5.TIMEFRAME_M1,
        bars: int = 1000,
        tick_size: float = 5,
    ):
        """
        Inicializa o Model.

        Args:
            symbol (str): ativo (ex: WINZ25, WDOF26).
            timeframe: constante MT5 (ex: mt5.TIMEFRAME_M1).
            bars (int): número de candles a serem processados.
            tick_size (float): tamanho do tick.
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self.bars = bars
        self.tick_size = tick_size

    def fetch_rates(self):
        """
        Inicializa o MT5 (se necessário) e busca candles.

        Returns:
            numpy.ndarray: array estruturado com candles MT5.

        Raises:
            RuntimeError: se MT5 não inicializar ou não retornar dados.
        """
        if not mt5.initialize():
            raise RuntimeError("Falha ao inicializar MetaTrader5.")

        rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, self.bars)

        if rates is None or len(rates) == 0:
            raise RuntimeError(f"Sem dados MT5 para o símbolo {self.symbol}.")

        return rates

    @staticmethod
    def _extract_volume(r) -> float:
        """
        Extrai o volume de um candle MT5.

        Prioridade:
        1) real_volume (quando disponível e > 0)
        2) tick_volume

        Args:
            r (numpy.void): candle individual do MT5.

        Returns:
            float: volume do candle.
        """
        if "real_volume" in r.dtype.names and r["real_volume"] > 0:
            return float(r["real_volume"])

        return float(r["tick_volume"])

    def _price_levels(self, low: float, high: float):
        """
        Gera os níveis de preço entre low e high respeitando o tick size.

        Args:
            low (float): mínima do candle.
            high (float): máxima do candle.

        Returns:
            list[float]: lista de preços.
        """
        prices = []
        p = low

        # proteção contra loops infinitos
        max_steps = int((high - low) / self.tick_size) + 1

        for _ in range(max_steps):
            prices.append(round(p, D))
            p += self.tick_size
            if p > high:
                break

        return prices

    def compute_vap(self, rates):
        """
        Calcula o Volume At Price (VAP).

        O volume de cada candle é distribuído igualmente
        entre todos os níveis de preço do seu range.

        Args:
            rates (numpy.ndarray): candles retornados pelo MT5.

        Returns:
            dict[float, float]: {preço: volume_acumulado}
        """
        vap = defaultdict(float)

        for r in rates:
            volume = self._extract_volume(r)

            low = round(float(r["low"]), D)
            high = round(float(r["high"]), D)

            # candle sem range (ex: doji exato)
            if high <= low:
                vap[low] += volume
                continue

            prices = self._price_levels(low, high)

            if not prices:
                continue

            vol_per_price = volume / len(prices)

            for price in prices:
                vap[price] += vol_per_price

        return dict(vap)

    def get_vap(self):
        """
        Fluxo de alto nível:
        - busca candles;
        - calcula VAP;
        - retorna dict preço -> volume.

        Returns:
            dict[float, float]: VAP agregado.
        """
        rates = self.fetch_rates()
        return self.compute_vap(rates)
