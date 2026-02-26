import os
import requests
from dotenv import load_dotenv

load_dotenv()

IPQS_API_KEY = os.getenv("IPQS_API_KEY")

def check_email_fraud_risk(email):
    """
    IPQualityScore Fraud API.
    Detects disposable emails and high-risk domain anomalies.
    """
    if not email or not IPQS_API_KEY:
        return {"risk_score": 0, "status": "skipped"}

    url = f"https://www.ipqualityscore.com/api/json/email/{IPQS_API_KEY}/{email}"
    
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return {"risk_score": 0, "status": "error"}
            
        data = resp.json()
        
        return {
            "fraud_score": data.get("fraud_score", 0),
            "disposable": data.get("disposable", False),
            "deliverability": data.get("deliverability", "unknown"),
            "high_risk": data.get("fraud_score", 0) > 75,
            "confidence": 95,
            "reasoning": f"Fraud risk score: {data.get('fraud_score')}/100. High risk: {data.get('fraud_score', 0) > 75}."
        }
    except Exception as e:
        return {"risk_score": 0, "error": str(e), "confidence": 0}
