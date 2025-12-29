# The main motto of this check is ensure that the application is not collecting more information than what is required for the business functionality.
# Un-necessary should not be collected
# Also one more very important thing is the data should not be unnecessarily sent to other apis, databases, logs, llms etc.

import os
import re
from typing import Dict, List, Any, Set, Optional
import requests
from bs4 import BeautifulSoup
import json
import time
from Digital_India_Act.config import get_api_key

LLM_BACKEND = "groq"
GROQ_API_KEY = get_api_key("GROQ_API_KEY")

class DataMinimizationChecker:

    name = "Data Minimization Compliance check"
    Description = """The main motto of this check is ensure that the application is not collecting more information than what is required for the business functionality.
Un-necessary should not be collected
Also one more very important thing is the data should not be unnecessarily sent to other apis, databases, logs, llms etc.
"""

    FRONTEND_EXTENSIONS = (".html",".jsx",".tsx",".js")

    FRONTEND_FIELD_PATTERNS = [
        r'name\s*=\s*["\']([^"\']+)["\']',
        r'id\s*=\s*["\']([^"\']+)["\']',
        r'placeholder\s*=\s*["\']([^"\']+)["\']',
        r'(\w+)\s*:\s*["\'].*["\']'         
    ]

    COMMON_PII_FIELDS = {
        "name", "email", "phone", "mobile", "password", "otp",
        "address", "dob", "age", "gender", "pan", "aadhaar",
        "creditcard", "cvv", "upi"
    }

    # PAYLOAD_PATTERNS = [
    #     r"\{([^}]+)\}",             
    #     r"JSON\.stringify\(([^)]+)\)"
    # ]

    BACKEND_EXTENSIONS = (".py", ".js", ".ts", ".java")

    DB_PATTERNS = [
        r"save_to_db\(",
        r"insert",
        r"create\(",
        r"update\("
    ]

    API_PATTERNS = [
        r"requests\.",
        r"axios\.",
        r"fetch\("
    ]

    LOG_PATTERNS = [
        r"logging\.",
        r"logger\.",
        r"print\(",
        r"console\.log"
    ]

    LLM_PATTERNS = [r"openai", r"groq", r"prompt", r"llm",r"gemini"]

    
    def collect_files(self,path: str, exts: tuple) -> Dict[str,str]:
        files = {}
        for root, _,fs in os.walk(path):
            for f in fs:
                if f.endswith(exts):
                    p = os.path.join(root,f)
                    try:
                        with open(p, "r",errors = "ignore") as fp:
                            files[p] = fp.read()
                    except:
                        pass
        return files

    # def extract_frontend_fields(self,frontend_files:Dict[str,str])-> Set[str]:
    #     fields = set()
    #     for content in frontend_files.values():
    #         for pattern in self.FORM_PATTERNS:
    #             fields |= set(re.findall(pattern,content,re.IGNORECASE))
    #     return {f.lower() for f in fields}

    # extracting fields from frontend path
    def extract_frontend_fields_from_path(self, frontend_path: str) -> Set[str]:
        frontend_files = self.collect_files(frontend_path, self.FRONTEND_EXTENSIONS)
        fields = set()

        for path, content in frontend_files.items():

            # ---------- HTML ----------
            if path.endswith(".html"):
                soup = BeautifulSoup(content, "html.parser")
                for form in soup.find_all("form"):
                    for tag in form.find_all(["input", "textarea", "select"]):
                        if tag.get("type") in ("submit", "button", "reset"):
                            continue
                        if tag.get("name"):
                            fields.add(tag.get("name").lower())

            # ---------- JSX / TSX / JS ----------
            else:
                for match in re.findall(
                    r'(?:name|id)\s*=\s*["\']([^"\']+)["\']',
                    content,
                    re.IGNORECASE
                ):
                    fields.add(match.lower())

        return fields

    
    def scrape_frontend_fields_from_url(self, url: str) -> Set[str]:
        headers = {
            "User-Agent": "Mozilla/5.0 (ComplianceCheckerBot/1.0)"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        fields = set()

        for form in soup.find_all("form"):
            for tag in form.find_all(["input", "textarea", "select"]):
                if tag.get("type") in ("submit", "button", "reset"):
                    continue

                for attr in ("name", "id"):
                    if tag.get(attr):
                        fields.add(tag.get(attr).lower())

        return fields

    
    def extract_json(self, text: str):
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except:
            return None
        
    def analyze_backend_rule_based(self, backend_files, frontend_fields):

        usage = {
            "db": set(),
            "api": set(),
            "logs": set(),
            "llm": set()
        }
    
        field_usage = {f: set() for f in frontend_fields}
    
        for path, content in backend_files.items():
            for line in content.splitlines():
                line_lower = line.lower()
    
                for field in frontend_fields:
                    if re.search(rf"\b{re.escape(field)}\b", line_lower):
                    
                        if any(re.search(p, line_lower) for p in self.DB_PATTERNS):
                            usage["db"].add(field)
                            field_usage[field].add("db")
    
                        if any(re.search(p, line_lower) for p in self.API_PATTERNS):
                            usage["api"].add(field)
                            field_usage[field].add("api")
    
                        if any(re.search(p, line_lower) for p in self.LOG_PATTERNS):
                            usage["logs"].add(field)
                            field_usage[field].add("logs")
    
                        if any(re.search(p, line_lower) for p in self.LLM_PATTERNS):
                            usage["llm"].add(field)
                            field_usage[field].add("llm")
    
        unused_fields = [f for f, u in field_usage.items() if not u]
    
        return {
            "field_usage": {k: list(v) for k, v in field_usage.items()},
            "unused_fields": unused_fields,
            "over_shared_fields": {k: list(v) for k, v in usage.items() if v}
        }
    
    
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
    
    def analyze_backend_llm_based(
    self,
    backend_files: Dict[str, str],
    frontend_fields: Set[str]
) -> Dict[str, Any]:
        """
        Uses Groq LLM to semantically analyze backend usage of user data
        for Data Minimization compliance.
        """

        # Combine backend code safely (limit size if needed)
        combined_backend_code = ""
        for path, content in backend_files.items():
            combined_backend_code += f"\n\n# FILE: {path}\n{content[:3000]}"

        prompt = f"""
    You are a compliance expert evaluating **Data Minimization** under privacy regulations
    (Digital India Act, GDPR-like principles).

    ### CONTEXT
    The frontend application collects the following user data fields:
    {sorted(list(frontend_fields))}

    Below is the backend server code.

    ### YOUR TASK
    Analyze the backend code and determine:

    1. **Field Necessity**
       - For each frontend-collected field, decide whether it is:
         - REQUIRED for core business logic
         - OPTIONAL but justified
         - UNNECESSARY / excessive

    2. **Excessive Usage**
       Identify any fields that are:
       - Stored in databases without clear purpose
       - Sent to third-party APIs unnecessarily
       - Logged in plaintext logs
       - Sent to analytics, monitoring, or LLM services

    3. **Data Minimization Violations**
       Flag violations where:
       - Fields are collected but never used
       - Fields are used beyond their original purpose
       - Sensitive fields are propagated too widely

    4. **Overall Risk Assessment**
       Rate overall compliance risk as:
       - LOW
       - MEDIUM
       - HIGH

    ### OUTPUT FORMAT (STRICT JSON)
    Respond ONLY in the following JSON format:

    {{
      "field_analysis": {{
        "field_name": {{
          "necessity": "required | optional | unnecessary",
          "backend_usage": ["db", "api", "logs", "analytics", "llm", "unknown"],
          "justification": "short explanation"
        }}
      }},
      "over_sharing_detected": [
        {{
          "field": "field_name",
          "issue": "description of over-sharing"
        }}
      ],
      "unused_or_excessive_fields": ["field1", "field2"],
      "overall_compliance_risk": "LOW | MEDIUM | HIGH",
      "summary": "Concise compliance summary"
    }}

    ### BACKEND CODE
    {combined_backend_code}
    """

        try:
            raw = self.call_llm(prompt)
            llm_response = self.extract_json(raw) or []

            return {
                "method": "llm_based",
                "llm_provider": "groq",
                "analysis": llm_response,
                "note": "Semantic analysis based on backend behavior and data minimization principles"
            }

        except Exception as e:
            return {
                "method": "llm_based",
                "error": str(e),
                "analysis": None,
                "note": "LLM analysis failed"
            }
        
    def run(
    self,
    backend_path: str,
    frontend_url: Optional[str] = None,
    frontend_path: Optional[str] = None,
    backend_mode: str = "rule"
) -> Dict[str, Any]:

        if frontend_url:
            frontend_fields = self.scrape_frontend_fields_from_url(frontend_url)
        elif frontend_path:
            frontend_fields = self.extract_frontend_fields_from_path(frontend_path)
        else:
            raise ValueError("Either frontend_url or frontend_path must be provided")

        backend_files = self.collect_files(backend_path, self.BACKEND_EXTENSIONS)

        # ---------------- Rule-based ----------------
        if backend_mode == "rule":
            backend_result = self.analyze_backend_rule_based(
                backend_files, frontend_fields
            )

            over_shared = backend_result.get("over_shared_fields", {})

            if backend_result.get("unused_fields"):
                severity = "high"

            elif any(over_shared.get(k) for k in ("logs", "api", "llm")):
                severity = "medium"

            elif over_shared.get("db"):
                severity = "low"

            else:
                severity = "low"

        # ---------------- LLM-based ----------------
        else:
            backend_result = self.analyze_backend_llm_based(
                backend_files, frontend_fields
            )

            try:
                severity = backend_result["analysis"]["overall_compliance_risk"].lower()
            except Exception:
                severity = "unknown"

        return {
            "frontend_collected_fields": sorted(frontend_fields),
            "backend_analysis_mode": backend_mode,
            "backend_result": backend_result,
            "severity": severity,
            "recommendation": (
                "Remove unnecessary fields and avoid forwarding personal data "
                "unless strictly required for business purposes."
                if severity in ("medium", "high")
                else "Data minimization principles are followed."
            )
        }
