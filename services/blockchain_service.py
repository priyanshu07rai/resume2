import hashlib
import json
import os
import time
from datetime import datetime, timezone

class BlockchainService:
    def __init__(self, storage_path="data/blockchain.json"):
        self.storage_path = storage_path
        self.chain = []
        self._load_chain()

    def _load_chain(self):
        """Loads the chain from JSON file or initializes with Genesis block."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    self.chain = json.load(f)
            except Exception as e:
                print(f"Blockchain Load Error: {e}")
                self._create_genesis_block()
        else:
            self._create_genesis_block()

    def _create_genesis_block(self):
        """Initializes the chain with a Genesis block."""
        genesis_block = self._create_block(
            index=0,
            previous_hash="0",
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            data={"message": "Genesis Block - Resume Intelligence Engine Audit Ledger"}
        )
        self.chain = [genesis_block]
        self._save_chain()

    def _create_block(self, index, previous_hash, timestamp, data):
        """Creates a new block structure."""
        block = {
            "index": index,
            "timestamp": timestamp,
            "data": data,
            "previous_hash": previous_hash,
            "hash": ""
        }
        block["hash"] = self._calculate_hash(block)
        return block

    def _calculate_hash(self, block):
        """Calculates SHA256 hash of a block."""
        # Exclude the hash field itself from calculation
        block_copy = {k: v for k, v in block.items() if k != "hash"}
        block_string = json.dumps(block_copy, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def _save_chain(self):
        """Persists the chain to JSON file."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump(self.chain, f, indent=2)

    def add_block(self, transaction_data: dict) -> dict:
        """Adds a new transaction to the blockchain as a new block."""
        last_block = self.chain[-1]
        new_block = self._create_block(
            index=len(self.chain),
            previous_hash=last_block["hash"],
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            data=transaction_data
        )
        self.chain.append(new_block)
        self._save_chain()
        return new_block

    def get_chain(self) -> list:
        """Returns the full blockchain."""
        return self.chain

    def validate_chain(self) -> bool:
        """Validates the integrity of the entire blockchain."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]

            # Check if current block's hash is correct
            if current["hash"] != self._calculate_hash(current):
                return False

            # Check if current block correctly points to previous block
            if current["previous_hash"] != previous["hash"]:
                return False

        return True

    def get_block_by_scan_id(self, scan_id: str) -> dict:
        """Searches the blockchain for a specific scan_id."""
        for block in self.chain:
            if block["data"].get("scan_id") == scan_id:
                return block
        return None
