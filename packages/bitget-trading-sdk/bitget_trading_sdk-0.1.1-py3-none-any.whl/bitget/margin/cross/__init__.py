from bitget.core import AuthRouter
from .account import Account
from .trade import Trade

class Cross(AuthRouter):
  account: Account
  trade: Trade