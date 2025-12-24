from dataclasses import dataclass
from .tickers import Tickers

@dataclass
class MarketStreams(
  Tickers,
):
  ...