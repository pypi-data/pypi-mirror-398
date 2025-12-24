from typing_extensions import Literal, AsyncIterable
from datetime import datetime

from mexc.core import TypedDict, validator, ApiError
from mexc.futures.core import FuturesMixin, FuturesResponse

class CandleData(TypedDict):
  time: list[int]
  """Start times of the candles. UNIX timestamp in **seconds** (not milliseconds as most endpoints)."""
  open: list[float]
  close: list[float]
  high: list[float]
  low: list[float]
  vol: list[float]
  amount: list[float]
  realOpen: list[float]
  realClose: list[float]
  realHigh: list[float]
  realLow: list[float]

Response: type[FuturesResponse[CandleData]] = FuturesResponse[CandleData] # type: ignore
validate_response = validator(Response)

Interval = Literal['Min1', 'Min5', 'Min15', 'Min30', 'Min60', 'Hour4', 'Day1', 'Week1']

class Candles(FuturesMixin):
  async def candles(
    self, symbol: str, *,
    interval: Interval | None = None,
    start: datetime | None = None, end: datetime | None = None,
    validate: bool | None = None,
  ) -> CandleData:
    """Get klines (candles) for a given symbol. Returns at most 2000 candles.
    
    - `symbol`: The symbol being traded, e.g. `BTC_USDT`.
    - `interval`: The interval of the klines (default: 1m).
    - `start`: The start time to query. If given, only klines after this time will be returned.
    - `end`: The end time to query. If given, only klines before this time will be returned.
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [MEXC API docs](https://mexcdevelop.github.io/apidocs/contract_v1_en/#k-line-data)
    """
    params = {}
    if interval is not None:
      params['interval'] = interval
    if start is not None:
      params['start'] = int(start.timestamp())
    if end is not None:
      params['end'] = int(end.timestamp())
    r = await self.request('GET', f'/api/v1/contract/kline/{symbol}', params=params)
    return self.output(r.text, validate_response, validate)

  async def candles_paged(
    self, symbol: str, *,
    interval: Interval,
    start: datetime, end: datetime,
    validate: bool | None = None,
  ) -> AsyncIterable[CandleData]:
    end_time = int(end.timestamp())
    while True:
      c = await self.candles(symbol, start=start, end=datetime.fromtimestamp(end_time), interval=interval, validate=validate)
      out = CandleData(
        time=[],
        open=[],
        close=[],
        high=[],
        low=[],
        vol=[],
        amount=[],
        realOpen=[],
        realClose=[],
        realHigh=[],
        realLow=[],
      )
      for i in range(len(c['close'])):
        if c['time'][i] < end_time:
          out['close'].append(c['close'][i])
          out['high'].append(c['high'][i])
          out['low'].append(c['low'][i])
          out['open'].append(c['open'][i])
          out['vol'].append(c['vol'][i])
          out['amount'].append(c['amount'][i])
          out['realOpen'].append(c['realOpen'][i])
          out['realClose'].append(c['realClose'][i])
          out['realHigh'].append(c['realHigh'][i])
          out['realLow'].append(c['realLow'][i])
          out['time'].append(c['time'][i])

      if len(out['time']) == 0:
        break
      
      out['close'].reverse()
      out['high'].reverse()
      out['realClose'].reverse()
      out['realHigh'].reverse()
      out['realLow'].reverse()
      out['low'].reverse()
      out['open'].reverse()
      out['vol'].reverse()
      out['amount'].reverse()
      out['realOpen'].reverse()
      out['realClose'].reverse()
      out['realHigh'].reverse()
      out['realLow'].reverse()
      yield out
      end_time = min(out['time'])