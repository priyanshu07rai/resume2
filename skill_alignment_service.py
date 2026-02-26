def align_skills_to_evidence(entities, verification_results, domain_info):
    """
    Industrial Skill Alignment & Evidence Fusion Engine.
    Maps claimed skills to verified repo languages and compute weighted alignment.
    Formula: (Verified Overlap * 0.6) + (Activity * 0.2) + (Maturity * 0.2)
    """
    domain = domain_info.get("domain", "General")
    claimed_skills = [s.strip().lower() for s in entities.get("skills", []) if s.strip()]
    
    verified_skills = []
    unverified_claims = []
    
    # 1. Platform Evidence Extraction
    api_signals = verification_results.get("api_signals", {})
    github = api_signals.get("github", {})
    metrics = github.get("metrics", {}) if github.get("exists") else {}
    
    evidence_pool = set()
    if github.get("exists"):
        langs = metrics.get("languages", {})
        evidence_pool.update([l.lower() for l in langs.keys()])

    # 2. Skill Overlap Calculation
    if claimed_skills:
        for skill in claimed_skills:
            # Check if skill exists globally in evidence pool
            if any(skill in ev or ev in skill for ev in evidence_pool):
                verified_skills.append(skill)
            else:
                unverified_claims.append(skill)
    
    overlap_ratio = len(verified_skills) / len(claimed_skills) if claimed_skills else 0
    
    # 3. Evidence Fusion Scoring
    # (verified_languages_overlap * 0.6) + (activity_score * 0.2) + (account_maturity_score * 0.2)
    activity_score = metrics.get("activity_score", 0) / 100
    maturity_score = metrics.get("account_maturity_score", 0) / 100
    
    # If not a tech domain or no GH provided, we degrade gracefully or use other signals
    if domain in ["Software Engineering", "Data / AI"] and github.get("exists"):
        fusion_score = (overlap_ratio * 60) + (activity_score * 20) + (maturity_score * 20)
    else:
        # For non-tech or missing GH, use overlap only or mock/baseline
        fusion_score = overlap_ratio * 100 if claimed_skills else 50
    
    return {
        "alignment_score": round(fusion_score, 1),
        "match_ratio": round(overlap_ratio * 100),
        "verified_skills": verified_skills,
        "unverified_claims": unverified_claims,
        "evidence_sources": ["GitHub"] if evidence_pool else [],
        "metrics_applied": {
            "activity": round(activity_score * 100),
            "maturity": round(maturity_score * 100),
            "overlap": round(overlap_ratio * 100)
        }
    }
