from .altbn128 import *
from .utils import hashs

hashx = lambda *x, msg: hashsn(*(masint(*x) + [msg] if msg is not None else masint(*x)))
masint = lambda *x: [asint(item) for sublist in x for item in sublist]

def borromean_ring_gen(n=4, m=[2, 2, 2, 2]):
  if isinstance(m, int):
    m = [m] * n
  assert len(m) == n
  from random import randint
  rings = []
  pairs = []
  for i in range(n):
    secrets = [randsn() for _ in range(m[i])]
    ring = [sbmul(s) for s in secrets]
    i = randint(0, m[i] - 1)
    rings.append(ring)
    pairs.append((ring[i], secrets[i]))
  return rings, pairs


def borromean_ring_verify(rings, e_0, s_mat, msg=None):
  assert isinstance(e_0, int)
  assert msg is None or isinstance(msg, int)
  assert len(rings) == len(s_mat) and len(rings) > 0
  R_0 = [(0, 0)] * len(rings)
  for i in range(len(rings)):
    e = e_0
    for j in range(len(rings[i])):
      assert len(s_mat[i]) == len(rings[i]) and len(rings[i]) > 0
      sG = multiply(G1, s_mat[i][j])
      eP = multiply(rings[i][j], e)
      R = add(sG, negp(eP))
      e = hashx(R, msg=msg)
    R_0[i] = R
  e_00 = hashx(*R_0, msg=msg)
  return e_0 == e_00


def borromean_ring_sign(rings, pairs, msg=None):
  assert msg is None or isinstance(msg, int)
  assert len(pairs) == len(rings) and len(rings) > 0
  n = len(rings)
  ring_s_mat = [[randsn() for p in ring] for ring in rings]
  ring_e_mat = [[0] * len(ring) for ring in rings]
  ring_alphas = [randsn() for _ in range(n)]
  # phase one: find the common e aka e_0
  R_i = [[(0, 0)] for _ in range(n)]
  for i in range(n):
    assert len(rings[i]) > 0
    j = rings[i].index(pairs[i][0])
    first_it = True
    while first_it or j != 0:
      if first_it:
        R_i[i] = multiply(G1, ring_alphas[i])
        first_it = False
      else:
        sG = multiply(G1, ring_s_mat[i][j])
        eP = multiply(rings[i][j], ring_e_mat[i][j])
        R_i[i] = add(sG, negp(eP))
      j = (j + 1) % len(rings[i])
      ring_e_mat[i][j] = hashx(R_i[i], msg=msg)
  e_0 = hashx(*R_i, msg=msg)
  # phase two: close the ring
  # TODO optimization required
  for i in range(n):
    j = rings[i].index(pairs[i][0])
    first_it = True
    for _ in range(len(rings[i])):
      e = 0
      if first_it:
        R = multiply(G1, ring_alphas[i])
        e = hashx(R, msg=msg)
        first_it = False
      else:
        sG = multiply(G1, ring_s_mat[i][j])
        eP = multiply(rings[i][j], ring_e_mat[i][j])
        R = add(sG, negp(eP))
        e = hashx(R, msg=msg)
      j = (j + 1) % len(rings[i])
      ring_e_mat[i][j] = e if j != 0 else e_0
    ring_s_mat[i][j] = addmodn(
        mulmodn(ring_e_mat[i][j], pairs[i][1]), ring_alphas[i])
  return e_0, ring_s_mat
