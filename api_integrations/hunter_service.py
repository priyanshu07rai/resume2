import os
import requests
from dotenv import load_dotenv

load_dotenv()

HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")

def verify_email_professionalism(email):
    """
    Hunter.io Email Validation API.
    Verifies if email is deliverable and linked to professional domains.
    """
    if not email or "@" not in email or not HUNTER_API_KEY:
        return {"status": "skipped", "confidence": 0}

    url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={HUNTER_API_KEY}"
    
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return {"status": "error", "confidence": 0}
            
        data = resp.json().get("data", {})
        
        return {
            "status": data.get("status"),
            "result": data.get("result"),
            "score": data.get("score"),
            "is_webmail": data.get("webmail"),
            "confidence": 100,
            "reasoning": f"Email {email} returned status: {data.get('result')} with score {data.get('score')}%."
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "confidence": 0}
