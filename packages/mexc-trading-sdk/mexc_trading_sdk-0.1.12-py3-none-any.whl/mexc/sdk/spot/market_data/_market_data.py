from dataclasses import dataclass
from .depth import Depth
from .instrument_info import InstrumentInfo
from .candles import Candles

@dataclass
class MarketData(Depth, InstrumentInfo, Candles):
  ...