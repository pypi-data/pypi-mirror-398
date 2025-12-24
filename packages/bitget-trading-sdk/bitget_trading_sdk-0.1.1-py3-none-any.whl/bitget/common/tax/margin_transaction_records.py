from typing_extensions import AsyncIterable, Literal
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta

from bitget.core import AuthEndpoint, validator, TypedDict, timestamp as ts, rate_limit, Timestamp

class MarginTransaction(TypedDict):
  id: str
  coin: str
  symbol: str
  marginTaxType: str
  amount: Decimal
  fee: Decimal
  balance: Decimal
  ts: Timestamp
  
validate_response = validator(list[MarginTransaction])

@dataclass
class MarginTransactionRecords(AuthEndpoint):
  @rate_limit(timedelta(seconds=1))
  async def margin_transaction_records(
    self, margin_type: Literal['isolated', 'crossed'], *,
    coin: str | None = None,
    start: datetime, end: datetime,
    limit: int | None = None,
    id_less_than: str | None = None,
    validate: bool | None = None
  ) -> list[MarginTransaction]:
    """Margin transaction records
    
    - `margin_type`: filter by margin type, e.g. isolated, crossed.
    - `coin`: filter by coin, e.g. USDT.
    - `start`, `end`: time range of the data. Difference must be at most 30 days (`end - start <= 30 days`).
    - `limit`: number of records to return (default: 500, max: 500).
    - `id_less_than`: The last recorded ID.
    - `validate`: Whether to validate the response against the expected schema (default: True).
    
    > [Bitget API docs](https://www.bitget.com/api-doc/common/tax/Get-Margin-Account-Record)
    """
    params: dict = {
      'startTime': ts.dump(start),
      'endTime': ts.dump(end),
    }
    if margin_type is not None:
      params['marginType'] = margin_type
    if coin is not None:
      params['coin'] = coin
    if limit is not None:
      params['limit'] = limit
    if id_less_than is not None:
      params['idLessThan'] = id_less_than
    path = '/api/v2/tax/margin-record'
    r = await self.authed_request('GET', path, params=params)
    return self.output(r.text, validate_response, validate=validate)

  
  async def margin_transaction_records_paged(
    self, margin_type: Literal['isolated', 'crossed'], *,
    coin: str | None = None,
    start: datetime, end: datetime,
    limit: int = 500,
    interval: timedelta = timedelta(days=30),
    validate: bool | None = None
  ) -> AsyncIterable[list[MarginTransaction]]:
    """Margin transaction records, automatically paginated.
    
    - `margin_type`: filter by margin type, e.g. isolated, crossed.
    - `coin`: filter by coin, e.g. USDT.
    - `start`, `end`: time range of the data, unbounded.
    - `limit`: number of records to return per request (default: 500, max: 500).
    - `interval`: time interval between requests (default: 30 days).
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/common/tax/Get-Margin-Account-Record)
    """
    ids = set[str]()
    while start < end:
      data = await self.margin_transaction_records(
        margin_type=margin_type, coin=coin,
        start=start, end=start+interval, limit=limit, validate=validate,
      )
      chunk: list[MarginTransaction] = []
      for tx in data:
        if tx['id'] not in ids:
          ids.add(tx['id'])
          chunk.append(tx)
      if chunk:
        yield chunk
      
      if len(data) == limit:
        t = data[-1]['ts']
        start = t if self.validate(validate) else ts.parse(int(t))
      else:
        start += interval
