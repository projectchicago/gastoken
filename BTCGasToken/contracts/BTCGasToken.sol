pragma solidity ^0.4.23;
 
import "./zeppelin/ERC721Token.sol";
 
contract TownCrier {
    function request(uint8 requestType, address callbackAddr, bytes4 callbackFID, uint timestamp, bytes32[] requestData) public payable returns (uint64);
    function cancel(uint64 requestId) public returns (bool);
}
 
contract BTCGasToken is ERC721Token {
    
    using SafeMath for uint;
    
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
    
    event DerivativeCreated(uint indexed id, address indexed maker, uint makerAmount, uint takerAmount, uint triggerPrice, uint triggerHeight);
    event DerivativeTaken(uint indexed id, address indexed maker, address indexed taker, uint makerAmount, uint takerAmount, uint triggerPrice, uint triggerHeight);
    event DerivativeSettled(uint indexed id, address indexed maker, address indexed taker, uint makerAmount, uint takerAmount, uint triggerPrice, uint actualPrice, uint triggerHeight, uint jackpot);
    event DerivativeCanceled(uint indexed id, address indexed maker, uint makerAmount, uint takerAmount, uint triggerPrice, uint triggerHeight);
    event DerivativeError(uint indexed id, address indexed maker, address indexed taker, uint makerAmount, uint takerAmount, uint triggerPrice, uint triggerHeight, int tcRequestId);
    
    TownCrier tcContract; 
    bytes4 constant TC_CALLBACK_FID = bytes4(keccak256("tcBTCFeeHandler(uint64,uint64,bytes32)"));
    uint constant MIN_GAS = 3* (30000 + 20000);
    uint constant GAS_PRICE = 5 * 10 ** 10;         // TODO figure out if there's a better non-static way to peg the TC fee, or if we're satisfied with this
    uint constant TC_FEE = MIN_GAS * GAS_PRICE;
    
    event TCRequestStatus(int256 TCRequestIDReturned);
    //event TCData(uint64 requestId, uint64 error, bytes32 respData);
    
    // Maps TownCrier returned IDs to Derivative IDs
    mapping (uint => uint) public tcIdToBTCFeeID;
 
    // Rinkeby test endpoint 0x9eC1874FF1deF6E178126f7069487c2e9e93D0f9
    constructor(address tcEndpointAddress) ERC721Token("BTCFees by gastoken.io", "BTCF") public {
        tcContract = TownCrier(tcEndpointAddress);
    }
    
    // Maybe some day in the future we'll allow people to donate to the contract
    //function() public payable {}
    
    function mint(uint takerAmount,  uint triggerPrice, uint triggerHeight) public payable returns (uint) {
        require(block.number < triggerHeight);
        require(msg.value > 9999999999999999); // minimum .01 ETH
        require(takerAmount > TC_FEE);
        address maker = msg.sender;
        uint makerAmount = msg.value;
        uint id = totalSupply();
        derivativeData[id] = Derivative(maker, 0x0, makerAmount, takerAmount, triggerPrice, triggerHeight, false, false);
        emit DerivativeCreated(id, maker, makerAmount, takerAmount, triggerPrice, triggerHeight);
        _mint(maker, id);
        return id;
    }
    
    function take(uint id) public payable {
        require(id < totalSupply());
        Derivative storage d = derivativeData[id];
        require(block.number < d.triggerHeight);
        require(!d.taken);
        require(!d.settled);
        require(msg.value == d.takerAmount);
        d.taken = true;
        d.taker = msg.sender;
        emit DerivativeTaken(id, d.maker, d.taker, d.makerAmount, d.takerAmount, d.triggerPrice, d.triggerHeight);
    }
    
    function settle(uint id) public {
        // anyone can call this for now; make it an option? 
        // restrict only to taker and/or maker to be settled?
        require(id < totalSupply());
        Derivative storage d = derivativeData[id];
        require(block.number >= d.triggerHeight);
        require(d.taken);
        require(!d.settled);
        d.settled = true;
        // Check whether triggerPrice is greater than current price
        // If so, pay maker full value; else pay taker full value
        bytes32[] memory requestData = new bytes32[](0);
        uint8 requestType = 2;
        int64 tcRequestId = int64(tcContract.request.value(TC_FEE)(requestType, this, TC_CALLBACK_FID, 0, requestData));
        /* TODO - Think about handling various requestId values differently
           If requestId > 0, then this is the Id uniquely assigned to this request. 
           If requestId = -2^250, then the request fails because the requester didn't send enough fee to the TC Contract. 
           If requestId = 0, then the TC service is suspended due to some internal reason. No more requests or cancellations can be made but previous requests will still be responded to by TC. 
           If requestId < 0 && requestId != -2^250, then the TC Contract is upgraded and requests should be sent to the new address -requestId.
        */
        if (tcRequestId < 1) { // Error occured from TownCrier
            d.maker.transfer(d.makerAmount);
            d.taker.transfer(d.takerAmount.sub(TC_FEE));
            emit DerivativeError(id, d.maker, d.taker, d.makerAmount, d.takerAmount, d.triggerPrice, d.triggerHeight, tcRequestId);
            return;
        }
        
        tcIdToBTCFeeID[uint256(tcRequestId)] = (id + 1); // prevent id from ever being 0 (mapping lookup)
        emit TCRequestStatus(tcRequestId);
    }
    
    function tcBTCFeeHandler(uint64 requestId, uint64 error, bytes32 respData) public {
        require(msg.sender == address(tcContract));
        require(tcIdToBTCFeeID[requestId] != 0);
        uint BTCFeeID = tcIdToBTCFeeID[requestId] - 1;
        require(BTCFeeID < totalSupply());
        Derivative storage d = derivativeData[BTCFeeID];
        require(block.number >= d.triggerHeight);
        require(d.taken);
        require(d.settled);
 
        //if (error == 0) {
        //    emit TCData(requestId, error, respData);
        //} else {
        if ( error != 0 ) {
        //    emit TCData(requestId, error, 0);
            return; // I don't like silently failing, but TC is the caller, and TC doesn't care whether this succeeds or not
        }
        uint256 actualFeePrice = uint256(respData);
 
        uint jackpot = d.makerAmount.add(d.takerAmount.sub(TC_FEE));
        // Check whether triggerPrice is greater than current price
        // If so, pay maker full value; else pay taker full value
        if (d.triggerPrice >  actualFeePrice) {
            d.maker.transfer(jackpot);
        } else {
            d.taker.transfer(jackpot);
        }
        emit DerivativeSettled(BTCFeeID, d.maker, d.taker, d.makerAmount, d.takerAmount, d.triggerPrice, actualFeePrice, d.triggerHeight, jackpot);
    }
    
    function cancel(uint id) public {
        require(id < totalSupply());
        Derivative storage d = derivativeData[id];
        require(msg.sender == d.maker);
        require(!d.taken);
        require(!d.settled);
        d.settled = true;
        d.maker.transfer(d.makerAmount);
        emit DerivativeCanceled(id, d.maker, d.makerAmount, d.takerAmount, d.triggerPrice, d.triggerHeight);
    }
}
 
