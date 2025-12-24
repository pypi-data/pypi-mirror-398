from dataclasses import dataclass
from decimal import Decimal
from functools import cached_property

from web3 import Web3, AsyncWeb3
from web3.contract import AsyncContract

from ethereum.node_rpc.core import NodeRpcMixin

ERC20_ABI = [
  {'constant': True, 'inputs': [{'name': 'owner', 'type': 'address'}],
    'name': 'balanceOf', 'outputs': [{'name': '', 'type': 'uint256'}],
    'type': 'function'},
  {'constant': True, 'inputs': [], 'name': 'decimals',
    'outputs': [{'name': '', 'type': 'uint8'}], 'type': 'function'},
  {'constant': True, 'inputs': [], 'name': 'symbol',
    'outputs': [{'name': '', 'type': 'string'}], 'type': 'function'},
]

@dataclass(frozen=True)
class ERC20:
  address: str
  w3: AsyncWeb3

  @cached_property
  def checksum_address(self) -> str:
    return Web3.to_checksum_address(self.address)

  @cached_property
  def contract(self) -> AsyncContract:
    return self.w3.eth.contract(address=self.checksum_address, abi=ERC20_ABI)

  async def symbol(self) -> str:
    return await self.contract.functions.symbol().call()

  async def decimals(self) -> int:
    return await self.contract.functions.decimals().call()

  async def raw_balance(self, address: str) -> int:
    address = Web3.to_checksum_address(address)
    return await self.contract.functions.balanceOf(address).call()

  async def balance(self, address: str) -> Decimal:
    raw_balance = await self.raw_balance(address)
    decimals = await self.decimals()
    return Decimal(raw_balance) / Decimal(10)**decimals


@dataclass
class Token(NodeRpcMixin):
  def token(self, address: str) -> ERC20:
    """A convenient wrapper for the ERC-20 interface."""
    return ERC20(address=address, w3=self.client)

  async def token_balance(self, address: str, *, token_address: str) -> Decimal:
    """Get the address' balance of a given ERC-20 token."""
    return await ERC20(address=token_address, w3=self.client).balance(address)