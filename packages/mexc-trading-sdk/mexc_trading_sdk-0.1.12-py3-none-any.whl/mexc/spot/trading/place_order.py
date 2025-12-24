from typing_extensions import Literal

from mexc.core import timestamp as ts, validator, TypedDict, OrderSide, OrderType
from mexc.spot.core import AuthSpotMixin, ErrorResponse

class BaseOrder(TypedDict):
  side: OrderSide

class LimitOrder(BaseOrder):
  type: Literal['LIMIT', 'LIMIT_MAKER']
  price: str
  quantity: str

class MarketOrder(BaseOrder):
  type: Literal['MARKET']
  quantity: str

class QuoteMarketOrder(BaseOrder):
  type: Literal['MARKET']
  quoteOrderQty: str

Order = LimitOrder | MarketOrder | QuoteMarketOrder

class NewOrder(TypedDict):
  symbol: str
  orderId: str
  orderListId: int
  price: str
  origQty: str
  type: OrderType
  side: OrderSide
  transactTime: int

Response: type[NewOrder | ErrorResponse] = NewOrder | ErrorResponse # type: ignore
validate_response = validator(Response)

class PlaceOrder(AuthSpotMixin):
  async def place_order(
    self, symbol: str, order: Order, *,
    recvWindow: int | None = None,
    timestamp: int | None = None,
    validate: bool | None = None,
  ) -> NewOrder:
    """Place a new order on the spot market.
    
    - `symbol`: The symbol to trade, e.g. `BTCUSDT`
    - `order`: The order to place.
    - `recvWindow`: If the server receives the request after `timestamp + recvWindow`, it will be rejected (default: 5000).
    - `timestamp`: The timestamp for the request, in milliseconds (default: now).
    - `validate`: Whether to validate the response against the expected schema (default: True).
    
    > [MEXC API docs](https://mexcdevelop.github.io/apidocs/spot_v3_en/#new-order)
    """
    params = order | {
      'symbol': symbol,
      'timestamp': timestamp or ts.now(),
    }
    if recvWindow is not None:
      params['recvWindow'] = recvWindow
    r = await self.signed_request('POST', '/api/v3/order', params=params)
    return self.output(r.text, validate_response, validate)