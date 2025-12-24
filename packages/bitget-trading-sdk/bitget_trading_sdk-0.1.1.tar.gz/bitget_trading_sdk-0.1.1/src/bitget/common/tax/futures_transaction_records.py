from typing_extensions import AsyncIterable, Literal
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta

from bitget.core import AuthEndpoint, validator, TypedDict, timestamp as ts, rate_limit, Timestamp

ProductType = Literal['USDT-FUTURES', 'USDC-FUTURES', 'COIN-FUTURES']

class FuturesTransaction(TypedDict):
  id: str
  symbol: str
  marginCoin: str
  futureTaxType: str
  amount: Decimal
  fee: Decimal
  ts: Timestamp

validate_response = validator(list[FuturesTransaction])

@dataclass
class FuturesTransactionRecords(AuthEndpoint):
  @rate_limit(timedelta(seconds=1))
  async def futures_transaction_records(
    self, *, product_type: ProductType | None = None,
    margin_coin: str | None = None,
    start: datetime, end: datetime,
    limit: int | None = None,
    id_less_than: str | None = None,
    validate: bool | None = None
  ) -> list[FuturesTransaction]:
    """Futures transaction records
    
    - `product_type`: filter by product type, e.g. USDT-FUTURES.
    - `margin_coin`: filter by margin coin, e.g. USDT.
    - `start`, `end`: time range of the data. Difference must be at most 30 days (`end - start <= 30 days`).
    - `limit`: number of records to return (default: 500, max: 500).
    - `id_less_than`: The last recorded ID.
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/common/tax/Get-Future-Account-Record)
    """
    params: dict = {
      'startTime': ts.dump(start),
      'endTime': ts.dump(end),
    }
    if product_type is not None:
      params['productType'] = product_type
    if margin_coin is not None:
      params['marginCoin'] = margin_coin
    if limit is not None:
      params['limit'] = limit
    if id_less_than is not None:
      params['idLessThan'] = id_less_than
    path = '/api/v2/tax/future-record'
    r = await self.authed_request('GET', path, params=params)
    return self.output(r.text, validate_response, validate=validate)

  
  async def futures_transaction_records_paged(
    self, *, product_type: ProductType | None = None,
    margin_coin: str | None = None,
    start: datetime, end: datetime,
    limit: int = 500,
    interval: timedelta = timedelta(days=30),
    validate: bool | None = None
  ) -> AsyncIterable[list[FuturesTransaction]]:
    """Futures transaction records, automatically paginated.
    
    - `product_type`: filter by product type, e.g. USDT-FUTURES.
    - `margin_coin`: filter by margin coin, e.g. USDT.
    - `start`, `end`: time range of the data, unbounded.
    - `limit`: number of records to return per request (default: 500, max: 500).
    - `interval`: time interval between requests (default: 30 days).
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/common/tax/Get-Future-Account-Record)
    """
    ids = set[str]()
    while start < end:
      data = await self.futures_transaction_records(
        product_type=product_type, margin_coin=margin_coin,
        start=start, end=start+interval, limit=limit, validate=validate,
      )
      chunk: list[FuturesTransaction] = []
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
