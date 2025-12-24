from dataclasses import dataclass
from decimal import Decimal
from web3 import Web3

from ethereum.node_rpc.core import NodeRpcMixin

@dataclass
class EthBalance(NodeRpcMixin):
  async def eth_balance(self, address: str) -> Decimal:
    """Get the ETH balance of an address."""
    wei_balance = await self.client.eth.get_balance(address)
    return Web3.from_wei(wei_balance, 'ether')