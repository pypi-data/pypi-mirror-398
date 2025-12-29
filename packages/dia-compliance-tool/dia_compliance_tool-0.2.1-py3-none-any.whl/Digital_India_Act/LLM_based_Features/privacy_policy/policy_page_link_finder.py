from bs4 import BeautifulSoup
from urllib.parse import urlparse,urljoin
from typing import List
import re

# Heuristically search for the privacy policy at most probable url endpoints

COMMON_PATHS = [
    "/privacy", "/privacy-policy", "/privacy_policy", "/legal/privacy",
    "/legal/privacy-policy", "/cookie-policy", "/policies/privacy", "/policy"
]

PRIVACY_KEYWORDS = ("privacy", "cookie", "data-protection", "data protection", "policy", "legal")


def find_candidate_links(html_bytes:bytes, base_url:str) -> List[str]:
    """
    This function is responsible for returning a tuple of urls possibly 
    containing the privacy policy.
    Strategy followed:
    1. Search at anchors with privacy-like text/href
    2. rel="canonical" or meta links
    3. guess common paths and follow a heuristic way
    """

    try:
        html = html_bytes.decode("utf-8", errors="ignore")
    except Exception:
        html = html_bytes.decode("latin-1", errors="ignore")

    soup = BeautifulSoup(html, "html.parser")
    candidates = []

    for a in soup.find_all("a", href=True):
        text = (a.get_text() or "").lower()
        href = a["href"]
        href_low = href.lower()

        # If the anchor text or href contains a privacy-related keyword
        if any(k in text for k in PRIVACY_KEYWORDS) or any(k in href_low for k in PRIVACY_KEYWORDS):
            candidates.append(urljoin(base_url, href))

    link_tags = soup.find_all("link", href=True)
    for l in link_tags:
        rel = (l.get("rel") or [])
        href = l.get("href")

        if href and ("privacy" in href.lower() or "policy" in href.lower()):
            candidates.append(urljoin(base_url, href))

    if not candidates:
        root = base_url.rstrip("/")
        for p in COMMON_PATHS:
            candidates.append(urljoin(root+"/", p.lstrip("/")))

    
    seen = set()
    out = []
    for u in candidates:
        if u not in seen:
            seen.add(u)
            out.append(u)

    return out
