from typing_extensions import Sequence, AsyncIterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from trading_sdk.market.user_data.my_trades import SpotMyTrades, Trade

from mexc.spot.user_data import MyTrades as Client
from mexc.core import timestamp
from mexc.sdk.core import SdkMixin, wrap_exceptions, spot_name

@dataclass
class MyTrades(SpotMyTrades, SdkMixin):
  @wrap_exceptions
  async def my_trades(
    self, instrument: str, /, *,
    start: datetime | None = None, end: datetime | None = None
  ) -> AsyncIterable[Sequence[Trade]]:
    async for trades in self.client.spot.my_trades_paged(instrument, start=start, end=end):
      yield [
        Trade(
          id=t['id'],
          price=Decimal(t['price']),
          qty=Decimal(t['qty']),
          time=timestamp.parse(t['time']),
          side='BUY' if t['isBuyer'] else 'SELL',
          maker=t['isMaker'],
          fee=Trade.Fee(
            asset=a,
            amount=Decimal(c),
          ) if (a := t.get('commissionAsset')) and (c := t.get('commission')) else None,
        )
        for t in trades
      ]

  async def spot_my_trades(self, base: str, quote: str, /, *, start: datetime | None = None, end: datetime | None = None) -> AsyncIterable[Sequence[Trade]]:
    instrument = spot_name(base, quote)
    async for trades in self.my_trades(instrument, start=start, end=end):
      yield trades