import os
from groq import Groq
from Digital_India_Act.config import get_api_key

GROQ_API_KEY = get_api_key("GROQ_API_KEY")

class GroqLLMClient:
    """
    This module is an abstraction over Groq Cloud API.
    Keeps LLM dependency isolated for reproducibility and testing.
    """

    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        api_key = GROQ_API_KEY
        if not api_key:
            raise EnvironmentError("GROQ_API_KEY variable is not set")
        self.client = Groq(api_key=api_key)
        self.model = model

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
             messages=[
                {"role": "system", "content": "You are an accessibility compliance expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1200
        )


        return response.choices[0].message.content