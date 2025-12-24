from .bot import Bot
from .funding import Funding
from .overview import Overview

class Assets(Bot, Funding, Overview):
  ...