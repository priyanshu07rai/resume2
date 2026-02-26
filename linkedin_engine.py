import re
import requests
import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

def extract_linkedin(text):
    """
    Deterministic LinkedIn URL extraction.
    Supports various formats and normalizes to canonical form.
    """
    # Pattern to find LinkedIn URLs
    pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/([a-zA-Z0-9-]+)/?'
    matches = re.findall(pattern, text)
    
    if not matches:
        return {"linkedin_url": "", "linkedin_slug": ""}
    
    slug = matches[0].rstrip('/.,')
    canonical_url = f"https://www.linkedin.com/in/{slug}"
    
    return {
        "linkedin_url": canonical_url,
        "linkedin_slug": slug
    }

def verify_linkedin_authenticity(url, resume_name):
    """
    Hybrid authenticity verification without direct scraping.
    Checks reachability, slug validity, and identity match.
    """
    if not url:
        return {"exists": False, "reachable": False, "slug_valid": False, "identity_match_score": 0}

    slug = url.split('/')[-1]
    
    # 1. Reachability Check (HEAD request)
    reachable = False
    try:
        response = requests.head(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        # LinkedIn returns 200, 999 (custom rate limit), or 403 (forbidden for bots)
        reachable = response.status_code in [200, 999, 403]
    except:
        reachable = False

    # 2. Slug Validity Check
    # Length > 3, no suspicious patterns (e.g., long numeric strings)
    slug_valid = len(slug) > 3
    is_suspicious = bool(re.search(r'\d{8,}', slug)) # 8+ consecutive digits is usually a default/lazy slug
    if is_suspicious:
        slug_valid = False

    # 3. Identity Match Score (0-10)
    identity_score = 0
    if resume_name and slug:
        clean_name = re.sub(r'[^a-zA-Z]', '', resume_name.lower())
        clean_slug = re.sub(r'[^a-zA-Z]', '', slug.lower())
        
        # Simple overlap check
        if clean_name in clean_slug or clean_slug in clean_name:
            identity_score = 10
        else:
            # Fuzzy match simulation: count matching chars or parts
            name_parts = set(re.findall(r'\w+', resume_name.lower()))
            slug_parts = set(re.findall(r'\w+', slug.lower()))
            overlap = name_parts & slug_parts
            identity_score = min(10, len(overlap) * 5)

    return {
        "exists": reachable,
        "reachable": reachable,
        "slug_valid": slug_valid,
        "identity_match_score": identity_score,
        "slug": slug
    }

def generate_career_summary(text):
    """
    AI Enrichment Layer: Generates 2-3 line professional summary.
    """
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Professional summary unavailable (API Key missing)."

        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        You are a professional career coach. 
        Based ONLY on the following resume text, generate a short 2-3 line professional summary.
        Rules:
        - Professional tone
        - 2-3 lines max
        - No exaggeration
        - Focus on key skills and experience level
        
        Resume:
        {text[:3000]}
        """

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )

        return response.text.strip() if response.text else "Summary could not be generated."
    except Exception as e:
        print(f"AI Summary Error: {e}")
        return "Summary generation failed."

def score_linkedin(auth_data, resume_data):
    """
    Calculates LinkedIn specific trust scores.
    """
    identity_match = auth_data.get("identity_match_score", 0) # 0-10
    profile_validity = 0
    if auth_data.get("reachable"): profile_validity += 3
    if auth_data.get("slug_valid"): profile_validity += 2
    
    # Career Consistency (0-10)
    # Penalize if slug is completely unrelated to candidate's name or domain
    consistency_score = 10
    if not auth_data.get("slug_valid"):
        consistency_score -= 5
    if auth_data.get("identity_match_score") < 5:
        consistency_score -= 3
        
    return {
        "identity_match_score": identity_match,
        "validity_score": profile_validity,
        "consistency_score": consistency_score,
        "total_extra": identity_match + profile_validity + consistency_score # Max 25
    }
