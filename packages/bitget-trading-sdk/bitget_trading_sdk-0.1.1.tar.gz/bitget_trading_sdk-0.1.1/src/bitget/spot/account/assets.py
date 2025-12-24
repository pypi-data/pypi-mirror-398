from typing_extensions import Literal
from dataclasses import dataclass
from decimal import Decimal

from bitget.core import AuthEndpoint, validator, TypedDict, Timestamp

class Asset(TypedDict):
  coin: str
  """Token name"""
  available: Decimal
  """Available assets"""
  frozen: Decimal
  """Amount of frozen assets. Usually frozen when the limit order is placed or join the Launchpad."""
  locked: Decimal
  """Amount of locked assets. Locked assests required to become a fiat merchants, etc."""
  limitAvailable: Decimal
  """Restricted availability. For spot copy trading"""
  uTime: Timestamp
  """Update time(ms)"""


validate_response = validator(list[Asset])

@dataclass
class Assets(AuthEndpoint):
  async def assets(
    self, *, coin: str | None = None,
    asset_type: Literal['hold_only', 'all'] | None = None,
    validate: bool | None = None
  ):
    """Get account assets.
    
    - `coin`: Token name, e.g. USDT. This field is used for querying the positions of a single coin.
    - `asset_type`: Asset type. `hold_only`: Position coin, `all`: All coins.This field is used used for querying the positions of multiple coins. The default value is `hold_only`. When only assetType is entered without coin, results of all eligible coins are returned. When both coin and assetType are entered, coin has higher priority.
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/spot/account/Get-Account-Assets)
    """
    params = {}
    if coin is not None:
      params['coin'] = coin
    if asset_type is not None:
      params['assetType'] = asset_type
    r = await self.authed_request('GET', '/api/v2/spot/account/assets', params=params)
    return self.output(r.text, validate_response, validate=validate)