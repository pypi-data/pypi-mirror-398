from typing_extensions import AsyncIterable, TypedDict
from dataclasses import dataclass

from ethereum.core import ApiError
from .core import ApiMixin, response_validator, is_ok

From = TypedDict('From', {'from': str})

class Transaction(From):
  blockNumber: str
  blockHash: str
  timeStamp: str
  hash: str
  nonce: str
  transactionIndex: str
  to: str
  value: str
  """Ether value [wei]"""
  gas: str
  gasPrice: str
  input: str
  methodId: str
  functionName: str
  contractAddress: str
  cumulativeGasUsed: str
  txreceipt_status: str
  gasUsed: str
  confirmations: str
  isError: str  

validate_response = response_validator(list[Transaction])

@dataclass
class Transactions(ApiMixin):
  async def transactions(
    self, address: str, chain_id: int = 1, *,
    start_block: int = 0,
    end_block: int = 99999999,
    page: int = 1,
    offset: int = 20,
    validate: bool | None = None,
  ) -> list[Transaction]:
    """Retrieves the transaction history of a specified address.
    
    Args:
    - `address`: The address to get transactions for.
    - `chain_id`: The chain ID to get transactions for. You can see supported chains [here](https://docs.etherscan.io/supported-chains).
    - `start_block`: The start block to get transactions for.
    - `end_block`: The end block to get transactions for.
    - `page`: Index for pagination.
    - `offset`: Number of transactions per page.
    - `validate`: Whether to validate the response.

    > [Etherscan API Docs](https://docs.etherscan.io/api-reference/endpoint/txlist)
    """
    r = await self.authed_request(
      'GET', params={
      'module': 'account',
      'action': 'txlist',
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

  async def transactions_paged(
    self, address: str, chain_id: int = 1, *,
    start_block: int = 0,
    end_block: int = 99999999,
    offset: int = 20,
    validate: bool | None = None,
  ) -> AsyncIterable[list[Transaction]]:
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
      txs = await self.transactions(address, chain_id, start_block=start_block, end_block=end_block, page=page, offset=offset, validate=validate)
      if not txs:
        break
      yield txs
      if len(txs) < offset:
        break
      page += 1