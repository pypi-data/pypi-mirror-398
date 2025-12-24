from bitget.core import AuthRouter
from .follower import Follower

class Spot(AuthRouter):
  follower: Follower