import requests
import re
from difflib import SequenceMatcher

def verify_identity(resume_data, linkedin_url):
    """
    Advanced Identity Structural Validation.
    Fuses slug normalization, name similarity, and anomaly detection.
    """
    candidate_name = resume_data.get("name", "").lower()
    email = resume_data.get("email", "").lower()
    
    # 1. Structural Normalization
    li_status = check_linkedin_reachability(linkedin_url)
    slug = extract_linkedin_slug(linkedin_url)
    
    # 2. Name Similarity (Fuzzy Match)
    similarity = 0
    if slug and candidate_name:
        clean_slug = re.sub(r'[^a-zA-Z]', '', slug)
        clean_name = re.sub(r'[^a-zA-Z]', '', candidate_name)
        similarity = SequenceMatcher(None, clean_slug, clean_name).ratio()
    
    # 3. Slug Anomaly Detection
    # Detect random string patterns or excessive digits
    slug_risk_score = 0
    if slug:
        if re.search(r'[0-9]{4,}', slug): # Many digits
            slug_risk_score += 20
        if len(slug) < 3: # Too short
            slug_risk_score += 30
    
    # 4. Handle Consistency
    email_user = email.split('@')[0] if '@' in email else ""
    handle_consistency = 0
    if email_user and slug:
        handle_consistency = SequenceMatcher(None, email_user, slug).ratio()

    # 5. Composite Scoring
    confidence = 80
    risk_flags = []
    
    if not li_status:
        risk_flags.append("LinkedIn profile unreachable (HTTP Failure or Invalid Link)")
        confidence -= 30
    
    if slug_risk_score > 0:
        risk_flags.append(f"Suspicious slug pattern detected (Structural Anomaly)")
        confidence -= 15

    identity_match_v = (similarity * 60) + (handle_consistency * 40)
    
    return {
        "identity_match_score": round(identity_match_v),
        "slug_risk_score": slug_risk_score,
        "linkedin_valid": li_status and (slug is not None),
        "confidence": max(0, confidence),
        "reasoning": f"Identity match at {round(identity_match_v)}%. LinkedIn structural check: {'PASS' if li_status else 'FAIL'}.",
        "risk_flags": risk_flags
    }

def check_linkedin_reachability(url):
    if not url or "linkedin.com/in/" not in url:
        return False
    try:
        # Simplified for demo; production would use rotating proxy/headers
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
        return resp.status_code == 200
    except:
        return False

def extract_linkedin_slug(url):
    if not url: return None
    match = re.search(r'linkedin\.com/in/([^/?]+)', url)
    return match.group(1) if match else None
