from typing_extensions import TypeVar, Any, Generic, TypedDict
from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass, field
from datetime import timedelta
import logging
import websockets

from ..exc import NetworkError

T = TypeVar('T')
M = TypeVar('M', default=Any)
R = TypeVar('R', default=Any)

logger = logging.getLogger('mexc.core.ws')

@dataclass
class Context:
  ws: websockets.ClientConnection
  pinger: asyncio.Task
  listener: asyncio.Task

@dataclass(kw_only=True)
class SocketClient(ABC):
  url: str
  timeout: timedelta = timedelta(seconds=10)
  ping_every: timedelta = timedelta(seconds=15)
  ctx_future: asyncio.Future[Context] = field(default_factory=asyncio.Future, init=False)
  open_lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)
  close_lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

  class Config(TypedDict, total=False):
    timeout: timedelta
    ping_every: timedelta

  @property
  async def ctx(self) -> Context:
    return await self.open()
  
  @property
  async def ws(self) -> websockets.ClientConnection:
    return (await self.ctx).ws
  
  async def __aenter__(self):
    await self.open()
    return self
  
  async def __aexit__(self, exc_type, exc_value, traceback):
    await self.close(await self.ctx, exc_type, exc_value, traceback)
  
  async def force_open(self):
    logger.info('Opening...')
    async def connect():
      try:
        return await websockets.connect(self.url, open_timeout=self.timeout.total_seconds())
      except websockets.exceptions.WebSocketException as e:
        raise NetworkError(f'Failed to connect to {self.url}') from e
    
    ws = await connect()
    logger.info('Connected!')
    return Context(
      ws=ws,
      listener=asyncio.create_task(self.listener(ws)),
      pinger=asyncio.create_task(self.pinger()),
    )

  async def open(self) -> Context:
    if self.open_lock.locked() or self.ctx_future.done():
      return await self.ctx_future

    async with self.open_lock:
      ctx = await self.force_open()
      self.ctx_future.set_result(ctx)
      return ctx

  async def force_close(self, ctx: Context, exc_type=None, exc_value=None, traceback=None):
    ctx.listener.cancel()
    ctx.pinger.cancel()
    await ctx.ws.__aexit__(exc_type, exc_value, traceback)

  async def close(self, ctx: Context, exc_type=None, exc_value=None, traceback=None):
    if not self.close_lock.locked():
      async with self.close_lock:
        await self.force_close(ctx, exc_type, exc_value, traceback)

  async def pinger(self):
    while True:
      await asyncio.sleep(self.ping_every.total_seconds())
      try:
        logger.debug('Pinging...')
        await asyncio.wait_for(self.ping(), self.timeout.total_seconds())
      except asyncio.TimeoutError:
        logger.warning('Ping timeout, restarting...')
        asyncio.create_task(self.restart())
        break

  async def listener(self, ws: websockets.ClientConnection, /):
    while True:
      try:
        msg = await ws.recv()
        logger.debug('Received: %s', msg)
        self.on_msg(msg)
      except websockets.exceptions.WebSocketException as e:
        logger.error('Error receiving message: %s', e)
        raise NetworkError('Error receiving message') from e

  async def wait_with_listener(self, fut: asyncio.Future[T]) -> T:
    """Wait for a future to complete, propagating any exceptions if the listener task fails or gets cancelled"""
    async def coro():
      return await fut
    ctx = await self.ctx
    task = asyncio.create_task(coro())
    done, _ = await asyncio.wait([task, ctx.listener], return_when='FIRST_COMPLETED')
    if ctx.listener in done:
      if (exc := ctx.listener.exception()) is not None:
        raise exc
      else:
        raise asyncio.CancelledError('Listener task got cancelled')
    return task.result()


  @abstractmethod
  def on_msg(self, msg: str | bytes):
    ...

  @abstractmethod
  async def ping(self):
    ...

class RpcSocketClient(SocketClient, Generic[M, R]):
  """Base request/response socket client."""
  @abstractmethod
  async def request(self, msg: M) -> R:
    ...
