from typing_extensions import TypeVar, Any
import os
from dataclasses import dataclass, field
import json

from .http import HttpMixin, AuthHttpMixin, HttpClient, AuthHttpClient
from .validation import ValidationMixin, validator, TypedDict
from .exc import ApiError

T = TypeVar('T')

BITGET_REST_URL = 'https://api.bitget.com'

class Response(TypedDict):
  code: str
  msg: str
  requestTime: int
  data: Any

def is_ok(r: Response):
  return r['code'] == '00000' and r['msg'] == 'success'

validate_response = validator(Response)

@dataclass
class BaseMixin(ValidationMixin):
  base_url: str = field(kw_only=True, default=BITGET_REST_URL)

  def output(self, data: str | bytes, validator: validator[T], validate: bool | None) -> T:
    r: Response = validate_response(data) if self.validate(validate) else json.loads(data)
    if not is_ok(r):
      raise ApiError(r)
    return validator(r['data']) if self.validate(validate) else r['data']

@dataclass
class Endpoint(BaseMixin, HttpMixin):
  ...

@dataclass
class AuthEndpoint(Endpoint, AuthHttpMixin):
  base_url: str = field(kw_only=True, default=BITGET_REST_URL)

  @classmethod
  def new(
    cls, access_key: str | None = None, secret_key: str | None = None, passphrase: str | None = None, *,
    base_url: str = BITGET_REST_URL, validate: bool = True,
  ):
    if access_key is None:
      access_key = os.environ['BITGET_ACCESS_KEY']
    if secret_key is None:
      secret_key = os.environ['BITGET_SECRET_KEY']
    if passphrase is None:
      passphrase = os.environ['BITGET_PASSPHRASE']
    client = AuthHttpClient(access_key=access_key, secret_key=secret_key, passphrase=passphrase)
    return cls(base_url=base_url, http=client, default_validate=validate)

@dataclass
class Router(Endpoint):
  def __post_init__(self):
    for field, cls in self.__annotations__.items():
      if issubclass(cls, Endpoint) or issubclass(cls, Router):
        setattr(self, field, cls(base_url=self.base_url, http=self.http, default_validate=self.default_validate))

@dataclass
class AuthRouter(Router, AuthEndpoint):
  ...