import os
import re
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

def extract_deterministic(text):
    """Primary layer: Extracts Email, GitHub, and LinkedIn using safe regex patterns."""
    results = {
        "name": None,
        "email": None,
        "github": None,
        "linkedin": None,
        "methods": {}
    }

    # 1. Email Regex (Production Safe)
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    emails = re.findall(email_pattern, text)
    if emails:
        results["email"] = emails[0]
        results["methods"]["email"] = "regex"

    # 2. GitHub URL Regex (Handles variants including missing https://)
    github_pattern = r'(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9-]+)'
    github_match = re.search(github_pattern, text, re.IGNORECASE)
    if github_match:
        # Construct clean URL
        results["github"] = "https://github.com/" + github_match.group(1).rstrip('/.,')
        results["methods"]["github"] = "regex"

    # 3. LinkedIn URL (Deterministic Engine)
    from linkedin_engine import extract_linkedin
    lh_res = extract_linkedin(text)
    if lh_res["linkedin_url"]:
        results["linkedin"] = lh_res["linkedin_url"]
        results["linkedin_slug"] = lh_res["linkedin_slug"]
        results["methods"]["linkedin"] = "regex"

    # 4. Heuristic Name Extraction
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    header_blacklist = {
        "RESUME", "CURRICULUM VITAE", "CONTACT", "EXPERIENCE", "EDUCATION", 
        "SUMMARY", "OBJECTIVE", "SKILLS", "PROJECTS", "CERTIFICATIONS", 
        "LANGUAGES", "INTERESTS", "ACHIEVEMENTS", "PROFILE", "WORK HISTORY",
        "TECHNICAL SKILLS", "PROFESSIONAL EXPERIENCE", "ADDITIONAL INFORMATION"
    }
    
    potential_name = None
    
    # PASS 1: The "Title Case" or "All Caps" name pattern in Top 10 lines
    for line in lines[:10]:
        clean_upper = line.upper()
        # Skip blacklisted headers
        if clean_upper in header_blacklist:
            continue
        # Skip lines that look like contact info
        if "@" in line or "http" in line or "/" in line or "github.com" in line or "linkedin.com" in line:
            continue
        # Skip lines with digits (phone numbers/years)
        if any(char.isdigit() for char in line):
            continue
            
        # Regex: 2 to 4 words, allowing Title Case (John Doe) or ALL CAPS (JOHN DOE)
        name_regex = r'^[A-Z][A-Za-z\.]+(?:\s[A-Z][A-Za-z\.]+){1,3}$'
        all_caps_regex = r'^[A-Z]+(?:\s[A-Z]+){1,3}$'
        
        if re.match(name_regex, line) or re.match(all_caps_regex, line):
            potential_name = line
            results["methods"]["name"] = "rules_regex"
            break
            
    # PASS 2: If Still None, take the VERY FIRST non-garbage line as the name
    if not potential_name:
        for line in lines[:5]:
            clean_upper = line.upper()
            if clean_upper in header_blacklist: continue
            if "@" in line or "http" in line: continue
            if len(line.split()) > 5: continue # Too long for a name
            
            potential_name = line
            results["methods"]["name"] = "rules_fallback"
            break
            
    results["name"] = potential_name
    return results

def extract_info_from_text(text):
    """Hybrid Engine: Deterministic first, AI Fallback second."""
    
    # Layer 1: Deterministic
    data = extract_deterministic(text)
    
    # Layer 2: LLM Fallback (only for missing fields)
    missing_fields = [k for k, v in data.items() if v is None and k != "methods"]
    
    if missing_fields:
        ai_data = call_gemini_fallback(text, missing_fields)
        for field in missing_fields:
            if ai_data.get(field):
                data[field] = ai_data[field]
                data["methods"][field] = "ai_fallback"

    # Final cleanup (guarantee dictionary)
    return {
        "name": data.get("name") or "",
        "email": data.get("email") or "",
        "github": data.get("github") or "",
        "linkedin": data.get("linkedin") or "",
        "extraction_method": data.get("methods", {})
    }

def call_gemini_fallback(text, fields):
    """Fallback layer using Gemini 1.5 Flash."""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {}

        client = genai.Client(api_key=api_key)
        field_list = ", ".join(fields)
        
        prompt = f"""
        Extract the following MISSING fields from the resume text: {field_list}
        Return ONLY valid JSON.
        Format:
        {{
            {", ".join([f'"{f}": ""' for f in fields])}
        }}
        Resume: {text[:4000]} # Truncate for efficiency
        """

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )

        raw_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(raw_text)
    except Exception as e:
        print(f"AI Fallback Error: {e}")
        return {}