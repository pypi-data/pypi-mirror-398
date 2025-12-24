from typing_extensions import NotRequired
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from enum import Enum

from mexc.core import validator, TypedDict
from mexc.futures.core import AuthFuturesMixin, FuturesResponse

class PositionType(Enum):
  long = 1
  short = 2

class OpenType(Enum):
  isolated = 1
  cross = 2

class Position(TypedDict):
  positionId: int
  symbol: str
  positionType: int
  openType: int
  state: int
  holdVol: Decimal
  frozenVol: Decimal
  closeAvgPrice: Decimal
  openAvgPrice: Decimal
  liquidatePrice: Decimal
  oim: Decimal
  im: Decimal
  holdFee: Decimal
  realised: Decimal
  adlLevel: NotRequired[int]
  leverage: int
  createTime: datetime
  updateTime: datetime
  autoAddIm: bool
  
Response: type[FuturesResponse[list[Position]]] = FuturesResponse[list[Position]] # type: ignore
validate_response = validator(Response)

@dataclass
class Positions(AuthFuturesMixin):
  async def positions(
    self, symbol: str | None = None, *,
    validate: bool | None = None,
  ) -> list[Position]:
    """Get futures positions of your account.

    - `symbol`: The symbol being traded, e.g. `BTCUSDT`. If not provided, positions for all symbols will be returned.
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [MEXC API docs](https://mexcdevelop.github.io/apidocs/contract_v1_en/#get-the-user-39-s-current-holding-position)
    """
    params = {}
    if symbol is not None:
      params['symbol'] = symbol
    r = await self.signed_request('GET', '/api/v1/private/position/open_positions', params=params)
    return self.output(r.text, validate_response, validate)