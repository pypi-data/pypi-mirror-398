from typing_extensions import Unpack
from dataclasses import dataclass, field
import asyncio
import os

from mexc.core import timestamp as ts, AuthError, ValidationMixin
from mexc.futures.core import sign
from .client import StreamsClient, Response, MEXC_FUTURES_SOCKET_URL

@dataclass
class AuthedStreamsClient(StreamsClient):
  api_key: str
  api_secret: str
  auth_lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)
  authorized: asyncio.Event = field(default_factory=asyncio.Event, init=False)

  @classmethod
  def new(
    cls, api_key: str | None = None, api_secret: str | None = None, *,
    url: str = MEXC_FUTURES_SOCKET_URL,
    **kwargs: Unpack[StreamsClient.Config],
  ):
    if api_key is None:
      api_key = os.environ['MEXC_ACCESS_KEY']
    if api_secret is None:
      api_secret = os.environ['MEXC_SECRET_KEY']
    return cls(api_key=api_key, api_secret=api_secret, url=url, **kwargs)

  @property
  async def authed(self):
    await self.authenticate()

  async def authenticate(self):
    if self.auth_lock.locked() or self.authorized.is_set():
      return

    async with self.auth_lock:
      await self.login()
      self.authorized.set()

  async def login(self):
    t = ts.now()
    signature = sign(f'{self.api_key}{t}', secret=self.api_secret)
    r: Response = await self.request({
      'method': 'login',
      'param': {
        'apiKey': self.api_key,
        'reqTime': t,
        'signature': signature,
      },
    })
    if r['data'] != 'success':
      raise AuthError(f'Failed to login: {r}')
    return r
  
  async def request_subscription(self, channel: str, params=None):
    await self.authed
    return await super().request_subscription(channel, params)
  #   await self.ctx # ensure connection is open
  #   # all channels are auto-subscribed
  
  async def request_unsubscription(self, channel: str):
    await self.authed
    return await super().request_unsubscription(channel)
  #   await self.ctx # ensure connection is open

@dataclass
class AuthedStreamsMixin(ValidationMixin):
  auth_ws: AuthedStreamsClient

  async def __aenter__(self):
    await self.auth_ws.__aenter__()
    return self
  
  async def __aexit__(self, exc_type, exc_value, traceback):
    await self.auth_ws.__aexit__(exc_type, exc_value, traceback)