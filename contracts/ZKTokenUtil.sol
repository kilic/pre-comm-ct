pragma solidity 0.5.0;

import "./Curve.sol";

contract ZKTokenUtil {

  using Curve for Curve.G1Point;
  Curve.G1Point public H;

  constructor () public {
    uint256 h = uint256(keccak256(abi.encodePacked(Curve.G1().X, Curve.G1().Y))) % Curve.Q();
    H = Curve.HashToPoint(h);
  }

  function schnorrIdentify(uint256[2] memory pubkey, uint256 e, uint256 s) 
  internal view
  returns(bool){
    Curve.G1Point memory R = Curve.G1().g1mul(s).g1add(Curve.G1Point(pubkey[0], pubkey[1]).g1mul(e));
    return e == uint256(keccak256(abi.encodePacked(R.X,R.Y)));
    // G1Point memory R = g1add(g1mul(G1(), s), g1mul(G1Point(pubkey[0], pubkey[1]),e));
    // return e == uint256(keccak256(abi.encodePacked(R.X,R.Y)));
  }
}