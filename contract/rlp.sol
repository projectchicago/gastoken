pragma solidity ^0.4.10;

contract Rlp {

    uint256 constant ADDRESS_BYTES = 20;
    uint256 constant MAX_SINGLE_BYTE = 128;
    uint256 constant MAX_NONCE = 256**9 - 1;

    // count number of bytes required to represent an unsigned integer
    function count_bytes(uint256 n) pure internal returns (uint256 c) {
        uint i = 0;
        uint mask = 1;
        while (n >= mask) {
            i += 1;
            mask *= 256;
        }

        return i;
    }

    function mk_contract_address(address a, uint256 n) pure internal returns (address rlp) {
        /*
         * make sure the RLP encoding fits in one word:
         * total_length      1 byte
         * address_length    1 byte
         * address          20 bytes
         * nonce_length      1 byte (or 0)
         * nonce           1-9 bytes
         *                ==========
         *                24-32 bytes
         */
        require(n <= MAX_NONCE);

        // number of bytes required to write down the nonce
        uint256 nonce_bytes;
        // length in bytes of the RLP encoding of the nonce
        uint256 nonce_rlp_len;

        if (0 < n && n < MAX_SINGLE_BYTE) {
            // nonce fits in a single byte
            // RLP(nonce) = nonce
            nonce_bytes = 1;
            nonce_rlp_len = 1;
        } else {
            // RLP(nonce) = [num_bytes_in_nonce nonce]
            nonce_bytes = count_bytes(n);
            nonce_rlp_len = nonce_bytes + 1;
        }

        // [address_length(1) address(20) nonce_length(0 or 1) nonce(1-9)]
        uint256 tot_bytes = 1 + ADDRESS_BYTES + nonce_rlp_len;

        // concatenate all parts of the RLP encoding in the leading bytes of
        // one 32-byte word
        uint256 word = ((192 + tot_bytes) * 256**31) +
                       ((128 + ADDRESS_BYTES) * 256**30) +
                       (uint256(a) * 256**10);

        if (0 < n && n < MAX_SINGLE_BYTE) {
            word += n * 256**9;
        } else {
            word += (128 + nonce_bytes) * 256**9;
            word += n * 256**(9 - nonce_bytes);
        }

        uint256 hash;

        assembly {
            let mem_start := mload(0x40)        // get a pointer to free memory
            mstore(mem_start, word)             // store the rlp encoding
            hash := sha3(mem_start,
                         add(tot_bytes, 1))     // hash the rlp encoding
        }

        // interpret hash as address (20 least significant bytes)
        return address(hash);
    }
}
