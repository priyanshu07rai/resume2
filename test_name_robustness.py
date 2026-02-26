import json
from extractor import extract_deterministic

test_cases = [
    {
        "desc": "ALL CAPS name on first line",
        "text": "JOHN DOE\nSoftware Engineer\njohn@example.com"
    },
    {
        "desc": "Title Case with middle initial",
        "text": "Jane A. Smith\nData Scientist\njane@example.com"
    },
    {
        "desc": "Name after a RESUME header",
        "text": "RESUME\nRobert Brown\nrobert@example.com"
    },
    {
        "desc": "Hyphenated name in ALL CAPS",
        "text": "ALICE-MARIE JOHNSON\nDeveloper"
    },
    {
        "desc": "Messy top lines with first line being the name",
        "text": "Michael O'Connor\n123 Street, NY\n@mike_dev"
    }
]

for i, tc in enumerate(test_cases):
    print(f"Test {i+1}: {tc['desc']}")
    res = extract_deterministic(tc['text'])
    print(f"  Extracted Name: {res['name']} (Method: {res['methods'].get('name')})")
    print("-" * 20)
