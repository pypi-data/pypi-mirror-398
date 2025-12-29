# In this module, we will be scanning the pages of the website taking the input as an URL.
# - Using the regex methodology, we will be scanning through the web pages and then find certain heuristic indicators
# - Then, they will categorized into buckets with the strength given based on their severity
# - In this module, we are just using the url for extracting and analyzing the data. Hence, it won't be a damage performing computations in the backend
# while maintaining the stateless property.
import re
from typing import List, Dict, Any

class AIDisclosureChecker:
    """
    This module is taking the input a public url and analyze all the data that is present in the webpage 
    and analyze the signals of AI content usage. 
    Then, these signals are assigned weights heuristically based on their importance.
    """

    STRONG_AI_PATTERNS = [
        r"\b(ai )?assistant\b",
        r"\bchat (with|to) (an|ai)? assistant\b",
        r"\bask (the )?(ai )?assistant\b",
        r"\bask me anything\b",


        r"\benter (a|your) prompt\b",
        r"\bdescribe what you want\b",

        r"\bsummarize (this|your|the) (text|document|article|content)\b",
        r"\brewrite (this|your|the) (text|content)\b",
        r"\bparaphrase (this|your|the) (text|content)\b",

        r"\bgenerate (an )?image\b",
        r"\bimage generation\b",
        r"\btext[-\s]?to[-\s]?image\b",
        r"\bcreate ai (art|image)\b",

        r"\bai[-\s]?powered (insights|decisions|recommendations)\b",
        r"\bautomated decision (system|making)\b",
        r"\bsmart reply\b",
    ]


    WEAK_AI_PATTERS = [
        r"\brecommended for you\b",
        r"\byou may like\b",
        r"\bsuggested for you\b",
        r"\bbased on your activity\b",
        r"\bfor you\b",
        r"\bdiscover\b",
        r"\btrending\b",
    ]

    # Disclosure Patterns that can be used for checking the presence of disclosure text on the interface

    DISCLOSURE_PATTERNS = [
        r"\bai[-\s]?generated\b",
        r"\bai[-\s]?assisted\b",
        r"\bpowered by ai\b",
        r"\buses ai\b",
        r"\bartificial intelligence\b",
        r"\bmachine learning\b",
        r"\bml[-\s]?based\b",
    ]

    VISIBILITY_WEIGHT = {
        "header": 1.0,
        "modal": 1.0,
        "main": 0.8,
        "footer": 0.4,
        "unknown": 0.5
    }

    def __init__(self, pages: List[Dict[str,Any]]):
        """
        Accepts a list of public pages (web) with extracted visible text.
        Each page must be in the following format:
        {
            "url": str,
            "text": str,
            "section": "header" | "main" | "footer" | "unknown"
        }
        """

        self.pages = [
            {
                **p,
                "text": p["text"].lower()
            } for p in pages
            if p.get("visibility", "visible") == "visible"
        ]


    # Helper functions

    def _match_patterns(self, text:str, patterns:List[str]) -> List[str]:
        return [p for p in patterns if re.search(p,text)]
    
    def _extract_snippets(self, text:str, patterns: List[str]) -> List[str]:
        sentences = re.split(r"[.!?]", text)
        snippets = []

        for s in sentences:
            for p in patterns:
                if re.search(p,s):
                    snippets.append(s.strip())
                    break
        return snippets
    
    def _analyze_page(self, page:Dict[str, Any]) -> Dict[str, Any]:
        strong_hits = self._match_patterns(page["text"], self.STRONG_AI_PATTERNS)
        weak_hits = self._match_patterns(page["text"], self.WEAK_AI_PATTERS)
        disclosure_hits = self._match_patterns(page['text'], self.DISCLOSURE_PATTERNS)

        return {
            "url": page["url"],
            "section": page.get("section", "unknown"),
            "Strong Hits": strong_hits,
            "Weak Hits": weak_hits,
            "Disclosure Hits": disclosure_hits,
        }
    
    def _false_positive_risk(self, strong_pages, disclosure_pages) -> str:
        if not strong_pages:
            return "LOW"
        if strong_pages and not disclosure_pages:
            return "MEDIUM"
        return "LOW"

    def _confidence_score(self, strong_pages, disclosure_pages) -> float:
        score = 0.0

        for p in strong_pages:
            score += 1.0 * self.VISIBILITY_WEIGHT.get(p['section'], 0.5)

        for p in disclosure_pages:
            score += 0.5 * self.VISIBILITY_WEIGHT.get(p['section'], 0.5)

        return round(min(score, 5.0),2)
    
    def run_check(self) -> Dict[str, Any]:
        page_results = [self._analyze_page(p) for p in self.pages]

        strong_pages = [p for p in page_results if p['Strong Hits']]
        weak_pages = [p for p in page_results if p['Weak Hits']]
        disclosure_pages = [p for p in page_results if p["Disclosure Hits"]]

        if not strong_pages:
            status = "NOT_APPLICABLE"
            reason = (
                "No strong AI-indicative User-Interface features detected "
                "across the analyzed public pages using the URL."
            )

        elif strong_pages and disclosure_pages:
            status = "COMPLIANT"
            reason = (
                "AI-indicatove features detected in the User-Interface and "
                "AI disclosure is present on atleast one public page"
            )
        else:
            status = "AT_RISK"
            reason = (
                "AI-Indicative features detected, but there is no explicit "
                "disclousure about the usage of AI is detected on analyzing the public pages"
            )

        confidence_score = self._confidence_score(strong_pages, disclosure_pages)


        return {
            "Check": "AI Disclosure Transparency",
            "status": status,
            "confidence_score": confidence_score,
            "false_positive_risk": self._false_positive_risk(strong_pages, disclosure_pages),
            "reason": reason,
            "summary": {
                "page_analyzed": len(self.pages),
                "pages with strong ai usage signals": len(strong_pages),
                "pages with weak ai usage signals": len(weak_pages),
                "pages with ai disclosure text": len(disclosure_pages),
            },
            "evidence":{
                "strong ai pages": strong_pages,
                "weak ai pages": weak_pages,
                "disclosure pages": disclosure_pages,
            },

            "interpretation": (
                " This is a stateless, public-content-only analysis. "
                "Results indicate potential disclosure risk and do not confirm the actual AI usage. "
                "Backend or documentation review may be required for further verification for the usage of AI."
            ),
        }