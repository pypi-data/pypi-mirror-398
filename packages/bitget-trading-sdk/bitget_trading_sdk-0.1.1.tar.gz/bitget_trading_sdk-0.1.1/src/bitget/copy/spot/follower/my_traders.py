from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

from bitget.core import AuthEndpoint, validator, TypedDict, Timestamp, timestamp as ts

class Trader(TypedDict):
  certificationType: str
  """Certification type: Uncertified, Certified"""
  traderId: str
  """Trader ID"""
  traderName: str
  """Alias"""
  maxFollowLimit: int
  """Maximum number of elite traders to follow"""
  bgbMaxFollowLimit: int
  """Maximum number of elite traders to follow granted by BGB holdings"""
  followCount: int
  """Number of elite traders that you have followed"""
  bgbFollowCount: int
  """Number of elite traders that you have followed granted by BGB holdings"""
  traceTotalMarginAmount: Decimal
  """Total opening margin"""
  traceTotalNetProfit: Decimal
  """Total net profit"""
  traceTotalProfit: Decimal
  """Total profit"""
  currentTradingPairs: list[str]
  """Current underlying assets for copy trading"""
  followerTime: Timestamp
  """Following date (milliseconds timestamp, e.g. 1597026383085)"""

class Response(TypedDict):
  resultList: list[Trader]

validate_response = validator(Response)

@dataclass
class MyTraders(AuthEndpoint):
  async def my_traders(
    self, *, start: datetime | None = None, end: datetime | None = None,
    page: int | None = None, page_size: int | None = None,
    validate: bool | None = None
  ):
    """My Trader List
    
    - `start`, `end`: time range of the data.
    - `page`: page number (default: 1).
    - `page_size`: page size (default: 50, max: 50).
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/copytrading/spot-copytrade/follower/Query-Traders)
    """
    params = {}
    if start is not None:
      params['startTime'] = ts.dump(start)
    if end is not None:
      params['endTime'] = ts.dump(end)
    if page is not None:
      params['pageNo'] = page
    if page_size is not None:
      params['pageSize'] = page_size
    r = await self.authed_request('GET', '/api/v2/copy/spot-follower/query-traders', params=params)
    return self.output(r.text, validate_response, validate=validate)