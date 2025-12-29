import json
import re
from groq import Groq
from Digital_India_Act.config import get_api_key

GROQ_API_KEY = get_api_key("GROQ_API_KEY")
print(f"Got the API key:{GROQ_API_KEY}")


class GroqLLMClient:
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY not set")

        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = model

    def _extract_json(self, text: str) -> dict:
        """
        Extracts the first JSON object found in text.
        """
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in LLM output")

        return json.loads(match.group(0))

    def complete(self, prompt: str) -> dict:
        system_prompt = (
            "You are a compliance auditor evaluating child safety and "
            "age-appropriate design under the Digital India Act. "
            "Respond with ONLY valid JSON in this format:\n"
            '{ "score": <number between 0 and 1>, "explanation": "<text>" }'
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        content = response.choices[0].message.content.strip()

        try:
            parsed = self._extract_json(content)
            return {
                "score": float(parsed.get("score", 0.0)),
                "explanation": parsed.get("explanation", "")
            }
        except Exception:
            return {
                "score": 0.0,
                "explanation": "LLM response could not be parsed as valid JSON"
            }
