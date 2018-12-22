```bash
vitrualenv -p python3 venv && ./venv/bin/activate
pip install py_ecc web3 future pysha3 numpy
./ganache/run.sh
python test.py
```

### Rationale

In most confidential transaction schemes, range proof is required for each output. Range proofs guarantee that outputs are not negative values. Verification of range proofs require numbers of elliptic curve multiplication operation which generates a major gas cost. As can be seen in [this table](https://github.com/solidblu1992/RingCTToken/blob/master/other/GasCosts.xlsx) bulletproofs and borromean ring signatures cost millions of gas for a reasonable size of n (16 or 32).

We tried to reduce range proof verification cost of join split confidential transactions on Ethereum contract. The main idea that we propose is to use commitments that are verified and stored in advance.

Instead of providing a range-proof for each transaction output, already verified and stored commitments can be used to compose an output value. In this way, composition requires only elliptic curve addition operations which is very affordable.


### Two Phase Setup

Each user must have her own set of reusable and verified pre-commitment set. Storing precommitments requires a setup which takes place in two phases.


####  Storing Bit Commitments

```
rG + {0,1}H
```

We firstly need store bit commitments to the contract. These bits will be used to compose pre-commitments. Note that the same bit can be used many times composing a pre-commitment.

Bit commitments are verified onchain using conventional techniques such as bulletproofs or borromean ring signatures. In this demonstration, we simply used borromean ring signatures. Bit commitments are stored in a map with an index. 


#### Composing Pre-commitments

We need pre-commitments to compose an actual output value in transactions. Each pre-commitments is composed of a bit commitment array without elliptic curve multiplication. Composed pre-commitments are also stored in a map with an index.

```python
sum = 0
for b in bit_array.reverse():
  sum = sum + sum + b
```


### Ownership

Notes are pedersen commitments. Similar to mimblewimble protocol, knowledge of blinding factor is defined as ownership.


### Transaction

Transactors provide  

* input notes
* pre-commitment index arrays
* a signature on excess value `(r_excess*G)`.

Input notes are notes that are going to be spent.

A precommitment index array is used to compose an output. It is like to say that I would like to use [5th, 19th, 3007th, ..] pre-commitments to compose an output. An output is composed by only adding of pre-commitments which are provided in the index array. Indexes of pre-commitments can be provided in any order since they always sum up to the same value. Precommitment index arrays are fixed sized and equal to the bit size of the protocol so that a composed output value definitely stays in a range without overflowing.

[Excess value](https://github.com/mimblewimble/grin/blob/master/doc/intro.md#ownership) is needed to hide blinding factors of outputs among transactors.

Transaction will be successful if `(input sum) == (output sum + excess value)`.  

To avoid the situation that receiver composes an output commitment that sender already knows its opening, both party may come up with inputs. 


### Performance & Implementation Details

Two input, two output 32 bit transaction costs around 330000 gas. It also contains schnorr signature verification on the excess value which costs slightly more than 80.000 gas.

Bit commitments and pre-commitments are indexed incrementally starting from 1, so as to benefit from low 0-byte input cost. Outputs are mappings from x to y.


### Precommitment strategy

#### Naive strategy

We implemented a simple strategy that a wallet has pre-commitments to the `2^n` vector `[1, 2, 4, 8, .. 2^(n-1)]` and `n` pre-commitments to `0`. So that any value in `[0,2^n)` can be constructed.

#### Cashlike strategy

Instead of having pre-commitments to different values, constructing a set with many 1s, 2s, 5s, 10s, 20s, 50s ... might be a better idea to obstruct attacker's guesses on openings of pre-commitments.


### Problems

* Transactors cannot be shielded since each of them her own stored commitment sets that are expected to be used in long-term.

* Commitment strategy is definitely a metric for privacy. For example in the naive implementation attacker may easily guess which precommitment might be `(2^31 for n=32)` that would not be used often. In order to use the same commitment set for long term, can we propose a publicly defined strategy that is resilient to pattern recognition?

* High cost of setup phase.