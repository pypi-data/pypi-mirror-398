from dataclasses import dataclass
from .balances import Balances
from .my_funding_history import MyFundingHistory
from .my_trades import MyTrades
from .positions import Positions

@dataclass
class UserData(Balances, MyFundingHistory, MyTrades, Positions):
  ...