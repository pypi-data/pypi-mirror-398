from typing_extensions import TypeVar, overload, Literal, Any
from dataclasses import dataclass, field
import json
import os

from ethereum.core import ValidationMixin, validator, ApiError
from . import AuthHttpMixin, AuthHttpClient, Response, is_ok

T = TypeVar('T')
E = TypeVar('E', default=Any)
AnyT: type = Any # type: ignore

ETHERSCAN_API_URL = 'https://api.etherscan.io/v2/api'

def response_validator(type: type[T], err_type: type[E] = AnyT) -> validator[Response[T, E]]:
  return validator(Response[type, err_type])

@dataclass
class BaseMixin(ValidationMixin):
  @overload
  def output(
    self, data: str | bytes, validator: validator[Response[T, E]], *,
    validate: bool | None, raw: Literal[False] = False
  ) -> T:
    ...
  @overload
  def output(
    self, data: str | bytes, validator: validator[Response[T, E]], *,
    validate: bool | None, raw: Literal[True]
  ) -> Response[T, E]:
    ...
  def output(
    self, data: str | bytes, validator: validator[Response[T, E]], *,
    validate: bool | None, raw: bool = False
  ):
    obj = validator(data) if self.validate(validate) else json.loads(data)
    if raw:
      return obj
    if not is_ok(obj):
      raise ApiError(obj)
    return obj['result']

@dataclass
class ApiMixin(BaseMixin, AuthHttpMixin):
  base_url: str = field(kw_only=True, default=ETHERSCAN_API_URL)

  @classmethod
  def new(
    cls, api_key: str | None = None, *,
    base_url: str = ETHERSCAN_API_URL, validate: bool = True,
  ):
    if api_key is None:
      api_key = os.environ['ETHERSCAN_API_KEY']
    client = AuthHttpClient(api_key=api_key)
    return cls(base_url=base_url, auth_http=client, default_validate=validate)