import json
import os


def deploy(w3, contractName, args=None):
  data = {}
  dir = os.path.dirname(os.path.realpath(__file__))
  with open(dir + '/combined.json') as f:
    data = f.read()
    import json
    contracts = json.loads(data)['contracts']
    contractName = ':' + contractName
    for k, v in contracts.items():
      if k.endswith(contractName):
        tx_hash = w3.eth.contract(abi=v['abi'], bytecode=v['bin']).constructor().transact({'gas': 3000000})
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
        return w3.eth.contract(address=tx_receipt.contractAddress, abi=v['abi'])
  return None