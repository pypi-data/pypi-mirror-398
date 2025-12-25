# This check looks if the features given are consent compliant that is are they:
# The consent screen must be:
# 1) Clear, 2) Specific, 3) Informed, 4) Unambiguous
#Examples that ARE consent:
#Asking permission for cookies
#Asking access to location
#Asking access to contacts
#Asking access to microphone
#Asking access for camera
#Asking to collect email
#Asking to collect personal data for analytics
#Asking to share data with third parties
#Asking to store biometric data
#Asking for advertising tracking

# Consent check mean the software should get consent/permission to use the needed parts of user data and this feature uses llm to check if the frontend code has any violations or not

import requests,ollama,json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import json
import time
import re
from typing import Dict, Any
from Digital_India_Act.config import get_api_key

LLM_BACKEND = "groq"
GROQ_API_KEY = get_api_key("GROQ_API_KEY")

class WebConsentChecker:
    name= "Consent screen semantic check"
    description = "Check if consent UI text meets Digital India Act Standards"

    # # ---- Download the model if not present ---
    # def ensure_model(self,model_name):
    #     import subprocess, json

    #     try:
    #         out = subprocess.check_output(['ollama','list'],text=True)
    #         if model_name in out:
    #             return
    #         print(f"[INFO] Model {model_name} not found. Pulling ...")
    #         subprocess.run(['ollama','pull',model_name],check=True)
    #     except Exception as e:
    #         raise RuntimeError(
    #             f"Ollama not installed or model pull failed: {str(e)}"
    #         )
        
    #     # warm-up load
    #     try:
    #         ollama.run(model=model_name, prompt="Hello")  # initializes model in memory
    #         print("[INFO] Model ready.")
    #     except Exception as e:
    #         print("[WARN] Warm up failed:", e)

    # ---- LLM utilities ---- #

    def call_llm(self, prompt: str, max_tokens: int = 4000) -> str:
        if LLM_BACKEND.lower() != "groq":
            raise RuntimeError("Unsupported LLM backend")

        from groq import Groq

        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY not set in environment")

        client = Groq(api_key=GROQ_API_KEY)

        retries = 3
        for attempt in range(retries):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0,
                )
                return response.choices[0].message.content
            except Exception:
                if attempt == retries - 1:
                    raise
                time.sleep(1)

    def extract_json(self, text: str) -> Dict[str, Any]:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return {"error": "No JSON returned"}
        try:
            return json.loads(match.group(0))
        except Exception:
            return {"error": "Invalid JSON returned"}
    
    # --- Web crawling ---- #
    def fetch_html(self,url):
        try:
            res = requests.get(url,timeout=10)
            return res.text
        except:
            return ""
        
    def extract_links(self,html,base_url):
        soup = BeautifulSoup(html,"html.parser")
        links = []
        for a in soup.find_all("a",href=True):
            href = a["href"]
            if href.startswith("http"):
                links.append(href)
            else:
                links.append(urljoin(base_url, href))
        return links
    
    def crawl_site(self,start_url,depth=1):
        visited = set()
        ui_pages = {}

        urls = [start_url]

        for _ in range(depth):
            next_urls = []
            for url in urls:
                if url in visited:
                    continue

                html = self.fetch_html(url)
                visited.add(url)

                text = BeautifulSoup(html,"html.parser").get_text()
                ui_pages[url] = text

                if len(ui_pages) > 30:
                    break

                links = self.extract_links(html,start_url)

                for l in links:
                    if l not in visited:
                        next_urls.append(l)

            urls = next_urls
        
        return ui_pages
    
    def analyze_page(self, url: str, text: str) -> Dict[str, Any]:
        prompt = f"""
You are a legal compliance auditor for the Digital India Act.

Evaluate the following UI text and determine whether consent mechanisms
are compliant. Specifically check for:

- Explicit consent
- Clear & specific explanation
- Informed purpose
- Ability to refuse
- No dark patterns
- Unambiguous permission

Return ONLY valid JSON in this exact format:

{{
  "url": "{url}",
  "score": 0-100,
  "severity": "low|medium|high",
  "issues": ["list concrete legal issues"],
  "recommendation": "exact changes required to become compliant"
}}

UI TEXT:
\"\"\"{text}\"\"\"
"""

        raw = self.call_llm(prompt)
        return self.extract_json(raw)

    def run(self,start_url):

        pages=self.crawl_site(start_url,depth=2)
        results=[]

        for url,text in pages.items():
            ans=self.analyze_page(url,text)
            results.append(ans)

        # collect violating URLs (score < 70 or severity != low)
        violating=[]
        for r in results:
            if "score" in r and (r["score"] < 70 or r.get("severity")!="low"):
                violating.append(r["url"])

        return {
            "site":start_url,
            "pages_scanned": len(results),
            "violating_pages": violating,
            "details": results
        }