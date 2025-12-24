from typing_extensions import AsyncIterable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from collections import defaultdict
from datetime import datetime

from web3 import Web3

from trading_sdk.reporting import (
  Transactions as TransactionsTDK, Transaction,
  EthereumTransaction, ERC20Transfer,
  CurrencyPosting
)

from ethereum.sdk.core import EtherscanMixin
from ethereum.etherscan import tx_value, tx_fee, token_value
from ethereum.etherscan.transactions import Transaction as NativeTransaction
from ethereum.etherscan.token_transactions import TokenTransaction

def parse_native_transaction(tx: NativeTransaction, address: str, *, chain_id: int) -> Transaction:
  assert Web3.is_checksum_address(address), f'{address} is not a checksum address'
  value = tx_value(tx)
  fee = tx_fee(tx)
  time = datetime.fromtimestamp(int(tx['timeStamp']))
  to_addr = Web3.to_checksum_address(tx['to'])
  from_addr = Web3.to_checksum_address(tx['from'])
  assert address in (to_addr, from_addr), f'{address} not in transaction {tx}'
  s = 1 if to_addr == address else -1
  transaction = Transaction(
    id=f"{chain_id};native;{tx['hash']}",
    time=time,
    operation=EthereumTransaction(
      tx_hash=tx['hash'],
      from_address=from_addr,
      to_address=to_addr,
      value=value,
      fee=fee,
      chain_id=chain_id
    ),
    postings=[]
  )
  if address == from_addr:
    transaction.postings.append(CurrencyPosting(
      asset='ETH',
      change=-fee,
    ))
  if value > 0:
    transaction.postings.append(CurrencyPosting(
      asset='ETH',
      change=s*value,
    ))
  return transaction

async def native_transactions(
  self: EtherscanMixin, *, start: datetime, end: datetime
) -> AsyncIterable[Sequence[Transaction]]:
  kwargs = {}
  if start is not None:
    kwargs['start_block'] = await self.client.block_by_time(start, self.chain_id, closest='after')
  if end is not None:
    end = min(end, datetime.now())
    kwargs['end_block'] = await self.client.block_by_time(end, self.chain_id, closest='before')
  async for chunk in self.client.transactions_paged(self.address, self.chain_id, **kwargs):
    yield [parse_native_transaction(tx, self.address, chain_id=self.chain_id) for tx in chunk]


def parse_token_transaction(tx: TokenTransaction, address: str, *, chain_id: int, idx: int) -> Transaction:
  assert Web3.is_checksum_address(address), f'{address} is not a checksum address'
  value = token_value(tx)
  time = datetime.fromtimestamp(int(tx['timeStamp']))
  to_addr = Web3.to_checksum_address(tx['to'])
  from_addr = Web3.to_checksum_address(tx['from'])
  assert address in (to_addr, from_addr), f'{address} not in transaction {tx}'
  s = 1 if to_addr == address else -1
  contract_addr = Web3.to_checksum_address(tx['contractAddress'])
  return Transaction(
    id=f"{chain_id};erc20;{tx['hash']};{idx}",
    time=time,
    operation=ERC20Transfer(
      tx_hash=tx['hash'],
      from_address=from_addr,
      recipient_address=to_addr,
      contract_address=contract_addr,
      value=value,
      chain_id=chain_id
    ),
    postings=[CurrencyPosting(
      asset=contract_addr,
      change=s*value,
    )]
  )

async def token_transactions(
  self: EtherscanMixin, *, start: datetime, end: datetime,
  ignore_zero_value: bool = True
) -> AsyncIterable[Sequence[Transaction]]:
  kwargs = {}
  if start is not None:
    kwargs['start_block'] = await self.client.block_by_time(start, self.chain_id, closest='after')
  if end is not None:
    end = min(end, datetime.now())
    kwargs['end_block'] = await self.client.block_by_time(end, self.chain_id, closest='before')
  transactions = await self.client.token_transactions_paged_sync(self.address, self.chain_id, **kwargs)
  groups = defaultdict[str, list[TokenTransaction]](list)
  for tx in transactions:
    if not ignore_zero_value or Decimal(tx['value']) > 0:
      groups[tx['hash']].append(tx)

  for group in groups.values():
    yield [
      parse_token_transaction(tx, self.address, chain_id=self.chain_id, idx=i)
      for i, tx in enumerate(group)
    ]

@dataclass
class Transactions(EtherscanMixin, TransactionsTDK):
  async def transactions(
    self, *, start: datetime, end: datetime
  ) -> AsyncIterable[Sequence[Transaction]]:
    async for chunk in native_transactions(self, start=start, end=end):
      yield chunk
    async for chunk in token_transactions(self, start=start, end=end, ignore_zero_value=self.ignore_zero_value):
      yield chunk