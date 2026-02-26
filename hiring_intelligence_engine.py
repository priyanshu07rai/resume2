"""
hiring_intelligence_engine.py — Adaptive Hiring Intelligence Engine
The core reasoning system. Replaces mechanical scoring with contextual analysis.
Thinks like a senior recruiter + background analyst + risk assessor simultaneously.
"""
import re
from datetime import datetime
from career_stage_engine import classify_career_stage, STAGE_BASELINES

CURRENT_YEAR = datetime.now().year

# ── Inflation Signal Dictionary ────────────────────────────────────────
INFLATION_PATTERNS = {
    "ai_ml": {
        "high_claims": ["deep learning specialist", "ai expert", "ml architect", "nlp expert", "llm specialist"],
        "evidence_markers": ["model", "dataset", "trained", "accuracy", "f1", "benchmark", "paper", "published", "kaggle", "research"],
        "project_required": True
    },
    "backend": {
        "high_claims": ["backend architect", "systems engineer", "distributed systems expert"],
        "evidence_markers": ["api", "microservice", "database", "latency", "throughput", "scale", "deployed", "production"],
        "project_required": True
    },
    "fullstack": {
        "high_claims": ["full stack expert", "senior full stack"],
        "evidence_markers": ["react", "node", "django", "flask", "deployed", "production", "repository", "users"],
        "project_required": False
    },
    "generic": {
        "high_claims": ["expert", "specialist", "master", "guru", "ninja", "rockstar", "10x developer", "visionary", "strategic leader"],
        "evidence_markers": ["project", "implemented", "built", "delivered", "led", "achieved", "result", "impact"],
        "project_required": False
    }
}

# AI-generated language fingerprints
AI_LANGUAGE_PATTERNS = [
    "demonstrated ability to", "proven track record of", "passionate about leveraging",
    "adept at utilizing", "committed to delivering", "possessing strong",
    "with a focus on synergy", "cutting-edge solutions", "dynamic team player",
    "results-driven professional", "seeking to leverage", "strong communicator"
]


def run_intelligence_analysis(entities, verification_results, raw_text, domain_info, extraction_metadata=None, fraud_probability=0.0, target_role="", expected_skills=None):
    """
    8-Stage Adaptive Hiring Intelligence Engine.
    Returns contextual reasoning, not mechanical scores.
    """
    domain = domain_info.get("domain", "General")

    # ─ STAGE 1: Career Stage Classification ──────────────────────────
    stage_data = classify_career_stage(entities, raw_text)
    stage = stage_data["stage"]
    stage_confidence = stage_data["confidence"]
    expectations = stage_data["expectations"]
    baseline = stage_data["baseline_score"]

    # ─ STAGE 2: Narrative Reconstruction ─────────────────────────────
    narrative = _reconstruct_narrative(entities, raw_text, stage)

    # ─ STAGE 3: Claim Proportionality Analysis ───────────────────────
    proportionality = _analyze_claim_proportionality(entities, raw_text, stage, domain)

    # ─ STAGE 4: Internal Consistency Analysis ────────────────────────
    consistency = _analyze_internal_consistency(entities, raw_text)

    # ─ STAGE 5: External Signal Integration (Stage-Aware) ────────────
    external_signals = _integrate_external_signals(verification_results, expectations, stage, domain)

    # ─ STAGE 6: Evidence Strength Calculation ────────────────────────
    evidence_strength = _calculate_evidence_strength(
        proportionality, consistency, external_signals, entities, stage
    )

    # ─ STAGE 7: Core Metrics Calculation ─────────────────────────────
    core_metrics = _compute_core_metrics(fraud_probability, evidence_strength)

    # ─ STAGE 8: Role-Based Fit Calculation ───────────────────────────
    role_match = _compute_role_match(entities, raw_text, expected_skills)

    # ─ STAGE 9: Stage-Adaptive Scoring ───────────────────────────────
    score = _compute_adaptive_score(
        baseline, proportionality, consistency, external_signals, fraud_probability, stage_data
    )

    # ─ STAGE 10: Intelligence Verdict (Reasoning First) ──────────────
    verdict = _generate_intelligence_verdict(
        stage, stage_confidence, narrative, proportionality,
        consistency, external_signals, core_metrics, score, domain,
        verification_results=verification_results,
        evidence_strength=evidence_strength,
        fraud_probability=fraud_probability,
        role_match=role_match
    )

    # ─ STAGE 11: Structured Analysis Table (deterministic, no Groq) ─────
    structured_analysis = build_structured_analysis(
        external_signals=external_signals,
        consistency=consistency,
        evidence_strength=evidence_strength,
        core_metrics=core_metrics,
        fraud_probability=fraud_probability,
        entities=entities,
        verification_results=verification_results
    )

    return {
        "career_stage": {
            "stage": stage,
            "confidence": stage_confidence,
            "baseline_score": baseline,
            "description": expectations.get("description", "")
        },
        "narrative": narrative,
        "proportionality": proportionality,
        "consistency": consistency,
        "external_signals": external_signals,
        "core_metrics": core_metrics,
        "evidence_strength": evidence_strength,
        "role_match": role_match,
        "score": score,
        "verdict": verdict,
        "structured_analysis": structured_analysis
    }



# ═══════════════════════════════════════════════════════════════════════
# STAGE 2: NARRATIVE RECONSTRUCTION
# ═══════════════════════════════════════════════════════════════════════

def _reconstruct_narrative(entities, raw_text, stage):
    """
    Rebuilds the candidate's story and checks if the progression
    feels natural given the stage and sequence of events.
    """
    education = entities.get("education", []) or []
    experience = entities.get("experience", []) or []
    skills = entities.get("skills", []) or []
    certifications = entities.get("certifications", []) or []

    # Education completeness
    has_education = len(education) > 0
    has_work_history = len(experience) > 0
    has_skills = len(skills) > 0

    # Progression logic check
    progression_notes = []
    progression_natural = True

    if stage in ("Academic", "Fresher"):
        if not has_education:
            progression_notes.append("Education section missing for an early-stage candidate — unusual.")
        if has_work_history and len(experience) > 3:
            progression_notes.append("Extensive work history claimed for early-stage; warrants closer review.")
        else:
            progression_notes.append("Limited or absent work history is appropriate for this career stage.")

    elif stage in ("Early Professional", "Mid-Level"):
        if not has_work_history:
            progression_notes.append("No structured work history despite expected professional experience.")
            progression_natural = False
        else:
            progression_notes.append(f"{len(experience)} role(s) documented; progression visible.")

    elif stage in ("Senior", "Executive"):
        if len(experience) < 3:
            progression_notes.append("Senior-level claim with very few documented roles — depth unexplained.")
            progression_natural = False
        else:
            progression_notes.append(f"{len(experience)} progressive roles documented; career timeline visible.")

    # Gap detection (rough — from text scan)
    year_mentions = sorted(set(int(y) for y in re.findall(r'20[0-2][0-9]', raw_text) if int(y) <= CURRENT_YEAR))
    gaps = []
    for i in range(1, len(year_mentions)):
        diff = year_mentions[i] - year_mentions[i - 1]
        if diff > 2:
            gaps.append(f"{year_mentions[i-1]}–{year_mentions[i]} ({diff}yr gap)")

    if gaps:
        progression_notes.append(f"Potential timeline gaps detected: {', '.join(gaps)}.")
    
    return {
        "has_education": has_education,
        "has_work_history": has_work_history,
        "has_skills": has_skills,
        "skill_count": len(skills),
        "role_count": len(experience),
        "certification_count": len(certifications),
        "timeline_gaps": gaps,
        "progression_natural": progression_natural,
        "notes": progression_notes
    }


# ═══════════════════════════════════════════════════════════════════════
# STAGE 3: CLAIM PROPORTIONALITY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

def _analyze_claim_proportionality(entities, raw_text, stage, domain):
    """
    For each major claim, measures whether the resume provides proportional
    supporting evidence. Produces inflation_index (not a fraud score).
    """
    text_lower = raw_text.lower()
    skills = [s.lower() for s in (entities.get("skills", []) or [])]
    experience = entities.get("experience", []) or []

    # Detect high-intensity claims in text
    inflation_flags = []
    evidence_count = 0
    claim_count = 0

    domain_key = _map_domain_to_key(domain)
    patterns = INFLATION_PATTERNS.get(domain_key, INFLATION_PATTERNS["generic"])
    all_patterns = {**INFLATION_PATTERNS["generic"], **patterns}

    # Check high-intensity claims
    active_high_claims = []
    for claim in patterns["high_claims"] + INFLATION_PATTERNS["generic"]["high_claims"]:
        if claim in text_lower:
            claim_count += 1
            active_high_claims.append(claim)

    # Check supporting evidence markers
    active_evidence = []
    for marker in patterns["evidence_markers"] + INFLATION_PATTERNS["generic"]["evidence_markers"]:
        if marker in text_lower:
            evidence_count += 1
            active_evidence.append(marker)

    # Proportionality ratio
    if claim_count > 0:
        evidence_ratio = evidence_count / (claim_count * 3)  # Expect 3 evidence points per claim
        if evidence_ratio < 0.4:
            inflation_flags.append(f"High-intensity claims ({', '.join(active_high_claims[:3])}) with insufficient supporting evidence.")
    
    # Project evidence check for tech domain  
    project_keywords = ["built", "developed", "implemented", "deployed", "designed", "created", "led", "architected"]
    project_hits = sum(1 for k in project_keywords if k in text_lower)
    
    if stage in ("Mid-Level", "Senior", "Executive") and claim_count > 0 and project_hits < 2:
        inflation_flags.append("Senior-level claim density without concrete project or delivery evidence.")

    # AI-generated language detection (inflation proxy)
    ai_hits = [p for p in AI_LANGUAGE_PATTERNS if p in text_lower]
    ai_language_detected = len(ai_hits) >= 3

    if ai_language_detected:
        inflation_flags.append(
            f"High density of template-style phrasing detected ({len(ai_hits)} patterns). "
            "Candidate narrative may be AI-assisted or heavily templated."
        )

    # Compute inflation index: 0 (none) → 100 (extreme)
    inflation_index = 0
    if claim_count > 0 and evidence_count < claim_count:
        inflation_index += min(40, (claim_count - evidence_count) * 10)
    if ai_language_detected:
        inflation_index += 25
    if stage in ("Mid-Level", "Senior") and project_hits < 2:
        inflation_index += 15
    inflation_index = min(100, inflation_index)

    return {
        "high_intensity_claims": active_high_claims[:5],
        "evidence_markers_found": len(active_evidence),
        "project_evidence_hits": project_hits,
        "ai_language_detected": ai_language_detected,
        "ai_language_patterns": ai_hits[:3],
        "inflation_flags": inflation_flags,
        "inflation_index": inflation_index,
        "proportionality_verdict": (
            "Proportionate" if inflation_index < 20 else
            "Mildly Inflated" if inflation_index < 45 else
            "Significantly Inflated" if inflation_index < 70 else
            "Highly Inflated"
        )
    }


# ═══════════════════════════════════════════════════════════════════════
# STAGE 4: INTERNAL CONSISTENCY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

def _analyze_internal_consistency(entities, raw_text):
    """
    Detects date overlaps, role escalation anomalies, grade/skill mismatches,
    and cross-declaration inconsistencies.
    """
    experience = entities.get("experience", []) or []
    flags = []

    # Date overlap detection
    role_years = []
    for exp in experience:
        sy = re.search(r'(20[0-2][0-9]|19[8-9][0-9])', str(exp.get("start_date", "")))
        ey = re.search(r'(20[0-2][0-9]|19[8-9][0-9])', str(exp.get("end_date", "present")))
        if sy:
            s = int(sy.group(1))
            e = int(ey.group(1)) if ey else CURRENT_YEAR
            role_years.append((s, e, exp.get("role", "Unknown")))

    overlap_detected = False
    for i in range(len(role_years)):
        for j in range(i + 1, len(role_years)):
            s1, e1, r1 = role_years[i]
            s2, e2, r2 = role_years[j]
            if s2 < e1 - 1:  # Allow 1yr grace for overlapping roles (consulting)
                flags.append(f"Timeline overlap: '{r1}' ({s1}–{e1}) overlaps with '{r2}' ({s2}–{e2}).")
                overlap_detected = True

    # Escalation speed — check for unrealistic jumps
    text_lower = raw_text.lower()
    rapid_escalation = False
    if "manager" in text_lower or "lead" in text_lower:
        all_years = sorted(set(int(y) for y in re.findall(r'20[0-2][0-9]', raw_text) if int(y) <= CURRENT_YEAR))
        if all_years and (CURRENT_YEAR - min(all_years)) < 3:
            flags.append("Leadership title claimed within 3 years of earliest documented year — verify escalation.")
            rapid_escalation = True

    # Formatting consistency check (declared skills vs described experience)
    skills_declared = set(s.lower() for s in (entities.get("skills", []) or []))
    exp_text = " ".join(str(e.get("details", "")) for e in experience).lower()
    
    mentioned_in_exp = sum(1 for s in skills_declared if s in exp_text) if exp_text and skills_declared else 0
    skill_mention_ratio = mentioned_in_exp / max(len(skills_declared), 1)

    if skills_declared and skill_mention_ratio < 0.2 and len(skills_declared) > 5:
        flags.append(
            f"Only {mentioned_in_exp}/{len(skills_declared)} declared skills appear in experience descriptions. "
            "Skills may be bolted on rather than demonstrated."
        )

    # Coherence score (100 = fully coherent)
    coherence_score = 100
    if overlap_detected: coherence_score -= 25
    if rapid_escalation: coherence_score -= 15
    if skill_mention_ratio < 0.2 and len(skills_declared) > 5: coherence_score -= 15
    coherence_score = max(0, coherence_score)

    return {
        "flags": flags,
        "date_overlap_detected": overlap_detected,
        "rapid_escalation_flag": rapid_escalation,
        "skill_mention_ratio": round(skill_mention_ratio, 2),
        "coherence_score": coherence_score,
        "verdict": (
            "High Coherence" if coherence_score >= 80 else
            "Moderate Coherence" if coherence_score >= 55 else
            "Low Coherence"
        )
    }


# ═══════════════════════════════════════════════════════════════════════
# STAGE 5: EXTERNAL SIGNAL INTEGRATION (Stage-Aware)
# ═══════════════════════════════════════════════════════════════════════

def _integrate_external_signals(verification_results, expectations, stage, domain):
    """
    External absence is neutral unless stage expects presence.
    External contradiction is a risk signal.
    Never treats lack of digital footprint as fraud.
    """
    api_signals = verification_results.get("api_signals", {}) if verification_results else {}
    identity = verification_results.get("identity_verification", {}) if verification_results else {}

    github = api_signals.get("github", {})
    stack_overflow = api_signals.get("stackoverflow", {})
    email_trust = verification_results.get("email_trust", {}) if verification_results else {}

    signals = {}
    contradictions = []
    neutral_absences = []
    positive_signals = []

    # GitHub
    github_present = github.get("exists", False)
    if github_present:
        positive_signals.append("GitHub profile verified.")
        activity = github.get("metrics", {}).get("activity_score", 0)
        if activity > 50:
            positive_signals.append(f"Active GitHub: activity score {activity}.")
    elif expectations.get("penalty_for_no_github") and domain.lower() in ("technology", "software", "ai/ml", "data science"):
        contradictions.append("No GitHub presence for a senior tech candidate — notable absence at this stage.")
    else:
        neutral_absences.append("No GitHub — not expected at this career stage or domain, non-penalizable.")
    signals["github"] = {"present": github_present, "metrics": github.get("metrics", {})}

    # Email
    ipqs = email_trust.get("ipqs", {}) if email_trust else {}
    if ipqs.get("status") == "success":
        fraud_score = ipqs.get("fraud_score", 0)
        if fraud_score > 70:
            contradictions.append(f"Email fraud risk score: {fraud_score}/100 — high-risk address pattern.")
        elif fraud_score < 30:
            positive_signals.append("Email address validated as low-risk.")
    signals["email"] = {"checked": bool(ipqs), "fraud_score": ipqs.get("fraud_score", "N/A")}

    # Stack Overflow
    so_present = stack_overflow.get("exists", False)
    if so_present and stage in ("Senior", "Executive"):
        positive_signals.append("Stack Overflow presence corroborates technical depth.")
    elif not so_present:
        neutral_absences.append("No Stack Overflow — supplementary signal, absence is neutral.")
    signals["stackoverflow"] = {"present": so_present}

    # Overall coverage assessment
    coverage_level = (
        "Strong" if len(positive_signals) >= 3 else
        "Adequate" if len(positive_signals) >= 1 else
        "Minimal"
    )

    return {
        "positive_signals": positive_signals,
        "contradictions": contradictions,
        "neutral_absences": neutral_absences,
        "coverage_level": coverage_level,
        "signals": signals
    }


# ═══════════════════════════════════════════════════════════════════════
# STAGE 5.5: EVIDENCE STRENGTH CALCULATION
# ═══════════════════════════════════════════════════════════════════════

def _calculate_evidence_strength(proportionality, consistency, external, entities, stage):
    """
    Measures how 'solid' the profile is based on concrete evidence markers.
    0 (Vacuum) -> 100 (Rock Solid)
    """
    strength = 0
    
    # 1. Skill Demonstration (max 40)
    ratio = consistency.get("skill_mention_ratio", 0)
    strength += (ratio * 40)
    
    # 2. Digital Footprint (max 30)
    gh = external.get("signals", {}).get("github", {})
    if gh.get("present"):
        strength += 15
        metrics = gh.get("metrics", {})
        repos = metrics.get("repo_count", 0)
        if repos > 10: strength += 15
        elif repos > 0: strength += 5
    
    # 3. Work Detail Depth (max 30)
    exp = entities.get("experience", []) or []
    detail_len = sum(len(str(e.get("details", ""))) for e in exp)
    if detail_len > 1000: strength += 30
    elif detail_len > 500: strength += 15
    elif detail_len > 100: strength += 5
    
    # Stage calibration
    if stage in ("Academic", "Fresher"):
        # Lower expectations for digital footprint/work depth
        strength = min(100, strength * 1.5)
        
    return {
        "score": round(strength, 1),
        "level": (
            "Strong" if strength >= 75 else
            "Moderate" if strength >= 45 else
            "Weak"
        ),
        "skill_ratio": ratio,
        "detail_depth": detail_len
    }


# ═══════════════════════════════════════════════════════════════════════
# STAGE 7: CORE METRICS
# ═══════════════════════════════════════════════════════════════════════

def _compute_core_metrics(fraud_probability, evidence_strength):
    """
    Computes real metrics based on AI fraud probability and evidence.
    """
    trust_score = round(max(0, 100 - fraud_probability), 1)
    ev_score = evidence_strength.get("score", 0)
    
    if fraud_probability > 60:
        val_req = "High"
    elif fraud_probability > 30 or ev_score < 50:
        val_req = "Medium"
    else:
        val_req = "Low"
        
    return {
        "trust_score": trust_score,
        "evidence_strength": evidence_strength.get("level", "Weak"),
        "validation_required_level": val_req
    }


# ═══════════════════════════════════════════════════════════════════════
# STAGE 7: STAGE-ADAPTIVE SCORING
# ═══════════════════════════════════════════════════════════════════════

def _compute_adaptive_score(baseline, proportionality, consistency, external, fraud_probability, stage_data):
    """
    Stage-adaptive scoring prevents index collapse for early-career candidates.
    base_score = stage_baseline
                 + proportionality_bonus
                 + coherence_bonus
                 - inflation_penalty
                 - contradiction_penalty
    """
    score = baseline

    # Proportionality bonus/penalty
    inf_idx = proportionality["inflation_index"]
    if inf_idx < 20:
        score += 12   # Good proportionality
    elif inf_idx < 45:
        score -= 5    # Mild inflation
    elif inf_idx < 70:
        score -= 15   # Significant inflation
    else:
        score -= 25   # Extreme inflation

    # Coherence bonus/penalty
    coh = consistency["coherence_score"]
    if coh >= 80:
        score += 10
    elif coh >= 55:
        score += 3
    else:
        score -= 12

    # External signal bonus (stage-weighted — less weight for early career)
    stage = stage_data["stage"]
    ext_weight = 0.05 if stage in ("Academic", "Fresher") else 0.15
    positive_count = len(external["positive_signals"])
    contradiction_count = len(external["contradictions"])
    score += (positive_count * 5 * ext_weight * 10)
    score -= (contradiction_count * 15)

    # Fraud penalty
    score -= (fraud_probability * 0.2)

    final_score = round(max(0, min(100, score)), 1)

    # System confidence: how complete is the evidence relative to stage expectation?
    # Different from extraction confidence — this is epistemic confidence
    stage_confidence = stage_data["confidence"]
    coherence_factor = coh / 100
    external_factor = min(1.0, (positive_count + 1) / 3) if stage in ("Mid-Level", "Senior", "Executive") else 0.9
    system_confidence = round((stage_confidence * 0.4 + coherence_factor * 100 * 0.35 + external_factor * 100 * 0.25))

    return {
        "hiring_index": final_score,
        "system_confidence": system_confidence,
        "baseline_used": baseline,
        "stage": stage
    }


# ═══════════════════════════════════════════════════════════════════════
# STAGE 8: ROLE-BASED MATCHING
# ═══════════════════════════════════════════════════════════════════════

import re

def _compute_role_match(entities, raw_text, expected_skills):
    """
    Computes how well the candidate's skills align with the expected skills.
    Extracts from structured entities and uses regex boundary checks on raw text.
    expected_skills should be a list of strings extracted by the AI upfront.
    """
    resume_skills = [s.lower() for s in (entities.get("skills", []) or [])]
    raw_text_lower = raw_text.lower() if raw_text else ""
    
    if not expected_skills:
        return {
            "match_score": 0,
            "is_evaluated": False,
            "verdict": "No specific skills or role requirements provided.",
            "matched_skills": [],
            "missing_skills": []
        }
        
    matched = set()
    missing = set()
    
    # Check each expected skill
    for skill in expected_skills:
        skill_lower = skill.lower().strip()
        # Check if in structured parsed list
        if any(skill_lower == s or skill_lower in s or s in skill_lower for s in resume_skills):
            matched.add(skill_lower)
        else:
            # Fallback: Check raw unstructured text with word boundaries
            # Handle tricky skills like 'c++', 'c#' which have punctuation
            pattern = r'\b' + re.escape(skill_lower) + r'(?:\b|$)' 
            if skill_lower in ["c++", "c#", "next.js", "node.js"]:
                # custom boundary for symbols
                pattern = r'(?:\b|\s)' + re.escape(skill_lower) + r'(?:\s|$|\.|\,)'
            
            if re.search(pattern, raw_text_lower):
                matched.add(skill_lower)
            else:
                missing.add(skill_lower)
    
    match_ratio = len(matched) / len(expected_skills) if expected_skills else 0
    match_score = round(match_ratio * 100)
    
    v_str = "High Match"
    if match_score < 40:
        v_str = "Low Match"
    elif match_score < 70:
        v_str = "Moderate Fit"
        
    return {
        "match_score": match_score,
        "is_evaluated": True,
        "verdict": v_str,
        "matched_skills": list(matched),
        "missing_skills": list(missing)
    }

# ═══════════════════════════════════════════════════════════════════════
# STAGE 9: INTELLIGENCE VERDICT (Reasoning First)
# ═══════════════════════════════════════════════════════════════════════

def _generate_intelligence_verdict(stage, stage_confidence, narrative, proportionality,
                                    consistency, external, core_metrics, score, domain, 
                                    verification_results=None, evidence_strength=None, fraud_probability=0.0, role_match=None):
    """
    Generates a professional, recruiter-readable verdict.
    Reasoning comes before numbers. No dramatic language.
    Passes internal self-check: "Would this help a recruiter decide?"
    """
    lines = []

    # 1. Stage summary
    lines.append(
        f"Profile classified as {stage} (confidence: {stage_confidence}%). "
        f"Evaluation expectations are calibrated accordingly."
    )

    # 2. Narrative coherence summary
    if narrative["progression_natural"]:
        lines.append("Career progression appears coherent and consistent with the declared stage.")
    else:
        lines.append("Career progression shows gaps or inconsistencies that warrant closer review.")

    if narrative["timeline_gaps"]:
        lines.append(f"Unaccounted periods identified: {', '.join(narrative['timeline_gaps'])}.")

    for note in narrative["notes"][:2]:
        lines.append(note)

    # 3. Claim proportionality
    pv = proportionality["proportionality_verdict"]
    if pv == "Proportionate":
        lines.append("Claims are proportionate to the level of supporting evidence provided.")
    else:
        lines.append(
            f"Claim proportionality assessment: {pv}. "
            + (proportionality["inflation_flags"][0] if proportionality["inflation_flags"] else "")
        )

    # 4. Internal consistency
    lines.append(f"Internal consistency: {consistency['verdict']} (score: {consistency['coherence_score']}/100).")

    if consistency["flags"]:
        lines.append(consistency["flags"][0])

    # 5. External signals
    if external["positive_signals"]:
        lines.append("External signals: " + " ".join(external["positive_signals"][:2]))
    elif external["neutral_absences"]:
        lines.append(f"External footprint: limited, consistent with {stage} stage.")
        
    # 6. Role Match integration
    if role_match and role_match.get("is_evaluated"):
        lines.append(f"Role Fit Score: {role_match['match_score']}%. {role_match['verdict']}.")
        if role_match['missing_skills']:
            # mention up to 2 missing skills
            ms = role_match['missing_skills'][:2]
            lines.append(f"Candidate lacks some expected core competencies mapped to this role (e.g., {', '.join(ms)}).")

    # 7. Core Metrics
    val_req = core_metrics["validation_required_level"]
    trust = core_metrics["trust_score"]
    ev_level = core_metrics["evidence_strength"]
    lines.append(
        f"Trust Score: {trust}/100. "
        f"Evidence Strength: {ev_level}. "
        f"Validation Required: {val_req}."
    )

    # 7. AI Forensic Overlay (The "Honest" Voice)
    # Check for Groq Forensic results in verification_results
    ai_forensic = {}
    if verification_results:
        # Standard location in older pipeline
        ai_forensic = verification_results.get("api_signals", {}).get("ai_consensus", {})
        # Support for unified_data from new Groq-Native pipeline
        if not ai_forensic:
            ai_forensic = verification_results.get("ai_consensus", {}).get("unified_data", {})
        if not ai_forensic:
            ai_forensic = verification_results.get("unified_data", {})

    forensic_critique = ai_forensic.get("forensic_narrative")
    if forensic_critique:
        lines.insert(0, f"AI FORENSIC ANALYSIS: {forensic_critique}")

    # 8. Verdict preparation
    hiring_index = score["hiring_index"]
    
    # 9. Dynamic System Confidence
    # Epistemic confidence = (Stage Confidence * 0.3) + (Consensus Score * 0.7)
    consensus_score = ai_forensic.get("confidence_score") or 70
    system_confidence = round((stage_confidence * 0.3) + (consensus_score * 0.7))
    
    lines.append(
        f"Hiring Index: {hiring_index}/100. "
        f"Dynamic System Confidence: {system_confidence}%."
    )

    # 11. Final recommendation (adjusted for role)
    ev_score = evidence_strength.get("score", 0) if evidence_strength else 0
    
    base_rec = "Moderate profile requiring standard verification."
    if fraud_probability < 30 and ev_score > 60:
        base_rec = "Strong candidate with supporting evidence."
    elif fraud_probability < 40 and ev_score < 50:
        base_rec = "Low fraud risk but limited supporting evidence. Technical claims must be validated."
    elif fraud_probability > 60:
        base_rec = "High risk profile requiring strict validation."
        
    if role_match and role_match.get("is_evaluated"):
        if role_match["match_score"] < 40 and fraud_probability < 40:
            base_rec = f"Technically genuine candidate, but low match ({role_match['match_score']}%) for selected role."
        elif role_match["match_score"] > 70 and fraud_probability < 30:
            base_rec = f"Excellent fit ({role_match['match_score']}%) for selected role with strong verification signals."
            
    lines.append("Recommendation: " + base_rec)

    return {
        "full_verdict": " ".join(lines),
        "verdict_lines": lines,
        "validation_required": val_req,
        "hiring_index": hiring_index,
        "system_confidence": system_confidence
    }


# ── Helpers ────────────────────────────────────────────────────────────

def _risk_label(score):
    if score < 20: return "Low"
    if score < 45: return "Moderate"
    if score < 70: return "Elevated"
    return "High"

def _map_domain_to_key(domain):
    d = domain.lower()
    if "ai" in d or "ml" in d or "machine" in d: return "ai_ml"
    if "backend" in d or "software" in d or "tech" in d: return "backend"
    if "full" in d: return "fullstack"
    return "generic"


# ═══════════════════════════════════════════════════════════════════════
# STAGE 11: DETERMINISTIC STRUCTURED ANALYSIS TABLE
# Generates the Forensic Verification Signals Card without any AI calls.
# ═══════════════════════════════════════════════════════════════════════

def build_structured_analysis(external_signals, consistency, evidence_strength,
                               core_metrics, fraud_probability, entities, verification_results):
    """
    Builds a deterministic forensic verification signals table from local data.
    No AI / Groq required. All signals are computed from in-memory pipeline results.

    Returns:
        {
            "positive_indicators": [...],
            "negative_indicators": [...],
            "summary_snapshot": {...}
        }
    """
    pos = []
    neg = []

    # ── GitHub Signals ─────────────────────────────────────────────────
    api_signals = (verification_results or {}).get("api_signals", {})
    github = api_signals.get("github", {})
    gh_metrics = github.get("metrics", {})

    if github.get("exists"):
        account_age = datetime.now().year - (gh_metrics.get("account_created_year") or datetime.now().year)
        repo_count  = gh_metrics.get("repo_count", 0)
        last_commit = gh_metrics.get("last_commit_days_ago", 9999)
        top_lang    = gh_metrics.get("top_language", "Unknown")

        if account_age >= 2:
            pos.append({"signal": f"GitHub Account Age {account_age} years",
                        "evidence_source": "GitHub", "impact": "Positive",
                        "severity": "Low" if account_age < 5 else "Moderate"})
        if repo_count > 10:
            pos.append({"signal": f"{repo_count} public repositories found",
                        "evidence_source": "GitHub", "impact": "Positive", "severity": "Moderate"})
        elif repo_count > 3:
            pos.append({"signal": f"{repo_count} repositories — adequate footprint",
                        "evidence_source": "GitHub", "impact": "Positive", "severity": "Low"})
        else:
            neg.append({"signal": "No Repositories Found" if repo_count == 0 else f"Only {repo_count} repo(s) — minimal footprint",
                        "evidence_source": "GitHub", "impact": "Negative",
                        "severity": "High" if repo_count == 0 else "Moderate"})

        if last_commit < 30:
            pos.append({"signal": f"Recent activity ({last_commit}d ago) — active contributor",
                        "evidence_source": "GitHub", "impact": "Positive", "severity": "Low"})
        elif last_commit < 180:
            pos.append({"signal": f"Moderate activity ({last_commit}d since last commit)",
                        "evidence_source": "GitHub", "impact": "Positive", "severity": "Low"})
        else:
            neg.append({"signal": f"No Recent Activity ({last_commit}d since last commit)" if last_commit < 9000 else "No Recent Activity",
                        "evidence_source": "GitHub", "impact": "Negative", "severity": "High"})

        if top_lang and top_lang != "Unknown":
            pos.append({"signal": f"Primary language: {top_lang}",
                        "evidence_source": "GitHub", "impact": "Positive", "severity": "Low"})
    else:
        neg.append({"signal": "No GitHub profile linked or found",
                    "evidence_source": "GitHub", "impact": "Negative", "severity": "Moderate"})

    # ── Email Signals ──────────────────────────────────────────────────
    email_trust = (verification_results or {}).get("email_trust", {})
    ipqs = email_trust.get("ipqs", {})
    if ipqs.get("status") == "success":
        fraud_score = ipqs.get("fraud_score", 0)
        if fraud_score < 30:
            pos.append({"signal": f"Email risk score {fraud_score}/100 — safe",
                        "evidence_source": "IPQS", "impact": "Positive", "severity": "Low"})
        elif fraud_score > 70:
            neg.append({"signal": f"Email fraud risk elevated ({fraud_score}/100)",
                        "evidence_source": "IPQS", "impact": "Negative", "severity": "High"})

    hunter = email_trust.get("hunter", {})
    if hunter.get("score", 0) > 70:
        pos.append({"signal": f"Email deliverability confirmed (score: {hunter.get('score')}%)",
                    "evidence_source": "Hunter.io", "impact": "Positive", "severity": "Low"})

    # ── Skill Alignment ────────────────────────────────────────────────
    skill_ratio = consistency.get("skill_mention_ratio", 0)
    alignment_pct = round(skill_ratio * 100)
    if alignment_pct >= 60:
        pos.append({"signal": f"Skill Alignment Score {alignment_pct}%",
                    "evidence_source": "model inference", "impact": "Positive", "severity": "Moderate"})
    elif alignment_pct >= 30:
        neg.append({"signal": f"Partial skill alignment ({alignment_pct}%) — some skills not evidenced",
                    "evidence_source": "model inference", "impact": "Negative", "severity": "Moderate"})
    else:
        neg.append({"signal": "Low skill evidence — skills listed but not demonstrated in work history",
                    "evidence_source": "model inference", "impact": "Negative", "severity": "High"})

    # ── Fraud Probability ──────────────────────────────────────────────
    if fraud_probability < 30:
        pos.append({"signal": f"Low Fraud Risk ({fraud_probability:.0f}%)",
                    "evidence_source": "ML fraud model", "impact": "Positive", "severity": "Low"})
    elif fraud_probability > 60:
        neg.append({"signal": f"High Fraud Probability ({fraud_probability:.0f}%)",
                    "evidence_source": "model inference", "impact": "Negative", "severity": "High"})
    else:
        neg.append({"signal": f"Moderate Fraud Probability ({fraud_probability:.0f}%)",
                    "evidence_source": "model inference", "impact": "Negative", "severity": "Moderate"})

    # ── Evidence Strength ──────────────────────────────────────────────
    ev_level = evidence_strength.get("level", "Weak")
    ev_score = evidence_strength.get("score", 0)
    if ev_level == "Strong":
        pos.append({"signal": f"Strong Evidence Index (score: {ev_score:.0f})",
                    "evidence_source": "metadata", "impact": "Positive", "severity": "Moderate"})
    elif ev_level == "Moderate":
        neg.append({"signal": f"Moderate Evidence Strength (score: {ev_score:.0f})",
                    "evidence_source": "metadata", "impact": "Neutral", "severity": "Moderate"})
    else:
        neg.append({"signal": "Low Evidence Strength Index",
                    "evidence_source": "metadata", "impact": "Negative", "severity": "Moderate"})

    # ── Consistency Flags ──────────────────────────────────────────────
    for flag in (consistency.get("flags") or [])[:2]:
        neg.append({"signal": flag[:80],
                    "evidence_source": "consistency engine", "impact": "Negative", "severity": "Moderate"})

    # ── Summary Snapshot ──────────────────────────────────────────────
    trust = core_metrics.get("trust_score", 50)
    val_req = core_metrics.get("validation_required_level", "Medium")

    if trust >= 70 and fraud_probability < 30:
        risk_level = "Low"
    elif trust >= 50 or fraud_probability < 50:
        risk_level = "Moderate"
    elif trust >= 30:
        risk_level = "Elevated"
    else:
        risk_level = "High"

    capability_certainty = "High" if ev_level == "Strong" else ("Medium" if ev_level == "Moderate" else "Low")

    gh_repos = gh_metrics.get("repo_count", 0) if github.get("exists") else 0
    digital_depth = "Strong" if gh_repos > 10 else ("Moderate" if gh_repos > 3 else "Weak")

    if risk_level == "Low" and capability_certainty != "Low":
        rec_action = "Auto-clear / Proceed to interview"
    elif risk_level in ("Moderate", "Elevated"):
        rec_action = "Technical Interview Required"
    else:
        rec_action = "Manual Review / Reject if unverified"

    return {
        "positive_indicators": pos,
        "negative_indicators": neg,
        "summary_snapshot": {
            "overall_risk_level": risk_level,
            "capability_certainty": capability_certainty,
            "digital_depth_rating": digital_depth,
            "recommended_action": rec_action
        }
    }

