import re
from ai_consensus_engine import get_ai_consensus

def extract_entities(text, domain_info):
    """
    Advanced Deterministic + Multi-AI Extraction.
    Uses regex for PII and AI Consensus for career structure.
    """
    # 1. Deterministic Extraction (High Precision)
    email = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    github = re.search(r'github\.com/([\w-]+)', text)
    linkedin = re.search(r'linkedin\.com/in/([\w-]+)', text)
    phone = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    # Use deterministic fallback from extractor.py for name if AI fails
    from extractor import extract_deterministic
    fallback_data = extract_deterministic(text)

    identity = {
        "email": email.group(0) if email else fallback_data.get("email"),
        "github": f"https://github.com/{github.group(1)}" if github else fallback_data.get("github"),
        "linkedin": f"https://linkedin.com/in/{linkedin.group(1)}" if linkedin else fallback_data.get("linkedin"),
        "phone": phone.group(0) if phone else None,
        "name": fallback_data.get("name") or "Unknown Candidate"
    }

    # 2. Multi-AI Consensus Extraction
    try:
        consensus = get_ai_consensus(text, task_type="extraction", domain_hint=domain_info["domain"])
        ai_data = consensus.get("data", {})
        
        # Merge identity (Robust mapping)
        ai_id = ai_data.get("identity", {})
        
        identity["name"] = (
            ai_id.get("full_name") or 
            ai_id.get("name") or 
            ai_data.get("full_name") or 
            ai_data.get("name") or 
            fallback_data.get("name") or
            "Unknown Candidate"
        )
        if not identity["email"]: identity["email"] = ai_id.get("email") or fallback_data.get("email")
        if not identity["phone"]: identity["phone"] = ai_id.get("phone")
        if not identity["linkedin"]: identity["linkedin"] = ai_id.get("linkedin") or fallback_data.get("linkedin")

        return {
            "identity": identity,
            "skills": ai_data.get("skills", []),
            "experience": ai_data.get("experience", []) or ai_data.get("job_history", []),
            "education": ai_data.get("education", []),
            "certifications": ai_data.get("certifications", []),
            "extraction_meta": {
                "consensus_score": consensus["consensus_score"],
                "models_used": consensus["models_used"],
                "disagreements": consensus["disagreements"]
            }
        }
    except Exception as e:
        print(f"Extraction Engine Error: {e}")
        return {
            "identity": identity,
            "skills": [],
            "experience": [],
            "education": [],
            "certifications": [],
            "extraction_meta": {"error": str(e), "consensus_score": 0}
        }
