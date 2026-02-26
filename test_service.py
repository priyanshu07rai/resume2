import json
from extraction_service import extract_entities

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

print("Running extraction engine...")
res = extract_entities(text, {"domain": "Software Engineering"})
print("Response Identity:")
print(json.dumps(res["identity"], indent=2))
