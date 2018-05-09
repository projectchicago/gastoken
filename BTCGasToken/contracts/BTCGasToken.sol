pragma solidity ^0.4.21;

import "./zeppelin/ERC721Token.sol";

contract TownCrier {
    function request(uint8 requestType, address callbackAddr, bytes4 callbackFID, uint timestamp, bytes32[] requestData) public payable returns (uint64);
    function cancel(uint64 requestId) public returns (bool);
}

contract BTCGasToken is ERC721Token {
    
    struct Derivative {
        address maker;
        address taker;
        uint makerAmount;
        uint takerAmount;
        uint triggerPrice;
        uint triggerHeight;
        bool settleStarted;
        bool settleFinished;
        bool taken;
    }
    
    mapping (uint => Derivative) public derivativeData;
    
    uint num_issued = 0;
    
    event DerivativeCreated(uint indexed id, address indexed maker, uint makerAmount, uint takerAmount, uint triggerPrice, uint triggerHeight);
    event DerivativeTaken(uint indexed id, address indexed maker, address indexed taker, uint makerAmount, uint takerAmount, uint triggerPrice, uint triggerHeight);
    event DerivativeSettled(uint indexed id, address indexed maker, address indexed taker, uint makerAmount, uint takerAmount, uint triggerPrice, uint triggerHeight);
    
    TownCrier tcContract; 
    bytes4 constant TC_CALLBACK_FID = bytes4(keccak256("tcBTCFeeHandler(uint64,uint64,bytes32)"));
    uint constant MIN_GAS = 30000 + 20000;
    uint constant GAS_PRICE = 5 * 10 ** 10;         // TODO figure out if there's a better non-static way to peg the TC fee
    uint constant TC_FEE = MIN_GAS * GAS_PRICE;
    
    event TCRequestStatus(int256 TCRequestIDReturned);
    event TCData(uint64 requestId, uint64 error, bytes32 respData);
    
    // TODO rewire TownCrier to pass through Derivative IDs 
    // So we aren't using a method that's vulnerable to race conditions
    uint256 globalLastFeeTicker;

    // Rinkeby test endpoint 0x9eC1874FF1deF6E178126f7069487c2e9e93D0f9
    constructor(address tcEndpointAddress) ERC721Token("BTCFees by gastoken.io", "BTCF") public {
        tcContract = TownCrier(tcEndpointAddress);
        globalLastFeeTicker = 0; // TODO lol change this
    }
    
    function() public payable {}
    
    function mint(uint takerAmount,  uint triggerPrice, uint triggerHeight) public payable returns (uint) {
        //require(block.number < triggerHeight);
        // minimum .01 ETH = 10000000000000000
        require(msg.value > 10000000000000000);
        require(takerAmount > TC_FEE);
        address maker = msg.sender;
        uint makerAmount = msg.value;
        uint id = num_issued;
        num_issued += 1;
        derivativeData[id] = Derivative(maker, 0x0, makerAmount, takerAmount, triggerPrice, triggerHeight, false, false, false);
        emit DerivativeCreated(id, maker, makerAmount, takerAmount, triggerPrice, triggerHeight);
        _mint(maker, id);
        return id;
    }
    
    function take(uint id) public payable {
        require(id < num_issued);
        Derivative storage d = derivativeData[id];
        require(block.number < d.triggerHeight);
        require(!d.taken);
        assert(!d.settleFinished);
        require(msg.value == d.takerAmount);
        d.taken = true;
        d.taker = msg.sender;
        emit DerivativeTaken(id, d.maker, d.taker, d.makerAmount, d.takerAmount, d.triggerPrice, d.triggerHeight);
    }
    
    function settleStep1(uint id) public {
        // anyone can call this for now; make it an option? 
        // restrict only to taker and/or maker to be settled?
        require(id < num_issued);
        Derivative storage d = derivativeData[id];
        require(block.number >= d.triggerHeight);
        require(d.taken);
        require(!d.settleFinished);
        require(!d.settleStarted);
        d.settleStarted = true;
        // Check whether triggerPrice is greater than current price
        // If so, pay maker full value; else pay taker full value
        bytes32[] memory requestData = new bytes32[](0);
        uint8 requestType = 2;
        int256 tcRequestId = tcContract.request.value(TC_FEE)(requestType, this, TC_CALLBACK_FID, 0, requestData);
        if (tcRequestId < 1) { // Error occured from TownCrier
            // TODO make sure no vuln here around sending money out of contract
            d.maker.send(d.makerAmount);
            d.taker.send(d.takerAmount - TC_FEE);
        } else {
        }
        emit TCRequestStatus(tcRequestId);
        require(tcRequestId != 0);
    }
    
    function tcBTCFeeHandler(uint64 requestId, uint64 error, bytes32 respData) public {
        require(msg.sender == address(tcContract));
        
        if (error == 0) {
            emit TCData(requestId, error, respData);
            globalLastFeeTicker = uint256(respData);
        } else {
            emit TCData(requestId, error, 0);
        }
    }
    
    function settleStep2(uint id) public {
        // anyone can call this for now; make it an option? 
        // restrict only to taker and/or maker to be settled?
        require(id < num_issued);
        Derivative storage d = derivativeData[id];
        require(block.number >= d.triggerHeight);
        require(d.taken);
        require(d.settleStarted);
        require(!d.settleFinished);
        d.settleFinished = true;
        // TODO Use Zeppelin SafeMath because in 2018 we apparently still have to worry about integer overflow in greenfield programming languages
        uint jackpot = d.makerAmount + d.takerAmount - TC_FEE;
        // Check whether triggerPrice is greater than current price
        // If so, pay maker full value; else pay taker full value
        if (d.triggerPrice > globalLastFeeTicker ) {
            d.maker.transfer(jackpot);
        } else {
            d.taker.transfer(jackpot);
        }
    }
    
    function cancel(uint id) public {
        require(id < num_issued);
        Derivative storage d = derivativeData[id];
        require(!d.taken);
        // TODO negotiate cancellations with TownCrier
        // and support cancellation in the in-between settlement1 and 2 phase
        require(!d.settleStarted);
        assert(!d.settleFinished);
        d.settleFinished = true;
        d.maker.transfer(d.makerAmount);
    }
}
