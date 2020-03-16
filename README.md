It was fun at that time to build an experimental confidential transaction scheme. However this proposal lack of many aspects of confidentiality.

Original readme as follows.

### Confidential Transactions with Reusable Commitments

We tried to reduce range-proof verification cost of confidential transactions on Ethereum contracts. The main idea that we are proposing is to use commitments that are verified and stored in advance multiple times. 

Doing so, we achieved to cut the cost of a simple 32-bit confidential transaction with two input and two output notes to 330000 gas.

In most confidential transaction schemes, coins or notes are represented as Pedersen commitments, instead of plain-text values. Pedersen commitments are additively homomorphic, so it is easy to check if input and output sum are equal. However, when one commits to negative number as an output value, input and output equation still holds. Therefore, transaction participants must provide range-proofs for each transaction output value to prove that they commit on a value which is not negative.

Although range-proof verification process consumes little time and energy on an average computer, it is still expensive on contracts on Ethereum blockchain since such processes require numbers of elliptic curve multiplication operation which comes with a significant gas cost. As shown [in the table](https://github.com/solidblu1992/RingCTToken/blob/master/other/GasCosts.xlsx) [bulletproofs](https://crypto.stanford.edu/bulletproofs/), [borromean ring signatures](https://github.com/Blockstream/borromean_paper) cost millions of gas for a reasonable bit size (eg. 16 or 32).

In this proposal, we argue that instead of providing a range-proof for each transaction output, already verified and stored commitments can be used to compose a transaction output value. In this way, a composition of an output value requires only group addition operations which are computationally [very affordable](https://github.com/ethereum/EIPs/blob/master/EIPS/eip-1108.md) on Ethereum blockchain.

Stored and verified commitments will be called as _pre-commitments_. Participants must have their own pre-commitments set to compose output notes. In order for users to store their own set, users initially must take two phase setup.

### Two Phase Setup

####  Storing Bit Commitments

First, we need store bit commitments to the contract. 

Here is how a bit commitment look like:

```
bit_commitment = rG + {0,1}H
```

Opening values of bit commitments must be either 1 or 0 to be verified on contract. Blinding factors (`r` values) are random numbers that are only known by an owner of a bit commitment. These stored bit commitments will be used to compose pre-commitments. A pre-commitment can be made with only bit commitments of which blinding factors are known. An arbitrary number of bit commitments can be stored. Bit commitments are verified on-chain using conventional techniques such as bulletproofs or borromean ring signatures. In this implementation, we simply used borromean ring signatures.


#### Composing Pre-commitments

Transaction participants use pre-commitments to compose actual transaction output values. Each pre-commitment is made up from a bit commitment array without group multiplication operation. A user can also compose and store an arbitrary number of pre-commitments.

Given a bit commitment array, a pre-commitment can be calculated simply by running the code below:

```python
sum = 0
for b in bit_array.reverse():
  sum = sum + sum + b
```

Since a pre-commitment is created with already verified bit-commitments, there is no need for a verification process.


### Ownership

##### Bit Commitments and Pre-commitments

Bit commitments and Pre-commitments are only used to compose actual number values of _notes_ which are valuable assets. They do not have inherent value inside but have a sense of ownership because a bit commitment or pre-commitment can be used only by a party who knows it opening and blinding factor values.

##### Notes

Notes represent valuable assets. They are also commitments made up by additions of pre-commitments. Similar to [Mimblewimble](https://github.com/mimblewimble/grin/blob/master/doc/intro.md) protocol, knowledge of blinding factor is defined as ownership. In a transaction input and output equality must hold for values on notes as mentioned before and the same equality also must hold for blinding factors. Without knowledge of blinding such equation cannot be built up.


### Transaction

Transaction participants provide input notes, pre-commitment index arrays and a signature on a excess value.

Input notes are notes that are going to be spent.

A pre-commitment index array is used to compose transaction output notes which are composed by only adding selected pre-commitments provided in the array. Providing indexes is like saying I would like to use [5th, 19th, 3007th, ..] pre-commitments to make up an output note. Indexes can be given in any order since they always sum up to the same value. Index arrays are fixed-size that have the same size with the bit size of the protocol, so that, a resulting output value definitely stays in a range without overflowing.

[Excess value](https://github.com/mimblewimble/grin/blob/master/doc/intro.md#ownership) is needed to hide blinding factors of outputs among parties in the transaction.

Transaction will be successful only if `(input sum) = (output sum + excess value)`.  

To avoid the situation that a receiver composes an output commitment that a sender already knows its opening, both parties may come up with input notes. 


### Performance and Implementation Details

A two inputs and two outputs 32-bit transaction costs around 330000 gas. The cost also contains Schnorr signature verification on the excess value which costs slightly more than 80000 gas.

Bit commitments and pre-commitments are stored in a mapping type with integer indexes which incrementally start from 1. Using a small numbers for indexes, we take advantage of a low 0-byte input gas cost. Notes are mappings from x coordinate to y coordinate.


### Pre-commitment Strategies

We would like a user to have the same pre-commitment set in use for the longest term possible. Using the same pre-commitment values multiple times will diminish the security of the set. In other words, an attacker will start guessing more accurately the openings of commitments in time. Therefore we need a strategy to make the attacker's work difficult.

#### Naive Strategy

We implemented a simple strategy that a wallet has pre-commitments to the `(2^n)` vector `[1, 2, 4, 8, .. 2^(n-1)]` and `n` sized pre-commitments to `0` value, where `n` is the bit size. So that any value in `[0,2^n)` can be constructed.

#### Cashlike Strategy

Instead of having pre-commitments to different values, like with `2^n` vector, constructing a set with many 1s, 2s, 5s, 10s, 20s, 50s ... will be a better strategy to eliminate the posibility of an attacker's guesses on openings of pre-commitments.


### Limitations

* Transaction participants cannot be shielded since each of them own a specific commitment sets that are expected to be used in the long-term.

* Commitment strategy is definitely related to the degree of privacy. For example, in the naive strategy an attacker may easily guess which pre-commitment might be `2^31` for `bit size = 32` which would not be used often. In order to use the same commitment set for a long-term, more publicly defined strategy that is resilient to pattern recognition should be proposed.

* High cost of setup phase could be reduced by using inner product proofs as in bulletproofs.

### Demo

Proposed approach is being demonstrated by [demo script](https://github.com/kilic/pre-comm-ct/blob/master/demo.py)

##### Demo setup

```bash
virtualenv -p python3 venv && . venv/bin/activate
pip install -r requirements.txt
npm install ganache-cli -g
```

##### Run the development chain and demo script

```bash
./ganache/run.sh
python demo.py
```
