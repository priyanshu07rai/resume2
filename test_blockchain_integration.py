import requests
import time
import json
import os

BASE_URL = "http://127.0.0.1:5000"

def test_blockchain():
    print("--- Starting Blockchain Integration Test ---")
    
    # 1. Check if blockchain.json exists (should have Genesis block)
    if os.path.exists("data/blockchain.json"):
        with open("data/blockchain.json", 'r') as f:
            chain = json.load(f)
            print(f"Initial Chain discovered. Blocks: {len(chain)}")
    else:
        print("Blockchain file not found yet. It should be created after the first scan or initialization.")

    # 2. Trigger Scan (Demo)
    print("Triggering Demo Scan...")
    try:
        response = requests.get(f"{BASE_URL}/scan/demo")
        if response.status_code == 200:
            print("Demo Scan Success.")
        else:
            print(f"Demo Scan Failed: {response.status_code}")
            return
    except Exception as e:
        print(f"Error connecting to server: {e}")
        print("Make sure the Flask app is running at http://127.0.0.1:5000")
        return

    # 3. Verify Blockchain
    print("Verifying Blockchain Integrity...")
    response = requests.get(f"{BASE_URL}/blockchain/verify")
    if response.status_code == 200:
        res_data = response.json()
        print(f"Blockchain Status: {json.dumps(res_data, indent=2)}")
        if res_data.get("valid") and res_data.get("total_blocks", 0) > 1:
            print("TEST PASSED: Blockchain is valid and recording scans.")
        else:
            print("TEST FAILED: Blockchain invalid or no blocks recorded.")
    else:
        print(f"Verify Endpoint Failed: {response.status_code}")

if __name__ == "__main__":
    test_blockchain()
