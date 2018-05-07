pragma solidity ^0.4.21;

import "./zeppelin/ERC721Token.sol";

contract BTCGasToken is ERC721Token {
    
    struct Derivative {
        address maker;
        address taker;
        uint makerAmount;
        uint takerAmount;
        uint triggerPrice;
        uint triggerHeight;
        bool settled;
        bool taken;
    }
    
    mapping (uint => Derivative) public derivativeData;
    
    uint num_issued = 0;
    
    event DerivativeCreated(uint indexed id, address indexed maker, uint makerAmount, uint takerAmount, uint triggerPrice, uint triggerHeight);
    event DerivativeTaken(uint indexed id, address indexed maker, address indexed taker, uint makerAmount, uint takerAmount, uint triggerPrice, uint triggerHeight);
    event DerivativeSettled(uint indexed id, address indexed maker, address indexed taker, uint makerAmount, uint takerAmount, uint triggerPrice, uint triggerHeight);
    
    constructor() ERC721Token("BTCFees by gastoken.io", "BTCF") public {
    }
    
    function mint(uint takerAmount,  uint triggerPrice, uint triggerHeight) public payable {
        //require(block.number < triggerHeight);
        address maker = msg.sender;
        uint makerAmount = msg.value;
        uint id = num_issued;
        num_issued += 1;
        derivativeData[id] = Derivative(maker, 0x0, makerAmount, takerAmount, triggerPrice, triggerHeight, false, false);
        emit DerivativeCreated(id, maker, makerAmount, takerAmount, triggerPrice, triggerHeight);
        _mint(maker, id);
    }
    
    function take(uint id) public payable {
        require(id < num_issued);
        Derivative storage d = derivativeData[id];
        require(block.number < d.triggerHeight);
        require(!d.taken);
        assert(!d.settled);
        require(msg.value == d.takerAmount);
        d.taken = true;
        d.taker = msg.sender;
        emit DerivativeTaken(id, d.maker, d.taker, d.makerAmount, d.takerAmount, d.triggerPrice, d.triggerHeight);
    }
    
    function settle(uint id) public {
        // anyone can call this for now; make it an option?
        require(id < num_issued);
        Derivative storage d = derivativeData[id];
        require(block.number >= d.triggerHeight);
        require(d.taken);
        require(!d.settled);
        d.settled = true;
        // Check whether triggerPrice is greater than current price
        // If so, pay maker full value; else pay taker full value
    }
    
    function cancel(uint id) public {
        require(id < num_issued);
        Derivative storage d = derivativeData[id];
        require(!d.taken);
        assert(!d.settled);
        d.settled = true;
        d.maker.transfer(d.makerAmount);
    }
}