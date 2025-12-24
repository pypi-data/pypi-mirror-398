from bitget.core import AuthRouter
from .futures import Futures
from .spot import Spot

class Copy(AuthRouter):
  futures: Futures
  spot: Spot