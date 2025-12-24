from typing_extensions import Unpack
from dataclasses import dataclass
import asyncio
import os

from mexc.spot.core import MEXC_SPOT_API_BASE, AuthHttpClient
from .market_data import MarketData
from .trading import Trading
from .user_data import UserData
from .wallet import Wallet
from .streams import Streams, MEXC_SPOT_SOCKET_URL

@dataclass
class Spot(MarketData, Trading, UserData, Wallet):
  streams: Streams

  def __init__(
    self, *,
    api_url: str = MEXC_SPOT_API_BASE,
    ws_url: str = MEXC_SPOT_SOCKET_URL,
    auth_http: AuthHttpClient,
    default_validate: bool = True,
    **kwargs: Unpack[Streams.Config],
  ):
    self.default_validate = default_validate
    self.base_url = api_url
    self.http = self.auth_http = auth_http
    self.streams = Streams(api_url=api_url, ws_url=ws_url, auth_http=auth_http, **kwargs)

  @classmethod
  def new(
    cls, api_key: str | None = None, api_secret: str | None = None, *,
    base_url: str = MEXC_SPOT_API_BASE,
    ws_url: str = MEXC_SPOT_SOCKET_URL,
    default_validate: bool = True,
    **kwargs: Unpack[Streams.Config],
  ):
    if api_key is None:
      api_key = os.environ['MEXC_ACCESS_KEY']
    if api_secret is None:
      api_secret = os.environ['MEXC_SECRET_KEY']
    auth_http = AuthHttpClient(api_key=api_key, api_secret=api_secret)
    return cls(api_url=base_url, ws_url=ws_url, auth_http=auth_http, default_validate=default_validate, **kwargs)

  async def __aexit__(self, exc_type, exc_value, traceback):
    await asyncio.gather(
      super().__aexit__(exc_type, exc_value, traceback),
      self.streams.__aexit__(exc_type, exc_value, traceback),
    )