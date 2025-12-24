from dataclasses import dataclass
from decimal import Decimal

from trading_sdk.types import ApiError
from trading_sdk.wallet.withdrawal_methods import WithdrawalMethod, WithdrawalMethods as WithdrawalMethodsTDK

from mexc.core.util import cacher
from mexc.sdk.core import SdkMixin, wrap_exceptions

cache = cacher()

@dataclass
class WithdrawalMethods(WithdrawalMethodsTDK, SdkMixin):
  @wrap_exceptions
  async def withdrawal_methods(self, asset: str):
    currencies = await cache(self.client.spot.currency_info)
    for c in currencies:
      if c['coin'] == asset:
        return [
          WithdrawalMethod(
            network=m['netWork'], # type: ignore
            contract_address=m.get('contract'),
            fee=WithdrawalMethod.Fee(
              asset=asset,
              amount=Decimal(m['withdrawFee']),
            ),
          )
          for m in c['networkList']
            if m['withdrawEnable']
        ]

    raise ApiError(f'Asset "{asset}" not found')