import os
import json
from ai_consensus_engine import get_ai_consensus

DOMAIN_KEYWORDS = {
    "Software Engineering": ["python", "java", "software engineer", "developer", "aws", "git", "coding", "linux", "backend", "frontend", "fullstack", "react", "node", "typescript"],
    "Data / AI": ["machine learning", "data scientist", "pytorch", "tensorflow", "nlp", "pandas", "sql", "ai model", "deep learning", "data engineer", "analytics"],
    "Healthcare / Fitness": ["doctor", "nurse", "physiotherapist", "clinical", "fitness coach", "nutrition", "patient care", "hospital", "gym", "medical", "pharmacy"],
    "Business / Sales": ["accounting", "financial analyst", "marketing", "sales", "revenue", "manager", "business development", "startup", "equity", "lead generation", "operations", "hr"],
    "Marketing": ["seo", "content strategy", "brand", "social media", "growth", "advertising", "campaign", "digital marketing"],
    "Finance": ["investment", "banking", "treasury", "audit", "compliance", "portfolio", "trading", "fintech", "tax"]
}

def classify_domain(text):
    """
    Industrial Domain Classification Engine.
    Layer 1: Deterministic Keyword Scoring (High precision, low recall)
    Layer 2: Multi-AI Consensus (Gemini + OpenAI)
    Layer 3: Confidence-Based Arbitration
    """
    # Layer 1: Deterministic Keyword Analysis
    text_lower = text.lower()
    keyword_scores = {domain: 0 for domain in DOMAIN_KEYWORDS}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                keyword_scores[domain] += 1
    
    # Calculate top deterministic match
    total_keyword_hits = sum(keyword_scores.values())
    top_deterministic = max(keyword_scores, key=keyword_scores.get) if total_keyword_hits > 0 else "General"
    deterministic_confidence = min(0.9, total_keyword_hits / 10) if total_keyword_hits > 0 else 0

    # Layer 2: AI Consensus Pulse
    try:
        # get_ai_consensus will return unified data and models used
        consensus = get_ai_consensus(text, task_type="domain_classification")
        unified_data = consensus.get("unified_data", {})
        ai_domain = unified_data.get("domain", "General")
        
        # Layer 3: Arbitration Logic
        # If AI is confident (Consensus > 60), trust AI.
        # If AI fails or low confidence, trust deterministic if it has high hits.
        final_domain = ai_domain
        final_confidence = consensus.get("consensus_score", 50) / 100
        
        # Prevent UNKNOWN defaulting
        if final_domain.upper() in ["UNKNOWN", "OTHER", "GENERAL"] and deterministic_confidence > 0.3:
            final_domain = top_deterministic
            final_confidence = 0.6 # Moderate confidence in keyword match

        return {
            "domain": final_domain,
            "confidence": round(final_confidence, 2),
            "reasoning": f"Keyword Density: {top_deterministic} ({total_keyword_hits} hits). AI Consensus: {ai_domain}.",
            "consensus_score": consensus.get("consensus_score", 0),
            "models_used": consensus.get("models_used", []),
            "disagreement_points": consensus.get("disagreement_points", [])
        }
    except Exception as e:
        print(f"Domain Arbitration Fault: {e}")
        return {
            "domain": top_deterministic,
            "confidence": 0.4,
            "reasoning": f"Critical AI Fault. Falling back to Keyword Density: {top_deterministic}.",
            "consensus_score": 0,
            "models_used": []
        }
