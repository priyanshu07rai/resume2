import requests

def scrape_linkedin_profile(url):
    """
    Lightweight web scraper to verify if a LinkedIn profile URL is active.
    It does not bypass heavy bot protections but checks if the profile endpoint exists.
    """
    if not url or "linkedin.com/in/" not in url:
        return {"exists": False, "status": "Invalid URL"}
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        
        # LinkedIn returns 999 for automated requests, but that means the profile exists
        # A 404 means the profile definitely does not exist
        if response.status_code == 200 or response.status_code == 999:
            return {
                "exists": True, 
                "status": "Profile Found",
                "risk_signal": "low_risk"
            }
        elif response.status_code == 404:
            return {
                "exists": False, 
                "status": "Profile Not Found",
                "risk_signal": "high_risk"
            }
        else:
            return {
                "exists": False, 
                "status": f"Unknown Status {response.status_code}",
                "risk_signal": "moderate_risk"
            }
    except requests.exceptions.RequestException as e:
        return {
            "exists": False, 
            "status": f"Connection Error: {str(e)}",
            "risk_signal": "moderate_risk"
        }
