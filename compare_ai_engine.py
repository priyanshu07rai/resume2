import json
import os
import re
from api_resilience import call_ai_with_schema

def generate_grok_analysis(groq_client, log, comparison_data: dict) -> dict:
    """Model A (Groq/Grok) - Forensic Analyst Role"""
    if not groq_client: return {}

    system = "You are a Forensic Hiring Intelligence Analyst. Return ONLY JSON."
    prompt = f"""
INPUT FORMAT
{json.dumps(comparison_data, indent=2)}

TASK: Produce a structured comparative analysis.
Focus on: Reliability difference, Fraud risk difference, Skill depth.

Rules:
- Be objective and decisive.
- End with a clear recommendation (Candidate A or Candidate B).

Exact JSON schema required:
{{
  "analysis_points": ["bullet 1", "bullet 2", "bullet 3"],
  "recommendation": "Candidate A"
}}
"""
    try:
        return call_ai_with_schema(
            system_prompt=system,
            user_prompt=prompt,
            schema_keys=["analysis_points", "recommendation"],
            groq_client=groq_client,
            groq_model="llama-3.3-70b-versatile",
            timeout_sec=15.0,
            max_retries=2
        )
    except Exception as e:
        log.error("Groq comparative error: %s", e)
        return {}

def generate_gemini_analysis(log, comparison_data: dict) -> dict:
    """Model B (Gemini API) - Conservative Recruiter Role"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: return {}
        
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        
        system = "You are a Senior Technical Recruiter performing risk assessment. Return ONLY JSON."
        prompt = f"""
INPUT:
{json.dumps(comparison_data, indent=2)}

TASK: Identify strengths, weaknesses, and hiring risk.
Rules:
- Be conservative. Highlight hidden risk signals.
- Pick a winner.

Exact JSON schema required:
{{
  "analysis_points": ["bullet 1", "bullet 2", "bullet 3"],
  "recommendation": "Candidate B"
}}
"""
        return call_ai_with_schema(
            system_prompt=system,
            user_prompt=prompt,
            schema_keys=["analysis_points", "recommendation"],
            gemini_client=client,
            timeout_sec=15.0
        )
    except Exception as e:
        log.error("Gemini comparative error: %s", e)
        return {}

def extract_verdict(ai_result: dict) -> str:
    """Extracts whether Candidate A or B won from structured JSON."""
    if not ai_result: return "Unclear"
    rec = str(ai_result.get("recommendation", "")).upper()
    if "CANDIDATE A" in rec or rec == "A": return "A"
    if "CANDIDATE B" in rec or rec == "B": return "B"
    return "Unclear"

def synthesize_final_decision(groq_client, log, data, result_a, result_b, final_verdict) -> list:
    """Synthesizes the final output bullet points via structured JSON."""
    if not groq_client: return ["Analysis failed."]
    
    system = "You are a Hiring Decision Synthesizer. Return ONLY JSON."
    prompt = f"""
Produce a final clean forensic hiring decision report.

Metrics:
{json.dumps(data.get('comparison_metrics', {}), indent=2)}

Analysis 1 (Groq Forensic):
{json.dumps(result_a.get('analysis_points', []), indent=2)}

Analysis 2 (Gemini Recruiter):
{json.dumps(result_b.get('analysis_points', []), indent=2)}

Final Computed Winner: Candidate {final_verdict}

Requirements:
- 5–7 bullet points
- Clear winner stated
- Clear risk summary
- Professional tone
- No mention of "AI model A/B" or internal mechanics.

Exact JSON schema required:
{{
  "final_bullets": ["bullet 1", "bullet 2", "bullet 3"]
}}
"""
    try:
        res = call_ai_with_schema(
            system_prompt=system,
            user_prompt=prompt,
            schema_keys=["final_bullets"],
            groq_client=groq_client,
            groq_model="llama-3.3-70b-versatile",
            timeout_sec=15.0,
            max_retries=2
        )
        bullets = res.get("final_bullets", [])
        if not bullets: return ["Synthesis parsed but empty."]
        return bullets
    except Exception as e:
        log.error("Synthesis error: %s", e)
        return ["Synthesis failure."]

def run_consensus_comparison(groq_client, safe_groq_call, log, comparison_data: dict):
    """Orchestrates the multi-model consensus layer using structured JSON."""
    
    log.info("Starting AI Consensus Protocol...")
    result_a = generate_grok_analysis(groq_client, log, comparison_data)
    result_b = generate_gemini_analysis(log, comparison_data)
    
    verdict_a = extract_verdict(result_a)
    verdict_b = extract_verdict(result_b)
    
    log.info(f"Model A Verdict: {verdict_a} | Model B Verdict: {verdict_b}")
    
    # 3. Compute Consensus
    if verdict_a != "Unclear" and verdict_a == verdict_b:
        final_verdict = verdict_a
        confidence = 90
    else:
        # Fallback to deterministic reliability
        metrics = comparison_data.get('comparison_metrics', {})
        rel_diff = metrics.get('reliability_diff', 0)
        final_verdict = "A" if rel_diff > 0 else "B"
        confidence = 65
        
    log.info(f"Final Consensus: Candidate {final_verdict} (Confidence: {confidence}%)")
        
    # 4. Synthesize Final Report
    bullets = synthesize_final_decision(groq_client, log, comparison_data, result_a, result_b, final_verdict)
    
    return {
        "final_bullets": bullets,
        "confidence": confidence,
        "verdict_a": verdict_a,
        "verdict_b": verdict_b,
        "final_verdict": final_verdict
    }
