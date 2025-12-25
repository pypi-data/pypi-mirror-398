import requests
import time
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from groq import Groq
import json
from Digital_India_Act.config import get_api_key

GROQ_API_KEY = get_api_key("GROQ_API_KEY")

HEADERS = {
    "User-Agent": "Digital-India-Act-Compliance-Checker/1.0",
    "Accept-Language": "en-IN,en;q=0.9"
}

COMMON_PATHS = [
    "", "grievance", "grievances", "complaint", "complaints",
    "lodgegrievance", "support", "help",
    "contact-support/grievance-redressal.html"
]

GRIEVANCE_URL_KEYWORDS = [
    "grievance", "complaint", "redressal",
    "lodge", "pgportal", "support"
]

GRIEVANCE_TEXT_KEYWORDS = [
    "grievance", "complaint", "redressal",
    "grievance officer", "nodal officer",
    "appeal", "escalation"
]

SOFT_404_KEYWORDS = [
    "404", "page not found", "not found",
    "does not exist", "error occurred"
]

class GrievanceExtractor:
    """
    
    """

    def __init__(self, base_url: str, timeout: int =10):
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.visited = set()
        self.llm = Groq(api_key=GROQ_API_KEY)

    def extract(self) -> List[Dict[str, Any]]:
        pages = []

        llm_urls = self.llm_suggest_urls()
        print(f"Urls suggested by llm:{llm_urls}")
        for url in llm_urls:
            page = self._process_url(url)
            if page:
                pages.append(page)
        
        for path in COMMON_PATHS:
            url = urljoin(self.base_url, path)
            page = self._process_url(url)
            if page:
                pages.append(page)
        
        unique = {}
        for p in pages:
            unique[p['url']] = p
        

        return list(unique.values())
    
    def llm_suggest_urls(self) -> List[str]:
        prompt = f"""
                You are given a government authority website URL.

        The grievance redressal mechanism may be:
        - hosted directly on this website, OR
        - hosted on an officially linked subdomain, OR
        - hosted on a delegated government grievance portal.

        Suggest up to 5 MOST PROBABLE absolute URLs
        that could contain grievance redressal or complaint mechanisms
        related to this authority.

        These URLs MAY be on:
        - the same domain
        - a subdomain
        - an official delegated portal (e.g., PG Portal)

        Return ONLY a valid JSON array of absolute URLs.
        If none are reasonably likely, return [].

        Base URL:
        {self.base_url}
        """
        try:
            response = self.llm.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            return self._json_safe_list(response.choices[0].message.content)
        except Exception:
            return []
        
    def _process_url(self, url:str) -> Optional[Dict[str, Any]]:
        if url in self.visited:
            return None
        print(f"Processing the url: {url}")
        self.visited.add(url)

        try:
            r = self.session.get(url, timeout=self.timeout, allow_redirects=True)
        except Exception:
            return None
        
        soup = BeautifulSoup(r.text, "html.parser")
        text = self._extract_visible_text(soup)
        normalized = self._normalize(text)

        soft_404 = self._is_soft_404(normalized)
        signals = self._detect_signals(url, normalized)

        is_js_only = (
            r.status_code == 200 and 
            not normalized and
            any(k in url.lower() for k in GRIEVANCE_URL_KEYWORDS)
        )

        if (signals or is_js_only) and not soft_404:
            return {
                "url": url,
                "text": normalized,
                "reachable": r.status_code == 200,
                "soft_404": soft_404,
                "is_js_only": is_js_only,
                "signals": signals
            }
        return None
    
    def _extract_visible_text(self, soup:BeautifulSoup) -> str:
        for tag in soup([
            "script", "style", "meta", "iframe", "svg", "canvas", "noscript"
        ]):
            tag.decompose()

        for form in soup.find_all("form"):
            for t in form(["input", "textarea", "select", "button"]):
                t.decompose()
        return soup.get_text(separator=" ", strip=True)
    
    def _normalize(self, text:str) -> str:
        return " ".join(text.split())
    
    def _is_soft_404(self, text:str) ->bool:
        low = text.lower()
        return any(k in low for k in SOFT_404_KEYWORDS)

    def _detect_signals(self, url: str, text: str) -> List[str]:
        signals = []

        for k in GRIEVANCE_URL_KEYWORDS:
            if k in url.lower():
                signals.append(f"url:{k}")

        for k in GRIEVANCE_TEXT_KEYWORDS:
            if k in text.lower():
                signals.append(f"text:{k}")

        return signals
    
    def _json_safe_list(raw:str) -> List[str]:
        try:
            start = raw.find("[")
            end = raw.rfind("]")
            return json.loads(raw[start:end+1])
        except Exception:
            return [] 