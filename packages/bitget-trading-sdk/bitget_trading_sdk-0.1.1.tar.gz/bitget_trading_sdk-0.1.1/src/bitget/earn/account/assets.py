from dataclasses import dataclass
from decimal import Decimal

from bitget.core import AuthEndpoint, validator, TypedDict

class Asset(TypedDict):
  coin: str
  amount: Decimal

validate_response = validator(list[Asset])

@dataclass
class Assets(AuthEndpoint):
  async def assets(
    self, *, coin: str | None = None,
    validate: bool | None = None
  ):
    """Earn account overview
    
    - `coin`: Filter by coin, e.g. USDT.
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/earn/account/Earn-Assets)
    """
    params = {}
    if coin is not None:
      params['coin'] = coin
    r = await self.authed_request('GET', '/api/v2/earn/account/assets', params=params)
    return self.output(r.text, validate_response, validate=validate)