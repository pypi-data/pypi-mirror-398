from typing_extensions import NotRequired
from dataclasses import dataclass
from decimal import Decimal

from mexc.core import validator, TypedDict
from mexc.futures.core import AuthFuturesMixin, FuturesResponse

class Asset(TypedDict):
  currency: str
  positionMargin: Decimal
  availableBalance: Decimal
  cashBalance: Decimal
  frozenBalance: Decimal
  equity: Decimal
  unrealized: Decimal
  bonus: Decimal
  availableCash: Decimal
  availableOpen: Decimal
  debtAmount: Decimal
  contributeMarginAmount: Decimal
  vcoinId: str
  bonusExpireTime: NotRequired[int]
  recentExpireTime: NotRequired[int]
  recentExpireAmount: NotRequired[Decimal]
  
Response: type[FuturesResponse[list[Asset]]] = FuturesResponse[list[Asset]] # type: ignore
validate_response = validator(Response)

@dataclass
class Assets(AuthFuturesMixin):
  async def assets(self, *, validate: bool | None = None, recvWindow: int | None = None) -> list[Asset]:
    """Get futures assets of your account.

    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [MEXC API docs](https://mexcdevelop.github.io/apidocs/contract_v1_en/#get-all-informations-of-user-39-s-asset)
    """
    headers = {}
    if recvWindow is not None:
      headers['Recv-Window'] = str(recvWindow)
    r = await self.signed_request('GET', '/api/v1/private/account/assets', headers=headers)
    return self.output(r.text, validate_response, validate)