from .altbn128 import *

def schnorr_create(secret, point=None):
  r = randsn()
  R = multiply(point, r) if point else sbmul(r)
  e = hashs(R[0].n, R[1].n)
  s = submodn(r, mulmodn(secret, e))
  return s, e 

def schnorr_verify(P, s, e, point=None):
  sG = multiply(point, s) if point else sbmul(s)
  eP = multiply(P, e)
  R_ = add(sG, eP)
  e_ = hashs(R_[0].n, R_[1].n)
  return e_ == e