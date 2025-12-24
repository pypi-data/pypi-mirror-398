from bitget.core import AuthRouter
from .account import Account
from .position import Position
from .trade import Trade

class Futures(AuthRouter):
  account: Account
  position: Position
  trade: Trade