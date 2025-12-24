from mexc.core import validator, TypedDict
from mexc.spot.core import SpotMixin, ErrorResponse

class ServerTime(TypedDict):
  serverTime: int

Response: type[ServerTime | ErrorResponse] = ServerTime | ErrorResponse # type: ignore
validate_response = validator(Response)

class Time(SpotMixin):
  async def time(self, validate: bool | None = None) -> ServerTime:
    """Get the server time.
    
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [MEXC API docs](https://mexcdevelop.github.io/apidocs/spot_v3_en/#check-server-time)
    """
    r = await self.request('GET', '/api/v3/time')
    return self.output(r.text, validate_response, validate)