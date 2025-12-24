# STDLIB IMPORTS
from typing_extensions import Literal
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from bitget.core import AuthEndpoint, validator, TypedDict, Timestamp, timestamp as ts, rate_limit

# RESPONSE MODELS

class WithdrawalRecord(TypedDict):
    orderId: str
    """Order ID"""
    tradeId: str
    """TX ID - when `dest` is `on_chain`, it's the on chain hash value - if the `dest` is `internal_transfer`, it is the trade ID"""
    coin: str
    """Token name"""
    clientOid: str | None
    """Client customized ID"""
    type: Literal['withdraw']
    """Type - Fixed value: `withdraw`"""
    dest: Literal['on_chain', 'internal_transfer']
    """Type of withdrawal - `on_chain`: withdrawal on chain - `internal_transfer`: internal transfer"""
    size: Decimal
    """Quantity"""
    fee: Decimal
    """Transaction Fee"""
    status: Literal['pending', 'fail', 'success']
    """Withdrawal status - `pending`:Pending preliminary examination - `fail`:Failed - `success`:Successful"""
    fromAddress: str
    """Withdrawal Initiators - If `dest` is `on_chain`, it's the on chain address - If `dest` is `internal_transfer`, it would be the UID,email or the mobile"""
    toAddress: str
    """Coin receiver address - If `dest` is `on_chain`, it's the on chain address - If `dest` is `internal_transfer`, it would be the UID,email or the mobile"""
    chain: str
    """Withdrawal network - if `dest` is `internal_transfer`, please ignore this parameter"""
    confirm: str
    """Number of confirmed blocks"""
    tag: str | None
    """Tag"""
    cTime: Timestamp
    """Creation time(ms)"""
    uTime: Timestamp
    """Update time(ms)"""

validate_response = validator(list[WithdrawalRecord])

# ENDPOINT CLASS

@dataclass
class WithdrawalRecords(AuthEndpoint):
    @rate_limit(timedelta(seconds=0.1))
    async def withdrawal_records(
        self,
        start_time: datetime,
        end_time: datetime,
        *,
        coin: str | None = None,
        client_oid: str | None = None,
        id_less_than: str | None = None,
        order_id: str | None = None,
        limit: int | None = None,
        validate: bool | None = None
    ):
        """Get Withdrawal Records
        
        - `start_time`: The record start time for the query. Unix millisecond timestamp, e.g. 1690196141868
        - `end_time`: The end time of the record for the query. Unix millisecond timestamp, e.g. 1690196141868
        - `coin`: Coin name, e.g. USDT
        - `client_oid`: Client customized ID
        - `id_less_than`: Requests the content on the page before this ID (older data), the value input should be the orderId of the corresponding interface.
        - `order_id`: The response orderId
        - `limit`: Number of entries per page - The default value is 20 and the maximum value is 100
        - `validate`: Whether to validate the response against the expected schema (default: True).

        > [Bitget API docs](https://www.bitget.com/api-doc/spot/account/Get-Withdraw-Record)
        """
        params = {}
        
        # Add required params
        params['startTime'] = ts.dump(start_time)
        params['endTime'] = ts.dump(end_time)
        
        # Add optional params conditionally
        if coin is not None:
            params['coin'] = coin
        if client_oid is not None:
            params['clientOid'] = client_oid
        if id_less_than is not None:
            params['idLessThan'] = id_less_than
        if order_id is not None:
            params['orderId'] = order_id
        if limit is not None:
            params['limit'] = str(limit)
        
        # Make request
        r = await self.authed_request('GET', '/api/v2/spot/wallet/withdrawal-records', params=params)
        return self.output(r.text, validate_response, validate=validate)

