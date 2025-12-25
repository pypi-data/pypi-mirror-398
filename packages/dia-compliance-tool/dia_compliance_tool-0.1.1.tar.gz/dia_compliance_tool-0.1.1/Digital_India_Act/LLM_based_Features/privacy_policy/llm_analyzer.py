import os
import json
from typing import List, Dict, Any
import time
import re
from Digital_India_Act.config import get_api_key

LLM_BACKEND = "groq"
GROQ_API_KEY = get_api_key("GROQ_API_KEY")

CHECKS_PRIVACY_POLICY  = {
    "data_usage": "Does the policy state clearly if the personal data is collected and what is that data and how is it used?",
    "rentention": "Does the policy state data retention periods and explain how long the data is being stored?",
    "deletion": "Does the policy explain how a user can delete their data or request deletion?",
    "third_party": "Does the policy explain about the data being shared with third parties or processors?",
    "cookies": "Does the software describe about cookies and tracking technologies and how users are can select or opt out using cookies?",
    "data_export": "Does it discuss the ability of the user to export the data or obtain a copy of it?",
    "ai_disclosure": "Does it mention anything about the usage of AI-generated content or automated decision making?",
    "minors": "Does it mention minors or age-based protections?"
}

# Utility function to extract JSON

def extract_json_from_text(text: str):
    """
    Extract the JSON from LLM output
    """

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None
    
    try:
        return json.loads(match.group(0))
    except:
        return None
    

def call_llm(prompt:str, max_tokens:int=512, timeout:int=20) -> str:
    """
    Minimal wrapper for calling the LLM. Can be made even more efficient embedding the following such as
    retries, metrics, error handling for rate limits or provider-specific optimization.
    """

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
                messages=[{"role":"user", "content":prompt}],
                    max_tokens=max_tokens,
                    temperature=0,
                )
                return response.choices[0].message.content
            except Exception as e:
                if attempt == retries - 1:
                    raise
                time.sleep(1)
    else:
        raise RuntimeError(f"Unsupported LLM backed: {LLM_BACKEND}")
    

def analyze_chunk_for_check(chunk: str, check_key: str) -> Dict[str, Any]:
    prompt = f"""
You are a policy compliance assistant. Answer the question concisely in JSON.
Question: {CHECKS_PRIVACY_POLICY[check_key]}

Return JSON exactly in the following format:
{{"answer":"yes|no|unclear", "reason":"one-sentence explanation", "evidence":"one short snippet from the text if present"}}

Text:
\"\"\"{chunk}\"\"\"
"""
    raw = call_llm(prompt)
    
    parsed_LLM_op = extract_json_from_text(raw)
    if parsed_LLM_op:
        return parsed_LLM_op
    
    return {
        "answer": "unclear",
        "reason": "Model retured unclear output.",
        "evidence": raw[:200]
    }

    

def analyze_policy_chunks(chunks: List[str], max_chunks_per_check: int=6) -> Dict[str,Any]:
    """
    For each check, iterate a few chunks and if we found an yes in the LLM reply then we can stop
    Then return a dictionary {check_key:{status, evidence_list, explanation}}
    """
    results = {}
    for key in CHECKS_PRIVACY_POLICY.keys():
        answers = []
        for i, ch in enumerate(chunks[:max_chunks_per_check]):
            output = analyze_chunk_for_check(ch,key)
            answers.append({"chunk_id":i, **output})
            if output.get("answer") == "yes":
                break

        yes = any(a["answer"] == "yes" for a in answers)
        no = any(a["answer"] == "no" for a in answers)
        if yes:
            status = "PASS"
        elif no:
            status = "FAIL"
        else:
            status = "UNCLEAR"
        
        results[key] = {
            "status": status,
            "evidence": answers,
            "explanation": answers[0].get("reason") if answers else ""
        }

    return results