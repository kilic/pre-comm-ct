from contracts import deploy
from web3 import Web3, HTTPProvider, IPCProvider
from wallet import Wallet, ZKToken
from composer import NaiveStrategy
from commitments import Commitment, Note

n = 8
provider = HTTPProvider('http://127.0.0.1:8545', request_kwargs={'timeout': 120})
web3 = Web3(provider)
web3.eth.defaultAccount = web3.eth.accounts[0]


def test_naive_bits_store():

  contract = ZKToken.deploy(web3, n)
  bit_commitments, e, s_mat = NaiveStrategy.make_bit_commitments(n, 0)
  receipt = contract.store_bits(bit_commitments, s_mat, e)
  log = contract.parse_log_bit_commitment_store(receipt)
  endIndex = log['endIndex']
  m = len(bit_commitments)
  for i in range(m):
    assert bit_commitments[i].eq(contract.get_bit_commitment(endIndex - m + i))


def test_naive_cmm_store():

  contract = ZKToken.deploy(web3, n)
  bit_commitments, e, s_mat = NaiveStrategy.make_bit_commitments(n, 0)
  receipt = contract.store_bits(bit_commitments, s_mat, e)
  log = contract.parse_log_bit_commitment_store(receipt)
  endIndex = log['endIndex']
  m = len(bit_commitments)
  for i in range(m):
    index = endIndex - m + i
    bit_commitments[i].set_index(index)
  commitments = NaiveStrategy.make_commitments(n, bit_commitments)
  receipt = contract.compose_from_bits(commitments)
  log = contract.parse_log_pre_commitment_store(receipt)
  endIndex = log['endIndex']
  m = len(commitments)
  for i in range(m):
    assert commitments[i].eq(contract.get_commitment(endIndex - m + i))


def test_quick_setup():

  contract = ZKToken.deploy(web3, n)
  wallet = Wallet('xyz', contract)
  gas_receipt = wallet.quick_setup(NaiveStrategy)


def test_deposit():

  from pysolcrypto.altbn128 import randsn, FQ, multiply as ecmul, add as ecadd
  contract = ZKToken.deploy(web3, n)
  wallet = Wallet('Alice', contract)
  value = 3.0
  receipt = wallet.deposit(value)
  bal = wallet.balance()
  assert bal == value


def test_withdraw():

  contract = ZKToken.deploy(web3, n)
  wallet = Wallet('xyz', contract)
  wallet.quick_setup(NaiveStrategy)
  value_deposit = 3.0
  _ = wallet.deposit(value_deposit)
  value_claim = 2.0
  receiver = Web3.toChecksumAddress('0xb656b2a9c3b2416437a811e07466ca712f5a5b5a')
  before_balance = web3.eth.getBalance(receiver)
  _ = wallet.withdraw(value_claim, receiver)
  assert Web3.toWei(value_claim, 'ether') == web3.eth.getBalance(receiver) - before_balance
