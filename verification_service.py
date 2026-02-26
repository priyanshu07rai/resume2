import os
from identity_engine import verify_identity
from skill_alignment_service import align_skills_to_evidence

# API Integrations
from api_integrations.github_service import fetch_github_signals
from api_integrations.stackexchange_service import fetch_stackoverflow_signals
from api_integrations.hunter_service import verify_email_professionalism
from api_integrations.ipqs_service import check_email_fraud_risk
from api_integrations.gmail_verifier import verify_gmail
from api_integrations.linkedin_scraper import scrape_linkedin_profile
def verify_external_evidence(entities, domain_info):
    """
    Industrial-Grade Verification Orchestrator.
    Fuses document data with all available platform signals.
    Employs graceful degradation for missing API keys or failed results.
    """
    domain = domain_info.get("domain", "General")
    candidate_id = entities.get("identity", {})
    email = candidate_id.get("email")
    github_handle = candidate_id.get("github", "").split("/")[-1] if candidate_id.get("github") else ""
    linkedin_url = candidate_id.get("linkedin", "")

    # 1. Base Layer: Identity Verification (Email + LinkedIn + Name Similarity)
    identity_res = verify_identity(candidate_id, linkedin_url)
    
    # 2. Base Layer: Email Integrity (Hunter + IPQS)
    # We ensure these run even if others fail.
    email_trust = {
        "gmail": verify_gmail(email) if email else {"status": "skipped", "score": 0},
        "hunter": verify_email_professionalism(email) if email else {"status": "skipped", "score": 0},
        "ipqs": check_email_fraud_risk(email) if email else {"status": "skipped", "fraud_score": 0}
    }

    # 3. Domain Layer: Technical Evidence (GitHub + StackOverflow)
    api_signals = {}
    
    # LinkedIn
    api_signals["linkedin"] = scrape_linkedin_profile(linkedin_url) if linkedin_url else {"exists": False, "status": "missing"}
    
    # GitHub is foundational for tech domains
    api_signals["github"] = fetch_github_signals(github_handle) if github_handle else {"exists": False, "status": "missing"}
    
    # StackOverflow
    if domain in ["Software Engineering", "Data / AI"]:
        api_signals["stackoverflow"] = fetch_stackoverflow_signals(github_handle) if github_handle else {"exists": False, "status": "skipped"}
    else:
        api_signals["stackoverflow"] = {"exists": False, "status": "skipped"}

    # 4. Intelligence Layer: Skill-to-Evidence Alignment
    # Alignment now integrates GH metrics directly.
    alignment = align_skills_to_evidence(entities, {"api_signals": api_signals}, domain_info)

    return {
        "identity_verification": identity_res,
        "api_signals": api_signals,
        "email_trust": email_trust,
        "alignment_evidence": alignment,
        "domain_context": domain,
        "success": True # Signal that pipeline finished
    }
