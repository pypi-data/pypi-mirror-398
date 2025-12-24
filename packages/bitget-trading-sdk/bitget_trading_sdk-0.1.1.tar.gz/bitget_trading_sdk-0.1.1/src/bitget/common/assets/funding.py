from typing_extensions import Literal
from dataclasses import dataclass
from decimal import Decimal

from bitget.core import AuthEndpoint, validator, TypedDict

class Asset(TypedDict):
  coin: str
  available: Decimal
  frozen: Decimal
  usdtValue: Decimal


validate_response = validator(list[Asset])

@dataclass
class Funding(AuthEndpoint):
  async def funding(self, coin: str | None = None, *, validate: bool | None = None):
    """Funding assets
    
    - `coin`: Filter by coin, e.g. USDT.
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/common/account/Funding-Assets)
    """
    params = {}
    if coin is not None:
      params['coin'] = coin
    r = await self.authed_request('GET', '/api/v2/account/funding-assets', params=params)
    return self.output(r.text, validate_response, validate=validate)