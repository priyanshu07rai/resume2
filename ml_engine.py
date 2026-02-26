"""
ml_engine.py — Fine-Tuned ML Scoring Engine v2
-----------------------------------------------
Provides:
  - predict_resume_category()   : LinearSVC domain classifier
  - predict_fraud_probability() : Calibrated fraud probability from joblib model
  - extract_ml_features()       : Rich structured feature dict shared with AI layer
  - compute_ml_composite_score(): Fused deterministic score (ML + heuristics)

Design principle: ML features are built ONCE and shared with the AI forensic
prompt, so both layers reason from the same structured evidence.
"""

import os
import pickle
import joblib
import logging
from datetime import datetime

log = logging.getLogger("HonestRecruiter.ML")

CURRENT_YEAR = datetime.now().year

# ── Model Loading ─────────────────────────────────────────────────────────────
_base = os.path.dirname(__file__)

def _load(path, loader=pickle.load):
    try:
        with open(path, "rb") as f:
            return loader(f)
    except Exception as e:
        log.warning("Failed to load model at %s: %s", path, e)
        return None

resume_model   = _load(os.path.join(_base, "resume_model.pkl"))
vectorizer     = _load(os.path.join(_base, "vectorizer.pkl"))
fraud_model    = joblib.load(os.path.join(_base, "fraud_model.pkl")) if os.path.exists(
                     os.path.join(_base, "fraud_model.pkl")) else None

if not fraud_model:
    log.warning("fraud_model.pkl could not be loaded — fraud score will use heuristic fallback.")
if not resume_model or not vectorizer:
    log.warning("resume_model.pkl / vectorizer.pkl missing — category prediction unavailable.")


# ── Public API ────────────────────────────────────────────────────────────────

def predict_resume_category(raw_text: str) -> str:
    """Returns the ML-predicted professional category (e.g. 'Data Science')."""
    if not raw_text or not isinstance(raw_text, str):
        return "Unknown"
    if not resume_model or not vectorizer:
        return "General"
    try:
        X = vectorizer.transform([raw_text])
        return str(resume_model.predict(X)[0])
    except Exception as e:
        log.error("predict_resume_category failed: %s", e)
        return "General"


def extract_ml_features(data: dict) -> dict:
    """
    Extracts the full 12-feature vector used for fraud scoring AND shared
    directly with the AI forensic prompt so both layers reason from the same
    structured evidence.

    Input `data` dict shape:
    {
      "structured_claims": {
          "claimed_years_experience": int,
          "skills": list[str],
          "role_count": int            (optional)
      },
      "digital_footprint": {
          "repo_count": int,
          "account_created_year": int,
          "last_commit_days_ago": int,
          "top_language": str
      },
      "email": {
          "domain_type": str,          # "corporate" | "personal" | "disposable"
          "fraud_score": int           # 0-100 from IPQS
      },
      "consistency": {
          "coherence_score": int,      # 0-100
          "overlap_detected": bool
      },
      "proportionality": {
          "inflation_index": int       # 0-100
      }
    }
    """
    struct   = data.get("structured_claims", {})
    footprint = data.get("digital_footprint", {})
    email    = data.get("email", {})
    consist  = data.get("consistency", {})
    prop     = data.get("proportionality", {})

    # Core claims
    claimed_exp   = int(struct.get("claimed_years_experience", 0) or 0)
    skills        = struct.get("skills", []) or []
    role_count    = int(struct.get("role_count", len(struct.get("experience", []))) or 0)

    # Digital footprint
    repo_count    = int(footprint.get("repo_count", 0) or 0)
    acct_year     = int(footprint.get("account_created_year", CURRENT_YEAR) or CURRENT_YEAR)
    account_age   = max(0, CURRENT_YEAR - acct_year)
    last_commit   = int(footprint.get("last_commit_days_ago", 999) or 999)
    top_lang      = footprint.get("top_language", "Unknown") or "Unknown"

    # Derived signals
    experience_gap = max(0, claimed_exp - account_age)
    skill_count    = len(skills)
    skill_match    = min(100, skill_count * 8)   # 8 pts per skill, capped at 100

    # Email trust
    email_type   = email.get("domain_type", "personal") or "personal"
    email_ipqs   = int(email.get("fraud_score", 50) or 50)
    email_score  = (
        100 if email_type == "corporate" else
        70  if email_type == "personal" else
        10
    )
    # Blend IPQS score if available
    if email.get("fraud_score") is not None:
        email_score = max(0, email_score - email_ipqs * 0.5)

    # Internal consistency signals
    coherence          = int(consist.get("coherence_score", 70) or 70)
    overlap_penalty    = 20 if consist.get("overlap_detected") else 0
    inflation_index    = int(prop.get("inflation_index", 0) or 0)

    # Activity recency signal (1=active today, 0=dormant >1yr)
    activity_signal = max(0.0, 1.0 - last_commit / 365.0)

    return {
        # 7 model features (same order as fraud_model training)
        "claimed_experience":   claimed_exp,
        "repo_count":           repo_count,
        "account_age":          account_age,
        "last_commit_days":     last_commit,
        "experience_gap":       experience_gap,
        "skill_match":          skill_match,
        "email_score":          email_score,

        # Extended features (used for heuristic scoring + AI context)
        "role_count":           role_count,
        "skill_count":          skill_count,
        "top_language":         top_lang,
        "coherence_score":      coherence,
        "overlap_penalty":      overlap_penalty,
        "inflation_index":      inflation_index,
        "activity_signal":      round(activity_signal, 2),
        "email_ipqs":           email_ipqs,
    }


def predict_fraud_probability(data: dict) -> float:
    """
    Returns fraud probability as a float 0–100.

    Uses the loaded fraud_model if available. If not, falls back to a
    calibrated heuristic formula so the pipeline always produces a
    meaningful, non-constant value.
    """
    features = extract_ml_features(data)

    # ── ML Model Path ─────────────────────────────────────────────────────
    if fraud_model is not None:
        try:
            import pandas as pd
            X = pd.DataFrame([{
                "claimed_experience": features["claimed_experience"],
                "repo_count":         features["repo_count"],
                "account_age":        features["account_age"],
                "last_commit_days":   features["last_commit_days"],
                "experience_gap":     features["experience_gap"],
                "skill_match":        features["skill_match"],
                "email_score":        features["email_score"],
            }])

            if hasattr(fraud_model, "predict_proba"):
                prob = fraud_model.predict_proba(X)[0][1] * 100
            else:
                # For models without predict_proba (e.g. LinearSVC)
                decision = fraud_model.decision_function(X)[0]
                # Sigmoid calibration
                import math
                prob = 100.0 / (1.0 + math.exp(-decision))

            # Clamp and log
            prob = float(max(1.0, min(99.0, prob)))
            log.info("ML fraud score: %.1f%% (model: %s)", prob, type(fraud_model).__name__)
            return round(prob, 1)

        except Exception as e:
            log.error("fraud_model.predict_proba failed: %s — using heuristic.", e)

    # ── Heuristic Fallback (calibrated, non-constant) ─────────────────────
    return _heuristic_fraud_score(features)


def compute_ml_composite_score(features: dict, fraud_probability: float) -> dict:
    """
    Fuses ML features into a composite score that the AI layer can use
    as calibrated pre-context. Returns a rich dict with:
      - fraud_probability (from ML model)
      - reliability_index (inverse of fraud, weighted by evidence quality)
      - evidence_quality (0-100)
      - risk_label
      - ml_flags (list of specific concerns)
    """
    # Evidence quality score — how much hard data do we have?
    eq = 0.0
    if features["repo_count"] > 0:   eq += 20
    if features["repo_count"] > 10:  eq += 15
    if features["account_age"] > 2:  eq += 15
    if features["last_commit_days"] < 60:  eq += 15
    if features["skill_match"] > 40: eq += 15
    if features["email_score"] > 60: eq += 10
    if features["coherence_score"] > 70: eq += 10
    evidence_quality = min(100.0, eq)

    # Reliability index: trust score weighted by evidence quality
    raw_reliability = max(0.0, 100.0 - fraud_probability)
    # Penalise reliability if evidence is thin (can't be confident of high trust)
    evidence_weight = evidence_quality / 100.0
    reliability = round(raw_reliability * (0.4 + 0.6 * evidence_weight), 1)

    # ML flags
    flags = []
    if features["experience_gap"] > 3:
        flags.append(f"Timeline gap: claims {features['claimed_experience']}yr exp but GitHub only {features['account_age']}yr old.")
    if features["repo_count"] == 0 and features["claimed_experience"] > 2:
        flags.append("No GitHub repos found despite claimed technical experience.")
    if features["last_commit_days"] > 180:
        flags.append(f"No GitHub activity in {features['last_commit_days']} days — stale digital footprint.")
    if features["inflation_index"] > 40:
        flags.append(f"Resume inflation index: {features['inflation_index']}/100 — claims exceed evidence.")
    if features["overlap_penalty"] > 0:
        flags.append("Overlapping work roles detected — timeline inconsistency.")
    if features["email_ipqs"] > 60:
        flags.append(f"Email address IPQS fraud score: {features['email_ipqs']}/100 — high-risk domain.")
    if features["skill_count"] > 25:
        flags.append(f"Skill list length ({features['skill_count']}) is unusually high — keyword stuffing risk.")

    # Risk label
    if fraud_probability < 20:   risk_label = "Low"
    elif fraud_probability < 45: risk_label = "Moderate"
    elif fraud_probability < 70: risk_label = "Elevated"
    else:                        risk_label = "High"

    return {
        "fraud_probability":  round(fraud_probability, 1),
        "reliability_index":  reliability,
        "evidence_quality":   round(evidence_quality, 1),
        "risk_label":         risk_label,
        "ml_flags":           flags,
        "feature_snapshot":   {
            "claimed_exp":    features["claimed_experience"],
            "repo_count":     features["repo_count"],
            "account_age":    features["account_age"],
            "last_commit":    features["last_commit_days"],
            "exp_gap":        features["experience_gap"],
            "skill_count":    features["skill_count"],
            "coherence":      features["coherence_score"],
            "inflation":      features["inflation_index"],
        }
    }


# ── Private Helpers ───────────────────────────────────────────────────────────

def _heuristic_fraud_score(f: dict) -> float:
    """
    Calibrated heuristic fallback when fraud_model is unavailable.
    Produces meaningful, non-constant scores. Range: 1–99.
    """
    score = 20.0  # Base risk (everyone starts low)

    # Experience gap is the strongest signal of fabrication
    gap = f["experience_gap"]
    if gap > 5:   score += 35
    elif gap > 3: score += 20
    elif gap > 1: score += 10

    # No repos despite claiming experience
    if f["repo_count"] == 0 and f["claimed_experience"] > 2:
        score += 20
    elif f["repo_count"] < 3 and f["claimed_experience"] > 4:
        score += 10

    # Stale activity
    if f["last_commit_days"] > 365:  score += 15
    elif f["last_commit_days"] > 90: score += 5

    # Email risk
    if f["email_score"] < 30:  score += 12
    elif f["email_score"] < 60: score += 4

    # Inflation penalty
    score += f["inflation_index"] * 0.2

    # Coherence bonus — good coherence means lower risk
    score -= (f["coherence_score"] - 70) * 0.15

    # Skill match bonus — more verified skills = lower risk
    score -= f["skill_match"] * 0.1

    result = max(1.0, min(99.0, score))
    log.info("Heuristic fraud score: %.1f%% (model unavailable)", result)
    return round(result, 1)
