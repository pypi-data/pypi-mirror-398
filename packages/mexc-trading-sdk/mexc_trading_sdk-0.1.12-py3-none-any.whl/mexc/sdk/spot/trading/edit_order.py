from dataclasses import dataclass
from decimal import Decimal

from trading_sdk.types import Num, fmt_num, ApiError
from trading_sdk.market.trading.edit_order import SpotEditOrder

from mexc.spot.trading.place_order import LimitOrder
from mexc.sdk.core import SdkMixin, wrap_exceptions, spot_name

@dataclass
class EditOrder(SpotEditOrder, SdkMixin):
  @wrap_exceptions
  async def edit_order(self, instrument: str, /, *, id: str, qty: Num | None = None, price: Num | None = None) -> str:
    state = await self.client.spot.cancel_order(instrument, orderId=id)

    if price is None:
      price = state['price']

    if qty is None:
      qty = Decimal(state['origQty']) - Decimal(state['executedQty'])

    r = await self.client.spot.place_order(instrument, LimitOrder(
      type='LIMIT',
      side=state['side'],
      price=fmt_num(price),
      quantity=fmt_num(qty)
    ))
    return r['orderId']

  
  async def spot_edit_order(self, base: str, quote: str, /, *, id: str, qty: Num | None = None, price: Num | None = None) -> str:
    instrument = spot_name(base, quote)
    return await self.edit_order(instrument, id=id, qty=qty, price=price)