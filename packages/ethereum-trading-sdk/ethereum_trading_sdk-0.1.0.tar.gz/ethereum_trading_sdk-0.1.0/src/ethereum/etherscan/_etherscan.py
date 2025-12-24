from dataclasses import dataclass

from .block_by_time import BlockByTime
from .token_transactions import TokenTransactions
from .transactions import Transactions
from .transaction_by_hash import TransactionByHash

@dataclass
class Etherscan(
  BlockByTime,
  Transactions,
  TokenTransactions,
  TransactionByHash,
):
  ...