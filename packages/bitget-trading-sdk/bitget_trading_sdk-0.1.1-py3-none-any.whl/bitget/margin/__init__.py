from bitget.core import AuthRouter
from .cross import Cross
from .isolated import Isolated

class Margin(AuthRouter):
  cross: Cross
  isolated: Isolated