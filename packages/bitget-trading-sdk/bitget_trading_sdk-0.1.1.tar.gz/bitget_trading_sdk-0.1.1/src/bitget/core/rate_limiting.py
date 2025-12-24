from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps
import asyncio

def rate_limit(max_freq: timedelta):
  def decorator(fn):
    lasts: defaultdict[str, datetime] = defaultdict(lambda: datetime.min)

    @wraps(fn)
    async def wrapper(self, *args, **kwargs):
      nonlocal lasts
      key = str(id(self))
      diff = datetime.now() - lasts[key]
      delay = (max_freq - diff).total_seconds()
      if delay > 0:
        await asyncio.sleep(delay)
      r = await fn(self, *args, **kwargs)
      lasts[key] = datetime.now()
      return r

    return wrapper
  return decorator
