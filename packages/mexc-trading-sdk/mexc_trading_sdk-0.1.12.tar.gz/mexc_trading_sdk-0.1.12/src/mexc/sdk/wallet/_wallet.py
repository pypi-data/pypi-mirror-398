from dataclasses import dataclass
from .withdrawal_history import WithdrawalHistory
from .deposit_history import DepositHistory
from .withdrawal_methods import WithdrawalMethods

@dataclass
class Wallet(WithdrawalHistory, DepositHistory, WithdrawalMethods):
  ...