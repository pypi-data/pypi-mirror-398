from trading_sdk.types import Network, is_network

def parse_network(network: str) -> Network:
  if is_network(network):
    return network
  else:
    raise ValueError(f'Invalid network: {network}')
  
def parse_asset(asset: str) -> str:
  return asset.split('-')[0] # some assets have names like "USDT-ARB"