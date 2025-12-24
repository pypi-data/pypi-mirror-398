from typing_extensions import TypedDict, TypeVar, Generic, Any, Literal
from dataclasses import dataclass, field
from mexc.core import HttpMixin, ValidationMixin, validator
from .auth import AuthHttpMixin

T = TypeVar('T', default=Any)

class OkResponse(TypedDict, Generic[T]):
  code: int
  success: Literal[True]
  data: T

class ErrResponse(TypedDict):
  code: int
  success: Literal[False]
  message: str

FuturesResponse = OkResponse[T] | ErrResponse

def raise_on_error(r: FuturesResponse[T]) -> T:
  from mexc.core import ApiError
  if 'data' not in r:
    raise ApiError(r)
  return r['data']

MEXC_FUTURES_API_BASE = 'https://contract.mexc.com'

class BaseMixin(ValidationMixin):
  def output(self, data, validator: validator[FuturesResponse[T]], validate: bool | None) -> T:
    """Parse the data (optionally validating) and raise if the response is an error."""
    obj = validator(data) if self.validate(validate) else data
    return raise_on_error(obj)

@dataclass
class FuturesMixin(HttpMixin, BaseMixin):
  base_url: str = field(default=MEXC_FUTURES_API_BASE, kw_only=True)

@dataclass
class AuthFuturesMixin(AuthHttpMixin, BaseMixin):
  base_url: str = field(default=MEXC_FUTURES_API_BASE, kw_only=True)
