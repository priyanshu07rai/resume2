import os
import requests
from dotenv import load_dotenv

load_dotenv()

STACKEXCHANGE_KEY = os.getenv("STACKEXCHANGE_KEY")

def fetch_stackoverflow_signals(handle):
    """
    StackExchange Credibility API.
    Audits technical reputation and community standing.
    """
    if not handle:
        return {"exists": False, "confidence": 0}

    # API key is optional for limited calls
    url = f"https://api.stackexchange.com/2.3/users?order=desc&sort=reputation&inname={handle}&site=stackoverflow"
    if STACKEXCHANGE_KEY:
        url += f"&key={STACKEXCHANGE_KEY}"

    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return {"exists": False, "error": "API Limit or Error", "confidence": 0}
            
        data = resp.json()
        items = data.get("items", [])
        
        if not items:
            return {"exists": False, "confidence": 80}

        # Select the best match (highest reputation with exact/close name)
        user = items[0]
        
        return {
            "exists": True,
            "reputation": user.get("reputation", 0),
            "badge_counts": user.get("badge_counts", {}),
            "user_id": user.get("user_id"),
            "display_name": user.get("display_name"),
            "confidence": 90,
            "reasoning": f"StackOverflow profile found for '{handle}' with {user.get('reputation')} reputation."
        }
    except Exception as e:
        return {"exists": None, "error": str(e), "confidence": 0}
