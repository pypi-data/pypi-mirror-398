# groq_client.py

import os
from groq import Groq
from dotenv import load_dotenv
from config import GROQ_MODELS

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def query_llm(prompt: str) -> str:
    for model in GROQ_MODELS:
        try:
            res = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            return res.choices[0].message.content.strip()
        except Exception:
            continue
    return "[LLM unavailable]"
