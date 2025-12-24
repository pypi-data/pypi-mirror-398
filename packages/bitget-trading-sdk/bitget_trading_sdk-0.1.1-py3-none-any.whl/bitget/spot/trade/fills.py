from typing_extensions import Literal
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from bitget.core import AuthEndpoint, validator, TypedDict, Timestamp, timestamp as ts, rate_limit

class FeeDetail(TypedDict):
  deduction: Literal['yes', 'no']
  feeCoin: str
  totalDeductionFee: Literal[''] | Decimal
  totalFee: Decimal

class Fill(TypedDict):
  userId: str
  symbol: str
  orderId: str
  tradeId: str
  orderType: str
  side: Literal['buy', 'sell']
  priceAvg: Decimal
  size: Decimal
  amount: Decimal
  cTime: Timestamp
  uTime: Timestamp
  tradeScope: Literal['maker', 'taker']
  feeDetail: FeeDetail

validate_response = validator(list[Fill])

@dataclass
class Fills(AuthEndpoint):
  @rate_limit(timedelta(seconds=0.1))
  async def fills(
    self, *, symbol: str | None = None,
    order_id: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int | None = None,
    id_less_than: str | None = None,
    validate: bool | None = None
  ):
    """Get Fills (It only supports to get the data within 90days.The older data can be downloaded from web)
    
    - `symbol`: Symbol filter, e.g. BTCUSDT.
    - `order_id`: Order ID filter.
    - `start`, `end`: Time range filter. Difference between them must be at most 90 days.
    - `limit`: Number of records to return (default: 100, max: 100).
    - `id_less_than`: The last recorded ID.
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/spot/trade/Get-Fills)
    """
    params = {}
    if symbol is not None:
      params['symbol'] = symbol
    if order_id is not None:
      params['orderId'] = order_id
    if start is not None:
      params['startTime'] = ts.dump(start)
    if end is not None:
      params['endTime'] = ts.dump(end)
    if limit is not None:
      params['limit'] = limit
    if id_less_than is not None:
      params['idLessThan'] = id_less_than
    r = await self.authed_request('GET', '/api/v2/spot/trade/fills', params=params)
    return self.output(r.text, validate_response, validate=validate)