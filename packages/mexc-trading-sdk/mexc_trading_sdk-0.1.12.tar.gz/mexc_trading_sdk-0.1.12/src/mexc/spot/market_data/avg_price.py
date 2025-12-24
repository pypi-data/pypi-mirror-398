from mexc.core import validator, TypedDict
from mexc.spot.core import SpotMixin, ErrorResponse


class AveragePrice(TypedDict):
  price: str | None
  mins: int | None

Response: type[AveragePrice | ErrorResponse] = AveragePrice | ErrorResponse # type: ignore
validate_response = validator(Response)

class AvgPrice(SpotMixin):
  async def avg_price(
    self, symbol: str, *,
    validate: bool | None = None,
  ) -> AveragePrice:
    """Get the current average price for a given symbol.
    
    - `symbol`: The symbol being traded, e.g. `BTCUSDT`.
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [MEXC API docs](https://mexcdevelop.github.io/apidocs/spot_v3_en/#current-average-price)
    """
    params: dict = {'symbol': symbol}
    r = await self.request('GET', f'/api/v3/avgPrice', params=params)
    return self.output(r.text, validate_response, validate)