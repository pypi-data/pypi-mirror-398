import os
import json
import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List,Dict, Any
from Digital_India_Act.config import get_api_key

LLM_BACKEND = "groq"
GROQ_API_KEY = get_api_key("GROQ_API_KEY")

MAX_CHUNK_SIZE = 30000

class ContentModerationChecker:
    name = "Content Moderation Filter Check"
    description = "Detects presence and adequacy of content moderation mechanisms"

    # ----- LLM Helper function ----- #
    def call_llm(self,prompt: str, max_tokens: int = 30000) -> str:
        from groq import Groq

        client = Groq(api_key=GROQ_API_KEY)

        for _ in range(3):
            try:
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0,
                )
                return res.choices[0].message.content
            except Exception:
                time.sleep(1)
        raise RuntimeError("LLM failed")
    
    def extract_json(self, text: str):
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except:
            return None
        
    # ------- Frontend web scraping ----- #
    def fetch_frontend_code(self,url: str)-> Dict[str,str]:
        html = requests.get(url,timeout=10).text
        soup = BeautifulSoup(html, "html.parser")

        files = {"index.html": soup.get_text(separator = " ")}

        for script in soup.find_all("script",src = True):
            js_url = urljoin(url, script["src"])
            try:
                files[js_url] = requests.get(js_url,timeout=10).text
            except:
                pass

        return files
    
    # ----- Backend file discovery ------ #

    def collect_backend_files(self,base_path: str) -> Dict[str,str]:
        files = {}
        for root, _ , fs in os.walk(base_path):
            for f in fs:
                if f.endswith((".js",".ts",".py",".java",".go")):
                    path = os.path.join(root,f)
                    try:
                        with open(path,"r",errors="ignore") as fp:
                            files[path] = fp.read()
                    except:
                        pass
        return files
    
    # ------ File Prioritization ------ #
    def select_relevant_files(self, file_paths: List[str]) -> List[str]:
        prompt = f"""
You are assisting in a compliance audit under the Digital India Act.

Goal:
Identify ALL files that MAY POSSIBLY be related to handling
user-generated content (UGC).

Definition of UGC (broad, inclusive):
Any content that may originate from users, including but not limited to:
- comments, posts, reviews, messages, chats
- form inputs, text submissions
- uploads, feedback, ratings
- API endpoints that accept user input
- database handlers storing user-provided text

Instructions (IMPORTANT):
- Be INCLUSIVE, not strict.
- If a file name even SUGGESTS user input or storage, INCLUDE it.
- If you are unsure, INCLUDE the file.
- False positives are acceptable.
- Do NOT exclude files just because certainty is low.

Files to analyze:
{json.dumps(file_paths, indent=2)}

Return format:
- A JSON array of file paths.
- Return an empty array ONLY if you are confident NONE are related.
"""
        raw = self.call_llm(prompt)
        return self.extract_json(raw) or []
    
    #chunking logic
    def chunk_text(self,text:str) -> List[str]:
        return [text[i:i + MAX_CHUNK_SIZE] for i in range(0,len(text), MAX_CHUNK_SIZE)]
    
    #analysis logic
    def analyze_chunks(self,file_path: str,chunks: List[str]) -> Dict[str,Any]:
        findings = []

        for ch in chunks:
            prompt = f"""
You are evaluating software compliance with content moderation obligations.

Analyze the following code/text and answer in JSON:

{{
  "ugc_present": true|false,
  "moderation_present": true|false,
  "moderation_type": "none|frontend|backend|ai|human_review",
  "issues": [list issues if any]
}}

Code/Text:
\"\"\"{ch}\"\"\"
"""
            raw = self.call_llm(prompt)
            parsed = self.extract_json(raw)
            if parsed:
                findings.append(parsed)
                if parsed.get("moderation_present"):
                    break

        return {
            "file": file_path,
            "analysis": findings
        }
    
    def generate_ai_recommendation(self, summary: Dict[str, Any]) -> str:
        prompt = f"""
You are a Digital India Act compliance auditor.

Based on the following content moderation findings, provide a
clear, legally actionable recommendation.

Findings (JSON):
{json.dumps(summary, indent=2)}

Your recommendation MUST:
- Mention whether backend moderation is required
- Mention reporting/flagging mechanisms if missing
- Mention human review where applicable
- Be concrete (what exactly to add or change)

Return ONLY plain text (no JSON).
"""

        try:
            return self.call_llm(prompt, max_tokens=600)
        except:
            return "Unable to generate AI recommendation due to LLM error."

    # ------- Main functionality ---- #

    def run(self,url: str,backend_path: str = None,analyze_all_files = True) -> Dict[str, Any]:
        frontend_files = {}
        backend_files = self.collect_backend_files(backend_path) if backend_path else {}

        if url:
            try:
                frontend_files = self.fetch_frontend_code(url)
                frontend_files = {
                    k: v for k, v in frontend_files.items()
                    if v and v.strip()
                }
            except Exception as e:
                # Never crash for frontend
                self.frontend_error = str(e)
                frontend_files = {}

        all_files = {**frontend_files,**backend_files}

        # for inadequate resources
        if not all_files:
            return {
                "status": "NOT_CHECKED",
                "reason": "Inadequate resources for analysis",
                "details": (
                    "Neither frontend code could be extracted from the provided URL "
                    "nor backend source code was supplied. "
                    "Content moderation compliance cannot be assessed."
                ),
                "ugc_detected": None,
                "moderation_present": None,
                "severity": "unknown",
                "files_analyzed": [],
                "human_inspection_recommended": [],
                "recommendation": (
                    "Provide access to frontend source code and/or backend application code "
                    "to enable content moderation compliance analysis."
                )
            }
        
        if analyze_all_files:
            relevant_files = list(all_files.keys())
        else:
            relevant_files = self.select_relevant_files(list(all_files.keys()))


        analyses = []
        for f in relevant_files:
            chunks = self.chunk_text(all_files.get(f,""))
            analyses.append(self.analyze_chunks(f,chunks))

        # gathering the final results
        ugc = any(
            a["analysis"] and a["analysis"][0].get('ugc_present')
            for a in analyses
        )

        moderation = any(
            any(x.get("moderation_present") for x in a['analysis'])
            for a in analyses
        )

        severity = (
            "high" if ugc and not moderation
            else "medium" if ugc
            else "low"
        )

        human_review = [
            a["file"] for a in analyses
            if not a["analysis"] or a["analysis"][0].get("moderation_type") == "frontend"
        ]

        summary_for_llm = {
            "ugc_detected": ugc,
            "moderation_present": moderation,
            "severity": severity,
            "moderation_types_detected": list({
                x.get("moderation_type")
                for a in analyses
                for x in a.get("analysis", [])
                if "moderation_type" in x
            }),
            "human_inspection_recommended_files": human_review,
            "files_analyzed": relevant_files
        }

        if not ugc:
            ai_recommendation = (
                "No user-generated content was detected. "
                "Content moderation obligations under the Digital India Act "
                "are not applicable for the analyzed system."
            )
        else:
            ai_recommendation = self.generate_ai_recommendation(summary_for_llm)


        return {
            "ugc_detected": ugc,
            "moderation_present": moderation,
            "severity": severity,
            "files_analyzed": relevant_files,
            "human_inspection_recommended": human_review,
            "details": analyses,
            "recommendation": ai_recommendation
        }