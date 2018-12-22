from pysolcrypto.borromean import borromean_ring_sign
from pysolcrypto.altbn128 import mpasint, pasint, randsn, G1, add as ecadd, multiply as ecmul, curve_order
from pysolcrypto.schnorr import schnorr_create
from web3 import Web3

from commitments import BitCommitment, Commitment, Note
from zktoken import ZKToken
from transaction import Transaction


class Wallet:

  def __init__(self, id, contract, notes=[], composer=None):
    self.id = id
    self.composer = composer
    self.contract = contract
    self.n = contract.n()
    self.notes = notes
    self.converter = self.Converter(contract)

  def quick_setup(self, composer_class):
    gas_receipt = ''
    bit_commitments, e, s_mat = composer_class.make_bit_commitments(self.n, 0)
    receipt = self.contract.store_bits(bit_commitments, s_mat, e)
    gas_receipt = 'store bits, # of bit commitments: ' + str(len(bit_commitments)) + '\ngas cost: ' + str(receipt.gasUsed)
    endIndex = self.contract.parse_log_bit_commitment_store(receipt)['endIndex']
    m = len(bit_commitments)
    for i in range(m):
      index = endIndex - m + i
      assert bit_commitments[i].set_index(index).eq(self.contract.get_bit_commitment(index))
    commitments = composer_class.make_commitments(self.n, bit_commitments)
    receipt = self.contract.compose_from_bits(commitments)
    gas_receipt += '\ncompose from bits, # of commitments: ' + str(len(commitments)) + '\ngas cost: ' + str(receipt.gasUsed)
    endIndex = self.contract.parse_log_pre_commitment_store(receipt)['endIndex']
    m = len(commitments)
    for i in range(m):
      index = endIndex - m + i
      assert commitments[i].set_index(index).eq(self.contract.get_commitment(index))
    self.composer = composer_class(self.n, bit_commitments, commitments)
    return gas_receipt

  # value in ether
  def deposit(self, value):
    r = randsn()
    s, e = schnorr_create(r, G1)
    rG = ecmul(G1, r)
    output = Note(self.converter.to_token(value), r)
    receipt = self.contract.deposit(rG, s, e, Web3.toWei(value, "ether"))
    y = self.contract.get_note(output.x())
    assert output.C()[1].n == y
    self.add_notes(output)
    return receipt

  def withdraw(self, claim, receiver):
    claim = self.converter.to_token(claim)
    inputs, residue, blinding_sum_in = self.composer.ct_inputs(self.notes, claim)
    residue_coms, blinding_sum_out = self.composer.ct_outputs(residue)
    excess_value = (blinding_sum_out - blinding_sum_in) % curve_order
    excess = ecmul(G1, excess_value)
    s, e = schnorr_create(excess_value, G1)
    receipt = self.contract.withdraw(inputs, residue_coms, claim, receiver, excess, s, e)
    output = Commitment.aggregate(residue_coms)
    y = self.contract.get_note(output.x())
    assert output.C()[1].n == y
    self.add_notes(output)
    for input in inputs:
      y = self.contract.get_note(input.x())
      assert y == 0
      self.remove_notes(input)
    return receipt

  def make_ct_phase_1(self, value):
    value = self.converter.to_token(value)
    inputs, change, blinding_sum_in = self.composer.ct_inputs(self.notes, value)
    output_coms, blinding_sum_out = self.composer.ct_outputs(change)
    tx = Transaction(value, self.contract)
    tx.add_inputs([i.x() for i in inputs], self.id)
    tx.add_outputs([[o.index for o in output_coms]], self.id)
    tx.blinding_sum = blinding_sum_in - blinding_sum_out
    return tx

  def make_ct_phase_2(self, tx):
    # no input here
    output_coms, blinding_sum_out = self.composer.ct_outputs(tx.value)
    tx.add_outputs([[o.index for o in output_coms]], self.id)
    excess_value = (tx.blinding_sum - blinding_sum_out) % curve_order
    excess = ecmul(G1, excess_value)
    s, e = schnorr_create(excess_value, G1)
    tx.set_excess(excess, s, e)
    return tx

  def update(self, tx):

    #self.remove_notes([self.get_note(x) for x in tx.inputs_of(self.id)])
    for input_x in tx.inputs_of(self.id):
      assert self.contract.get_note(input_x) == 0
      self.remove_notes(input_x)

    #self.add_notes([Commitment.aggregate([self.get_commitment(i) for i in output]) for output in tx.outputs_of(self.id)])
    for output in tx.outputs_of(self.id):
      note = Commitment.aggregate([self.get_commitment(index) for index in output])
      assert note.y() == self.contract.get_note(note.x())
      self.add_notes(note)

  def add_notes(self, note):
    if isinstance(note, Commitment):
      note.__class__ = Note
      self.notes.append(note)
    elif isinstance(note, list):
      for n in note:
        self.add_notes(n)

  def remove_notes(self, note):
    if isinstance(note, Commitment):
      if note in self.notes:
        self.notes.remove(note)
    elif isinstance(note, int):
      self.remove_notes(self.get_note(note))
    elif isinstance(note, list):
      for notes in notes:
        self.remove_notes(note)

  def get_note(self, x):
    for o in self.notes:
      if o.x() == x:
        return o
    return None

  # return in wei
  def balance(self):
    return self.converter.to_eth(sum([note.value for note in self.notes]))

  def get_commitment(self, x_or_index):
    return self.composer.get_commitment(x_or_index)

  class Converter:

    def __init__(self, contract):
      self.n = contract.n()
      self.base = contract.base_wei()
      self.step = contract.step_wei()
      self.max = contract.max_wei()

    def to_eth(self, value):
      return float(Web3.fromWei(self.base + (value - 1) * self.step, "ether"))

    def to_wei(self, value):
      return self.base + (value - 1) * self.step

    def to_token(self, value):
      value = Web3.toWei(value, "ether")
      return 1 + (value - self.base) // self.step if (value > self.base or value < self.max) else None
