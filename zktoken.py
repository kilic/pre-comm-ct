class ZKToken:

  def __init__(self, web3, zk_token):
    self.web3 = web3
    self.zk_token = zk_token
    self.wait_tx = web3.eth.waitForTransactionReceipt
    self.address = zk_token.address

  def n(self):
    return self.zk_token.functions.N().call()

  def base_wei(self):
    return self.zk_token.functions.BaseWei().call()

  def step_wei(self):
    return self.zk_token.functions.StepWei().call()

  def max_wei(self):
    return self.zk_token.functions.MaxWei().call()

  def store_bits(self, bit_commitments, s_mat, e):
    from pysolcrypto.altbn128 import mpasint
    bit_commitments_ = [b.C() for b in bit_commitments]
    tx_hash = self.zk_token.functions.storeBits(mpasint(*bit_commitments_), s_mat, e).transact({'gas': 19000000})
    receipt = self.wait_tx(tx_hash)
    return receipt

  def compose_from_bits(self, commitments):
    bit_commitments = [[b.index for b in c.bit_commitments] for c in commitments]
    tx_hash = self.zk_token.functions.composeFromBits(bit_commitments).transact({'gas': 19000000})
    receipt = self.wait_tx(tx_hash)
    return receipt

  def get_note(self, x):
    return self.zk_token.functions.getNote(x).call()

  def get_commitment(self, i):
    return self.zk_token.functions.getCommitment(i).call()

  def get_bit_commitment(self, i):
    return self.zk_token.functions.getBitCommitment(i).call()

  def deposit(self, rG, e, s, value):
    from pysolcrypto.altbn128 import pasint
    tx_hash = self.zk_token.functions.deposit(pasint(rG), e, s).transact({'value': value})
    receipt = self.wait_tx(tx_hash)
    return receipt

  def ct(self, inputs, output_indexes, rG, e, s):
    from pysolcrypto.altbn128 import pasint
    tx_hash = self.zk_token.functions.ct(inputs, output_indexes, pasint(rG), e, s).transact()
    receipt = self.wait_tx(tx_hash)
    return receipt

  def withdraw(self, inputs, residue_comm, claim, receiver, rG, e, s):
    from pysolcrypto.altbn128 import pasint
    inputs = [i.x() for i in inputs]
    residue_comm = [i.index for i in residue_comm]
    tx_hash = self.zk_token.functions.withdraw(inputs, residue_comm, claim, receiver, pasint(rG), e, s).transact()
    receipt = self.wait_tx(tx_hash)
    return receipt

  def parse_log_bit_commitment_store(self, receipt):
    return self.zk_token.events.BitCommitmentStore().processReceipt(receipt)[0]['args']

  def parse_log_pre_commitment_store(self, receipt):
    return self.zk_token.events.PreCommitmentStore().processReceipt(receipt)[0]['args']

  @staticmethod
  def deploy(web3, n):
    from contracts import deploy
    contractName = 'ZKToken' + str(n)
    contract = deploy(web3, contractName)
    return ZKToken(web3, contract)
