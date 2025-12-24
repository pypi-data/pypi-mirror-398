from typing_extensions import NamedTuple, Literal, AsyncIterable
from datetime import datetime
from mexc.core import timestamp as ts, validator
from mexc.spot.core import SpotMixin, ErrorResponse, raise_on_error

class Candle(NamedTuple):
  open_time: int
  open: str
  high: str
  low: str
  close: str
  volume: str
  close_time: int
  quote_volume: str

Response: type[list[Candle] | ErrorResponse] = list[Candle] | ErrorResponse # type: ignore
validate_response = validator(Response)

Interval = Literal['1m', '5m', '15m', '30m', '60m', '4h', '1d', '1W', '1M']

class Candles(SpotMixin):
  async def candles(
    self, symbol: str, *,
    interval: Interval,
    start: datetime | None = None, end: datetime | None = None,
    limit: int | None = None,
    validate: bool | None = None,
  ) -> list[Candle]:
    """Get klines (candles) for a given symbol.
    
    - `symbol`: The symbol being traded, e.g. `BTCUSDT`.
    - `interval`: The interval of the klines (default: 1m).
    - `start`: The start time to query. If given, only klines after this time will be returned.
    - `end`: The end time to query. If given, only klines before this time will be returned.
    - `limit`: The maximum number of klines to return (default: 500, max: 1000).
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [MEXC API docs](https://mexcdevelop.github.io/apidocs/spot_v3_en/#kline-candlestick-data)
    """
    params: dict = {'symbol': symbol, 'interval': interval}
    if limit is not None:
      params['limit'] = limit
    if start is not None:
      params['startTime'] = ts.dump(start)
    if end is not None:
      params['endTime'] = ts.dump(end)
    r = await self.request('GET', '/api/v3/klines', params=params)
    return self.output(r.text, validate_response, validate)

  
  async def candles_paged(
    self, symbol: str, *,
    interval: Interval,
    start: datetime, end: datetime,
    limit: int | None = None,
    validate: bool | None = None,
  ) -> AsyncIterable[list[Candle]]:
    last_time = ts.dump(start)
    while True:
      candles = await self.candles(symbol, interval=interval, start=ts.parse(last_time), end=end, limit=limit, validate=validate)
      candles = [c for c in candles if c.close_time > last_time]
      if not candles:
        break
      yield candles
      last_time = candles[-1].close_time