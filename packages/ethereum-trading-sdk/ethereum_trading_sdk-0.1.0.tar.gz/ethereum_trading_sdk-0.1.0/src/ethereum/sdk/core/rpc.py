from dataclasses import dataclass

from ethereum.node_rpc import NodeRpc

@dataclass
class NodeRpcMixin:
  client: NodeRpc
  address: str
  ignore_bad_contracts: bool = True

  @classmethod
  def at(cls, rpc_url: str, *, address: str, ignore_bad_contracts: bool = True):
    client = NodeRpc.at(rpc_url)
    return cls(client=client, address=address, ignore_bad_contracts=ignore_bad_contracts)
  
  async def __aenter__(self):
    await self.client.__aenter__()
    return self

  async def __aexit__(self, exc_type, exc_value, traceback):
    await self.client.__aexit__(exc_type, exc_value, traceback)