from dataclasses import dataclass
from decimal import Decimal

from bitget.core import AuthEndpoint, validator, TypedDict, Timestamp
from bitget.futures.core import ProductType

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
class SubaccountAssets(AuthEndpoint):
  async def subaccount_assets(
    self, product_type: ProductType, *,
    validate: bool | None = None
  ):
    """Query the contract asset information of all sub-accounts. ND Brokers are not allowed to call this endpoint.
    
    - `product_type`: Product type.
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/contract/account/Get-Sub-Account-Contract-Assets)
    """
    r = await self.authed_request('GET', '/api/v2/mix/account/sub-account-assets', params={
      'productType': product_type,
    })
    return self.output(r.text, validate_response, validate=validate)