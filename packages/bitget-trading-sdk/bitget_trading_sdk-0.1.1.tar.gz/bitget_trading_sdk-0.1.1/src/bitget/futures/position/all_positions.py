from typing_extensions import Literal, NotRequired
from dataclasses import dataclass
from decimal import Decimal

from bitget.core import AuthEndpoint, validator, TypedDict, Timestamp
from bitget.futures.core import ProductType

class Position(TypedDict):
    symbol: str
    """Trading pair name"""
    marginCoin: str
    """Margin coin"""
    holdSide: Literal['long', 'short']
    """Position direction
    - long: long position
    - short: short position
    """
    openDelegateSize: Decimal
    """Amount to be filled of the current order (base coin)"""
    marginSize: Decimal
    """Margin amount (margin coin)"""
    available: Decimal
    """Available amount for positions (base currency)"""
    locked: Decimal
    """Frozen amount in the position (base currency)"""
    total: Decimal
    """Total amount of all positions (available amount + locked amount)"""
    leverage: Decimal
    """Leverage"""
    achievedProfits: Decimal
    """Realized PnL (exclude the funding fee and transaction fee)"""
    openPriceAvg: Decimal
    """Average entry price"""
    marginMode: Literal['isolated', 'crossed']
    """Margin mode
    - isolated: isolated margin
    - crossed: cross margin
    """
    posMode: Literal['one_way_mode', 'hedge_mode']
    """Position mode
    - one_way_mode: positions in one-way mode
    - hedge_mode: positions in hedge-mode
    """
    unrealizedPL: Decimal
    """Unrealized PnL"""
    liquidationPrice: Decimal
    """Estimated liquidation price
    If the value <= 0, it means the position is at low risk and there is no liquidation price at this time
    """
    keepMarginRate: Decimal
    """Tiered maintenance margin rate"""
    markPrice: Decimal
    """Mark price"""
    marginRatio: Decimal
    """Maintenance margin rate (MMR), 0.1 represents 10%"""
    breakEvenPrice: Decimal
    """Position breakeven price"""
    totalFee: Decimal
    """Funding fee, the accumulated value of funding fee during the position.
    The initial value is empty, indicating that no funding fee has been charged yet."""
    takeProfit: Decimal | Literal['']
    """Take profit price"""
    stopLoss: Decimal | Literal['']
    """Stop loss price"""
    takeProfitId: NotRequired[str]
    """Take profit order ID"""
    stopLossId: NotRequired[str]
    """Stop loss order ID"""
    deductedFee: Decimal
    """Deducted transaction fees: transaction fees deducted during the position"""
    cTime: Timestamp
    """Creation time, timestamp, milliseconds
    The set is in descending order from the latest time.
    """
    assetMode: Literal['single', 'union']
    """- single: single asset mode
    - union: multi-Assets mode
    """
    uTime: Timestamp
    """Last updated time, timestamp, milliseconds"""


validate_response = validator(list[Position])

@dataclass
class AllPositions(AuthEndpoint):
  async def all_positions(
    self, product_type: ProductType, *,
    margin_coin: str | None = None,
    validate: bool | None = None
  ):
    """Query the contract asset information of all sub-accounts. ND Brokers are not allowed to call this endpoint.
    
    - `product_type`: Product type.
    - `margin_coin`: Margin coin, e.g. USDT.
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/contract/position/get-all-position)
    """
    params = {'productType': product_type}
    if margin_coin is not None:
      params['marginCoin'] = margin_coin
    r = await self.authed_request('GET', '/api/v2/mix/position/all-position', params=params)
    return self.output(r.text, validate_response, validate=validate)