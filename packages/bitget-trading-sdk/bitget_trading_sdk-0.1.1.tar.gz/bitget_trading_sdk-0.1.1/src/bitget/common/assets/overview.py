from typing_extensions import Literal
from dataclasses import dataclass
from decimal import Decimal

from bitget.core import AuthEndpoint, validator, TypedDict

AccountType = Literal['spot', 'futures', 'funding', 'earn', 'bots', 'margin']

class AssetOverview(TypedDict):
  accountType: AccountType
  usdtBalance: Decimal

validate_response = validator(list[AssetOverview])

@dataclass
class Overview(AuthEndpoint):
  async def overview(self, *, validate: bool | None = None):
    """Assets overview
    
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/common/account/All-Account-Balance)
    """
    r = await self.authed_request('GET', '/api/v2/account/all-account-balance')
    return self.output(r.text, validate_response, validate=validate)