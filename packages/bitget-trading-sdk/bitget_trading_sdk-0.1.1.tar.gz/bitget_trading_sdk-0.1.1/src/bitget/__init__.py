from bitget.core import AuthRouter
from .common import Common
from .copy import Copy
from .earn import Earn
from .futures import Futures
from .margin import Margin
from .spot import Spot

class Bitget(AuthRouter):
  common: Common
  copy: Copy
  earn: Earn
  futures: Futures
  margin: Margin
  spot: Spot