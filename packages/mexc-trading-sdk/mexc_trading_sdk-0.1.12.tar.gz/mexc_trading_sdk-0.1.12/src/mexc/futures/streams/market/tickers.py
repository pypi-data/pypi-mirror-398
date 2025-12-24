from typing_extensions import AsyncIterable
from dataclasses import dataclass

from mexc.core import validator, TypedDict
from mexc.futures.streams.core import StreamsMixin

class Ticker(TypedDict):
  ...

validate_response = validator(list[Ticker])

@dataclass
class Tickers(StreamsMixin):
  async def tickers(self, *, validate: bool = True) -> AsyncIterable[list[Ticker]]:
    """Subscribe to all future instrument tickers.

    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [MEXC API docs](https://mexcdevelop.github.io/apidocs/contract_v1_en/#filter-subscription)
    """
    async for msg in self.ws.subscribe('tickers'):
      yield validate_response(msg) if self.validate(validate) else msg