from typing_extensions import TypeVar, Mapping, Callable, Awaitable
import time
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_DOWN, ROUND_FLOOR

T = TypeVar('T')
D = TypeVar('D', bound=Mapping)

def filter_kwargs(Params: type[D], params: D | dict) -> D:
  return { k: params[k] for k in getattr(Params, '__annotations__', {}) if k in params } # type: ignore

class timestamp:
  @staticmethod
  def parse(time: int) -> datetime:
    return datetime.fromtimestamp(time/1e3)
  
  @staticmethod
  def dump(dt: datetime) -> int:
    return int(1e3*dt.timestamp())
  
  @staticmethod
  def now() -> int:
    return int(time.time() * 1e3)

def round2tick(x: Decimal, tick_size: Decimal) -> Decimal:
  r = (x / tick_size).quantize(Decimal('1.'), rounding=ROUND_HALF_DOWN) * tick_size
  return r.normalize()

def trunc2tick(x: Decimal, tick_size: Decimal) -> Decimal:
  r = (x / tick_size).to_integral_value(rounding=ROUND_FLOOR) * tick_size
  return r.normalize()

def json():
  try:
    import orjson
    return orjson
  except ImportError:
    import json
    return json
    
def cacher(ttl: timedelta = timedelta(seconds=10)):
  value = None
  last = None
  async def cached_fn(fn: Callable[[], Awaitable[T]]) -> T:
    nonlocal value, last
    if last is None or datetime.now() - last > ttl:
      value = await fn()
      last = datetime.now()
    return value # type: ignore

  return cached_fn