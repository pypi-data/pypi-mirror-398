from dataclasses import dataclass
from collections import defaultdict
from decimal import Decimal
import asyncio

from trading_sdk.market.user_data.positions import Positions as PositionsTDK, Position

from mexc.core.util import cacher
from mexc.sdk.core import SdkMixin, wrap_exceptions
from mexc.futures.user_data.positions import PositionType

cache = cacher()

def merge_positions(positions: list[Position]) -> Position | None:
  if positions:
    total_size = sum(p.size for p in positions)
    return Position(
      size=Decimal(sum(p.size for p in positions)),
      entry_price=Decimal(sum(p.size * p.entry_price for p in positions)) / total_size,
    )

@dataclass
class Positions(PositionsTDK, SdkMixin):
  @wrap_exceptions
  async def positions(self, *instruments: str) -> dict[str, Position]:
    r = await self.client.futures.positions()
    symbols = instruments or set(p['symbol'] for p in r)
    contracts = await asyncio.gather(*(
      cache(lambda: self.client.futures.contract_info(s))
      for s in symbols
    ))
    contract_sizes = {c['symbol']: c['contractSize'] for c in contracts}
    positions = defaultdict[str, list[Position]](list)

    for p in r:
      s = 1 if p['positionType'] == PositionType.long.value else -1
      size = s * abs(p['holdVol']) * contract_sizes[p['symbol']]
      positions[p['symbol']].append(Position(size=size, entry_price=p['openAvgPrice']))

    return {
      s: p for s in symbols
      if (p := merge_positions(positions[s])) is not None
    }