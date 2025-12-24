from dataclasses import dataclass
from decimal import Decimal

from trading_sdk.types import ApiError
from trading_sdk.market.market_data.depth import SpotDepth, Book

from mexc.sdk.core import SdkMixin, wrap_exceptions, spot_name

@dataclass
class Depth(SpotDepth, SdkMixin):
  @wrap_exceptions
  async def depth(self, instrument: str, /, *, limit: int | None = None) -> Book:
    r = await self.client.spot.depth(instrument, limit=limit)
    return Book(
      asks=[Book.Entry(
        price=Decimal(p.price),
        qty=Decimal(p.qty)
      ) for p in r['asks'][:limit]],
      bids=[Book.Entry(
        price=Decimal(p.price),
        qty=Decimal(p.qty)
      ) for p in r['bids'][:limit]],
    )

  async def spot_depth(self, base: str, quote: str, /, *, limit: int | None = None) -> Book:
    instrument = spot_name(base, quote)
    return await self.depth(instrument, limit=limit)
