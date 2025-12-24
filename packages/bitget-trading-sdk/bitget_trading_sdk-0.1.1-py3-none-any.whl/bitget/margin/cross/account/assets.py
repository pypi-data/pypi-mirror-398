from dataclasses import dataclass
from decimal import Decimal

from bitget.core import AuthEndpoint, validator, TypedDict, Timestamp

class Asset(TypedDict):
  coin: str
  """Token name"""
  totalAmount: Decimal
  """Total amount"""
  available: Decimal
  """Available amount"""
  frozen: Decimal
  """Assets frozen"""
  borrow: Decimal
  """Borrow"""
  interest: Decimal
  """Interest, Interest-only payments with a minimum payment of interest."""
  net: Decimal
  """Net assets = available + frozen - borrow - interest. Liquidation is triggered when the Maintenance Margin Ratio (MMR) is reached."""
  coupon: Decimal
  """Trading bonus"""
  cTime: Timestamp
  """Creation time"""
  uTime: Timestamp
  """Update time"""

validate_response = validator(list[Asset])

@dataclass
class Assets(AuthEndpoint):
  async def assets(
    self, *, coin: str | None = None,
    validate: bool | None = None
  ):
    """Get cross margin account assets.
    
    - `coin`: Token name, e.g. USDT. This field is used for querying the balance of a single coin.
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/margin/cross/account/Get-Cross-Assets)
    """
    params = {}
    if coin is not None:
      params['coin'] = coin
    r = await self.authed_request('GET', '/api/v2/margin/crossed/account/assets', params=params)
    return self.output(r.text, validate_response, validate=validate)