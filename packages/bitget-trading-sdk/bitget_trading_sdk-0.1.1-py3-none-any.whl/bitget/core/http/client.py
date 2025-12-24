from typing_extensions import Any, Mapping
from dataclasses import dataclass, field
import asyncio
import httpx

from ..exc import NetworkError

@dataclass
class HttpClient:
  lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)
  client_future: asyncio.Future[httpx.AsyncClient|None] = field(default_factory=asyncio.Future, init=False, repr=False)

  @property
  async def client(self) -> httpx.AsyncClient:
    if self.lock.locked() or self.client_future.done():
      if (client := await self.client_future) is not None:
        return client

    async with self.lock:
      client = await httpx.AsyncClient().__aenter__()
      self.client_future.set_result(client)
      return client

  async def __aenter__(self):
    await self.client

  async def __aexit__(self, exc_type, exc_value, traceback):
    client = await self.client
    if not self.lock.locked():
      async with self.lock:
        await client.__aexit__(exc_type, exc_value, traceback)
        self.client_future = asyncio.Future()

  async def request(
    self, method: str, url: str,
    *,
    content: httpx._types.RequestContent | None = None,
    data: httpx._types.RequestData | None = None,
    files: httpx._types.RequestFiles | None = None,
    json: Any | None = None,
    params: Mapping[str, Any] | None = None,
    headers: Mapping | None = None,
    cookies: httpx._types.CookieTypes | None = None,
    auth: httpx._types.AuthTypes | httpx._client.UseClientDefault | None = httpx.USE_CLIENT_DEFAULT,
    follow_redirects: bool | httpx._client.UseClientDefault = httpx.USE_CLIENT_DEFAULT,
    timeout: httpx._types.TimeoutTypes | httpx._client.UseClientDefault = httpx.USE_CLIENT_DEFAULT,
    extensions: httpx._types.RequestExtensions | None = None,
  ):
    try:
      client = await self.client
      return await client.request(
        method, url, params=params, cookies=cookies, json=json,
        content=content, data=data, files=files, auth=auth, follow_redirects=follow_redirects,
        timeout=timeout, extensions=extensions,
        headers=headers,
      )
    except httpx.HTTPError as e:
      req = f'{method} {url}'
      raise NetworkError(f'Error sending request to {req}', *e.args) from e

@dataclass
class HttpMixin:
  base_url: str = field(kw_only=True)
  http: HttpClient = field(kw_only=True, default_factory=HttpClient)

  async def __aenter__(self):
    await self.http.__aenter__()
    return self
  
  async def __aexit__(self, exc_type, exc_value, traceback):
    await self.http.__aexit__(exc_type, exc_value, traceback)

  async def request(
    self, method: str, path: str,
    *,
    content: httpx._types.RequestContent | None = None,
    data: httpx._types.RequestData | None = None,
    files: httpx._types.RequestFiles | None = None,
    json: Any | None = None,
    params: Mapping[str, Any] | None = None,
    headers: Mapping | None = None,
    cookies: httpx._types.CookieTypes | None = None,
    auth: httpx._types.AuthTypes | httpx._client.UseClientDefault | None = httpx.USE_CLIENT_DEFAULT,
    follow_redirects: bool | httpx._client.UseClientDefault = httpx.USE_CLIENT_DEFAULT,
    timeout: httpx._types.TimeoutTypes | httpx._client.UseClientDefault = httpx.USE_CLIENT_DEFAULT,
    extensions: httpx._types.RequestExtensions | None = None,
  ):
    return await self.http.request(
      method, self.base_url + path, params=params, headers=headers, cookies=cookies, json=json,
      content=content, data=data, files=files, auth=auth, follow_redirects=follow_redirects,
      timeout=timeout, extensions=extensions,
    )