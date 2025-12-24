from typing_extensions import Literal
from dataclasses import dataclass

from trading_sdk.types import fmt_num
from trading_sdk.market.trading.place_order import SpotPlaceOrder, Order as OrderTDK, OrderState

from mexc.spot.trading.place_order import Order, LimitOrder, MarketOrder
from mexc.sdk.core import SdkMixin, wrap_exceptions, spot_name
from ..user_data.query_order import query_order

def parse_order(order: OrderTDK) -> Order:
  if order['type'] == 'LIMIT':
    return LimitOrder(
      type='LIMIT',
      side=order['side'],
      price=fmt_num(order['price']),
      quantity=fmt_num(order['qty'])
    )
  elif order['type'] == 'MARKET':
    return MarketOrder(
      type='MARKET',
      side=order['side'],
      quantity=fmt_num(order['qty'])
    )

@dataclass
class PlaceOrder(SpotPlaceOrder, SdkMixin):
  @wrap_exceptions
  async def _place_order(self, instrument: str, /, *, order: OrderTDK, response: Literal['id', 'state'] = 'id') -> str | OrderState:
    r = await self.client.spot.place_order(instrument, parse_order(order))
    if response == 'id':
      return r['orderId']
    else:
      return await query_order(self.client.spot, instrument, id=r['orderId'])

  async def _spot_place_order(self, base: str, quote: str, /, *, order: OrderTDK, response: Literal['id', 'state'] = 'id') -> str | OrderState:
    instrument = spot_name(base, quote)
    return await self.place_order(instrument, order=order, response=response)
  