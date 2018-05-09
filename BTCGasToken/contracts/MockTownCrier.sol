pragma solidity ^0.4.23;

contract MockTownCrier {

    uint64 idCounter;
    address tocall;
    bytes4 fid;
    uint8 caseSwitcher; 
    
    constructor() public {
        idCounter = 1;
        caseSwitcher = 0;
    }
    
    function request(uint8 requestType, address callbackAddr, bytes4 callbackFID, uint timestamp, bytes32[] requestData) public payable returns (uint64) {
        tocall = callbackAddr;
        fid = callbackFID;
        idCounter++;
        if (caseSwitcher == 0) {
            return idCounter;
        } else if (caseSwitcher == 1) {
            return 0xFFFFFFFFFFFFFF04;
        } else if (caseSwitcher == 2) {
            return 0;
        } else {
            return 0xEFFFFFFFFFFFFFFE;
        }

    }
    
    function fakeCallback() public {
        if (caseSwitcher == 0) {
            tocall.call(fid, idCounter, 0, 52);
        } else {
            tocall.call(fid, idCounter, -23, 0);
        }
    }

    function mockSuccess() public {
        caseSwitcher = 0;
    }

    function mockFailUpgradedContract() public {
        caseSwitcher = 3;
    }

    function mockFailNotEnoughFee() public {
        caseSwitcher = 1;
    }

    function mockTCPaused() public {
        caseSwitcher = 2;
    }

    function cancel(uint64 requestId) public returns (bool){
        return true;
    }
}
