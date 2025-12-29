import os
import json
from typing import List, Dict, Any
from groq import Groq
from Digital_India_Act.config import get_api_key

GROQ_API_KEY = get_api_key("GROQ_API_KEY")
MAX_CHARS = 25_000

class GrievanceRedressalChecker:
    """
    This module is responsible for checking the Grievance Redressal mechanism present.
    We are using LLM-based approach for the analysis. 
    
    In this module, we are using the Groq Cloud hosted API with Llama 8B model for performing the semantic analysis.
    Here, we are using only publicly visible content and ensure stateless execution.
    """

    def __init__(self, pages: List[Dict[str, Any]]):
        """
        Each page sent as input must be of the format:
        {
            "url": str,
            "text": str
        }
        """

        self.pages = pages
        # print("The pages found are:")
        # print(self.pages)
        self.client = Groq(api_key=GROQ_API_KEY)
    
    def _build_prompt(self) -> str:
        combined_text = ""
        for p in self.pages:
            combined_text += f"\nURL: {p['url']}\nCONTENT:\n{p['text']}\n"
            if len(combined_text) > MAX_CHARS:
                break

        return f"""
        You are a compliance analysis assistant.

        Analyze the CONTENT below to assess the QUALITY of grievance redressal
        mechanism under the Digital India Act.

        IMPORTANT:
        - Analyze ONLY provided content
        - Do NOT assume missing info
        - Do NOT judge existence

        Return STRICT JSON:

        {{
        "grievance_officer_identified": true | false,
        "contact_details_present": true | false,
        "accessibility_clear": true | false,
        "evidence": {{
            "officer_text": string | null,
            "contact_text": string | null
        }},
        "confidence": "High" | "Medium" | "Low",
        "reasoning": string
        }}

        CONTENT:
        {combined_text}
        """
    
    def _call_llm(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        prompt = self._build_prompt()

        resp = self.client.chat.completions.create(
           model="llama-3.3-70b-versatile",
           messages=[
                {"role": "system", "content": "You are a strict compliance analysis engine."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )

        raw = resp.choices[0].message.content.strip()
        start, end = raw.find("{"), raw.rfind("}")
        return json.loads(raw[start:end+1])
    
    def _final_decision(self, exists:bool, llm: Dict[str, Any]) -> str:
        if not exists:
            return "AT_RISK"
        if exists and not llm:
            return "COMPLIANT"
        if llm.get("accessibility_clear"):
            return "COMPLIANT"
        return "AT_RISK"
    
    def _grievance_exists(self) -> bool:
        return any(
            p.get("signals") or p.get("is_js_only")
            for p in self.pages
        )
    
    def run(self) -> Dict[str, Any]:
        grievance_exists = self._grievance_exists()
        semantic_pages = [
            p for p in self.pages
            if p.get("text") and not p.get("soft_404")
        ]

        llm_result = {}
        if semantic_pages:
            llm_result = self._call_llm(semantic_pages)

        final_status = self._final_decision(grievance_exists, llm_result)

        return {
            "Check": "Grievance Redressal Mechanism",
            "status": final_status,
            "confidence": llm_result.get("confidence", "High"),
            "details": {
                "grievance_mechanism_present": grievance_exists,
                "grievance_officer_identified": llm_result.get("grievance_officer_identified", False),
                "contact_details_present": llm_result.get("contact_details_present", False),
                "accessibility_clear": llm_result.get("accessibility_clear", False),
            },
            "evidence": llm_result.get("evidence", {}),
            "reasoning": llm_result.get(
                "reasoning",
                "Assessment based on deterministic extraction and semantic analysis."
            )
        }