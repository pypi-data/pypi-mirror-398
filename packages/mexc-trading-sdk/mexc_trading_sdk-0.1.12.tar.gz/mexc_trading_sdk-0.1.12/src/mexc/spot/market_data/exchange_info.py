from typing_extensions import TypeVar

from mexc.core import validator, TypedDict
from mexc.spot.core import SpotMixin, ErrorResponse

S = TypeVar('S', bound=str, default=str)

class Info(TypedDict):
  symbol: str
  baseAsset: str
  baseAssetPrecision: int
  quoteAsset: str
  quotePrecision: int
  quoteAssetPrecision: int
  maxQuoteAmount: str
  quoteAmountPrecision: str
  baseSizePrecision: str

class OkResponse(TypedDict):
  timezone: str
  serverTime: int
  symbols: list[Info]

Response: type[OkResponse | ErrorResponse] = OkResponse | ErrorResponse # type: ignore
validate_response = validator(Response)

class ExchangeInfo(SpotMixin):
  async def exchange_info(
    self, *symbols: S, validate: bool | None = None,
  ) -> dict[S, Info]:
    """Get the exchange information for the given symbol, symbols, or all symbols (if none provided)
    
    - `symbols`: The symbols to get information for. If none provided, all symbols are returned.
    - `validate`: Whether to validate the response against the expected schema (default: True).
    """
    params = {}
    if len(symbols) == 1:
      params['symbol'] = symbols[0]
    elif len(symbols) > 1:
      params['symbols'] = ','.join(symbols)
    r = await self.request('GET', '/api/v3/exchangeInfo', params=params)
    obj = self.output(r.text, validate_response, validate)
    dct: dict[str, Info] = {s['symbol']: s for s in obj['symbols']}
    return dct # type: ignore