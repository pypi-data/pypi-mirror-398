from dataclasses import dataclass
from web3 import AsyncWeb3

@dataclass(kw_only=True)
class NodeRpcMixin:
  client: AsyncWeb3

  @classmethod
  def at(cls, rpc_url: str):
    client = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(rpc_url))
    return cls(client=client)
  
  async def __aenter__(self):
    await self.client.__aenter__()
    return self

  async def __aexit__(self, exc_type, exc_value, traceback):
    await self.client.__aexit__(exc_type, exc_value, traceback)