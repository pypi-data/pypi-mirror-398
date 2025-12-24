from dataclasses import dataclass
from enum import Enum
from mexc.core import OrderSide
from mexc.spot.streams.core import UserStreamsMixin

class TradeType(Enum):
  BUY = 1
  SELL = 2

  def fmt(self) -> OrderSide:
    match self:
      case TradeType.BUY:
        return 'BUY'
      case TradeType.SELL:
        return 'SELL'

@dataclass
class Trade:
  symbol: str
  price: str
  quote_amount: str
  base_qty: str
  side: OrderSide
  tradeId: str
  orderId: str
  fee_amount: str
  fee_currency: str
  time: int

  @classmethod
  def from_proto(cls, proto):
    deal = proto.privateDeals
    return cls(
      symbol=proto.symbol,
      price=deal.price,
      base_qty=deal.quantity,
      quote_amount=deal.amount,
      side=TradeType(deal.tradeType).fmt(),
      tradeId=deal.tradeId,
      orderId=deal.orderId,
      fee_amount=deal.feeAmount,
      fee_currency=deal.feeCurrency,
      time=deal.time
    )

@dataclass
class MyTrades(UserStreamsMixin):
  async def my_trades(self):
    """Subscribe to your trades.
    
    > [MEXC API docs](https://mexcdevelop.github.io/apidocs/spot_v3_en/#spot-account-deals)
    """
    async for msg in self.authed_subscribe('spot@private.deals.v3.api.pb'):
      yield Trade.from_proto(msg)