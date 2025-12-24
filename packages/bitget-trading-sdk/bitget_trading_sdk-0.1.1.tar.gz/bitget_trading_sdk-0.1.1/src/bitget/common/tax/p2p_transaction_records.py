from typing_extensions import AsyncIterable, Literal
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta

from bitget.core import AuthEndpoint, validator, TypedDict, timestamp as ts, rate_limit

class P2PTransaction(TypedDict):
  id: str
  """Record id lastEndId"""
  coin: str
  """Coin"""
  p2pTaxType: Literal['transfer-in', 'transfer-out', 'sell', 'buy']
  """p2p taxation types: transfer-in (Inbound transfer), transfer-out (Outbound transfer), sell (Sell), buy (Buy)"""
  balance: Decimal
  """Quantity"""
  ts: int
  """Timestamp"""
  
validate_response = validator(list[P2PTransaction])

@dataclass
class P2PTransactionRecords(AuthEndpoint):
  @rate_limit(timedelta(seconds=1))
  async def p2p_transaction_records(
    self, coin: str | None = None, *,
    start: datetime, end: datetime,
    limit: int | None = None,
    id_less_than: str | None = None,
    validate: bool | None = None
  ) -> list[P2PTransaction]:
    """P2P transaction records
    
    - `coin`: filter by coin, e.g. USDT. Default all coin type
    - `start`, `end`: time range of the data. Difference must be at most 30 days (`end - start <= 30 days`).
    - `limit`: number of records to return (default: 500, max: 500).
    - `id_less_than`: The last recorded ID.
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/common/tax/Get-P2P-Account-Record)
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
    path = '/api/v2/tax/p2p-record'
    r = await self.authed_request('GET', path, params=params)
    return self.output(r.text, validate_response, validate=validate)

  
  async def p2p_transaction_records_paged(
    self, coin: str | None = None, *,
    start: datetime, end: datetime,
    limit: int = 500,
    interval: timedelta = timedelta(days=30),
    validate: bool | None = None
  ) -> AsyncIterable[list[P2PTransaction]]:
    """P2P transaction records, automatically paginated.
    
    - `coin`: filter by coin, e.g. USDT. Default all coin type
    - `start`, `end`: time range of the data, unbounded.
    - `limit`: number of records to return per request (default: 500, max: 500).
    - `interval`: time interval between requests (default: 30 days).
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/common/tax/Get-P2P-Account-Record)
    """
    ids = set[str]()
    while start < end:
      data = await self.p2p_transaction_records(coin, start=start, end=start+interval, limit=limit, validate=validate)
      chunk: list[P2PTransaction] = []
      for tx in data:
        if tx['id'] not in ids:
          ids.add(tx['id'])
          chunk.append(tx)
      if chunk:
        yield chunk
      
      if len(data) == limit:
        start = ts.parse(data[-1]['ts'])
      else:
        start += interval

