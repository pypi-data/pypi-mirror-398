from typing_extensions import Literal
from dataclasses import dataclass
from datetime import datetime

from .core import ApiMixin, response_validator

validate_response = response_validator(int)

@dataclass
class BlockByTime(ApiMixin):
  async def block_by_time(
    self, time: datetime, chain_id: int = 1, *,
    closest: Literal['before', 'after'] = 'before',
    validate: bool | None = None,
  ) -> int:
    """Retrieves the block number mined at a specific timestamp.
    
    Args:
    - `time`: The time to get the block for.
    - `chain_id`: The chain ID to get the block for. You can see supported chains [here](https://docs.etherscan.io/supported-chains).
    - `closest`: Whether to get the closest block before or after the given time.
    - `validate`: Whether to validate the response.

    > [Etherscan API Docs](https://docs.etherscan.io/api-reference/endpoint/getblocknobytime)
    """
    r = await self.authed_request(
      'GET', params={
      'module': 'block',
      'action': 'getblocknobytime',
      'timestamp': int(time.timestamp()),
      'chainid': chain_id,
      'closest': closest,
    })
    block = self.output(r.text, validate_response, validate=validate)
    return int(block)