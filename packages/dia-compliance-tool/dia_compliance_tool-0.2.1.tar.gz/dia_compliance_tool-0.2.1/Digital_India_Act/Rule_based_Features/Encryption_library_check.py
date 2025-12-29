# This is a feature that checks for existence of libraries that does the encryption of safety info like passwords etc

import os
import re   
import json
import ollama
import subprocess, shutil
import time
from Digital_India_Act.config import get_api_key

LLM_BACKEND = "groq"
GROQ_API_KEY = get_api_key("GROQ_API_KEY")

class Encryption_libraries_checker:
    name = "Encryption libraries existence check"
    description="This is a feature that checks for existence of libraries that does the encryption of safety info like passwords etc"
    usage = "There are two methods that are provided:" \
    "1) LLM based heuristic scan which looks for potential files to be scanned to look for encryption libraries, it is fast but not fully accurate" \
    "2) Manual scan looks all the files and counts violations rate"

    #---- encryption libraries keywords that will be searched for----
    encryption_keywords = [
        r"aes", r"bcrypt", r"crypto", r"hashlib", r"argon2",
        r"scrypt", r"hmac", r"openssl", r"fernet", r"pbkdf2"
    ]

    # ---- where encryption SHOULD exist (password, tokens, credentials) ----
    places_needing_encryption = [
        r"password", r"credential", r"secret", r"token", r"auth", r"jwt"
    ]

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

    # --- LLM utilities ----
    def call_llm(self,prompt: str, max_tokens: int = 512) -> str:
        if LLM_BACKEND.lower() == "groq":
            from groq import Groq

            if not GROQ_API_KEY:
                raise RuntimeError("GROQ_API_KEY is not set.")

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
        else:
            raise RuntimeError(f"Unsupported LLM backend: {LLM_BACKEND}")


    def extract_json_from_text(self,text: str):
        match = re.search(r"\[.*\]", text, flags=re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except:
            return None


    # ---- full manual scan ----
    def full_scan(self,base_path):
        total_used = 0
        total_needed = 0
        violating_files=[]
        for root, dirs , files in os.walk(base_path):
            for f in files:
                if f.endswith((".js",".ts",".py",".java",".go",".rb")):
                    file_path = os.path.join(root,f)
                    with open(file_path,"r",errors="ignore") as fp:
                        content = fp.read().lower()

                        used = any(re.search(k,content) for k in self.encryption_keywords)
                        needed = any(re.search(k,content) for k in self.places_needing_encryption)

                        if used:
                            total_used+=1
                        if needed:
                            total_needed+=1

                        # violation means encryption NEEDED but NOT USED
                        if needed and not used:
                            violating_files.append(file_path)
        
        score = total_used * 100.0/total_needed if total_needed > 0 else 0

        return {
            "method": "full_scan",
            "total_used": total_used,
            "total_needed": total_needed,
            "score": score, # higher the score less is the violation
            "violations:" : len(violating_files),
            "violating_files":violating_files
        }
    
    # ---- LLM Scan ----
    def llm_scan(self, base_path):
        file_paths = []
        for root, _, files in os.walk(base_path):
            for f in files:
                file_paths.append(os.path.join(root, f))

        prompt = f"""
You are a static security analyzer.

From the following list of files, identify which files are MOST LIKELY
to contain passwords, secrets, credentials, auth logic, or tokens.

Return ONLY a raw JSON array of file paths.
No explanation. No markdown.

Files:
{json.dumps(file_paths, indent=2)}
"""

        raw = self.call_llm(prompt)
        predicted_files = self.extract_json_from_text(raw) or []

        total_used = 0
        total_needed = 0
        violating_files = []

        for file_path in predicted_files:
            if not os.path.exists(file_path):
                continue

            with open(file_path, "r", errors="ignore") as fp:
                content = fp.read().lower()

            used = any(re.search(k, content) for k in self.encryption_keywords)
            needed = any(re.search(k, content) for k in self.places_needing_encryption)

            if used:
                total_used += 1
            if needed:
                total_needed += 1
            if needed and not used:
                violating_files.append(file_path)

        score = (total_used * 100.0 / total_needed) if total_needed > 0 else 0

        return {
            "method": "llm_based_heuristic_scan",
            "heuristic_scanned_files": predicted_files,
            "total_used": total_used,
            "total_needed": total_needed,
            "score": score,
            "violations": len(violating_files),
            "violating_files": violating_files
        }