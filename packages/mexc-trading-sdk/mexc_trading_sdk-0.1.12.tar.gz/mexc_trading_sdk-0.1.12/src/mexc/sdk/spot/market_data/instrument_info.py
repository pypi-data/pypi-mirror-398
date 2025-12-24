from dataclasses import dataclass
from decimal import Decimal

from trading_sdk.types import ApiError
from trading_sdk.market.market_data.instrument_info import SpotInfo, Info

from mexc.sdk.core import SdkMixin, wrap_exceptions, spot_name

@dataclass
class InstrumentInfo(SpotInfo, SdkMixin):
  @wrap_exceptions
  async def instrument_info(self, instrument: str, /) -> Info:
    r = await self.client.spot.exchange_info(instrument)
    info = r[instrument]
    return Info(
      tick_size=Decimal(1) / Decimal(10 ** info['quotePrecision']),
      step_size=Decimal(info['baseSizePrecision']),
    )

  async def spot_info(self, base: str, quote: str, /) -> Info:
    instrument = spot_name(base, quote)
    return await self.instrument_info(instrument)