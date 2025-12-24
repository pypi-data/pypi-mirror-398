from dataclasses import dataclass
from .place_order import PlaceOrder
from .edit_order import EditOrder
from .cancel_order import CancelOrder

@dataclass
class Trading(PlaceOrder, EditOrder, CancelOrder):
  ...