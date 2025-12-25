from .policy_page_fetcher import FetchError, policy_page_fetcher
from .policy_page_link_finder import find_candidate_links
from .policy_extractor import extract_text
from .long_policy_chunker import chunk_text
from .llm_analyzer import analyze_policy_chunks
from typing import Optional
import logging

logger = logging.getLogger("privacy_checker")

class PrivacyPolicyChecker:
    def __init__(self, fetcher: Optional[policy_page_fetcher] = None):
        self.fetcher = fetcher or policy_page_fetcher()

    
    def find_policy_url(self, homepage_url:str) -> Optional[str]:
        try:
            content_type, content = self.fetcher.fetch(homepage_url)

        except FetchError:
            return None
        candidates = find_candidate_links(content, homepage_url)

        for c in candidates:
            try:
                ct, _ = self.fetcher.fetch(c)
                return c
            except FetchError:
                continue

        return None
    
    def run_check(self, homepage_url: str) -> dict:
        result = {
            "input_url": homepage_url,
            "policy_found": False,
            "policy_url": None,
            "checks": {},
            "overall_score": 0,
            "confidence": 0.0,
            "human_review_recommended": False,
            "extracted_text_snippet": ""
        }

        policy_url = self.find_policy_url(homepage_url)
        print(f"Debugging: Found the policy url:{policy_url}")
        content = None
        content_type = None
        if not policy_url:
            
            candidates = [homepage_url.rstrip("/") + p for p in ("/privacy", "/privacy-policy")]
            found = None
            for c in candidates:
                try:
                    ct, content = self.fetcher.fetch(c)
                    found = (c,ct,content)
                    break
                except FetchError:
                    continue
            if not found:
                result["policy_found"] = False
                result["checks"] = {k:{"status":"MISSING", "explanation": "Policy page not found"} for k in analyze_policy_chunks([]).keys()}
                result["overall_score"] = 0
                result["human_review_recommended"] = True
                return result
            else:
                policy_url, content_type, content = found

                
        else:
            try:
                content_type, content = self.fetcher.fetch(policy_url)

            except FetchError:
                result["policy_found"] = False
                result["checks"] = {k: {"status": "MISSING", "explanation": "Policy URL unreachable"} for k in analyze_policy_chunks([]).keys()}
                result['overall_score'] = 0
                result['human_review_recommended'] = True
                return result
            
        result['policy_found'] = True
        result['policy_url'] = policy_url

        _type, text = extract_text(content_type, content)

        if not text or len(text.strip()) < 50:
            result['checks'] = {k: {"status": "MISSING", "explanation": "Policy content not extractable"} for k in analyze_policy_chunks([]).keys()}
            result['overall_score'] = 0
            result['human_review_recommended'] = True
            return result
        
        print(f"Debugging:  Found the text. Now going to chunk this down...(Size of the found text: {len(text)})")
        with open("policy_text.txt", "w", encoding="utf-8") as f:
            f.write(text)
        chunks = chunk_text(text, max_words=700, overlap=80)
        print("Debugging: Done with chunking the policy. Now initiating the analysis...")

        analysis = analyze_policy_chunks(chunks)
        print("Analysis returned. Now building the results...")

        result['checks'] = analysis

        total = len(analysis)
        passes = sum(1 for v in analysis.values() if v['status'] == "PASS")
        score = int((passes/total) * 100) if total else 0
        result['overall_score'] = score

        unclear = sum(1 for v in analysis.values() if v['status'] == "UNCLEAR")
        result['confidence'] = round(max(0.2, 1- (unclear / total if total else 1)),2)
        result['human_review_recommended'] = any(v['status'] != "PASS" for v in analysis.values()) or result["confidence"] < 0.7
        result['extracted_text_snippet'] = text[:3000]

        print("THERE YOU GO!!!")
        return result
        