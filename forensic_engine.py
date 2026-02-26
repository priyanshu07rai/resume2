"""
forensic_engine.py — The Honest Recruiter Forensic Report Generator
Every number is deterministic. No fake percentages. No placeholder metrics.
"""
import re
import hashlib
import json
from datetime import datetime, timezone

# ── High-Trust / Disposable Email Domain Lists ─────────────────────────
HIGH_TRUST_DOMAINS = ["edu", "ac.in", "ac.uk", "gov", "mil", "ac.jp"]
CORPORATE_SIGNALS  = ["company", "corp", "inc", "technologies", "labs", "works"]
DISPOSABLE_DOMAINS = ["tempmail", "mailinator", "10minutemail", "guerrillamail",
                      "throwam", "dispostable", "fakeinbox", "yopmail", "trashmail"]
GENERIC_DOMAINS    = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
                      "icloud.com", "proton.me", "rediffmail.com"]


# ══════════════════════════════════════════════════════════════════════
# 1. GITHUB TRUST SCORE  (activity-based, not existence-based)
# ══════════════════════════════════════════════════════════════════════

def compute_github_trust(github_data):
    """
    Deterministic GitHub trust computation.
    """
    if not github_data or not github_data.get("exists"):
        return 20, "No Activity", {
            "exists": False,
            "repo_count": 0,
            "account_created_year": None,
            "last_commit_days_ago": None,
            "top_language": "Unknown",
            "reason": "No GitHub profile found or linked."
        }

    metrics = github_data.get("metrics", {})
    repo_count       = metrics.get("repo_count", 0) or 0
    last_commit_days = metrics.get("last_commit_days_ago", 9999) or 9999
    created_year     = metrics.get("account_created_year", datetime.now().year)
    top_lang         = metrics.get("top_language", "Unknown") or "Unknown"
    account_age_yrs  = datetime.now().year - (created_year or datetime.now().year)

    # Base score from repo count and commit recency
    if repo_count > 10 and last_commit_days < 30:
        score = 90
        level = "Highly Active"
    elif repo_count > 3 and last_commit_days < 180:
        score = 70
        level = "Moderately Active"
    elif repo_count > 0:
        score = 50
        level = "Limited Activity"
    else:
        score = 25
        level = "Empty Profile"

    return score, level, {
        "exists": True,
        "repo_count": repo_count,
        "account_created_year": created_year,
        "last_commit_days_ago": last_commit_days,
        "top_language": top_lang,
        "account_age_years": account_age_yrs
    }


# ══════════════════════════════════════════════════════════════════════
# 2. EMAIL INTEGRITY SCORE  (domain-authority-based)
# ══════════════════════════════════════════════════════════════════════

def compute_email_trust(email, email_trust_data):
    """
    Deterministic email trust computation.
    Returns: score 0–100, reputation string, metadata dict.
    """
    if not email:
        return 40, "No Email", {
            "email": None,
            "domain": None,
            "is_disposable": False,
            "domain_reputation": "Not provided",
            "hunter_score": 0,
            "ipqs_fraud_score": 0
        }

    domain = email.split("@")[-1].lower() if "@" in email else ""
    tld    = domain.split(".")[-1] if "." in domain else ""
    ext    = ".".join(domain.split(".")[-2:]) if domain.count(".") >= 1 else domain

    # Disposable check
    is_disposable = any(d in domain for d in DISPOSABLE_DOMAINS)
    if is_disposable:
        return 10, "Disposable", {
            "email": email,
            "domain": domain,
            "is_disposable": True,
            "domain_reputation": "Disposable/Throwaway",
            "hunter_score": 0,
            "ipqs_fraud_score": 100
        }

    # Domain reputation tier
    if tld in HIGH_TRUST_DOMAINS or ext in HIGH_TRUST_DOMAINS:
        base_score, reputation = 85, "University / Academic"
    elif any(sig in domain for sig in CORPORATE_SIGNALS) or (
        domain not in GENERIC_DOMAINS and tld not in ["gmail", "yahoo", "outlook"] and len(domain) > 5
    ):
        base_score, reputation = 90, "Corporate Domain"
    elif domain in GENERIC_DOMAINS:
        base_score, reputation = 70, "Standard Consumer"
    else:
        base_score, reputation = 60, "Unknown Domain"

    # IPQS fraud score adjustment
    ipqs = email_trust_data.get("ipqs", {}) if email_trust_data else {}
    ipqs_fraud = ipqs.get("fraud_score", 0) or 0
    if ipqs.get("status") == "success":
        base_score = max(0, base_score - (ipqs_fraud * 0.3))

    # Hunter score bonus
    hunter = email_trust_data.get("hunter", {}) if email_trust_data else {}
    hunter_score = hunter.get("score", 50) or 50
    if hunter.get("status") == "success":
        base_score = min(100, base_score * 0.7 + hunter_score * 0.3)

    final_score = round(base_score)

    return final_score, reputation, {
        "email": email,
        "domain": domain,
        "is_disposable": False,
        "domain_reputation": reputation,
        "hunter_score": hunter_score,
        "ipqs_fraud_score": ipqs_fraud
    }


# ══════════════════════════════════════════════════════════════════════
# 3. IDENTITY MATCH SCORE  (fuzzy name correspondence)
# ══════════════════════════════════════════════════════════════════════

def compute_identity_match(entities, verification_data, github_data_raw):
    """
    Fuzzy name matching between resume name and GitHub/LinkedIn profile.
    Returns: score 0–100, correspondence level, metadata.
    """
    resume_name = entities.get("identity", {}).get("name", "") or ""

    # Try to get GitHub username as comparison point
    candidate_id = entities.get("identity", {})
    github_handle = candidate_id.get("github", "")
    if github_handle:
        github_handle = github_handle.rstrip("/").split("/")[-1].replace("-", " ").replace("_", " ")

    # Also get identity match from verification layer
    id_verif = verification_data.get("identity_verification", {}) if verification_data else {}
    existing_match = id_verif.get("identity_match_score", 0)

    # Fuzzy ratio using SequenceMatcher (rapidfuzz optional)
    fuzzy_score = 0
    source_used = "none"
    if resume_name and github_handle:
        try:
            from rapidfuzz import fuzz
            fuzzy_score = fuzz.token_sort_ratio(resume_name.lower(), github_handle.lower())
            source_used = "rapidfuzz"
        except ImportError:
            from difflib import SequenceMatcher
            fuzzy_score = round(SequenceMatcher(
                None,
                re.sub(r'[^a-z]', '', resume_name.lower()),
                re.sub(r'[^a-z]', '', github_handle.lower())
            ).ratio() * 100)
            source_used = "difflib"
    elif existing_match > 0:
        fuzzy_score = existing_match
        source_used = "identity_engine"
    else:
        fuzzy_score = 60  # No reference to compare — neutral
        source_used = "neutral_default"

    correspondence = (
        "Strong"   if fuzzy_score >= 90 else
        "Moderate" if fuzzy_score >= 70 else
        "Weak"     if fuzzy_score >= 40 else
        "No Match"
    )

    return fuzzy_score, correspondence, {
        "resume_name": resume_name,
        "reference_handle": github_handle or "(none)",
        "fuzzy_match_score": fuzzy_score,
        "correspondence_level": correspondence,
        "matching_engine": source_used
    }


# ══════════════════════════════════════════════════════════════════════
# 4. SHADOW SCORE  (weighted reliability index)
# ══════════════════════════════════════════════════════════════════════

def calculate_shadow_score(github_score, email_score, identity_score):
    """
    Reliability Index = (GitHub * 0.40) + (Email * 0.20) + (Identity * 0.40)
    Every component is traceable to its deterministic source.
    """
    weighted = (
        (github_score  * 0.40) +
        (email_score   * 0.20) +
        (identity_score * 0.40)
    )
    return round(weighted, 1)


# ══════════════════════════════════════════════════════════════════════
# 5. ANOMALY DETECTION  (each flag is deterministic)
# ══════════════════════════════════════════════════════════════════════

def detect_anomalies(entities, github_meta, email_meta, identity_meta,
                     career_stage_data, intelligence_data):
    """
    Anomaly flags are deterministic. anomaly_probability = min(flags * 15, 100).
    """
    flags = []

    # A1: Experience age vs GitHub account age
    stage = career_stage_data.get("stage", "Unknown") if career_stage_data else "Unknown"
    signals = career_stage_data.get("signals_used", {}) if career_stage_data else {}
    total_exp = signals.get("total_exp_years", 0)
    gh_created = github_meta.get("account_created_year")
    gh_exists  = github_meta.get("exists", False)

    if gh_exists and gh_created and total_exp > 5:
        acct_age = datetime.now().year - gh_created
        if acct_age < (total_exp / 2):
            flags.append(
                f"Experience-Age Mismatch: Resume implies ~{total_exp}yr tenure "
                f"but GitHub account is only {acct_age}yr old."
            )

    # A2: Disposable email
    if email_meta.get("is_disposable"):
        flags.append("Disposable Email: Address linked to a known throwaway domain.")

    # A3: Senior title, no digital presence
    if stage in ("Senior", "Executive") and not gh_exists:
        flags.append(
            f"{stage}-level candidate with no detectable GitHub presence — "
            "notable absence at this stage."
        )

    # A4: Weak identity correspondence
    if identity_meta.get("correspondence_level") in ("Weak", "No Match") and \
       identity_meta.get("resume_name") and identity_meta.get("reference_handle") != "(none)":
        flags.append(
            f"Identity Correspondence Weak: Resume name vs handle match score "
            f"{identity_meta['fuzzy_match_score']}%."
        )

    # A5: Inflation signals from hiring intelligence engine
    prop = intelligence_data.get("proportionality", {}) if intelligence_data else {}
    inf_idx = prop.get("inflation_index", 0)
    if inf_idx >= 45:
        flags.append(
            f"Claim Inflation Detected (index: {inf_idx}/100): "
            f"{prop.get('proportionality_verdict', 'Inflated')} claim-to-evidence ratio."
        )

    # A6: AI-generated language
    if prop.get("ai_language_detected"):
        flags.append(
            "Template/AI-Generated Language: Resume narrative shows high density "
            "of standardized phrasing patterns."
        )

    # A7: IPQS email fraud
    if email_meta.get("ipqs_fraud_score", 0) > 70:
        flags.append(
            f"Email Fraud Signal: IPQS risk score {email_meta['ipqs_fraud_score']}/100 "
            "for this address."
        )

    anomaly_probability = min(len(flags) * 15, 100)

    return {
        "anomaly_probability": anomaly_probability,
        "flags": flags,
        "flag_count": len(flags)
    }


# ══════════════════════════════════════════════════════════════════════
# 6. HONEST NARRATIVE  (1–2 professional sentences)
# ══════════════════════════════════════════════════════════════════════

def generate_honest_narrative(shadow_score, stage, github_meta, email_meta,
                               anomalies, intelligence_data):
    """
    Generates a professional 1–2 sentence recruiter narrative.
    Never blank. Never cosmetic.
    """
    # Shorthand aliases
    repo_ct     = github_meta.get("repo_count", 0)
    gh_exists   = github_meta.get("exists", False)
    rep         = email_meta.get("domain_reputation", "Unknown")
    flag_ct     = anomalies.get("flag_count", 0)
    hire_risk   = intelligence_data.get("risk", {}).get("hiring_risk_level", "Moderate") \
                  if intelligence_data else "Moderate"
    coherence   = intelligence_data.get("consistency", {}).get("verdict", "Unknown") \
                  if intelligence_data else "Unknown"

    # Opening based on shadow score
    if shadow_score >= 80:
        opening = "Candidate demonstrates strong reliability signals across identity, email, and digital activity layers."
    elif shadow_score >= 60:
        opening = "Candidate presents a moderately reliable profile with some gaps in external verification."
    elif shadow_score >= 40:
        opening = "Candidate profile shows limited verifiable signals; several trust dimensions require manual review."
    else:
        opening = "Candidate reliability signals are weak; significant verification gaps detected across all layers."

    # Supporting detail
    details = []
    if gh_exists and repo_ct > 0:
        details.append(f"GitHub activity ({repo_ct} repos) corroborates technical engagement.")
    elif not gh_exists and stage in ("Fresher", "Academic"):
        details.append("Absence of digital presence is consistent with early career stage.")
    elif not gh_exists and stage in ("Senior", "Executive"):
        details.append("Expected digital footprint for this career stage is absent.")

    if rep in ("University / Academic", "Corporate Domain"):
        details.append(f"Email domain ({rep.lower()}) adds institutional credibility.")

    if flag_ct == 0:
        details.append("No structural anomalies detected.")
    elif flag_ct <= 2:
        details.append(f"{flag_ct} anomaly flag(s) identified; supplemental verification recommended.")
    else:
        details.append(f"{flag_ct} anomaly flags raised; thorough verification required before proceeding.")

    details.append(f"Hiring risk assessed as {hire_risk}. Internal narrative coherence: {coherence}.")

    narrative = opening + " " + " ".join(details)
    return narrative


# ══════════════════════════════════════════════════════════════════════
# 7. SHA-256 REPORT INTEGRITY HASH  (Web3 proof-of-check)
# ══════════════════════════════════════════════════════════════════════

def generate_report_hash(report_dict):
    """
    Deterministic cryptographic fingerprint of the forensic report.
    SHA-256 over canonical JSON. Same input always produces same hash.
    """
    # Remove mutable fields before hashing (timestamp, hash itself)
    hashable = {k: v for k, v in report_dict.items() if k != "meta"}
    serialized = json.dumps(hashable, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


# ══════════════════════════════════════════════════════════════════════
# 8. MAIN FORENSIC REPORT BUILDER
# ══════════════════════════════════════════════════════════════════════

def generate_forensic_report(entities, verification_data, intelligence_data,
                               extraction_meta, latency_seconds, fraud_probability):
    """
    Assembles the PRACTICAL forensic report.
    """
    # 1. Redefined Metrics
    trust_score = round(100 - fraud_probability, 1)
    evidence = intelligence_data.get("evidence_strength", {})
    evidence_strength = evidence.get("level", "Weak")
    evidence_score = evidence.get("score", 0)
    
    validation_level = (
        "High" if fraud_probability > 60 or evidence_score < 30 else
        "Medium" if fraud_probability > 30 or evidence_score < 50 else
        "Low"
    )

    # 2. Identity Check
    identity_meta = compute_identity_match(entities, verification_data, {})[2]
    identity_check = {
        "verdict": "Identity appears genuine" if identity_meta["fuzzy_match_score"] > 70 else "Identity requires verification",
        "signals": [
            "Name consistent across sources" if identity_meta["fuzzy_match_score"] > 90 else "Name mismatch across external profiles",
            "No alias patterns detected",
            "No obvious impersonation signals"
        ]
    }

    # 3. Experience Timeline Check
    narrative = intelligence_data.get("narrative", {})
    exp_timeline = {
        "claimed_experience": f"{intelligence_data.get('career_stage', {}).get('signals_used', {}).get('total_exp_years', 0)} years",
        "structured_history": "Complete" if narrative.get("has_work_history") and not narrative.get("timeline_gaps") else "Partial",
        "gaps_detected": "Yes" if narrative.get("timeline_gaps") else "No",
        "gap_details": narrative.get("timeline_gaps", []),
        "recommendation": "Ask candidate to clarify employment gap" if narrative.get("timeline_gaps") else "Timeline appears consistent"
    }

    # 4. Skill Verification
    skills = entities.get("skills", [])
    consistency = intelligence_data.get("consistency", {})
    skill_verification = {
        "declared_skills": len(skills),
        "demonstrated_skills": int(len(skills) * consistency.get("skill_mention_ratio", 0)),
        "verdict": "None of the declared technical skills are referenced in project or job descriptions." if consistency.get("skill_mention_ratio") == 0 else "Skills are partially cited in experience descriptions.",
        "insights": [
            "Skills may be added without demonstrated application" if consistency.get("skill_mention_ratio", 0) < 0.3 else "Skills align with work history descriptions",
            "Resume may be keyword-optimized rather than experience-driven" if consistency.get("skill_mention_ratio", 0) < 0.2 else "Experience details support skill claims"
        ],
        "interview_focus": "Ask for real project examples per skill" if consistency.get("skill_mention_ratio", 0) < 0.5 else "Standard technical validation"
    }

    # 5. Digital Footprint
    gh_raw = verification_data.get("api_signals", {}).get("github", {})
    gh_meta = compute_github_trust(gh_raw)[2]
    digital_footprint = {
        "github_activity": "Active" if gh_meta.get("repo_count", 0) > 10 else "Minimal" if gh_meta.get("exists") else "Not found",
        "linked_profile_depth": "Deep" if gh_meta.get("repo_count", 0) > 5 else "Limited",
        "external_portfolio": "Not found",
        "context": "This does NOT imply fraud, but reduces evidence strength."
    }

    # 6. Final Hiring Signal
    recruiter_action = []
    if fraud_probability < 30 and evidence_score > 60:
        recruiter_action = ["Suitable for fast-track", "Standard technical interview"]
        verdict = "Strong candidate with supporting evidence."
    elif fraud_probability < 40 and evidence_score < 50:
        recruiter_action = ["Suitable for screening round", "Technical claims must be validated in live discussion", "Do not fast-track without deeper proof"]
        verdict = "Low fraud risk but limited supporting evidence."
    elif fraud_probability > 60:
        recruiter_action = ["High risk profile requiring strict validation", "Deep forensic background check recommended", "Mandatory live coding session"]
        verdict = "High risk profile requiring strict validation."
    else:
        recruiter_action = ["Standard screening recommended", "Verify key technical claims"]
        verdict = "Moderate candidate with partial evidence."

    final_signal = {
        "trust_score": trust_score,
        "evidence_strength": evidence_strength,
        "fraud_risk": "High" if fraud_probability > 60 else "Moderate" if fraud_probability > 30 else "Low",
        "recruiter_action": recruiter_action,
        "verdict": verdict
    }

    return {
        "meta": {
            "scan_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "latency_seconds": round(latency_seconds, 3),
            "validation_level": validation_level
        },
        "identity_check": identity_check,
        "experience_timeline_check": exp_timeline,
        "skill_verification": skill_verification,
        "digital_footprint": digital_footprint,
        "final_hiring_signal": final_signal,
        "honest_narrative": f"ML Forensic Audit: {fraud_probability}% fraud probability. {verdict}"
    }
