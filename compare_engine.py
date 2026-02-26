def calculate_overlap(skills1, skills2):
    """Calculates the percentage of skills shared between two lists."""
    if not skills1 and not skills2:
        return 0.0
    
    set1 = set([s.lower().strip() for s in skills1])
    set2 = set([s.lower().strip() for s in skills2])
    
    if not set1 or not set2:
        return 0.0
        
    overlap = set1.intersection(set2)
    # Return percentage relative to the smaller skill set (or average, here we use union)
    return (len(overlap) / len(set1.union(set2))) * 100

def compare_profiles(p1: dict, p2: dict) -> dict:
    """
    Deterministically computes the comparison metrics between two candidate dictionaries.
    Required by the Antigravity Intelligence specs.
    """
    
    # We may not have full arrays of skills/years if they are just from DB, 
    # but let's safely default to 0 for missing data.
    skills1 = p1.get('skills', [])
    skills2 = p2.get('skills', [])
    
    years1 = p1.get('experience_years', 0)
    years2 = p2.get('experience_years', 0)
    
    return {
        "reliability_diff": p1.get('reliability', 0) - p2.get('reliability', 0),
        "fraud_diff": p1.get('fraud_score', 0) - p2.get('fraud_score', 0),
        "skill_overlap": calculate_overlap(skills1, skills2),
        "experience_gap": abs(years1 - years2)
    }
