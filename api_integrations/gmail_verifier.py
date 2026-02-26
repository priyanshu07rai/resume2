import re

def verify_gmail(email):
    """
    Validates if an email is a structurally sound Gmail address.
    """
    if not email:
        return {"status": "skipped", "reason": "No email provided"}
        
    email = email.lower().strip()
    
    if not email.endswith("@gmail.com"):
        return {"status": "skipped", "reason": "Not a Gmail address"}
        
    # Basic Gmail rules: 6-30 chars before @, alphanumeric and periods
    username = email.split("@")[0]
    
    if len(username) < 6 or len(username) > 30:
        return {"status": "failed", "reason": "Invalid length for Gmail", "score": 20}
        
    if not re.match(r"^[a-z0-9.]+$", username):
        return {"status": "failed", "reason": "Invalid characters in Gmail", "score": 20}
        
    username_clean = username.replace(".", "")
    if len(username_clean) < 6:
        return {"status": "warning", "reason": "Too short when periods removed", "score": 50}
        
    return {
        "status": "verified",
        "reason": "Valid Gmail structure",
        "score": 85  # Inherently trusted structure
    }
