from typing_extensions import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone

from web3.exceptions import ContractLogicError, BadFunctionCallOutput

from trading_sdk import ApiError
from trading_sdk.reporting import Snapshots as SnapshotsTDK, CurrencySnapshot

from ethereum.sdk.core import NodeRpcMixin

@dataclass
class Snapshots(SnapshotsTDK, NodeRpcMixin):
  async def snapshots(self, assets: Sequence[str] = []) -> list[CurrencySnapshot]:
    eth_balance = await self.client.eth_balance(self.address)
    time = datetime.now(timezone.utc)
    snapshots: list[CurrencySnapshot] = [CurrencySnapshot(asset='ETH', qty=eth_balance, time=time)]
    for asset in assets:
      if asset != 'ETH':
        try:
          balance = await self.client.token(asset).balance(self.address)
        except (ContractLogicError, BadFunctionCallOutput) as e:
          if self.ignore_bad_contracts:
            continue
          else:
            raise ApiError(f'Contract {asset} raised a logic error', *e.args) from e
        time = datetime.now(timezone.utc)
        snapshots.append(CurrencySnapshot(asset=asset, qty=balance, time=time))

    return snapshots