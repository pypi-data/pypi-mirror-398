# STDLIB IMPORTS
from typing_extensions import Literal
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from bitget.core import (
  AuthEndpoint, timestamp as ts, rate_limit,
  validator, TypedDict, Timestamp
)

# RESPONSE MODELS

class DepositRecord(TypedDict):
  orderId: str
  """Order ID"""
  tradeId: str
  """TX ID - when `dest` is `on_chain`, it's the on chain hash value - if the `dest` is `internal_transfer`, it is the trade ID"""
  coin: str
  """Token name"""
  type: Literal['deposit']
  """Type - Fixed value: `deposit`"""
  size: Decimal
  """Quantity"""
  status: Literal['pending', 'fail', 'success']
  """Withdrawal status - `pending`: pending confirmation - `fail`: failed - `success`: successed"""
  fromAddress: str
  """Deposit Initiators - If `dest` is `on_chain`, it's the on chain address - If `dest` is `internal_transfer`, it would be the UID,email or the mobile"""
  toAddress: str
  """Coin Receiver - If `dest` is `on_chain`, it's the on chain address - If `dest` is `internal_transfer`, it would be the UID,email or the mobile"""
  chain: str
  """Deposit network - if `dest` is `internal_transfer`, please ignore this parameter"""
  dest: Literal['on_chain', 'internal_transfer']
  """Deposit Type - `on_chain`: the on chain deposit - `internal_transfer`: internal deposit"""
  cTime: Timestamp
  """Creation time, ms"""
  uTime: Timestamp
  """Edit time, ms"""

validate_response = validator(list[DepositRecord])

# ENDPOINT CLASS

@dataclass
class DepositRecords(AuthEndpoint):
  @rate_limit(timedelta(seconds=0.1))
  async def deposit_records(
    self,
    start: datetime,
    end: datetime,
    *,
    coin: str | None = None,
    order_id: str | None = None,
    id_less_than: str | None = None,
    limit: int | None = None,
    validate: bool | None = None
  ):
    """Get Deposit Records
    
    - `start`: The record start time for the query. Unix millisecond timestamp, e.g. 1690196141868
    - `end`: The end time of the record for the query. Unix millisecond timestamp, e.g. 1690196141868
    - `coin`: Coin name, e.g. USDT
    - `order_id`: The response orderId
    - `id_less_than`: Requests the content on the page before this ID (older data), the value input should be the orderId of the corresponding interface.
    - `limit`: Number of entries per page - The default value is 20 and the maximum value is 100
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/spot/account/Get-Deposit-Record)
    """
    params = {}
    
    # Add required params
    params['startTime'] = ts.dump(start)
    params['endTime'] = ts.dump(end)
    
    # Add optional params conditionally
    if coin is not None:
      params['coin'] = coin
    if order_id is not None:
      params['orderId'] = order_id
    if id_less_than is not None:
      params['idLessThan'] = id_less_than
    if limit is not None:
      params['limit'] = str(limit)
    
    # Make request
    r = await self.authed_request('GET', '/api/v2/spot/wallet/deposit-records', params=params)
    return self.output(r.text, validate_response, validate=validate)

