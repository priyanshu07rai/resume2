// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title ResumeVerifier
 * @dev Stores resume authenticity hashes on-chain for tamper-proof verification.
 */
contract ResumeVerifier {
    mapping(string => bool) public verifiedHashes;
    
    event HashStored(string indexed resumeHash, uint256 timestamp);

    function storeHash(string memory _hash) public {
        verifiedHashes[_hash] = true;
        emit HashStored(_hash, block.timestamp);
    }

    function isVerified(string memory _hash) public view returns (bool) {
        return verifiedHashes[_hash];
    }
}
