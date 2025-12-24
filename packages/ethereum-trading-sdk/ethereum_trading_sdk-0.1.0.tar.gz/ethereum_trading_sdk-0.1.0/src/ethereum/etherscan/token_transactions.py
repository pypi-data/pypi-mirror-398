from typing_extensions import AsyncIterable, TypedDict
from dataclasses import dataclass
from decimal import Decimal

from ethereum.core import wei2eth, ApiError
from .core import ApiMixin, response_validator, is_ok

From = TypedDict('From', {'from': str})

class TokenTransaction(From):
  blockNumber: str
  timeStamp: str
  hash: str
  nonce: str
  blockHash: str
  contractAddress: str
  to: str
  value: str
  tokenName: str
  tokenSymbol: str
  tokenDecimal: str
  transactionIndex: str
  gas: str
  gasPrice: str
  gasUsed: str
  cumulativeGasUsed: str
  input: str
  methodId: str
  functionName: str
  confirmations: str

def token_value(tx: TokenTransaction) -> Decimal:
  return Decimal(tx['value']) / Decimal(10**int(tx['tokenDecimal']))

validate_response = response_validator(list[TokenTransaction])

@dataclass
class TokenTransactions(ApiMixin):
  async def token_transactions(
    self, address: str, chain_id: int = 1, *,
    start_block: int = 0,
    end_block: int = 99999999,
    page: int = 1,
    offset: int = 20,
    validate: bool | None = None,
  ) -> list[TokenTransaction]:
    """Retrieves the transaction history of a specified address.
    
    Args:
    - `address`: The address to get transactions for.
    - `chain_id`: The chain ID to get transactions for. You can see supported chains [here](https://docs.etherscan.io/supported-chains).
    - `start_block`: The start block to get transactions for.
    - `end_block`: The end block to get transactions for.
    - `page`: Index for pagination.
    - `offset`: Number of transactions per page.
    - `validate`: Whether to validate the response.

    > [Etherscan API Docs](https://docs.etherscan.io/api-reference/endpoint/tokentx)
    """
    r = await self.authed_request(
      'GET', params={
      'module': 'account',
      'action': 'tokentx',
      'address': address,
      'startblock': start_block,
      'endblock': end_block,
      'page': page,
      'offset': offset,
      'chainid': chain_id,
    })
    r = self.output(r.text, validate_response, validate=validate, raw=True)
    if is_ok(r) or r['result'] == []:
      return r['result']
    else:
      raise ApiError(r)

  async def token_transactions_paged(
    self, address: str, chain_id: int = 1, *,
    start_block: int = 0,
    end_block: int = 99999999,
    offset: int = 20,
    validate: bool | None = None,
  ) -> AsyncIterable[list[TokenTransaction]]:
    """Retrieves the transaction history of a specified address, automatically paginating results.
    
    Args:
    - `address`: The address to get transactions for.
    - `chain_id`: The chain ID to get transactions for. You can see supported chains [here](https://docs.etherscan.io/supported-chains).
    - `start_block`: The start block to get transactions for.
    - `end_block`: The end block to get transactions for.
    - `offset`: Number of transactions per page.
    - `validate`: Whether to validate the response.
    """
    page = 1
    while True:
      txs = await self.token_transactions(address, chain_id, start_block=start_block, end_block=end_block, page=page, offset=offset, validate=validate)
      if not txs:
        break
      yield txs
      if len(txs) < offset:
        break
      page += 1

  async def token_transactions_paged_sync(
    self, address: str, chain_id: int = 1, *,
    start_block: int = 0,
    end_block: int = 99999999,
    offset: int = 20,
    validate: bool | None = None,
  ) -> list[TokenTransaction]:
    """Retrieves the transaction history of a specified address, automatically paginating results.
    
    Args:
    - `address`: The address to get transactions for.
    - `chain_id`: The chain ID to get transactions for. You can see supported chains [here](https://docs.etherscan.io/supported-chains).
    - `start_block`: The start block to get transactions for.
    - `end_block`: The end block to get transactions for.
    - `offset`: Number of transactions per page.
    - `validate`: Whether to validate the response.
    """
    return [
      tx async for chunk in self.token_transactions_paged(address, chain_id, start_block=start_block, end_block=end_block, offset=offset, validate=validate)
      for tx in chunk
    ]