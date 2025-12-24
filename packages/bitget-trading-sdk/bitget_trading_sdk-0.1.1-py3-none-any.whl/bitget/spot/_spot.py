from bitget.core import AuthRouter
from .account import Account
from .trade import Trade

class Spot(AuthRouter):
  account: Account
  trade: Trade