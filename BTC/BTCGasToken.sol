pragma solidity ^0.4.21;

import "./zeppelin/ERC721Token.sol";

contract BTCGasToken is ERC721Token {
    
    struct Derivative {
        address maker;
        address taker;
        uint256 makerAmount;
        uint256 takerAmount;
        uint256 triggerPrice;
        uint256 triggerHeight;
        bool settled;
    }
    
    mapping (uint => Derivative) public derivativeData;
    
    uint num_issued = 0;
    
    event DerivativeCreated(uint id, address maker, address taker, uint makerAmount, uint takerAmount, uint triggerPrice, uint triggerHeight);
    
    constructor() ERC721Token("BTCFees by gastoken.io", "BTCF") public {
    }
    
    function mint(address taker, uint256 takerAmount, 
      uint256 triggerPrice, uint256 triggerHeight) public {
        address maker = msg.sender;
        uint makerAmount = msg.value;
        uint id = num_issued;
        num_issued += 1;
        derivativeData[id] = Derivative(maker, taker, makerAmount, takerAmount, triggerPrice, triggerHeight, false);
        DerivativeCreated(id, maker, taker, makerAmount, takerAmount, triggerPrice, triggerHeight);
        _mint(maker, id);
    }
    
    function settle(uint256 id) {
        // anyone can call this for now; make it an option?
        require(id < num_issued);
        Derivative d = derivativeData[id];
        require(block.number >= d.triggerHeight);
        require(!d.settled);
        
        // Check whether triggerPrice is greater than current price
        // If so, pay maker full value; else pay taker full value
    }
}