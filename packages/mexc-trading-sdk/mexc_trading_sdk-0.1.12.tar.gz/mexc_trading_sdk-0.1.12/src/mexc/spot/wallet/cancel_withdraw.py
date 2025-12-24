from mexc.core import timestamp as ts, validator, TypedDict
from mexc.spot.core import AuthSpotMixin, ErrorResponse

class WithdrawId(TypedDict):
  id: str

Response: type[WithdrawId | ErrorResponse] = WithdrawId | ErrorResponse # type: ignore
validate_response = validator(Response)

class CancelWithdraw(AuthSpotMixin):
  async def cancel_withdraw(
    self, id: str, *,
    timestamp: int | None = None, validate: bool | None = None,
  ) -> WithdrawId:
    """Cancel a withdrawal, given its ID.
    
    - `id`: The ID of the withdrawal to cancel. Will be returned by the `withdraw` endpoint.
    - `timestamp`: The timestamp for the request, in milliseconds (default: now).
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [MEXC API docs](https://mexcdevelop.github.io/apidocs/spot_v3_en/#cancel-withdraw)
    """
    params = {
      'id': id, 'timestamp': timestamp or ts.now(),
    }
    r = await self.signed_request('DELETE', '/api/v3/capital/withdraw', params=params)
    return self.output(r.text, validate_response, validate)
