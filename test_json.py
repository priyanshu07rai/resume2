import os
import json
from ai_consensus_engine import generate_structured_evaluation

structured_signals = {
    "predicted_domain": "Software Engineering",
    "confidence_score": "85%",
    "fraud_probability": "15%",
    "account_age": "5 years",
    "repo_count": 0,
    "fork_count": 0,
    "last_commit_days": "Unknown",
    "alignment_score": "Unknown%",
    "experience_years": "Unknown", 
    "evidence_strength": "Weak"
}

v4_reasoning = """AI FORENSIC ANALYSIS: The candidate's digital footprint begins with their identity... this account age is a crucial piece of information. However, with no experience listed in their resume data..."""

try:
    print("Sending prompt to Groq API...")
    result = generate_structured_evaluation(structured_signals, v4_reasoning)
    print("Result Type:", type(result))
    if isinstance(result, str):
        print("STRING RETURNED:")
        print(result)
    else:
        print("JSON PARSED CORRECTLY:")
        print(json.dumps(result, indent=2))
except Exception as e:
    print("ERROR:", e)
