from typing_extensions import Mapping, Any
from dataclasses import dataclass, field
import hmac
import base64
import hashlib
from urllib.parse import urlencode, quote, urlparse

import httpx
import orjson

from .client import HttpClient, HttpMixin
from ..util import timestamp

def sign(payload: bytes, *, secret: str) -> bytes:
  d = hmac.new(secret.encode(), payload, hashlib.sha256).digest()
  return base64.b64encode(d)

def payload(*, timestamp: int, method: str, path: str, query: str = '', body: bytes = b'') -> bytes:
  return f'{timestamp}{method}{path}{query}'.encode() + body


def query_string(params: Mapping[str, Any]) -> str:
  def fix(v):
    # fix bools, which would show otherwise as "hello=True" instead of "hello=true"
    if isinstance(v, bool):
      return str(v).lower()
    else:
      return v
  fixed_params = [(k, fix(v)) for k, v in params.items()]
  return urlencode(fixed_params, quote_via=quote)

@dataclass
class AuthHttpClient(HttpClient):
  access_key: str = field(kw_only=True)
  secret_key: str = field(kw_only=True, repr=False)
  passphrase: str = field(kw_only=True, repr=False)

  async def authed_request(
    self, method: str, url: str,
    *,
    content: httpx._types.RequestContent | None = None,
    data: httpx._types.RequestData | None = None,
    files: httpx._types.RequestFiles | None = None,
    json: Any | None = None,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    cookies: httpx._types.CookieTypes | None = None,
    auth: httpx._types.AuthTypes | httpx._client.UseClientDefault | None = httpx.USE_CLIENT_DEFAULT,
    follow_redirects: bool | httpx._client.UseClientDefault = httpx.USE_CLIENT_DEFAULT,
    timeout: httpx._types.TimeoutTypes | httpx._client.UseClientDefault = httpx.USE_CLIENT_DEFAULT,
    extensions: httpx._types.RequestExtensions | None = None,
  ):
    query = '?' + query_string(params) if params else ''
    path = urlparse(url).path
    ts = timestamp.now()
    body = orjson.dumps(json) if json is not None else b''
    prehash = payload(timestamp=ts, method=method, path=path, query=query, body=body)
    signature = sign(prehash, secret=self.secret_key)
    new_headers = {
      'Access-Key': self.access_key,
      'Access-Sign': signature,
      'Access-Timestamp': str(ts),
      'Access-Passphrase': self.passphrase,
    }
    new_headers.update(headers or {})
    return await self.request(
      method, url, headers=new_headers, params=params, json=json,
      content=content, data=data, files=files, auth=auth,
      follow_redirects=follow_redirects, cookies=cookies,
      timeout=timeout, extensions=extensions,
    )


@dataclass
class AuthHttpMixin(HttpMixin):
  base_url: str = field(kw_only=True)
  http: AuthHttpClient = field(kw_only=True) # type: ignore

  @classmethod
  def new(cls, access_key: str, secret_key: str, passphrase: str, *, base_url: str):
    client = AuthHttpClient(access_key=access_key, secret_key=secret_key, passphrase=passphrase)
    return cls(base_url=base_url, http=client)
  
  async def __aenter__(self):
    await self.http.__aenter__()
    return self
  
  async def __aexit__(self, exc_type, exc_value, traceback):
    await self.http.__aexit__(exc_type, exc_value, traceback)

  async def authed_request(
    self, method: str, path: str,
    *,
    content: httpx._types.RequestContent | None = None,
    data: httpx._types.RequestData | None = None,
    files: httpx._types.RequestFiles | None = None,
    json: Any | None = None,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    cookies: httpx._types.CookieTypes | None = None,
    auth: httpx._types.AuthTypes | httpx._client.UseClientDefault | None = httpx.USE_CLIENT_DEFAULT,
    follow_redirects: bool | httpx._client.UseClientDefault = httpx.USE_CLIENT_DEFAULT,
    timeout: httpx._types.TimeoutTypes | httpx._client.UseClientDefault = httpx.USE_CLIENT_DEFAULT,
    extensions: httpx._types.RequestExtensions | None = None,
  ):
    return await self.http.authed_request(
      method, self.base_url + path, headers=headers, json=json,
      content=content, data=data, files=files, auth=auth,
      follow_redirects=follow_redirects, cookies=cookies,
      timeout=timeout, extensions=extensions, params=params,
    )