from typing_extensions import NotRequired

from mexc.core import timestamp as ts, validator, TypedDict
from mexc.spot.core import AuthSpotMixin, ErrorResponse

class Balance(TypedDict):
  asset: str
  free: str
  locked: str

class AccountInfo(TypedDict):
  canTrade: bool
  canWithdraw: bool
  canDeposit: bool
  updateTime: NotRequired[int | None]
  accountType: str
  permissions: list[str]
  balances: list[Balance]

Response: type[AccountInfo | ErrorResponse] = AccountInfo | ErrorResponse # type: ignore
validate_response = validator(Response)

class Account(AuthSpotMixin):
  async def account(
    self, *, recvWindow: int | None = None,
    timestamp: int | None = None, validate: bool | None = None,
  ) -> AccountInfo:
    """Get account information (of your account), including trading/deposit/withdrawal permissions and asset balances.
    
    - `recvWindow`: If the server receives the request after `timestamp + recvWindow`, it will be rejected (default: 5000).
    - `timestamp`: The timestamp for the request, in milliseconds (default: now).
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [MEXC API docs](https://mexcdevelop.github.io/apidocs/spot_v3_en/#account-information)
    """
    params: dict = {
      'timestamp': timestamp or ts.now(),
    }
    if recvWindow is not None:
      params['recvWindow'] = recvWindow
    r = await self.signed_request('GET', '/api/v3/account', params=params)
    return self.output(r.text, validate_response, validate)