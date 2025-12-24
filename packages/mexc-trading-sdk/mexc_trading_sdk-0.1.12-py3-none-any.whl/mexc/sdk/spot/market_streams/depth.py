from typing_extensions import Literal
from dataclasses import dataclass
from decimal import Decimal

from trading_sdk.market.market_streams.depth import SpotDepth, Book

from mexc.sdk.core import SdkMixin, wrap_exceptions, spot_name

def level(limit: int | None) -> Literal[5, 10, 20]:
  if limit is None:
    return 20
  elif limit < 5:
    return 5
  elif limit < 10:
    return 10
  else:
    return 20

@dataclass
class Depth(SpotDepth, SdkMixin):
  @wrap_exceptions
  async def depth(self, instrument: str, /, *, limit: int | None = None):
    async for book in self.client.spot.streams.depth(instrument, level(limit)):
      yield Book(
        bids=[Book.Entry(price=Decimal(e.price), qty=Decimal(e.qty)) for e in book.bids],
        asks=[Book.Entry(price=Decimal(e.price), qty=Decimal(e.qty)) for e in book.asks]
      )

  async def spot_depth(self, base: str, quote: str, /, *, limit: int | None = None):
    instrument = spot_name(base, quote)
    async for book in self.depth(instrument, limit=limit):
      yield book