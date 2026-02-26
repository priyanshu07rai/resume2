"""
career_stage_engine.py — Career Stage Classifier
Classifies resume into a career stage BEFORE any scoring happens.
All downstream evaluation adapts to the stage.
"""
import re
from datetime import datetime

CURRENT_YEAR = datetime.now().year

# ── Stage Definitions ──────────────────────────────────────────────────
STAGES = ["Academic", "Fresher", "Early Professional", "Mid-Level", "Senior", "Executive"]

# Stage baselines: prevents index collapse for early-career candidates
STAGE_BASELINES = {
    "Academic": 58,
    "Fresher": 60,
    "Early Professional": 62,
    "Mid-Level": 65,
    "Senior": 68,
    "Executive": 70
}

# Stage-aware expectation rules: tells the system what's NORMAL to expect
STAGE_EXPECTATIONS = {
    "Academic": {
        "expects_github":        False,
        "expects_certifications":False,
        "expects_work_history":  False,
        "expects_metrics":       False,
        "penalty_for_no_github": False,
        "focus":                 "internal_coherence",
        "description":           "student or pre-graduation candidate"
    },
    "Fresher": {
        "expects_github":        False,
        "expects_certifications":False,
        "expects_work_history":  False,
        "expects_metrics":       False,
        "penalty_for_no_github": False,
        "focus":                 "project_coherence",
        "description":           "recent graduate with < 1 year experience"
    },
    "Early Professional": {
        "expects_github":        False,  # Optional, not mandatory
        "expects_certifications":False,
        "expects_work_history":  True,
        "expects_metrics":       False,
        "penalty_for_no_github": False,
        "focus":                 "progression_coherence",
        "description":           "1–3 years professional experience"
    },
    "Mid-Level": {
        "expects_github":        True,   # For tech roles
        "expects_certifications":True,
        "expects_work_history":  True,
        "expects_metrics":       True,
        "penalty_for_no_github": True,   # Only for tech domain
        "focus":                 "depth_and_impact",
        "description":           "3–7 years with specialization"
    },
    "Senior": {
        "expects_github":        True,
        "expects_certifications":False,  # Experience > certs at senior level
        "expects_work_history":  True,
        "expects_metrics":       True,
        "penalty_for_no_github": True,
        "focus":                 "evidence_depth",
        "description":           "7–12 years with leadership"
    },
    "Executive": {
        "expects_github":        False,  # Execs rarely maintain personal GitHub
        "expects_certifications":False,
        "expects_work_history":  True,
        "expects_metrics":       True,
        "penalty_for_no_github": False,
        "focus":                 "strategic_impact",
        "description":           "12+ years in leadership/management"
    }
}


def classify_career_stage(entities, raw_text):
    """
    Classifies career stage based on:
    1. Graduation year (recency)
    2. Total work experience duration
    3. Role title seniority signals
    4. Language complexity and claim density
    5. Education level
    Returns: stage string, confidence (0–100), and expectation rules.
    """
    signals = _extract_classification_signals(entities, raw_text)
    stage, confidence = _reason_stage(signals)
    expectations = STAGE_EXPECTATIONS[stage]
    baseline = STAGE_BASELINES[stage]

    return {
        "stage": stage,
        "confidence": confidence,
        "baseline_score": baseline,
        "expectations": expectations,
        "signals_used": signals
    }


def _extract_classification_signals(entities, raw_text):
    """Extract measurable signals for stage classification."""
    text_lower = raw_text.lower()

    # 1. Graduation year
    grad_years = re.findall(r'20[0-2][0-9]', raw_text)
    grad_years = [int(y) for y in grad_years if int(y) <= CURRENT_YEAR]
    earliest_year = min(grad_years) if grad_years else None
    latest_year = max(grad_years) if grad_years else None
    years_since_graduation = (CURRENT_YEAR - latest_year) if latest_year else None

    # 2. Work duration proxy (from experience list)
    experience = entities.get("experience", []) or []
    num_roles = len(experience)

    # Estimate total experience from role dates or count
    total_exp_years = 0
    for exp in experience:
        start = exp.get("start_date", "")
        end = exp.get("end_date", "present")
        sy = re.search(r'(20[0-2][0-9]|19[8-9][0-9])', str(start))
        ey = re.search(r'(20[0-2][0-9]|19[8-9][0-9])', str(end))
        if sy:
            s = int(sy.group(1))
            e = int(ey.group(1)) if ey else CURRENT_YEAR
            total_exp_years += max(0, e - s)

    # 3. Title seniority signals in raw text
    exec_titles = ["ceo", "cto", "coo", "chief", "vp ", "vice president", "president", "founder", "director"]
    senior_titles = ["senior", "lead", "principal", "staff engineer", "architect", "head of", "engineering manager"]
    mid_titles = ["engineer", "developer", "analyst", "specialist", "consultant", "associate"]
    student_signals = ["student", "fresher", "graduate", "intern", "b.tech", "b.e.", "b.sc", "pursuing", "final year", "cgpa", "gpa", "sgpa"]

    exec_hits = sum(1 for t in exec_titles if t in text_lower)
    senior_hits = sum(1 for t in senior_titles if t in text_lower)
    mid_hits = sum(1 for t in mid_titles if t in text_lower)
    student_hits = sum(1 for t in student_signals if t in text_lower)

    # 4. Language complexity (proxy: avg word length, claim density)
    words = raw_text.split()
    avg_word_len = sum(len(w) for w in words) / max(len(words), 1)
    
    # Claim intensity words
    power_claims = ["expert", "specialist", "deep", "advanced", "extensive", "10+ years", "15+ years", "proven track record"]
    claim_density = sum(1 for c in power_claims if c in text_lower)

    return {
        "years_since_graduation": years_since_graduation,
        "total_exp_years": total_exp_years,
        "num_roles": num_roles,
        "exec_hits": exec_hits,
        "senior_hits": senior_hits,
        "mid_hits": mid_hits,
        "student_hits": student_hits,
        "avg_word_len": round(avg_word_len, 2),
        "claim_density": claim_density
    }


def _reason_stage(s):
    """
    Reason through available signals to determine the most likely career stage.
    Returns (stage, confidence).
    """
    ysg = s["years_since_graduation"]
    exp = s["total_exp_years"]
    
    # Executive
    if s["exec_hits"] >= 2 or exp >= 15:
        return "Executive", 90

    # Senior
    if s["senior_hits"] >= 2 or exp >= 7:
        conf = 85 if exp >= 7 else 70
        return "Senior", conf

    # Mid-Level
    if exp >= 3 or (s["num_roles"] >= 2 and s["mid_hits"] >= 1):
        conf = 80 if exp >= 3 else 65
        return "Mid-Level", conf

    # Fresher / Early Professional
    if s["student_hits"] >= 2 or (ysg is not None and ysg <= 1):
        return "Fresher", 85

    if ysg is not None and ysg <= 3:
        return "Early Professional", 80

    # Academic (still studying)
    if s["student_hits"] >= 1 or (ysg is not None and ysg == 0):
        return "Academic", 88

    # Default to Early Professional with low confidence
    return "Early Professional", 55
