from dataclasses import dataclass
from typing_extensions import Any, Mapping
import httpx

from ethereum.core import HttpClient, HttpMixin

@dataclass
class AuthHttpClient(HttpClient):
  api_key: str

  async def authed_request(
    self, method: str, url: str,
    *,
    content: httpx._types.RequestContent | None = None,
    data: httpx._types.RequestData | None = None,
    files: httpx._types.RequestFiles | None = None,
    json: Any | None = None,
    params: httpx._types.QueryParamTypes | None = None,
    headers: Mapping[str, str] | None = None,
    cookies: httpx._types.CookieTypes | None = None,
    auth: httpx._types.AuthTypes | httpx._client.UseClientDefault | None = httpx.USE_CLIENT_DEFAULT,
    follow_redirects: bool | httpx._client.UseClientDefault = httpx.USE_CLIENT_DEFAULT,
    timeout: httpx._types.TimeoutTypes | httpx._client.UseClientDefault = httpx.USE_CLIENT_DEFAULT,
    extensions: httpx._types.RequestExtensions | None = None,
  ):
    params = {'apikey': self.api_key, **(params or {})}
    return await self.request(
      method, url, headers=headers, params=params, json=json,
      content=content, data=data, files=files, auth=auth,
      follow_redirects=follow_redirects, cookies=cookies,
      timeout=timeout, extensions=extensions,
    )
  
  
@dataclass
class AuthHttpMixin(HttpMixin):
  base_url: str
  auth_http: AuthHttpClient

  def __init__(self, *, base_url: str, auth_http: AuthHttpClient):
    self.base_url = base_url
    self.http = self.auth_http = auth_http

  @classmethod
  def new(cls, api_key: str, api_secret: str, *, base_url: str):
    client = AuthHttpClient(api_key=api_key, api_secret=api_secret)
    return cls(base_url=base_url, auth_http=client)
  
  async def __aenter__(self):
    await self.auth_http.__aenter__()
    return self
  
  async def __aexit__(self, exc_type, exc_value, traceback):
    await self.auth_http.__aexit__(exc_type, exc_value, traceback)

  async def authed_request(
    self, method: str, path: str = '',
    *,
    content: httpx._types.RequestContent | None = None,
    data: httpx._types.RequestData | None = None,
    files: httpx._types.RequestFiles | None = None,
    json: Any | None = None,
    params: httpx._types.QueryParamTypes | None = None,
    headers: Mapping[str, str] | None = None,
    cookies: httpx._types.CookieTypes | None = None,
    auth: httpx._types.AuthTypes | httpx._client.UseClientDefault | None = httpx.USE_CLIENT_DEFAULT,
    follow_redirects: bool | httpx._client.UseClientDefault = httpx.USE_CLIENT_DEFAULT,
    timeout: httpx._types.TimeoutTypes | httpx._client.UseClientDefault = httpx.USE_CLIENT_DEFAULT,
    extensions: httpx._types.RequestExtensions | None = None,
  ):
    return await self.auth_http.authed_request(
      method, self.base_url + path, headers=headers, json=json,
      content=content, data=data, files=files, auth=auth,
      follow_redirects=follow_redirects, cookies=cookies,
      timeout=timeout, extensions=extensions, params=params,
    )