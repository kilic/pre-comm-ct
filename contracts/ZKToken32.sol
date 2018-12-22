pragma solidity ^0.5.0;

import "./Curve.sol";
import "./ZKTokenUtil.sol";

contract ZKToken32 is ZKTokenUtil {
  
  uint256 public constant N = 32;
  // 10 ** 12 Wei, 0.000001 ETH, 1 Szabo
  uint256 public constant BaseWei = 1000000000000;
  // 10 ** 12 Wei, 0.000001 ETH, 1 Szabo
  uint256 public constant StepWei = 1000000000000;
  // ~ 4284 ETH
  uint256 public constant MaxWei = BaseWei + StepWei * ( 2 ** N );

  uint256 nb = 1;
  uint256 np = 1;
  mapping(uint256 => Curve.G1Point) preCommitments;
  mapping(uint256 => Curve.G1Point) bitCommitments;
  mapping(uint256 => uint256) notes;
  
  constructor () public ZKTokenUtil() {
  }

  event BitCommitmentStore(uint256 endIndex, uint256 vectorLen);
  function storeBits(uint256[2][] memory _bitCommitments, uint256[2][] memory tees, uint256 e0) 
  public {

    Curve.G1Point memory P0;
    Curve.G1Point memory P1;
    Curve.G1Point memory R;
    uint256[2][] memory R_0 = new uint[2][](_bitCommitments.length);
    uint256 e;
    uint256 nb_t = nb;
    for(uint256 i; i < _bitCommitments.length; i++){
      e = e0;
      P0 = Curve.G1Point(_bitCommitments[i][0], _bitCommitments[i][1]);
      P1 = P0.g1add(H.g1neg());
      R = Curve.G1().g1mul(tees[i][0]).g1add(P0.g1mul(e).g1neg());
      e = uint256(keccak256(abi.encodePacked(R.X, R.Y))) % Curve.Q();
      R = Curve.G1().g1mul(tees[i][1]).g1add(P1.g1mul(e).g1neg());
      R_0[i] = [R.X, R.Y];
      bitCommitments[nb_t] = P0;
      nb_t++;
    }
    nb = nb_t;
    require(e0 == (uint256(keccak256(abi.encodePacked(R_0))) % Curve.Q()), "invalid ring signature");
    emit BitCommitmentStore(nb, _bitCommitments.length);
  }

  event PreCommitmentStore(uint256 endIndex, uint256 vectorLen);
  function composeFromBits(uint256[N][] memory indexes)
  public {

    Curve.G1Point memory C;
    uint256 np_t = np;
    for(uint256 i = 0 ; i < indexes.length; i++){
      C = Curve.G1Point(0,0);
      for (uint256 j = 0; j < N ; j ++){
        C = C.g1add(C).g1add(bitCommitments[indexes[i][j]]);
      }
      preCommitments[np_t] = C;
      np_t++;
    }
    np = np_t;
    emit PreCommitmentStore(np, indexes.length);
  }

  event Deposit(address indexed sender, uint256 value, uint256 denominated);
  function deposit(uint256[2] memory rG, uint256 e, uint256 s) 
  public payable {
    
    require(msg.value > BaseWei && msg.value < MaxWei, "bad value");
    schnorrIdentify(rG, e, s);
    uint256 value = 1 + (msg.value - BaseWei) / StepWei;
    Curve.G1Point memory C = H.g1mul(value).g1add(Curve.G1Point(rG[0], rG[1]));
    notes[C.X] = C.Y;
    emit Deposit(msg.sender, msg.value, value);
  }

  event Withdraw(address indexed receiver, uint256 indexed claimed, uint256 indexed sent);
  function withdraw(
  uint256[] memory inputs, uint256[N] memory outputIndexes,
  uint256 claim, address payable receiver,
  uint256[2] memory rG, uint256 e, uint256 s)
  public {
    
    schnorrIdentify(rG, e, s);
    Curve.G1Point memory inputSum;
    for(uint i = 0 ; i < inputs.length; i ++){
      require(notes[inputs[i]] != 0, "no such output exists");
      inputSum = inputSum.g1add(Curve.G1Point(inputs[i], notes[inputs[i]]));
      notes[inputs[i]] = 0;
    }
    Curve.G1Point memory output = composeFromCommitments(outputIndexes);
    require(notes[output.X] == 0, "output already exists");
    notes[output.X] = output.Y;
    require(H.g1mul(claim).g1add(output).g1eq(inputSum.g1add(Curve.G1Point(rG[0], rG[1]))), "in/out eq does not hold");
    uint256 value = BaseWei + (claim - 1) * StepWei;
    address(receiver).transfer(value);
    emit Withdraw(receiver, claim, value);
  }

  function ct(
    uint256[] memory inputs,
    uint256[N][] memory outputCommitmentIndexes,
    uint256[2] memory rG, uint256 e, uint256 s) 
    public {

    schnorrIdentify(rG, e, s);
    require(inputs.length > 0, "bad input");
    Curve.G1Point memory inputSum;
    for(uint i = 0 ; i < inputs.length; i ++){
      require(notes[inputs[i]] != 0, "");
      inputSum = inputSum.g1add(Curve.G1Point(inputs[i], notes[inputs[i]]));
      notes[inputs[i]] = 0;
    }
    Curve.G1Point memory outputSum;
    Curve.G1Point memory output;
    for (uint i = 0; i < outputCommitmentIndexes.length; i++){
      output = composeFromCommitments(outputCommitmentIndexes[i]);
      notes[output.X] = output.Y;
      outputSum = outputSum.g1add(output);
    }
    outputSum = outputSum.g1add(Curve.G1Point(rG[0], rG[1]));
    require(inputSum.g1eq(outputSum), "in/out equation does not hold");
  }

  function composeFromCommitments(uint256[N] memory indexes)
  internal view
  returns(Curve.G1Point memory C){
    
    for (uint256 i = 0; i < N ; i ++){
      C = C.g1add(preCommitments[indexes[i]]);
    }
  }

  function getBitCommitment(uint256 i)
  public view
  returns (uint256[2] memory p){

    return [bitCommitments[i].X, bitCommitments[i].Y];
  }

  function getCommitment(uint256 i)
  public view
  returns (uint256[2] memory p){

    return [preCommitments[i].X, preCommitments[i].Y];
  }

  function getNote(uint256 x)
  public view
  returns (uint256){

    return notes[x];
  }
}