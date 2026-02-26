import re

def detect_fraud(resume_data, github_data, linkedin_data):
    """
    Advanced Fraud Detection Layer.
    Detects identity mismatches and suspicious profile activity.
    """
    flags = []
    risk_points = 0
    
    candidate_name = resume_data.get("name", "").lower()
    
    # 1. Identity Validation (Resume vs GitHub Name)
    if github_data.get("exists"):
        gh_name = (github_data.get("name_on_profile") or "").lower()
        if gh_name and candidate_name:
            name_parts = set(re.findall(r'\w+', candidate_name))
            gh_name_parts = set(re.findall(r'\w+', gh_name))
            if not name_parts & gh_name_parts:
                flags.append("LinkedIn Name mismatch between Resume and GitHub profile")
                risk_points += 20

    # 2. LinkedIn Fraud Signals
    li_metrics = linkedin_data.get("linkedin_metrics", {})
    if linkedin_data.get("exists"):
        if li_metrics.get("identity_match_score", 0) < 5:
            flags.append("LinkedIn slug does not match candidate name")
            risk_points += 20
        if not li_metrics.get("slug_valid"):
            flags.append("Suspicious LinkedIn slug pattern detected")
            risk_points += 15
    elif resume_data.get("linkedin"):
        flags.append("LinkedIn provided but profile is unreachable")
        risk_points += 10

    # 3. GitHub "Inflation" Detection
    if github_data.get("exists"):
        repos = github_data.get("repos_count", 0)
        followers = github_data.get("followers", 0)
        if repos > 20 and followers < 2:
            flags.append("Potential GitHub activity inflation (High repos, zero followers)")
            risk_points += 20

    # Determine Risk Level
    risk_level = "low"
    if risk_points >= 50:
        risk_level = "high"
    elif risk_points >= 20:
        risk_level = "medium"
        
    return {
        "fraud_flags": flags,
        "risk_level": risk_level,
        "risk_score": risk_points
    }
