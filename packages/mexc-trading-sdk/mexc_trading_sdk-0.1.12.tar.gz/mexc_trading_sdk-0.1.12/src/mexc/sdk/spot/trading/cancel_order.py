from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from trading_sdk.types import ApiError

from trading_sdk.market.trading.cancel_order import SpotCancelOrder
from trading_sdk.market.user_data.query_order import OrderState

from mexc.sdk.core import SdkMixin, wrap_exceptions, spot_name

@dataclass
class CancelOrder(SpotCancelOrder, SdkMixin):
  @wrap_exceptions
  async def cancel_order(self, instrument: str, /, *, id: str) -> OrderState:
    r = await self.client.spot.cancel_order(instrument, orderId=id)
    return OrderState(
      id=r['orderId'],
      price=Decimal(r['price']),
      qty=Decimal(r['origQty']),
      filled_qty=Decimal(r['executedQty']),
      side=r['side'],
      time=datetime.now(),
      status=r['status']
    )

  async def spot_cancel_order(self, base: str, quote: str, /, *, id: str) -> OrderState:
    instrument = spot_name(base, quote)
    return await self.cancel_order(instrument, id=id)