import json
import os

SESSION_DIR = "sessions"

def save_session(candidate_hash, data):
    if not os.path.exists(SESSION_DIR):
        os.makedirs(SESSION_DIR)
        
    filepath = os.path.join(SESSION_DIR, f"{candidate_hash}_session.json")
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)
        
def load_session(candidate_hash):
    filepath = os.path.join(SESSION_DIR, f"{candidate_hash}_session.json")
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return None
