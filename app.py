import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
import time
import logging
import concurrent.futures
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime
import hashlib
import json

# ── Database Import ──────────────────────────────────────────────────────
import candidate_db
from compare_engine import compare_profiles
import compare_ai_engine
from ai_consensus_engine import groq_client, gemini_client, safe_groq_call
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger("HonestRecruiter")

# ── Service Imports ─────────────────────────────────────────────────────
from ingestion_service import ingest_document
from domain_service import classify_domain
from extraction_service import extract_entities
from verification_service import verify_external_evidence
from hiring_intelligence_engine import run_intelligence_analysis
from forensic_engine import generate_forensic_report
from ml_engine import predict_resume_category, predict_fraud_probability, extract_ml_features, compute_ml_composite_score
from ai_consensus_engine import (
    generate_live_forensic_narrative,
    generate_github_deep_analysis,
    generate_structured_forensic_analysis,
)

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'web cam'))
from interview_engine import InterviewEngine
from session_storage import save_session, load_session
import uuid

# In-memory storage for active sessions
active_sessions = {}

load_dotenv()

app = Flask(__name__)
CORS(app)

ALLOWED_EXTENSIONS = {'pdf'}

# ── Helpers ─────────────────────────────────────────────────────────────
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def safe_future(fut, timeout, fallback):
    """Wait on a future with a hard timeout. Return fallback on miss."""
    done, _ = concurrent.futures.wait([fut], timeout=timeout)
    if fut in done:
        try:
            return fut.result()
        except Exception as exc:
            log.error("Future raised exception: %s", exc)
            return fallback
    log.warning("Future timed out after %ss", timeout)
    return fallback

def _make_error(message, detail="", code=500, meta=None):
    return jsonify({
        "success": False,
        "error": message,
        "detail": detail,
        "meta": meta or {}
    }), code

# ── Global Exception Handler ─────────────────────────────────────────────
@app.errorhandler(Exception)
def handle_exception(e):
    log.critical("Unhandled exception reached Flask: %s", e, exc_info=True)
    return jsonify({
        "success": False,
        "error": "Internal engine failure. Please retry.",
        "detail": str(e)
    }), 500

# ── Health Check ─────────────────────────────────────────────────────────
@app.route('/health')
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat() + "Z"})

# ── Root Route ───────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return '', 404

@app.route('/report/hash/<string:resume_hash>')
def report_by_hash(resume_hash):
    """
    Canonical, hash-based single candidate forensic report view.
    Hash is immutable — survives DB resets, server restarts.
    Falls back to reports/<hash>.json on disk if DB is empty.
    """
    cand = candidate_db.get_candidate_by_hash(resume_hash)
    if not cand:
        return render_template('report.html', initial_data='null',
                               error="Candidate not found.")
    payload = cand.get("forensic_payload") or {}
    if not payload:
        return render_template('report.html', initial_data='null',
                               error="Candidate report is incomplete.")
    return render_template('report.html',
                           initial_data=json.dumps({"data": payload, "meta": payload.get("meta", {})}))

@app.route('/report/<int:candidate_id>')
def report_view(candidate_id):
    """
    ID-based candidate report. Redirects to hash route for canonical URL.
    """
    cand = candidate_db.get_candidate_by_id(candidate_id)
    if not cand:
        return render_template('report.html', initial_data='null',
                               error="Candidate not found.")
    return redirect(url_for('report_by_hash', resume_hash=cand['hash']))

# ── Circuit-Breaker Fallback Payload ────────────────────────────────────
def _circuit_breaker_response(entities, domain, ml_category, fraud_probability, reason="AI service unavailable"):
    """
    Generates a graceful degraded report using only ML/local signals.
    No Groq / external AI required.
    """
    log.warning("Circuit breaker engaged: %s", reason)

    name = entities.get("identity", {}).get("name", "Candidate")
    skills = entities.get("skills", [])

    return {
        "candidate": {"name": name},
        "domain": domain,
        "intelligence": entities,
        "verification": {"api_signals": {}, "email_trust": {}, "alignment_evidence": {}, "success": False},
        "hiring_intelligence": {
            "verdict": {
                "verdict_lines": [
                    f"ML Domain Prediction: {ml_category}",
                    f"Fraud Risk Score (ML): {fraud_probability:.0f}%",
                    "Full AI analysis unavailable — Groq API rate limited or unreachable.",
                    "Degraded mode: showing ML-only signals.",
                ],
                "system_confidence": 30
            },
            "core_metrics": {
                "trust_score": max(0, 100 - fraud_probability),
                "evidence_strength": "Low (Degraded Mode)"
            },
            "role_match": {"is_evaluated": False},
            "consistency": {"verdict": "Unavailable", "coherence_score": 0},
            "external_signals": {"coverage_level": "No Coverage"},
        },
        "forensic_report": {
            "ai_narrative": f"Analysis degraded: {reason}",
            "reliability": {"shadow_score": 0, "risk_level": "Unknown"},
        }
    }

# ── Main Scan Route ──────────────────────────────────────────────────────
@app.route('/scan', methods=['POST'])
def scan_resume():
    """
    Production-Grade Intelligence Orchestrator.
    - Handles multiple files at once.
    - Skips duplicates using SHA-256.
    - Saves parsed candidates to DB.
    """
    overall_start = time.time()
    log.info("=== NEW BATCH SCAN REQUEST ===")

    # ── Input Validation ────────────────────────────────────────────────
    files = request.files.getlist("resumes")
    if not files or not files[0].filename:
        return _make_error("No file uploaded. Please attach at least one PDF.", code=400)

    target_role = request.form.get("target_role", "").strip()
    must_have_raw = request.form.get("must_have_skills", "").strip()
    job_description = request.form.get("job_description", "").strip()

    expected_skills = []
    if must_have_raw:
        expected_skills = [s.strip() for s in must_have_raw.split(",") if s.strip()]
    elif job_description:
        try:
            from ai_consensus_engine import extract_skills_from_jd
            expected_skills = extract_skills_from_jd(job_description, target_role)
        except Exception as exc:
            log.warning("JD skill extraction failed (non-fatal): %s", exc)
            expected_skills = []

    processed_count = 0
    skipped_count = 0

    file_datas = []
    for file in files:
        if allowed_file(file.filename):
            file_datas.append((file.read(), file.filename))

    def _process_file(file_data):
        file_bytes, filename = file_data
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        
        if candidate_db.is_duplicate(file_hash):
            log.info(f"Duplicate resume detected, updating: {filename} ({file_hash[:8]}...)")

        log.info("Processing file: %s (%d bytes)", filename, len(file_bytes))
        log.info("STAGE 1 — Document Ingestion")
        try:
            ingestion_result = ingest_document(file_bytes, filename)
        except Exception as exc:
            log.error("Ingestion service crashed: %s", exc, exc_info=True)
            return "error"
            
        if not ingestion_result.get("success"):
            err_msg = ingestion_result.get("error", "Unknown ingestion error")
            log.warning("Ingestion rejected: %s", err_msg)
            return "error"

        raw_text = ingestion_result["extraction"]["text"]

        # ── Stage 2: Concurrent AI Processing (with hard timeouts) ──────────
        log.info("STAGE 2 — Concurrent AI Processing")
        domain_fallback = {"domain": "General", "confidence": 0.5, "models_used": ["fallback"]}
        entity_fallback = {"identity": {"name": "Unknown Candidate"}, "skills": [], "extraction_meta": {"error": "timeout"}}
        verif_fallback  = {"api_signals": {}, "email_trust": {}, "alignment_evidence": {}, "success": False}

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            domain_future = executor.submit(classify_domain, raw_text)
            domain = safe_future(domain_future, timeout=30, fallback=domain_fallback)

            extract_future = executor.submit(extract_entities, raw_text, domain)
            entities = safe_future(extract_future, timeout=90, fallback=entity_fallback)

            verif_future = executor.submit(verify_external_evidence, entities, domain)
            verification = safe_future(verif_future, timeout=45, fallback=verif_fallback)

        # ── Stage 3: ML Feature Extraction + Scoring ────────────────────────
        log.info("STAGE 3 — ML Feature Extraction + Scoring")
        ml_category = "General"
        try:
            ml_category = predict_resume_category(raw_text)
            domain["ml_prediction"] = ml_category
        except Exception as exc:
            log.warning("  ML categorization failed: %s", exc)

        # Build full feature dict — shared with hiring intelligence and AI prompt
        identity_data  = entities.get("identity", {})
        consistency_rt = {}  # will be filled after Stage 4 runs; pre-pass uses defaults
        gh_metrics     = verification.get("api_signals", {}).get("github", {}).get("metrics", {})
        ipqs_data      = verification.get("email_trust", {}).get("ipqs", {})

        ml_input = {
            "structured_claims": {
                "claimed_years_experience": identity_data.get(
                    "experience_years", len(entities.get("experience", []))
                ),
                "skills": entities.get("skills", []),
                "role_count": len(entities.get("experience", [])),
            },
            "digital_footprint": gh_metrics,
            "email": {
                "domain_type": ipqs_data.get("domain_type", "personal"),
                "fraud_score": ipqs_data.get("fraud_score", 50),
            },
            "consistency": {"coherence_score": 70, "overlap_detected": False},   # pre-pass
            "proportionality": {"inflation_index": 0},                            # pre-pass
        }

        ml_features = extract_ml_features(ml_input)
        fraud_probability = predict_fraud_probability(ml_input)
        log.info("  ML Fraud Probability: %.2f%% | exp_gap=%d | repos=%d | days_since_commit=%d",
                 fraud_probability, ml_features["experience_gap"],
                 ml_features["repo_count"], ml_features["last_commit_days"])

        # ── Stage 4: Hiring Intelligence ──────────────────────────────────────
        log.info("STAGE 4 — Hiring Intelligence")
        try:
            intelligence = run_intelligence_analysis(
                entities=entities,
                verification_results=verification,
                raw_text=raw_text,
                domain_info=domain,
                extraction_metadata=ingestion_result.get("extraction"),
                fraud_probability=fraud_probability,
                target_role=target_role,
                expected_skills=expected_skills if expected_skills else None
            )
        except Exception as exc:
            log.error("  Hiring intelligence failed: %s", exc, exc_info=True)
            fallback_trust = round(max(0.0, 100.0 - fraud_probability), 1)
            intelligence = {
                "core_metrics": {"trust_score": fallback_trust, "evidence_strength": "Unknown"},
                "verdict": {"verdict_lines": ["Analysis degraded — see deterministic scores."]},
                "external_signals": {"coverage_level": "Unknown"},
                "consistency": {"verdict": "Unavailable", "coherence_score": 0},
                "role_match": {"is_evaluated": False},
            }

        # Stage 3.5: Refine ML features with actual coherence/inflation data from Stage 4
        try:
            consist_rt = intelligence.get("consistency", {})
            prop_rt    = intelligence.get("proportionality", {})
            ml_input["consistency"] = {
                "coherence_score":  consist_rt.get("coherence_score", 70),
                "overlap_detected": consist_rt.get("date_overlap_detected", False),
            }
            ml_input["proportionality"] = {
                "inflation_index": prop_rt.get("inflation_index", 0)
            }
            ml_features   = extract_ml_features(ml_input)
            fraud_probability = predict_fraud_probability(ml_input)
            log.info("  Refined ML Fraud Probability (post-consistency): %.2f%%", fraud_probability)
        except Exception as exc:
            log.warning("  ML refinement step: %s", exc)

        # Build the composite ML score object passed to the AI layer
        ml_composite = compute_ml_composite_score(ml_features, fraud_probability)
        log.info("  ML Composite: reliability=%.1f%% evidence_quality=%.0f%% risk=%s flags=%d",
                 ml_composite["reliability_index"], ml_composite["evidence_quality"],
                 ml_composite["risk_label"], len(ml_composite["ml_flags"]))

        # ── Stage 5: Structured Forensic AI Analysis ──────────────────────────
        log.info("STAGE 5 — Structured Forensic AI Analysis")
        candidate_out = entities.get("identity", {})
        c_name   = candidate_out.get("name", candidate_out.get("full_name", "Unknown Candidate"))
        c_domain = domain.get("domain", "General")

        # Use ml_composite reliability as the canonical trust score (blends ML + evidence quality)
        trust_score  = float(ml_composite.get("reliability_index", 50.0))
        evidence_str = intelligence.get("core_metrics", {}).get("evidence_strength", "Unknown")
        
        # Safe score calculation
        try:
            safe_fraud = float(fraud_probability) if fraud_probability is not None else 50.0
            final_score = round((trust_score + max(0.0, 100.0 - safe_fraud)) / 2, 2)
        except (TypeError, ValueError):
            final_score = trust_score
            
        risk_label   = ml_composite.get("risk_label", "Unknown")

        # AI forensic analysis receives the pre-computed ML composite and deterministic flags
        ai_forensics = generate_structured_forensic_analysis(
            resume_text=raw_text,
            entities=entities,
            verification=verification,
            fraud_probability=fraud_probability,
            trust_score=trust_score,
            domain_hint=c_domain,
            target_role=target_role,
            ml_composite=ml_composite,           # ← NEW: ML evidence fed into AI prompt
        )

        # Calibrate trust_score using AI confidence if AI succeeded
        if ai_forensics.get("ai_status") != "deterministic_fallback":
            ai_conf = ai_forensics.get("credibility_assessment", {}).get("confidence_score", 0)
            if ai_conf:
                # Weighted blend: 60% ML reliability + 40% AI confidence
                trust_score = round(trust_score * 0.6 + ai_conf * 0.4, 1)
                final_score = round((trust_score + max(0, 100 - fraud_probability)) / 2, 2)
                log.info("  Calibrated trust: %.1f%% (ML=%.1f%% AI_conf=%d%%)",
                         trust_score, ml_composite["reliability_index"], ai_conf)

        # ── Assemble Atomic Forensic Payload (Single Source of Truth) ────────
        # Calculate Data Completeness Confidence (Enterprise Metric)
        github_present = 1 if verification.get("api_signals", {}).get("github", {}).get("exists") else 0
        email_valid = 1 if verification.get("email_trust", {}).get("hunter", {}).get("status") == "valid" or verification.get("email_trust", {}).get("gmail", {}).get("status") == "verified" else 0
        experience_parse_success = 1 if len(entities.get("experience", [])) > 0 else 0
        model_prediction_confidence = ml_composite["evidence_quality"] / 100.0

        data_completeness_confidence = int(
            (github_present * 30) +
            (email_valid * 20) +
            (experience_parse_success * 20) +
            (model_prediction_confidence * 30)
        )

        insights = [
            f"Trust Score: {trust_score}% | Completeness: {data_completeness_confidence}%",
            f"Domain: {c_domain} | Risk: {risk_label}",
            "Strong external web/github footprint" if verification.get("success") else "Limited internet footprint"
        ]

        # ── Assemble Atomic Forensic Payload (Single Source of Truth) ────────
        forensic_payload = {
            "meta": {
                "name":          c_name,
                "domain":        c_domain,
                "hash":          file_hash,
                "pipeline_version": "v3.0",
                "model_version":    "fraud_model_v2",
                "scan_timestamp":   datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "target_role":      target_role or "",
            },
            "scores": {
                "reliability":  round(trust_score, 1),
                "fraud_score":  round(fraud_probability, 1),
                "final_score":  final_score,
                "risk_level":   risk_label,
                "evidence_strength": evidence_str,
                "data_completeness": data_completeness_confidence,
            },
            "deterministic_insights": insights,
            "ai_analysis":       ai_forensics,
            "hiring_intelligence": intelligence,
            "candidate":         candidate_out,
            "domain_info":       domain,
            "verification":      {
                "success":        verification.get("success", False),
                "github":         verification.get("api_signals", {}).get("github", {}),
                "email_trust":    verification.get("email_trust", {}),
            },
        }

        # ── Persist atomically ───────────────────────────────────────────────
        final_score_db = round(max(0.0, final_score), 2)   # clamp to 0 — display as positive index
        candidate_db.save_candidate(
            name=c_name,
            domain=c_domain,
            file_hash=file_hash,
            final_score=final_score_db,
            forensic_payload=forensic_payload,
        )
        # processed_count += 1
        log.info("  Saved '%s' | trust=%.1f%% fraud=%.1f%% final=%.2f",
                 c_name, trust_score, fraud_probability, final_score_db)

        return "processed"

    # Reduced workers to 2 to prevent rapid 429 rate-limiting from Groq
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(2, len(file_datas) or 1)) as executor:
        results = list(executor.map(_process_file, file_datas))
    
    for res in results:
        if res == "skipped":
            skipped_count += 1
        elif res == "processed":
            processed_count += 1

    log.info("=== BATCH SCAN COMPLETE in %.2fs ===", time.time() - overall_start)
    return jsonify({
        "success": True,
        "processed": processed_count,
        "skipped_duplicates": skipped_count,
        "redirect_url": "/shortlist"
    })

# ── Feature Routes ─────────────────────────────────────────────────────

@app.route('/shortlist')
def shortlist_view():
    candidates = candidate_db.get_all_candidates()
    return render_template('shortlist.html', candidates=candidates)

@app.route('/api/shortlist')
def api_shortlist():
    candidates = candidate_db.get_all_candidates()
    return jsonify(candidates)

@app.route('/api/clear_all', methods=['POST'])
def clear_all_data():
    candidate_db.clear_all()
    return jsonify({"success": True})

@app.route('/compare', methods=['POST'])
def compare_view():
    """Handles the 2-candidate selection from the Shortlist and computes differences."""
    c1_id = request.form.get('candidate_1')
    c2_id = request.form.get('candidate_2')
    
    if not c1_id or not c2_id:
        return redirect(url_for('shortlist_view'))
    return render_template("compare_loading.html", c1_id=c1_id, c2_id=c2_id)

@app.route('/api/run_compare', methods=['POST'])
def run_compare():
    c1_id = request.form.get('candidate_1')
    c2_id = request.form.get('candidate_2')
    
    if not c1_id or not c2_id:
        return redirect(url_for('shortlist_view'))
        
    p1 = candidate_db.get_candidate_by_id(int(c1_id))
    p2 = candidate_db.get_candidate_by_id(int(c2_id))
    
    if not p1 or not p2:
        return redirect(url_for('shortlist_view'))
    # ── Hydrate payloads ───────────────────────────────────────────────
    # _hydrate already expanded payload into flat fields: reliability, fraud_score, skills, etc.

    fp1 = p1.get("forensic_payload", {})
    fp2 = p2.get("forensic_payload", {})

    # Skills: prefer entities from candidate block, fall back to hiring_intelligence
    def _get_skills(fp):
        skills = fp.get("candidate", {}).get("skills", [])
        if not skills:
            skills = fp.get("hiring_intelligence", {}).get("narrative", {}).get("skills", [])
        return skills or []

    def _get_exp_years(fp):
        v = fp.get("candidate", {}).get("experience_years", 0)
        if not v:
            v = fp.get("scores", {}).get("reliability", 0) / 10  # rough fallback
        return v or 0

    # Enrich p1/p2 for compare_engine
    p1["skills"] = _get_skills(fp1)
    p2["skills"] = _get_skills(fp2)
    p1["experience_years"] = _get_exp_years(fp1)
    p2["experience_years"] = _get_exp_years(fp2)

    # Build comparison math
    metrics = compare_profiles(p1, p2)

    # ── Build AI synthesis payload (use hydrated flat fields) ────────────────────
    def _github_strength(fp):
        v = fp.get("verification", {}).get("github", {})
        if isinstance(v, dict) and v.get("exists"):
            return "Present"
        det = fp.get("deterministic_insights", [])
        if any("github" in str(i).lower() for i in det):
            return "Present"
        return "Absent"

    payload = {
        "candidate_A": {
            "name":             p1.get("name", "Candidate A"),
            "domain":           p1.get("domain", "General"),
            "reliability":      p1.get("reliability", 50),
            "fraud_score":      p1.get("fraud_score", 50),
            "skill_count":      len(p1["skills"]),
            "skills_sample":    p1["skills"][:8],
            "github_strength":  _github_strength(fp1),
            "experience_years": p1["experience_years"],
            "risk":             fp1.get("scores", {}).get("risk_level", "Unknown"),
            "ai_verdict":       fp1.get("ai_analysis", {}).get("summary_snapshot", {}).get("overall_risk_level", fp1.get("ai_analysis", {}).get("credibility_assessment", {}).get("overall_verdict", "N/A")),
        },
        "candidate_B": {
            "name":             p2.get("name", "Candidate B"),
            "domain":           p2.get("domain", "General"),
            "reliability":      p2.get("reliability", 50),
            "fraud_score":      p2.get("fraud_score", 50),
            "skill_count":      len(p2["skills"]),
            "skills_sample":    p2["skills"][:8],
            "github_strength":  _github_strength(fp2),
            "experience_years": p2["experience_years"],
            "risk":             fp2.get("scores", {}).get("risk_level", "Unknown"),
            "ai_verdict":       fp2.get("ai_analysis", {}).get("summary_snapshot", {}).get("overall_risk_level", fp2.get("ai_analysis", {}).get("credibility_assessment", {}).get("overall_verdict", "N/A")),
        },
        "comparison_metrics": {
            "reliability_diff":       metrics["reliability_diff"],
            "fraud_diff":             metrics["fraud_diff"],
            "skill_overlap_percent":  metrics["skill_overlap"],
            "experience_gap_years":   metrics["experience_gap"]
        }
    }

    # Run AI Consensus Comparison (Groq + Gemini)
    consensus_result = compare_ai_engine.run_consensus_comparison(
        groq_client=groq_client,
        gemini_client=gemini_client,
        safe_groq_call=safe_groq_call,
        log=log,
        comparison_data=payload
    )

    return render_template(
        "compare.html", p1=p1, p2=p2, metrics=metrics,
        narrative=consensus_result["final_bullets"],
        confidence=consensus_result["confidence"]
    )


# ── Demo Route ───────────────────────────────────────────────────────────
@app.route('/scan/demo', methods=['GET'])
def demo_scan():
    """Demo mode — no file upload, no API calls, full pre-verified response."""
    demo_report = {
        "meta": {
            "scan_timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "latency_seconds": 2.847,
            "system_confidence": 88,
            "report_hash_sha256": ""
        },
        "reliability": {
            "shadow_score": 83.0, "risk_level": "Low",
            "stage_classification": "Mid-Level", "consensus_status": "High Agreement",
            "components": {"github_score": 90, "email_score": 90, "identity_score": 78}
        },
        "identity": {
            "resume_name": "Arjun Mehta", "reference_handle": "arjun-mehta",
            "fuzzy_match_score": 84, "correspondence_level": "Strong",
            "matching_engine": "rapidfuzz"
        },
        "digital_activity": {
            "github_exists": True, "repo_count": 14,
            "account_created_year": 2019, "last_commit_days_ago": 5,
            "top_language": "Python", "account_age_years": 6,
            "activity_trust_level": "Highly Trusted"
        },
        "email_integrity": {
            "email": "arjun.mehta@infosys.com", "domain": "infosys.com",
            "is_disposable": False, "domain_reputation": "Corporate Domain",
            "hunter_score": 92, "ipqs_fraud_score": 4
        },
        "anomalies": {"anomaly_probability": 0, "flags": [], "flag_count": 0},
        "honest_narrative": (
            "Candidate demonstrates strong reliability signals across identity, email, and digital "
            "activity layers. GitHub activity (14 repos, last commit 5d ago) corroborates technical "
            "engagement. Email domain (corporate) adds institutional credibility. "
            "No structural anomalies detected. Hiring risk assessed as Low."
        )
    }
    demo_report["meta"]["report_hash_sha256"] = hashlib.sha256(
        json.dumps(demo_report, sort_keys=True).encode()
    ).hexdigest()
    return jsonify({"success": True, "data": demo_report, "meta": demo_report["meta"]})


# ── Web Cam Live Interaction Routes ──────────────────────────────────────

@app.route('/interview/<candidate_hash>')
def interview(candidate_hash):
    return render_template('interview.html', candidate_hash=candidate_hash)

@app.route('/start_session', methods=['POST'])
def start_session():
    data = request.json
    candidate_hash = data.get('candidate_hash', str(uuid.uuid4()))
    active_sessions[candidate_hash] = InterviewEngine(candidate_hash)
    return jsonify({"status": "success", "candidate_hash": candidate_hash})

@app.route('/process_frame', methods=['POST'])
def process_frame():
    data = request.json
    candidate_hash = data.get('candidate_hash')
    image_b64 = data.get('image')
    engine = active_sessions.get(candidate_hash)
    if not engine or not image_b64:
        return jsonify({"error": "Invalid session or missing image"}), 400
    metrics = engine.process_frame(image_b64)
    return jsonify(metrics)

@app.route('/cheating_event', methods=['POST'])
def cheating_event():
    data = request.json
    candidate_hash = data.get('candidate_hash')
    event_type = data.get('event_type')
    engine = active_sessions.get(candidate_hash)
    if not engine or not event_type:
        return jsonify({"error": "Invalid session or missing event"}), 400
    engine.log_cheating_event(event_type)
    return jsonify({"status": "logged"})

@app.route('/load_questions/', defaults={'pattern': ''}, methods=['GET'])
@app.route('/load_questions/<pattern>', methods=['GET'])
def load_questions_api(pattern):
    import glob
    q_dir = os.path.join(app.root_path, 'web cam', 'questions')
    if not os.path.exists(q_dir):
        q_dir = os.path.join(app.root_path, 'questions') # Fallback if merged
    files = glob.glob(os.path.join(q_dir, f"*{pattern}*.json"))
    questions = []
    for f in files:
        try:
            with open(f, 'r') as q_file:
                questions.append(json.load(q_file))
        except Exception as e:
            print(f"Error loading {f}: {e}")
    questions.sort(key=lambda item: item.get("id", ""))
    return jsonify(questions)

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.json
    candidate_hash = data.get('candidate_hash')
    question = data.get('question')
    answer = data.get('answer')
    engine = active_sessions.get(candidate_hash)
    if not engine:
        return jsonify({"error": "Invalid session"}), 400
    metrics = engine.get_current_metrics()
    from answer_evaluator import AnswerEvaluator
    evaluator = AnswerEvaluator()
    eval_result = evaluator.evaluate(question, answer, metrics)
    engine.log_evaluated_answer({
        "question": question,
        "answer": answer,
        "evaluation": eval_result
    })
    return jsonify(eval_result)

@app.route('/get_metrics', methods=['GET'])
def get_metrics():
    candidate_hash = request.args.get('candidate_hash')
    engine = active_sessions.get(candidate_hash)
    if not engine:
        return jsonify({"error": "Invalid session"}), 400
    return jsonify(engine.get_current_metrics())

@app.route('/end_session', methods=['POST'])
def end_session_api():
    data = request.json
    candidate_hash = data.get('candidate_hash')
    engine = active_sessions.get(candidate_hash)
    if not engine:
        return jsonify({"error": "Invalid session"}), 400
    summary = engine.finalize_session()
    save_session(candidate_hash, summary)
    if candidate_hash in active_sessions:
        del active_sessions[candidate_hash]
    return jsonify({"status": "success", "summary": summary})

@app.route('/session_summary/<candidate_hash>')
def session_summary_view(candidate_hash):
    summary = load_session(candidate_hash)
    if not summary:
        return "Session not found", 404
    return render_template('session_complete.html', summary=summary, candidate_hash=candidate_hash)

@app.route("/save_interview_results", methods=["POST"])
def save_interview_results():
    payload = request.json
    candidate_hash = payload.get("candidate_hash")
    results = payload.get("interview_results", {})

    import candidate_db as db
    candidate = db.get_candidate_by_hash(candidate_hash)
    if not candidate:
        return jsonify({"error": "Not Found"}), 404

    # Map engine metrics to user's requested schema
    live_integrity = results.get("integrity_index", 50.0)
    speech_score = results.get("answer_quality", 50.0)
    # Fraud Risk scaled based on anomaly points logic inside engine
    fraud_risk = min(100, results.get("anomaly_points", 0) * 5)
    
    anomalies_list = results.get("cheating_flags", [])
    anomalies_count = len(anomalies_list) if isinstance(anomalies_list, list) else results.get("anomaly_points", 0)

    mapped_results = {
        "integrity_score": live_integrity,
        "fraud_risk": fraud_risk,
        "speech_score": speech_score,
        "anomalies": anomalies_count,
        "raw_engine_data": results
    }

    forensic = candidate.get("forensic_payload", {})
    forensic["connect_results"] = mapped_results
    forensic["connect_timestamp"] = datetime.now().isoformat()

    scores = forensic.get("scores", {})
    resume_reliability = scores.get("reliability", 50.0)

    # 50% resume_reliability + 30% live_integrity + 20% speech_reliability
    final_combined_score = (0.5 * resume_reliability) + (0.3 * live_integrity) + (0.2 * speech_score)

    try:
        from ai_consensus_engine import generate_live_forensic_narrative
        # Pass resume text if available, or empty string
        resume_text = candidate.get("forensic_payload", {}).get("resume_text", "")
        synthesis = generate_live_forensic_narrative(resume_text=resume_text)
    except Exception:
        synthesis = {
            "resume_reliability": resume_reliability,
            "behavioral_integrity": live_integrity,
            "fraud_risk": fraud_risk,
            "hiring_recommendation": "Hire" if final_combined_score >= 70 else ("Review" if final_combined_score >= 40 else "Reject")
        }

    forensic["final_synthesis"] = synthesis
    
    candidate["final_score"] = round(final_combined_score, 2)
    candidate["forensic_payload"] = forensic
    
    db.update_candidate(candidate)

    return jsonify({"status": "saved"})


if __name__ == '__main__':
    log.info("Starting The Honest Recruiter on port 5000")
    app.run(host='0.0.0.0', debug=True, port=5000, use_reloader=False)
