from bitget.core import AuthRouter
from .assets import Assets
from .tax import Tax

class Common(AuthRouter):
  assets: Assets
  tax: Tax