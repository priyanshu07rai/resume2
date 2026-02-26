import os
import json
import time
import logging
import threading
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# ── Groq Client ────────────────────────────────────────────────────────────────
groq_api_key = os.getenv("GROQ_API_KEY")
groq_client  = Groq(api_key=groq_api_key) if groq_api_key else None
groq_lock    = threading.Lock()

# ── Gemini Client (used as Groq fallback) ──────────────────────────────────────
gemini_client = None
try:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if gemini_api_key:
        try:
            import google.genai as genai
            gemini_client = genai.Client(api_key=gemini_api_key)
        except ImportError:
            import google.generativeai as genai2
            genai2.configure(api_key=gemini_api_key)
            gemini_client = genai2.GenerativeModel("gemini-1.5-flash")
except Exception as _ge:
    pass  # Gemini is optional fallback

log = logging.getLogger("HonestRecruiter.AI")
CURRENT_YEAR = datetime.now().year

# ── Enterprise Resilience Layer ───────────────────────────────────────────────────
from api_resilience import (
    call_ai_with_schema,
    safe_groq_call,        # hardened: backoff + jitter + timeout + repair
    trim_input,
    build_compact_prompt,
)


def get_ai_consensus(text, task_type="full_audit", domain_hint="General"):
    """
    Industrial-Grade Groq Forensic Engine.
    Executes deep forensic analysis using Llama-3.3-70b.
    """
    if not groq_client:
        return {
            "consensus_score": 0,
            "disagreement_points": ["Critical: Groq API key missing."],
            "unified_data": {},
            "models_used": []
        }

    # Execute Forensic Audit
    result = call_groq_audit(text, task_type, domain_hint)
    
    if not result:
        return {
            "consensus_score": 0,
            "disagreement_points": ["Critical: Groq Audit failed."],
            "unified_data": {},
            "models_used": []
        }

    return {
        "consensus_score": result.get("confidence_score", 70),
        "disagreement_points": [],
        "disagreements": [],
        "unified_data": result,
        "data": result,
        "models_used": ["groq-llama-3.3-70b"]
    }

def call_groq_audit(text, task_type, domain_hint):
    """Executes high-speed forensic audit via Groq Cloud using Llama-3.3-70b.
    Implements Two-Pass Method for self-critique.
    """
    
    # PASS 1: Extract structured reasoning.
    prompt_pass1 = f"""
    [TASK: FORENSIC_RESUME_INTELLIGENCE_AUDIT]
    Domain Context: {domain_hint}
    
    You are a forensic analytical engine.
    You do not produce HR-style summaries.
    You do not produce motivational language.
    You do not invent scores.
    You do not generalize.

    You produce:
    Evidence-bound reasoning
    Contradiction detection
    Explicit data comparisons
    Practical hiring insight
    Every statement must trace back to input evidence.

    BEHAVIORAL RULES
    Never use abstract phrases like:
    "Calibrated expectations"
    "Dynamic system confidence"
    "Profile appears balanced"
    "Holistic evaluation"

    Always cite evidence explicitly:
    Instead of:
    "Limited digital footprint"
    Say:
    "GitHub account created in 2024 with 2 repositories and no commits in last 90 days."

    If a skill is claimed, check:
    Is it mentioned in experience text?
    Is it supported by digital footprint?
    If not supported -> say:
    "Skill declared but not demonstrated in resume text or digital activity."

    If data is insufficient:
    Say:
    "Insufficient evidence to validate claim."

    Never assume fraud without contradiction.

    🔥 FORCE RIGOR MODE 
    If contradictions exist: You must explicitly describe the contradiction and list the conflicting data points.
    Example:
    Claimed 12 years ML leadership.
    GitHub account created 2025 with 2 HTML repositories.
    No ML repositories detected.
    High inflation signal.

    Target Data (JSON ONLY - Strict Format Required):
    {{
      "identity": {{ "full_name": "EXTRACT EXACT NAME FROM TOP OF RESUME", "email": "...", "phone": "...", "location": "..." }},
      "skills": ["skill1", "skill2"],
      "experience": [{{ "role": "...", "company": "...", "years_active": "...", "key_achievement_metric": "..." }}],
      "education": [{{ "degree": "...", "institution": "...", "year": "..." }}],
      "certifications": ["cert1"],
      "forensic_reasoning": {{
          "IDENTITY ANALYSIS": {{
              "Name consistency": "...",
              "Account age vs experience": "...",
              "Timeline anomalies": "..."
          }},
          "SKILL VERIFICATION": {{
              "Skills declared": "...",
              "Skills demonstrated in experience": "...",
              "Skills demonstrated digitally": "...",
              "Evidence gaps": "..."
          }},
          "DIGITAL FOOTPRINT": {{
              "Repo count": "...",
              "Account age": "...",
              "Activity recency": "...",
              "Language alignment": "..."
          }},
          "ROLE ALIGNMENT": {{
              "Critical required skills missing": "...",
              "Over/Under qualification indicators": "..."
          }},
          "RISK ANALYSIS": {{
              "Inflation risk": "...",
              "Fabrication risk": "...",
              "Capability uncertainty": "..."
          }},
          "BOTTOM LINE": "2 sentences max. Concrete. No fluff."
      }},
      "confidence_score": 0
    }}

    FEW-SHOT EXAMPLES:
    Example 1 (Clean Profile):
    "forensic_reasoning": {{
        "IDENTITY ANALYSIS": {{ "Name consistency": "Name matches across all provided links.", "Account age vs experience": "Github created 2018, 6 years experience.", "Timeline anomalies": "None detected." }},
        "SKILL VERIFICATION": {{ "Skills declared": "Python, React, AWS", "Skills demonstrated in experience": "Python and AWS frequently cited in role descriptions.", "Skills demonstrated digitally": "GitHub shows 15 Python repositories.", "Evidence gaps": "React is claimed but not found in experience or GitHub." }},
        "DIGITAL FOOTPRINT": {{ "Repo count": "42 repositories", "Account age": "6 years", "Activity recency": "Last commit 2 days ago", "Language alignment": "Matches declared skills (Python)" }},
        "ROLE ALIGNMENT": {{ "Critical required skills missing": "None", "Over/Under qualification indicators": "Appropriate level for senior role." }},
        "RISK ANALYSIS": {{ "Inflation risk": "Low", "Fabrication risk": "Low", "Capability uncertainty": "React expertise unverified." }},
        "BOTTOM LINE": "Profile demonstrates strong evidence of claimed Python and AWS skills through active digital footprint and experience text. React capability remains unverified."
    }}

    Example 2 (Fraudulent Profile):
    "forensic_reasoning": {{
        "IDENTITY ANALYSIS": {{ "Name consistency": "Resume name differs from GitHub profile name.", "Account age vs experience": "Claimed 10 years experience; GitHub created 2 months ago.", "Timeline anomalies": "Overlap of 3 full-time roles in 2023." }},
        "SKILL VERIFICATION": {{ "Skills declared": "Machine Learning, Kubernetes, Go", "Skills demonstrated in experience": "None explicitly mentioned in job achievements.", "Skills demonstrated digitally": "Only basic HTML/CSS repos found.", "Evidence gaps": "No ML, Kubernetes, or Go evidence in text or code." }},
        "DIGITAL FOOTPRINT": {{ "Repo count": "2 repositories", "Account age": "2 months", "Activity recency": "No activity since creation", "Language alignment": "HTML/CSS only, contradicts ML claims" }},
        "ROLE ALIGNMENT": {{ "Critical required skills missing": "No evidence of core ML/Go requirements.", "Over/Under qualification indicators": "Claims senior tech lead, evidence suggests entry-level." }},
        "RISK ANALYSIS": {{ "Inflation risk": "Critical. Claims unsupported by data.", "Fabrication risk": "High. Timeline overlaps and GitHub mismatch.", "Capability uncertainty": "High. No verification of any technical claim." }},
        "BOTTOM LINE": "High risk of fabrication given contradiction between 10-year ML claim and 2-month-old HTML GitHub account. Severe timeline anomalies detected."
    }}

    Source Text:
    ---
    {text[:30000]}
    ---
    """
    
    try:
        completion1 = safe_groq_call(
            groq_client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a Forensic Analytical Engine: Hard Logic Variant. Return JSON ONLY."},
                {"role": "user", "content": prompt_pass1}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        if not completion1: return None
        pass1_result = json.loads(completion1.choices[0].message.content)
        
        # Optimization: Only run Pass 2 (self-critique) for full_audit tasks.
        # This saves one API round-trip for all other task types.
        if task_type != "full_audit":
            return pass1_result

        # Format the reasoning for Pass 2 context
        reasoning_str = json.dumps(pass1_result.get("forensic_reasoning", {}), indent=2)
        
        # PASS 2: Self-Critique
        prompt_pass2 = f"""
        [TASK: SELF-CRITIQUE FORENSIC REASONING]
        
        Source Text:
        ---
        {text[:30000]}
        ---
        
        Pass 1 Forensic Reasoning:
        {reasoning_str}
        
        Identify weak assumptions or unsupported conclusions in the Pass 1 reasoning. 
        Update the JSON object to fix any flaws. Ensure the final output is robust, evidence-backed, and adheres strictly to the rigid forensic format provided in Pass 1.
        
        Return the FULL updated JSON, containing all the original fields (identity, skills, experience, education, certifications, forensic_reasoning, confidence_score), with the forensic_reasoning revised for maximum hard logic.
        """
        
        completion2 = safe_groq_call(
            groq_client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a Forensic Analytical Engine: Hard Logic Variant. Return JSON ONLY."},
                {"role": "user", "content": prompt_pass2}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        if not completion2: return pass1_result # Fallback to pass 1 if pass 2 fails
        final_result = json.loads(completion2.choices[0].message.content)
        
        # Merge missing identities from Pass 1 back into Final Result (Prevent Data Loss)
        for key in ["identity", "skills", "experience", "education", "certifications", "confidence_score"]:
            if key not in final_result or not final_result[key]:
                if key in pass1_result:
                    final_result[key] = pass1_result[key]
        
        # Reconstruct the requested EXACT text format into the forensic_narrative field
        reasoning = final_result.get("forensic_reasoning", {})
        narrative_parts = []
        for section, content in reasoning.items():
            if isinstance(content, dict):
                narrative_parts.append(f"{section}:")
                for k, v in content.items():
                    narrative_parts.append(f"- {k}: {v}")
                narrative_parts.append("")
            else:
                narrative_parts.append(f"{section}:")
                narrative_parts.append(f"{content}")
                narrative_parts.append("")
                
        final_result["forensic_narrative"] = "\n".join(narrative_parts).strip()
            
        return final_result
    except Exception as e:
        log.error("Groq Forensic Fault: %s", e)
        return None


def extract_skills_from_jd(job_description, target_role=""):
    """
    Fast extraction of required skills from a job description.
    Uses llama-3.1-8b-instant for speed (sub-2s typical).
    Returns a list of skill strings.
    """
    if not groq_client:
        log.warning("Groq not configured — JD skill extraction skipped.")
        return []

    role_hint = f" for the role of '{target_role}'" if target_role else ""
    prompt = f"""Extract the technical skills and requirements{role_hint} from the job description below.
Return ONLY a JSON array of skill strings. No prose, no keys, just the array.
Example: ["Python", "AWS", "Docker", "REST APIs", "PostgreSQL"]

Job Description:
---
{job_description[:4000]}
---
"""
    try:
        completion = safe_groq_call(
            groq_client.chat.completions.create,
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You extract skill lists from job descriptions. Return a JSON array of strings only."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=300
        )
        if not completion:
            return []
        raw = json.loads(completion.choices[0].message.content)
        # Handle both {"skills": [...]} and bare [...] responses
        if isinstance(raw, list):
            skills = raw
        else:
            # Try common wrapper keys
            for key in ["skills", "required_skills", "technical_skills", "requirements"]:
                if key in raw and isinstance(raw[key], list):
                    skills = raw[key]
                    break
            else:
                # Fallback: grab first list value found
                skills = next((v for v in raw.values() if isinstance(v, list)), [])
        result = [str(s).strip() for s in skills if s]
        log.info("JD skill extraction: %d skills found", len(result))
        return result
    except Exception as e:
        log.error("extract_skills_from_jd error: %s", e)
        return []


def generate_live_forensic_narrative(resume_text, github_data=None, entities=None, domain="General"):
    """
    Generates a rich, evidence-bound forensic narrative using Groq LLama-3.3-70b.
    Injects real GitHub API data directly into the prompt for concrete, accurate analysis.
    This is the AI that powers the 'LIVE FORENSIC NARRATIVE' section in the UI.
    """
    if not groq_client:
        return "Groq API key not configured. AI narrative unavailable."

    # ── Build GitHub Context Block ─────────────────────────────────────
    gh_block = "No GitHub profile linked or found."
    if github_data and github_data.get("exists"):
        m = github_data.get("metrics", {})
        p = github_data.get("profile", {})
        languages_str = ", ".join(f"{k}({v})" for k, v in dict(list(m.get("languages", {}).items())[:5]).items()) or "Unknown"
        topics_str    = ", ".join(m.get("pinned_repo_topics", [])[:8]) or "none"
        gh_block = f"""
GitHub Profile Verified:
- Handle: {p.get("handle", "unknown")}
- Created: {p.get("created_at", "unknown")} ({m.get("account_created_year", "?")})
- Public Repositories: {m.get("repo_count", 0)} ({m.get("forked_repo_count", 0)} forks)
- Stars Received: {m.get("starred_repo_count", 0)}
- Followers: {m.get("follower_count", 0)}
- Last Activity: {m.get("last_commit_days_ago", "unknown")} days ago
- Activity Score: {m.get("activity_score", 0)}/100
- Language Distribution: {languages_str}
- Repository Topics: {topics_str}
"""

    # ── Build Skills / Experience Summary ─────────────────────────────
    skills     = entities.get("skills", []) if entities else []
    experience = entities.get("experience", []) if entities else []
    name       = entities.get("identity", {}).get("name", "Unknown") if entities else "Unknown"
    email      = entities.get("identity", {}).get("email", "N/A") if entities else "N/A"

    skills_str = ", ".join(skills[:20]) if skills else "None declared"
    exp_str    = "; ".join(
        f"{e.get('role','?')} @ {e.get('company','?')} ({e.get('years_active','?')})"
        for e in experience[:5]
    ) if experience else "No structured work history"

    prompt = f"""
[TASK: LIVE_FORENSIC_NARRATIVE_GENERATION]

You are The Honest Recruiter's AI Forensic Analyst.
Your task: produce ONE continuous, evidence-bound forensic narrative paragraph (250-400 words).

RULES:
- Cite every claim from data provided below.
- Never invent data, Never use vague language.
- Cross-reference resume claims vs GitHub activity explicitly.
- Flag contradictions or gaps with precise data references.
- Do NOT use bullet points. Write as flowing analytical prose.
- Start directly with the analysis. No preamble.

CANDIDATE DATA:
Name: {name}
Email: {email}
Domain: {domain}
Skills Declared: {skills_str}
Work History: {exp_str}

GITHUB INTELLIGENCE:
{gh_block}

RESUME TEXT (first 8000 chars):
---
{resume_text[:8000]}
---

Produce the forensic narrative now. Evidence-first. No filler. No HR language.
"""

    try:
        completion = safe_groq_call(
            groq_client.chat.completions.create,
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a forensic analytical engine. Output ONLY the narrative prose paragraph. No JSON. No preamble."},
                {"role": "user",   "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        if not completion:
            return "AI narrative generation failed — Groq API unavailable. Showing local analysis only."

        narrative = completion.choices[0].message.content.strip()
        log.info("Live forensic narrative generated (%d chars)", len(narrative))
        return narrative

    except Exception as e:
        log.error("generate_live_forensic_narrative error: %s", e)
        return f"AI narrative unavailable: {str(e)}"


def generate_github_deep_analysis(github_data, entities=None, resume_skills=None):
    """
    Sends the candidate's full GitHub profile (repos, languages, commits, bio)
    to Groq for a structured forensic deep-dive analysis.
    Returns structured JSON used by the 'View Detailed Forensic AI Analysis' section.
    """
    if not groq_client:
        return {"error": "Groq API key not configured", "available": False}

    if not github_data or not github_data.get("exists"):
        return {"error": "No GitHub profile linked", "available": False}

    m       = github_data.get("metrics", {})
    p       = github_data.get("profile", {})
    repos   = github_data.get("repo_inventory", [])
    commits = github_data.get("recent_commits", [])
    skills  = resume_skills or (entities.get("skills", []) if entities else [])

    # Build repo summary for Groq
    repo_lines = []
    for r in repos[:15]:
        line = (f"  - {r['name']} [{r['language']}]"
                f" | Stars:{r['stars']} Forks:{r['forks']}"
                f" | Fork:{r['is_fork']} | README:{r['has_readme']}"
                f" | Topics:{','.join(r['topics'][:5]) or 'none'}"
                f" | Desc: {r['description'][:80] or 'no description'}")
        repo_lines.append(line)

    lang_str    = ", ".join(f"{k}:{v}" for k, v in list(m.get("languages", {}).items())[:8])
    topics_str  = ", ".join(m.get("pinned_repo_topics", [])[:10]) or "none"
    commits_str = "\n".join(f"  - {c}" for c in commits[:10]) or "  No recent commits found"
    skills_str  = ", ".join(skills[:20]) or "Not declared"

    prompt = f"""
[TASK: GITHUB_DEEP_FORENSIC_ANALYSIS]

You are a senior engineering recruiter and code forensic analyst.
Analyze the following GitHub profile data and produce a STRUCTURED JSON forensic report.

CANDIDATE GITHUB PROFILE:
- Handle: {p.get('handle')}
- Account Created: {p.get('created_at', 'unknown')} (Age: {m.get('account_created_year', '?')})
- Public Repos: {m.get('repo_count', 0)} ({m.get('forked_repo_count', 0)} forks)
- Followers: {m.get('follower_count', 0)} | Following: {p.get('following', 0)}
- Stars Received Total: {m.get('starred_repo_count', 0)}
- Bio: {p.get('bio') or 'Not set'}
- Company: {p.get('company') or 'Not listed'}
- Location: {p.get('location') or 'Not listed'}
- Last Activity: {m.get('last_commit_days_ago', 'unknown')} days ago
- Activity Score: {m.get('activity_score', 0)}/100
- Language Distribution: {lang_str}
- Repository Topics: {topics_str}

REPOSITORY INVENTORY (top {len(repos[:15])} repos):
{chr(10).join(repo_lines) if repo_lines else 'No repositories found'}

RECENT COMMIT MESSAGES:
{commits_str}

RESUME DECLARED SKILLS (for cross-reference):
{skills_str}

ANALYSIS INSTRUCTIONS:
1. Cross-reference declared skills vs GitHub languages and repo content
2. Assess project quality (READMEs, descriptions, star counts, original vs fork ratio)
3. Evaluate commit consistency and recency
4. Identify technical strengths and gaps
5. Produce RED FLAGS (concrete contradictions/concerns) and GREEN FLAGS (verified evidence)
6. Give a final hiring recommendation from GitHub evidence alone

Return VALID JSON ONLY, no prose outside JSON:
{{
  "technical_stack_assessment": {{
    "verified_languages": ["..."],
    "verified_from_github": "paragraph describing what is confirmed",
    "declared_but_unverified": ["skills from resume not seen in github"],
    "github_exclusive_skills": ["skills evident in github but not in resume"]
  }},
  "project_quality": {{
    "original_repos": 0,
    "forked_repos": 0,
    "documented_repos": 0,
    "average_star_rating": 0.0,
    "quality_verdict": "Strong/Moderate/Weak",
    "quality_notes": "explanation"
  }},
  "activity_assessment": {{
    "last_activity_days": 0,
    "activity_score": 0,
    "consistency_verdict": "Active/Sporadic/Dormant",
    "consistency_notes": "explanation"
  }},
  "red_flags": [
    {{"flag": "exact description", "severity": "High/Moderate/Low"}}
  ],
  "green_flags": [
    {{"evidence": "exact description", "strength": "Strong/Moderate"}}
  ],
  "github_hiring_recommendation": {{
    "verdict": "Strong Candidate/Verify Further/High Risk",
    "reason": "2-3 sentence evidence-based summary",
    "interview_questions": ["specific question based on evidence", "..."]
  }}
}}
"""

    try:
        completion = safe_groq_call(
            groq_client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a forensic code analyst. Output VALID JSON ONLY. No text outside JSON."},
                {"role": "user",   "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=1500
        )
        if not completion:
            return {"error": "Groq unavailable", "available": False}

        result = json.loads(completion.choices[0].message.content)
        result["available"] = True
        result["handle"]    = p.get("handle")
        result["profile_url"] = p.get("html_url", f"https://github.com/{p.get('handle','')}")
        log.info("GitHub deep analysis complete for %s", p.get("handle"))
        return result

    except Exception as e:
        log.error("generate_github_deep_analysis error: %s", e)
        return {"error": str(e), "available": False}


# ══════════════════════════════════════════════════════════════════════════════
# STRUCTURED FORENSIC AI ANALYSIS — Production Grade
# Forces adversarial forensic auditor behavior with strict JSON schema output.
# ══════════════════════════════════════════════════════════════════════════════

def generate_structured_forensic_analysis(
    resume_text: str,
    entities: dict,
    verification: dict,
    fraud_probability: float,
    trust_score: float,
    domain_hint: str = "General",
    target_role: str = "",
    ml_composite: dict = None,      # ← NEW: pre-computed ML evidence
) -> dict:
    """
    Calls Groq (Llama-3.3-70b) with a strict forensic auditor persona.
    Injects ML-computed signals as pre-context so the model reasons from
    structured evidence, not just from raw text.

    Returns the JSON dict on success, or a deterministic fallback on failure.
    """
    if not groq_client:
        log.warning("generate_structured_forensic_analysis: Groq client not available.")
        return _deterministic_forensic_fallback(fraud_probability, trust_score)

    # ── Build structured input for the model ─────────────────────────────────
    identity     = entities.get("identity", {})
    skills_list  = entities.get("skills", [])
    github_data  = verification.get("api_signals", {}).get("github", {})
    email_trust  = verification.get("email_trust", {}).get("ipqs", {})

    gh_metrics   = github_data.get("metrics", {})
    gh_repos     = gh_metrics.get("repo_count", 0)
    gh_created   = gh_metrics.get("account_created_year", 0)
    gh_language  = gh_metrics.get("top_language", "Unknown")
    gh_last_days = gh_metrics.get("last_commit_days_ago", 999)
    claimed_exp  = identity.get("experience_years", 0)

    # Pre-compute deterministic contradiction flag
    current_year = CURRENT_YEAR if 'CURRENT_YEAR' in dir() else 2025
    timeline_conflict = ""
    if gh_created and claimed_exp:
        account_age = current_year - gh_created
        if claimed_exp > account_age + 1:
            timeline_conflict = (
                f"TIMELINE MISMATCH: Candidate claims {claimed_exp} years experience, "
                f"but GitHub account only {account_age} years old."
            )

    # ML composite block — gives AI quantitative pre-context
    ml_block = {}
    if ml_composite:
        ml_block = {
            "ml_fraud_probability":  ml_composite.get("fraud_probability"),
            "ml_reliability_index":  ml_composite.get("reliability_index"),
            "ml_evidence_quality":   ml_composite.get("evidence_quality"),
            "ml_risk_label":         ml_composite.get("risk_label"),
            "ml_flags":              ml_composite.get("ml_flags", []),   # specific ML-detected flags
            "ml_feature_snapshot":   ml_composite.get("feature_snapshot", {}),
        }

    input_data = {
        "resume_text_excerpt": resume_text[:7000],
        "target_role": target_role or "Not specified",
        "claimed_years_experience": claimed_exp,
        "skills": skills_list[:30],
        "github_data": {
            "repo_count": gh_repos,
            "top_language": gh_language,
            "account_created_year": gh_created,
            "last_commit_days_ago": gh_last_days,
        },
        "email_domain_type": email_trust.get("domain_type", "unknown"),
        "model_scores": {
            "fraud_probability": round(fraud_probability, 1),
            "reliability_score": round(trust_score, 1),
        },
        "deterministic_flags": [f for f in [timeline_conflict] if f],
        "pre_computed_ml_signals": ml_block,    # ← ML evidence injected here
    }

    system_prompt = """You are a Forensic Resume Intelligence Engine.

You receive candidate data including PRE-COMPUTED ML SIGNALS that you MUST incorporate into your reasoning.
The `pre_computed_ml_signals` field contains quantified scores from a trained fraud detection model — treat these as hard evidence.

Your job:
- Cross-validate ML predictions against the raw resume evidence
- Detect contradictions between claims and signals
- Quantify credibility dimensions
- Identify specific inflation risk indicators
- Map out clear verification signals (positive and negative) with exact sources

STRICT RULES:
- Incorporate `ml_fraud_probability`, `ml_reliability_index`, and `ml_flags` EXPLICITLY in your reasoning.
- Every observation must cite specific data: dates, counts, scores, or skill names.
- Avoid HR language. Think like a financial auditor, not a recruiter.
- If ML signals diverge from the resume narrative, call it out explicitly.
- NEVER use the word "Unknown" for any rating or verdict. If data is missing, make a best-effort forensic judgment based on available ML signals.

Return ONLY valid JSON with this EXACT schema. No text outside JSON:

{
  "verdict_lines": [
    "string: specific ML prediction narrative line 1 (e.g., Profile classified as Fresher...)",
    "string: narrative line 2 based on evidence..."
  ],
  "digital_maturity": {
    "rating": "Adequate | Weak | Strong",
    "verified_platform_signals": "number: count of external links/repos"
  },
  "internal_coherence": {
    "rating": "High Coherence | Moderate Coherence | Low Coherence",
    "score": "number 0-100"
  },
  "verification_signals": [
    {
      "signal": "string: short description of what was found",
      "source": "string: GitHub | metadata | model inference | resume",
      "impact": "Positive | Negative",
      "severity": "Low | Moderate | High"
    }
  ],
  "summary_snapshot": {
    "overall_risk_level": "Low | Moderate | High",
    "capability_certainty": "Low | Moderate | High",
    "digital_depth_rating": "Weak | Adequate | Strong",
    "recommended_action": "string: e.g. Technical Interview Required"
  },
  "full_verdict": "string: a long cohesive paragraph detailing the complete forensic analysis of the digital footprint and timeline"
}"""

    # Token-trim input_data so we never exceed context window
    # Resume text is already capped above; trim embedded structured fields
    input_trimmed = trim_input(input_data, max_chars=400)
    # Cap resume excerpt separately (most signal-dense first N chars)
    input_trimmed["resume_text_excerpt"] = resume_text[:3500]
    # Cap skills to 20
    input_trimmed["skills"] = skills_list[:20]

    user_prompt = (
        f"Perform a full forensic audit on this candidate.\n"
        f"The `pre_computed_ml_signals` block contains quantified ML evidence — treat it as hard data.\n\n"
        f"{json.dumps(input_trimmed, ensure_ascii=False, indent=2)}"
    )

    SCHEMA_KEYS = [
        "verdict_lines",
        "digital_maturity",
        "internal_coherence",
        "verification_signals",
        "summary_snapshot",
        "full_verdict",
    ]

    result = call_ai_with_schema(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema_keys=SCHEMA_KEYS,
        groq_client=groq_client,
        groq_model="llama-3.3-70b-versatile",
        gemini_client=gemini_client,
        deterministic_fn=lambda: _deterministic_forensic_fallback(fraud_probability, trust_score),
        timeout_sec=28.0,
        max_retries=3,
        temperature=0.05,
        max_tokens=2000,
    )

    if result:
        status = result.get("ai_status", "groq_primary")
        overall_risk = result.get("summary_snapshot", {}).get("overall_risk_level", "?")
        log.info("Forensic analysis complete via [%s]. Overall Risk: %s", status, overall_risk)
    return result


def _deterministic_forensic_fallback(fraud_probability: float, trust_score: float) -> dict:
    """Pure-deterministic fallback — no AI, no external calls, always succeeds."""
    if fraud_probability < 25:
        risk = "Low"
    elif fraud_probability < 55:
        risk = "Moderate"
    else:
        risk = "High"

    # Heuristic ratings for UI instead of "Unknown"
    maturity_rating = "Adequate" if trust_score > 65 else ("Weak" if trust_score < 40 else "Moderate")
    coherence_rating = "High Coherence" if trust_score > 75 else ("Low Coherence" if trust_score < 30 else "Moderate Coherence")
    
    return {
        "verdict_lines": [
            f"Deterministic fallback activated.",
            f"Calculated fraud probability: {fraud_probability}% | Trust Score: {trust_score}%",
            f"AI engines (Groq/Gemini) currently rate-limited; showing deterministic ML scan results."
        ],
        "digital_maturity": {
            "rating": maturity_rating,
            "verified_platform_signals": 0
        },
        "internal_coherence": {
            "rating": coherence_rating,
            "score": round(trust_score)
        },
        "verification_signals": [
            {
                "signal": f"Base reliability score computed mathematically as {round(trust_score)}%",
                "source": "deterministic_engine",
                "impact": "Positive" if trust_score > 60 else "Negative",
                "severity": "Moderate"
            },
            {
                "signal": "AI Deep-Dive skipped due to API rate limits",
                "source": "system_guard",
                "impact": "Negative",
                "severity": "Low"
            }
        ],
        "summary_snapshot": {
            "overall_risk_level": risk,
            "capability_certainty": "Moderate" if trust_score > 50 else "Low",
            "digital_depth_rating": maturity_rating,
            "recommended_action": "Technical Interview Required" if risk != "Low" else "Standard Screening"
        },
        "full_verdict": f"The AI analysis engine timed out or was unavailable due to API rate limits. This is a deterministic report based on numerical scoring. Trust Index is {round(trust_score)}% and Fraud Probability is {fraud_probability}%. Technical validation via live interaction is recommended to confirm these ML predictions.",
        "ai_status": "deterministic_fallback"
    }
