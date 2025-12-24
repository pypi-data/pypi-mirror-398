from typing_extensions import AsyncIterable
from decimal import Decimal

from mexc.core import validator, TypedDict
from mexc.futures.core import FuturesMixin, FuturesResponse

class FundingRate(TypedDict):
  symbol: str
  fundingRate: Decimal
  settleTime: int
  collectCycle: int
  """Settlement period in hours."""

class Data(TypedDict):
  pageSize: int
  totalCount: int
  totalPage: int
  currentPage: int
  resultList: list[FundingRate]

Response: type[FuturesResponse[Data]] = FuturesResponse[Data] # type: ignore
validate_response = validator(Response)

class FundingRateHistory(FuturesMixin):
  async def funding_rate_history(
    self, symbol: str, *,
    page_num: int | None = None,
    page_size: int | None = None,
    validate: bool | None = None
  ) -> Data:
    """Get the funding rate history for a given symbol.
    
    - `symbol`: The symbol being traded, e.g. `BTC_USDT`.
    - `page_num`: The page number (default: 1).
    - `page_size`: The page size (default: 20, max: 1000).
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [MEXC API docs](https://mexcdevelop.github.io/apidocs/contract_v1_en/#get-contract-funding-rate-history)
    """
    params: dict = {'symbol': symbol}
    if page_num is not None:
      params['page_num'] = page_num
    if page_size is not None:
      params['page_size'] = page_size
    r = await self.request('GET', '/api/v1/contract/funding_rate/history', params=params)
    return self.output(r.text, validate_response, validate)

  
  async def funding_rate_history_paged(
    self, symbol: str, *,
    page_size: int | None = None,
    validate: bool | None = None
  ) -> AsyncIterable[list[FundingRate]]:
    page_num = 1
    while True:
      r = await self.funding_rate_history(symbol, page_num=page_num, page_size=page_size, validate=validate)
      yield r['resultList']
      page_num += 1
      if page_num >= r['totalPage']:
        break