from typing_extensions import Unpack
from dataclasses import dataclass
import os

from .core import StreamsClient, AuthedStreamsClient, MEXC_FUTURES_SOCKET_URL
from .user import UserStreams
from .market import MarketStreams

@dataclass
class Streams(
  UserStreams,
  MarketStreams,
):
  @classmethod
  def new(
    cls, api_key: str | None = None, api_secret: str | None = None, *,
    url: str = MEXC_FUTURES_SOCKET_URL,
    default_validate: bool = True,
    **kwargs: Unpack[StreamsClient.Config],
  ):
    if api_key is None:
      api_key = os.environ['MEXC_ACCESS_KEY']
    if api_secret is None:
      api_secret = os.environ['MEXC_SECRET_KEY']
    ws = AuthedStreamsClient(api_key=api_key, api_secret=api_secret, url=url, **kwargs)
    return cls(auth_ws=ws, ws=ws, default_validate=default_validate)
  