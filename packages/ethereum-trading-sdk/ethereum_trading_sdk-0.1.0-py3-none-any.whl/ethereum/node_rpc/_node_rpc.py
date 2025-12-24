from dataclasses import dataclass
from .eth_balance import EthBalance
from .token_balance import Token

@dataclass
class NodeRpc(
  EthBalance,
  Token,
):
  ...