pragma solidity 0.5.0;
pragma experimental ABIEncoderV2;

import "./Curve.sol";

contract Borromean{
  using Curve for Curve.G1Point;
  Curve.G1Point public H;
  constructor () public {
    uint256 h = uint256(keccak256(abi.encodePacked(Curve.G1().X, Curve.G1().Y))) % Curve.Q();
    H = Curve.HashToPoint(h);
  }
  function Borr(uint256[2] memory pubkey, uint256 s, uint256 e)
  internal view 
  returns(uint256[2] memory){
    Curve.G1Point memory sG = Curve.G1().g1mul(s);
    Curve.G1Point memory eP = Curve.G1Point(pubkey[0], pubkey[1]).g1mul(e);
    Curve.G1Point memory R = sG.g1add(eP.g1neg());
    return [R.X, R.Y];
  }
  function Verify(
    uint256[2][][] memory rings,
    uint256[][] memory tees,
    uint256 e0)
  public view
  returns(bool)
  {
    uint256[2] memory R;
    uint256 n = rings.length;
    uint256[2][] memory R_0 = new uint[2][](n);
    for (uint256 i = 0; i < n; i ++){
      uint256 e = e0;
      for (uint256 j = 0; j < tees[i].length; j ++){
        R = Borr(rings[i][j], tees[i][j], e);
        e = uint256(keccak256(abi.encodePacked(R))) % Curve.N();
      }
      R_0[i] = R;
    }
    return e0 == (uint256(keccak256(abi.encodePacked(R_0))) % Curve.N());
  }
  function Bits(uint256[2][] memory bitCommitments, uint256[2][] memory tees, uint256 e0) 
  public view
  returns(bool){
    Curve.G1Point memory P0;
    Curve.G1Point memory P1;
    Curve.G1Point memory sG;
    Curve.G1Point memory eP;
    Curve.G1Point memory R;
    uint256[2][] memory R_0 = new uint[2][](bitCommitments.length);
    for(uint256 i; i < bitCommitments.length; i++){
      uint256 e = e0;
      P0 = Curve.G1Point(bitCommitments[i][0], bitCommitments[i][1]);
      P1 = Curve.g1add(P0, H.g1neg());
      sG = Curve.G1().g1mul(tees[i][0]);
      eP = P0.g1mul(e); 
      R = sG.g1add(eP.g1neg());
      e = uint256(keccak256(abi.encodePacked(R.X, R.Y))) % Curve.N();
      sG = Curve.G1().g1mul(tees[i][1]);
      eP = P1.g1mul(e);
      R = sG.g1add(eP.g1neg());
      R_0[i] = [R.X, R.Y];
    }
    return e0 == (uint256(keccak256(abi.encodePacked(R_0))) % Curve.N());
  }
}