from pysolcrypto.borromean import borromean_ring_sign
from commitments import BitCommitment, PreCommitment, pedersen_c, H
from pysolcrypto.altbn128 import mpasint, curve_order, add as ecadd, negp as ecneg


class NaiveStrategy():

  #def __init__(self, n, bit_commitments, commitments, outputs = {}):
  def __init__(self, n, bit_commitments, commitments):
    self.n = n
    self.bit_commitments = bit_commitments
    self.commitments = {}
    for c in commitments:
      if c.value not in self.commitments:
        self.commitments[c.value] = []
      self.commitments[c.value].append(c)

  def get_commitment(self, x_or_index):
    for _, l in self.commitments.items():
      for c in l:
        if c.x() == x_or_index or c.index == x_or_index:
          return c
    return None

  @staticmethod
  def make_bit_commitments(n, true_index):
    import numpy as np
    bit_vector = [0 if i != true_index else 1 for i in range(2 * n)]
    rings = [[[0, 0] for _ in range(2)] for _ in range(len(bit_vector))]
    pairs = []  ## TODO init
    blindings = []  ## TODO init
    bit_commitments = [[0, 0] for _ in range(len(bit_vector))]
    bit_commitments_ = []
    for i in range(len(bit_vector)):
      bit_value = bit_vector[i]
      bit_commitments[i], r = pedersen_c(bit_value)
      C_1 = ecadd(bit_commitments[i], ecneg(H()))
      rings[i] = [bit_commitments[i], C_1]
      pairs.append((rings[i][0 if bit_value == 0 else 1], r))
      blindings.append(r)
      bit_commitments_.append(BitCommitment(bit_value, r))
    e, s_mat = borromean_ring_sign(rings, pairs, msg=None)
    return bit_commitments_, e, s_mat

  @staticmethod
  def make_commitments(n, bit_commitments):
    import numpy as np
    to_commitment = lambda ndarray: PreCommitment(ndarray.tolist())
    arr = np.array([], dtype=BitCommitment)
    bit_vector = [bc for bc in bit_commitments]
    for i in range(n):
      arr = np.concatenate((arr, np.roll(bit_vector, i)))
    arr = arr.reshape(n, n * 2)
    np.random.shuffle(arr)
    arr = np.transpose(arr)
    np.random.shuffle(arr)
    return np.apply_along_axis(to_commitment, axis=1, arr=arr[:, :n * 2])

  # minimum number of input strategy
  def ct_inputs(self, outputs, target):
    import random
    outputs = sorted(outputs, reverse=True)
    selected = []
    total, blinding_sum = 0, 0
    for o in outputs:
      total += o.value
      blinding_sum = (blinding_sum + o.blinding) % curve_order
      selected.append(o)
      if total >= target:
        break
    if total < target:
      return None, None, None
    random.shuffle(selected)
    return selected, total - target, blinding_sum

  def ct_outputs(self, target):
    import random
    values = to_two_n(target, self.n)
    selected = []
    i = 0
    blinding_sum = 0
    while i < self.n:
      c = random.choice(self.commitments[values[i]])
      if c not in selected:
        selected.append(c)
        blinding_sum = (blinding_sum + c.blinding) % curve_order
        i += 1
    random.shuffle(selected)
    return selected, blinding_sum


class CashlikeStrategy():
  pass


def to_two_n(value, n):
  digits = []
  i = 0
  while i < n:
    i += 1
    if value == 0:
      digits.insert(0, 0)
      continue
    digits.insert(0, (value % 2) * 2**(i - 1))
    value = value // 2
  return digits