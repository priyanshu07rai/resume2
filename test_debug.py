import json
import logging
from ai_consensus_engine import generate_structured_forensic_analysis, _deterministic_forensic_fallback

logging.basicConfig(level=logging.INFO)

def test_forensic_fallback():
    print("--- Testing Deterministic Fallback ---")
    # Low Risk
    res_low = _deterministic_forensic_fallback(fraud_probability=10.0, trust_score=80.0)
    print(f"Low Risk Rating: {res_low['digital_maturity']['rating']} (Expected: Adequate/Strong)")
    print(f"Low Risk Coherence: {res_low['internal_coherence']['rating']} (Expected: High Coherence)")
    assert "Unknown" not in str(res_low)
    
    # High Risk
    res_high = _deterministic_forensic_fallback(fraud_probability=70.0, trust_score=20.0)
    print(f"High Risk Rating: {res_high['digital_maturity']['rating']} (Expected: Weak)")
    print(f"High Risk Coherence: {res_high['internal_coherence']['rating']} (Expected: Low Coherence)")
    assert "Unknown" not in str(res_high)
    print("Fallback test passed (No 'Unknown' values).")

def test_structured_analysis_mock():
    print("\n--- Testing Structured Analysis (Heurictics/Fallback) ---")
    # Simulate Groq failure by passing no client or inducing error (already handled by calling fallback if no client)
    # Since we are running in a script where groq_client might be None, it should trigger fallback
    entities = {"identity": {"experience_years": 5}, "skills": ["Python"]}
    verification = {"api_signals": {"github": {"metrics": {"repo_count": 10}}}}
    
    res = generate_structured_forensic_analysis(
        resume_text="Sample text",
        entities=entities,
        verification=verification,
        fraud_probability=30.0,
        trust_score=60.0
    )
    
    print("Result AI Status:", res.get("ai_status"))
    print("Digital Maturity Rating:", res.get("digital_maturity", {}).get("rating"))
    assert res.get("digital_maturity", {}).get("rating") != "Unknown"
    print("Structured analysis test passed.")

if __name__ == "__main__":
    test_forensic_fallback()
    test_structured_analysis_mock()
