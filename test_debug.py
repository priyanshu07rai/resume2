import asyncio
from ai_consensus_engine import generate_forensic_reasoning_v4

text = {'education': [], 'experience': [], 'skills': []}
github = {}

try:
    res = generate_forensic_reasoning_v4(text, github)
    print("RES:", res)
except Exception as e:
    import traceback
    traceback.print_exc()
