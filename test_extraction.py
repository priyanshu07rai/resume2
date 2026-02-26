import json
from ai_consensus_engine import get_ai_consensus

# Minimal resume text
text = """
JOHN DOE
Software Engineer
johndoe@example.com
https://github.com/johndoe
https://linkedin.com/in/johndoe

EXPERIENCE
Software Engineer at Tech Corp (2020-2023)
- Built Python and AWS microservices.

EDUCATION
B.S. Computer Science, University X
"""

print("Running Groq extraction...")
res = get_ai_consensus(text, "extraction", "Software Engineering")
print("Response:")
print(json.dumps(res, indent=2))
