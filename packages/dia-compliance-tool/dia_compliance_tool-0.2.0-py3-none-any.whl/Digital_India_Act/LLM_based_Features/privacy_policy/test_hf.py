import os
from groq import Groq
from Digital_India_Act.config import get_api_key

# Load API key from environment
api_key = get_api_key("GROQ_API_KEY")
if not api_key:
    raise RuntimeError("GROQ_API_KEY not set.")

client = Groq(api_key=api_key)

prompt = """
You are a strict JSON-generating assistant.
Return ONLY JSON.

Question: Does the policy mention personal data collection?

Text:
"Our app collects minimal diagnostic information to improve performance."

Return only JSON:
{
  "answer": "yes|no|unclear",
  "reason": "short explanation",
  "evidence": "snippet from text"
}
"""

print("Sending request to Groq Cloud...\n")

resp = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=200,
    temperature=0,
)

output = resp.choices[0].message.content
print("=== MODEL OUTPUT ===\n")
print(output)
