from bs4 import BeautifulSoup
from typing import List, Dict
from .models import SemanticFinding
import requests
import json
from playwright.sync_api import sync_playwright

MAX_IMAGES = 15
MAX_BUTTONS = 20
MAX_LINKS = 30
MAX_INPUTS = 20
MAX_TEXT_LEN = 200
MAX_PROMPT_CHARS = 8000

class SemanticAccessibilityChecker_LLM:
    """
    In this module, we will be using the Groq cloud api for performing the LLM inferencing
    Here, we extract 5 stages of data that will be having the most impact on accessibility in case of a violation.
    """

    def __init__(self, url:str, llm_client):
        self.url = url
        self.llm_client = llm_client

    def _get_html(self) -> str:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                page.goto(self.url, timeout=60000, wait_until="networkidle")
                html = page.content()
            finally:
                browser.close()
        return html
    
    def _extract_context(self, soup:BeautifulSoup) -> Dict:
        return {
            "images": [
                {
                    "alt": img.get("alt", "")[:MAX_TEXT_LEN],
                    "context": img.parent.get_text(strip=True)[:MAX_TEXT_LEN]
                }
                for img in soup.find_all("img")[:MAX_IMAGES]
            ],
            "buttons": [
                {
                    "text": btn.get_text(strip=True)[:MAX_TEXT_LEN],
                    "aria": btn.get("aria-label", "")[:MAX_TEXT_LEN],
                    "context": btn.parent.get_text(strip=True)[:MAX_TEXT_LEN]
                }
                for btn in soup.find_all("button")[:MAX_BUTTONS]
            ],
            "links": [
                {
                    "text": a.get_text(strip=True)[:MAX_TEXT_LEN],
                    "context": a.parent.get_text(strip=True)[:MAX_TEXT_LEN]
                }
                for a in soup.find_all("a")[:MAX_LINKS]
            ],
            "inputs": [
                {
                    "type": inp.get("type", ""),
                    "placeholder": inp.get("placeholder", "")[:MAX_TEXT_LEN],
                    "aria": inp.get("aria-label", "")[:MAX_TEXT_LEN],
                    "label": soup.find("label", {"for": inp.get("id")}).get_text(strip=True)[:MAX_TEXT_LEN]
                    if inp.get("id") and soup.find("label", {"for": inp.get("id")})
                    else ""
                }
                for inp in soup.find_all("input")[:MAX_INPUTS]
            ],
            "errors": [
                el.get_text(strip=True)[:MAX_TEXT_LEN]
                for el in soup.find_all(
                    lambda tag: tag.name in ["div", "span"]
                    and "error" in " ".join(tag.get("class", [])).lower()
                )
            ]
        }
    
    def _build_prompt(self, context:Dict) -> str:
        return f"""
        Analyze the following UI context for semantic accessibility issues.

        Focus on:
        - Meaningfulness of alt text
        - Clarity of actions (buttons/links)
        - Form comprehension
        - Error message usefulness
        - Cognitive accessibility

        Rules:
        - Do NOT claim WCAG compliance
        - Do NOT speculate beyond given context
        - Return ONLY valid JSON in the format below

        Output format:
        [
        {{
            "component": "image|button|link|form|error|navigation",
            "issue": "...",
            "severity": "low|medium|high",
            "explanation": "..."
        }}
        ]

        UI CONTEXT:
        {json.dumps(context, indent=2)}
        """
    
    def run(self) -> List[SemanticFinding]:
        html = self._get_html()
        soup = BeautifulSoup(html, "lxml")
        context = self._extract_context(soup)

        prompt = self._build_prompt(context)

        if len(prompt) > MAX_PROMPT_CHARS:
            raise ValueError(
                f"Prompt too large for LLM ({len(prompt)} chars). "
                "Reduce semantic context size."
            )
        response_text = self.llm_client.generate(prompt)

        try:
            raw_findings = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Groq LLM returned non-JSON output."
                f" Raw response:\n{response_text}"
            ) from e
        
        findings = []

        for f in raw_findings:
            findings.append(
                SemanticFinding(
                    component=f["component"],
                    issue=f["issue"],
                    severity=f["severity"],
                    explanation=f["explanation"]
                )
            )

        return findings