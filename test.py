from contracts import deploy
from web3 import Web3, HTTPProvider, IPCProvider
from wallet import Wallet, ZKToken
from composer import NaiveStrategy
from commitments import Commitment, Note
import random

n = 32
Alice = 'Alice'
Bob = 'Bob'
provider = HTTPProvider('http://127.0.0.1:8545', request_kwargs={'timeout': 120})
web3 = Web3(provider)
web3.eth.defaultAccount = web3.eth.accounts[0]


def test_confidential_transaction():
  from pysolcrypto.altbn128 import randsn, FQ, multiply as ecmul, add as ecadd
  print('bit size: ' + str(n))
  contract = ZKToken.deploy(web3, n)
  wallet_alice = Wallet('Alice', contract, notes=[], composer=None)
  gas_receipt = wallet_alice.quick_setup(NaiveStrategy)
  print('\nAlice setup\n' + gas_receipt)
  wallet_bob = Wallet('Bob', contract, notes=[], composer=None)
  print('\nBob setup\n' + gas_receipt)
  gas_receipt = wallet_bob.quick_setup(NaiveStrategy)
  receipt = wallet_alice.deposit(3.0)
  print('\nAlice is to deposit 3 eth' + '\ngas cost: ' + str(receipt.gasUsed))
  receipt = wallet_alice.deposit(8.0)
  print('\nAlice is to deposit 8 eth' + '\ngas cost: ' + str(receipt.gasUsed))
  print('\nbalances ' + '\nAlice: ' + str(wallet_alice.balance()) + ' eth' 
  + '\nBob: ' + str(wallet_bob.balance()) + ' eth' 
  + '\nContract: ' + str(Web3.fromWei(web3.eth.getBalance(contract.address), 'ether')) + ' eth')
  print('\nAlice is to send 10 eth to Bob')
  tx = wallet_alice.make_ct_phase_1(10.0)
  tx = wallet_bob.make_ct_phase_2(tx)
  receipt = tx.broadcast()
  print('2 input, 2 output transaction' + '\ngas cost: ' + str(receipt.gasUsed))
  for input in tx.inputs_of('Alice'):
    assert contract.get_note(input) == 0
  for output in tx.outputs_of('Alice'):
    note = Commitment.aggregate([wallet_alice.get_commitment(index) for index in output])
    assert note.y() == contract.get_note(note.x())
  for output in tx.outputs_of('Bob'):
    note = Commitment.aggregate([wallet_bob.get_commitment(index) for index in output])
    assert note.y() == contract.get_note(note.x())
  wallet_alice.update(tx)
  wallet_bob.update(tx)
  print('\nbalances ' + '\nAlice: ' + str(wallet_alice.balance()) + ' eth' 
  + '\nBob: ' + str(wallet_bob.balance()) + ' eth' 
  + '\nContract: ' + str(Web3.fromWei(web3.eth.getBalance(contract.address), 'ether')) + ' eth')
  receiver = Web3.toChecksumAddress(Web3.toHex(Web3.sha3(random.randint(1, 44000))[-20:]))
  receipt = wallet_bob.withdraw(4.0, receiver)
  print('\nBob withdraws 4 eth' + '\ngas cost: ' + str(receipt.gasUsed))
  assert Web3.toWei(4.0, 'ether') == web3.eth.getBalance(receiver)
  print('\nbalances ' + '\nAlice: ' + str(wallet_alice.balance()) + ' eth' 
  + '\nBob: ' + str(wallet_bob.balance()) + ' eth' 
  + '\nContract: ' + str(Web3.fromWei(web3.eth.getBalance(contract.address), 'ether')) + ' eth'
  + '\nReceiver of the withdrawal: ' + str(Web3.fromWei(web3.eth.getBalance(receiver), 'ether')) + ' eth')
  print()
  print('fin')


test_confidential_transaction()