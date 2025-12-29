from bs4 import BeautifulSoup
from io import BytesIO
import pdfminer.high_level
import re
from typing import Tuple
import trafilatura


def extract_text(content_type: str, content: bytes) -> Tuple[str, str]:
    """
    Returns the source of the policy found and the extracted text from the policy found using the above heuristic ways
    Uses Trafilatura for HTML and a lightweight fallback for PDFs.
    """
    raw_text = ""

    content_type = (content_type or "").lower()

    # Extract content from HTML 
    if "html" in content_type or "text" in content_type:
        html = content.decode("utf-8", errors="ignore")

        extracted_txt = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            no_fallback=True,   # this avoids extracting unnecessary noise
        )

        if extracted_txt:
            raw_text = extracted_txt
        else:
            raw_text = trafilatura.extract(html, include_comments=False) or ""

    elif "pdf" in content_type:
        try:
            raw_text = pdfminer.high_level.extract_text(content)
        except Exception:
            raw_text = ""
    else:
        raw_text = ""
    
    MAX_CHARS = 2_000_000   # impose text limit to 2MB

    if len(raw_text) > MAX_CHARS:
        raw_text = raw_text[:MAX_CHARS]

    return ("text/plain", raw_text)
    


    
