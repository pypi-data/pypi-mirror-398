from typing_extensions import TypedDict, Generic, TypeVar, Literal, TypeGuard, Any
from decimal import Decimal

from ethereum.core import wei2eth

T = TypeVar('T')
E = TypeVar('E', default=Any)

class OkResponse(TypedDict, Generic[T]):
  status: Literal['1']
  message: str
  result: T

class ErrResponse(TypedDict, Generic[E]):
  status: Literal['0']
  message: str
  result: E

Response = OkResponse[T] | ErrResponse[E]

def is_ok(r: Response[T]) -> TypeGuard[OkResponse[T]]:
  return r['status'] == '1'

class Value(TypedDict):
  value: str
  """Ether value [wei]"""

def tx_value(tx: Value) -> Decimal:
  """Transaction value [ETH]"""
  return wei2eth(Decimal(tx['value']))

class GasFields(TypedDict):
  gas: str
  """Gas limit [gas]"""
  gasPrice: str
  """Gas price [wei/gas]"""
  gasUsed: str
  """Gas used [gas]"""
  cumulativeGasUsed: str
  """Cumulative gas used [gas]"""

def tx_fee(tx: GasFields) -> Decimal:
  """Transaction fee [ETH]"""
  used = Decimal(tx['gasUsed']) # gas
  price = Decimal(tx['gasPrice']) # wei/gas
  return wei2eth(price*used)