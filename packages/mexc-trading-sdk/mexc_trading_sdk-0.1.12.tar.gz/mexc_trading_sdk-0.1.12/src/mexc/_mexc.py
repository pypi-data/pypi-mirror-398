import os
from dataclasses import dataclass
import asyncio

from .spot import Spot
from .futures import Futures

@dataclass
class MEXC:
  spot: Spot
  futures: Futures

  @classmethod
  def new(
    cls, api_key: str | None = None, api_secret: str | None = None, *,
    validate: bool = True,
  ):
    if api_key is None:
      api_key = os.environ['MEXC_ACCESS_KEY']
    if api_secret is None:
      api_secret = os.environ['MEXC_SECRET_KEY']
    return cls(
      spot=Spot.new(api_key=api_key, api_secret=api_secret, default_validate=validate),
      futures=Futures.new(api_key=api_key, api_secret=api_secret, default_validate=validate),
    )
  
  async def __aenter__(self):
    await asyncio.gather(
      self.spot.__aenter__(),
      self.futures.__aenter__(),
    )
    return self
  
  async def __aexit__(self, exc_type, exc_value, traceback):
    await asyncio.gather(
      self.spot.__aexit__(exc_type, exc_value, traceback),
      self.futures.__aexit__(exc_type, exc_value, traceback),
    )