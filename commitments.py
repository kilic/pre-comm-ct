from pysolcrypto.altbn128 import hashtopoint, G1, hashpn, hashp, addmodn, add as ecadd, multiply as ecmultiply, randsn, curve_order, asint


def pedersen_c(v, r=None):
  if r is None:
    r = randsn()
  return ecadd(ecmultiply(G1, r), ecmultiply(H(), v)), r


def H():
  h = hashpn(G1)
  return hashtopoint(h)


class Commitment:

  def __init__(self, value, blinding):
    self.value = value
    self.blinding = blinding

  def C(self):
    C, _ = pedersen_c(self.value, r=self.blinding)
    return C

  def x(self):
    return self.C()[0].n

  def y(self):
    return self.C()[1].n

  @staticmethod
  def aggregate(commitments):
    value, blinding = 0, 0
    for c in commitments:
      value, blinding = addmodn(value, c.value), addmodn(blinding, c.blinding)
    return Commitment(value, blinding)

  def eq(self, other):
    if isinstance(other, Commitment):
      return self.x() == other.x() and self.y() == other.y()
    elif not isinstance(other, list) or len(other) != 2:
      return False
    return self.x() == other[0] and self.y() == other[1]

  def __eq__(self, other):
    if isinstance(other, Commitment):
      return self.x() == other.x() and self.y() == other.y()
    return False

  def __lt__(self, other):
    return self.value < other.value


class PreCommitment(Commitment):

  def __init__(self, bit_commitments):
    self.bit_commitments = bit_commitments
    value, r = 0, 0
    for c in bit_commitments:
      r = addmodn(r, addmodn(r, c.blinding))
      value = value + value + c.value
    super().__init__(value, r)
    self.index = None

  def set_index(self, i):
    self.index = i
    return self


class Note(Commitment):

  def __init__(self, value, blinding):
    super().__init__(value, blinding)


class BitCommitment(Commitment):

  def __init__(self, value, blinding):
    super().__init__(value, blinding)
    self.index = None

  def set_index(self, i):
    self.index = i
    return self