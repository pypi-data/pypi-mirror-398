from bitget.core import AuthRouter
from .follower import Follower

class Futures(AuthRouter):
  follower: Follower