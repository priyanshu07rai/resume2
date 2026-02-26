import os
import json
import logging
from dotenv import load_dotenv
from api_resilience import call_ai_with_schema
from groq import Groq

logging.basicConfig(level=logging.INFO)
load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=groq_api_key)

if __name__ == "__main__":
    print("Testing Groq API Schema Call...")
    res = call_ai_with_schema(
        system_prompt="You return valid JSON.",
        user_prompt="Give me a simple valid JSON with key 'status'='ok'",
        schema_keys=["status"],
        groq_client=groq_client,
        gemini_client=None,
        timeout_sec=10,
        max_retries=2,
        max_tokens=50
    )
    print("RESULT:", json.dumps(res, indent=2))
