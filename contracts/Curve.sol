// This file is MIT Licensed.
//
// From: https://gist.githubusercontent.com/chriseth/f9be9d9391efc5beb9704255a8e2989d/raw/4d0fb90847df1d4e04d507019031888df8372239/snarktest.solidity
// 
// Copyright 2017 Christian Reitwiessner
// Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
// The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

pragma solidity 0.5.0;

library Curve {
  
  // p = p(u) = 36u^4 + 36u^3 + 24u^2 + 6u + 1
  uint256 internal constant FIELD_ORDER = 0x30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd47;

  // Number of elements in the field (often called `q`)
  // n = n(u) = 36u^4 + 36u^3 + 18u^2 + 6u + 1
  uint256 internal constant GEN_ORDER = 0x30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001;

  uint256 internal constant CURVE_B = 3;

  // a = (p+1) / 4
  uint256 internal constant CURVE_A = 0xc19139cb84c680a6e14116da060561765e05aa45a1c72a34f082305b61f3f52;

	struct G1Point {
		uint X;
		uint Y;
	}

	// (P+1) / 4
	function A() internal pure returns (uint256) {
		return CURVE_A;
	}

	function P() internal pure returns (uint256) {
		return FIELD_ORDER;
	}

	function Q() internal pure returns (uint256) {
		return GEN_ORDER;
	}

	/// @return the generator of G1
	function G1() internal pure returns (G1Point memory) {
		return G1Point(1, 2);
	}

	function HashToPoint(uint256 s)
  internal view 
  returns (G1Point memory){
    uint256 beta = 0;
    uint256 y = 0;
    // XXX: Gen Order (n) or Field Order (p) ?
    uint256 x = s % GEN_ORDER;
    while( true ) {
      (beta, y) = FindYforX(x);
      // y^2 == beta
      if( beta == mulmod(y, y, FIELD_ORDER) ) {
          return G1Point(x, y);
      }
      x = addmod(x, 1, FIELD_ORDER);
    }
  }


    /**
    * Given X, find Y
    *
    *   where y = sqrt(x^3 + b)
    *
    * Returns: (x^3 + b), y
    */
    function FindYforX(uint256 x)
    internal view 
    returns (uint256, uint256) {
      // beta = (x^3 + b) % p
      uint256 beta = addmod(mulmod(mulmod(x, x, FIELD_ORDER), x, FIELD_ORDER), CURVE_B, FIELD_ORDER);
      // y^2 = x^3 + b
      // this acts like: y = sqrt(beta)
      uint256 y = expMod(beta, CURVE_A, FIELD_ORDER);

      return (beta, y);
    }


    function expMod(uint256 _base, uint256 _exponent, uint256 _modulus)
    internal view 
    returns (uint256 retval){
      bool success;
      uint256[1] memory output;
      uint[6] memory input;
      input[0] = 0x20;        // baseLen = new(big.Int).SetBytes(getData(input, 0, 32))
      input[1] = 0x20;        // expLen  = new(big.Int).SetBytes(getData(input, 32, 32))
      input[2] = 0x20;        // modLen  = new(big.Int).SetBytes(getData(input, 64, 32))
      input[3] = _base;
      input[4] = _exponent;
      input[5] = _modulus;
      assembly {
          success := staticcall(sub(gas, 2000), 5, input, 0xc0, output, 0x20)
          switch success case 0 { revert(0,0) }
      }
      require(success);
      return output[0];
    }

	function g1neg(G1Point memory p) 
  internal pure 
  returns (G1Point memory) {
		uint q = 21888242871839275222246405745257275088696311157297823662689037894645226208583;
		if (p.X == 0 && p.Y == 0)
			return G1Point(0, 0);
		return G1Point(p.X, q - (p.Y % q));
	}

	function g1add(G1Point memory p1, G1Point memory p2) 
  internal view 
  returns (G1Point memory r) {
		uint[4] memory input;
		input[0] = p1.X;
		input[1] = p1.Y;
		input[2] = p2.X;
		input[3] = p2.Y;
		bool success;
		assembly {
			success := staticcall(sub(gas, 2000), 6, input, 0xc0, r, 0x60)
			switch success case 0 { revert(0,0) }
		}
		require(success);
  }

	function g1mul(G1Point memory p, uint s) 
  internal view returns (G1Point memory r) {
		uint[3] memory input;
		input[0] = p.X;
		input[1] = p.Y;
		input[2] = s;
		bool success;
		assembly {
			success := staticcall(sub(gas, 2000), 7, input, 0x80, r, 0x60)
			switch success case 0 { revert(0,0) }
		}
		require (success);
	}


  function g1eq(G1Point memory p1, G1Point memory p2) 
  internal pure returns(bool){
    return p1.X == p2.X && p1.Y == p2.Y;
  }

  function g1isnull(G1Point memory p1)
  internal pure returns(bool){
    return p1.X == 0 || p1.Y == 0;
  }
}