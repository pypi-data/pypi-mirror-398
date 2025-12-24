from typing_extensions import AsyncIterable
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta

from bitget.core import AuthEndpoint, validator, TypedDict, timestamp as ts, rate_limit, Timestamp

class SpotTransaction(TypedDict):
  id: str
  coin: str
  spotTaxType: str
  amount: Decimal
  fee: Decimal
  balance: Decimal
  ts: Timestamp
  bizOrderId: str
  
validate_response = validator(list[SpotTransaction])

@dataclass
class SpotTransactionRecords(AuthEndpoint):
  @rate_limit(timedelta(seconds=1))
  async def spot_transaction_records(
    self, coin: str | None = None, *,
    start: datetime, end: datetime,
    limit: int | None = None,
    id_less_than: str | None = None,
    validate: bool | None = None
  ) -> list[SpotTransaction]:
    """Spot transaction records
    
    - `coin`: filter by coin, e.g. USDT.
    - `start`, `end`: time range of the data. Difference must be at most 30 days (`end - start <= 30 days`).
    - `limit`: number of records to return (default: 500, max: 500).
    - `id_less_than`: The last recorded ID.
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/common/tax/Get-Spot-Account-Record)
    """
    params: dict = {
      'startTime': ts.dump(start),
      'endTime': ts.dump(end),
    }
    if coin is not None:
      params['coin'] = coin
    if limit is not None:
      params['limit'] = limit
    if id_less_than is not None:
      params['idLessThan'] = id_less_than
    path = '/api/v2/tax/spot-record'
    r = await self.authed_request('GET', path, params=params)
    return self.output(r.text, validate_response, validate=validate)

  
  async def spot_transaction_records_paged(
    self, coin: str | None = None, *,
    start: datetime, end: datetime,
    limit: int = 500,
    interval: timedelta = timedelta(days=30),
    validate: bool | None = None
  ) -> AsyncIterable[list[SpotTransaction]]:
    """Spot transaction records, automatically paginated.
    
    - `coin`: filter by coin, e.g. USDT.
    - `start`, `end`: time range of the data, unbounded.
    - `limit`: number of records to return per request (default: 500, max: 500).
    - `interval`: time interval between requests (default: 30 days).
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/common/tax/Get-Spot-Account-Record)
    """
    ids = set[str]()
    while start < end:
      data = await self.spot_transaction_records(coin, start=start, end=start+interval, limit=limit, validate=validate)
      chunk: list[SpotTransaction] = []
      for tx in data:
        if tx['id'] not in ids:
          ids.add(tx['id'])
          chunk.append(tx)
      if chunk:
        yield chunk
      
      if len(data) == limit:
        t = data[-1]['ts']
        start = t if self.validate(validate) else ts.parse(int(t)) # type: ignore
      else:
        start += interval
