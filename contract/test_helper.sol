pragma solidity ^0.4.10;

contract Token {
    function free(uint256 value) returns (bool success);
    function freeUpTo(uint256 value) returns (uint256 freed);
    function freeFrom(address from, uint256 value) returns (bool success);
    function freeFromUpTo(address from, uint256 value) returns (uint256 freed);
}

contract TestHelper {

    function dummy() {
        assembly{
            invalid
        }
    }

    // Burns at least burn gas by calling itself and throwing
    function burnGas(uint256 burn) {
        // call self.dummy() to burn a bunch of gas
        assembly {
            mstore(0x0, 0x32e43a1100000000000000000000000000000000000000000000000000000000)
            let ret := call(burn, address, 0, 0x0, 0x04, 0x0, 0)
        }
    }

    function burnGasAndFree(address gas_token, uint256 burn, uint256 free) {
        burnGas(burn);
        require(Token(gas_token).free(free));
    }

    function burnGasAndFreeUpTo(address gas_token, uint256 burn, uint256 free) {
        burnGas(burn);
        require(free == Token(gas_token).freeUpTo(free));
    }

    function burnGasAndFreeFrom(address gas_token, uint256 burn, uint256 free) {
        burnGas(burn);
        require(Token(gas_token).freeFrom(tx.origin, free));
    }

    function burnGasAndFreeFromUpTo(address gas_token, uint256 burn, uint256 free) {
        burnGas(burn);
        require(free == Token(gas_token).freeFromUpTo(tx.origin, free));
    }
}