from typing_extensions import NamedTuple
from decimal import Decimal

from mexc.core import TypedDict, validator
from mexc.futures.core import FuturesMixin, FuturesResponse

class BookEntry(NamedTuple):
  price: Decimal
  qty: Decimal
  orders: int
  """Order count at this price level."""

class DepthData(TypedDict):
  asks: list[BookEntry]
  bids: list[BookEntry]
  version: int
  timestamp: int
  

Response: type[FuturesResponse[DepthData]] = FuturesResponse[DepthData] # type: ignore
validate_response = validator(Response)

class Depth(FuturesMixin):
  async def depth(
    self, symbol: str, *,
    limit: int | None = None,
    validate: bool | None = None,
  ) -> DepthData:
    """Get the order book for a given symbol.
    
    - `symbol`: The symbol being traded, e.g. `BTC_USDT`.
    - `interval`: The interval of the klines (default: 1m).
    - `start`: The start time to query. If given, only klines after this time will be returned.
    - `end`: The end time to query. If given, only klines before this time will be returned.
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [MEXC API docs](https://mexcdevelop.github.io/apidocs/contract_v1_en/#k-line-data)
    """
    params = {}
    if limit is not None:
      params['limit'] = limit
    r = await self.request('GET', f'/api/v1/contract/depth/{symbol}', params=params)
    return self.output(r.text, validate_response, validate)
