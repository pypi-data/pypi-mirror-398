import requests
from urllib.parse import urljoin, urlparse
from typing import Tuple, Optional
import time

HEADERS = {"User-Agent": "DIA-PrivacyPolicy-Checker/1.0"}

class FetchError(Exception):
    pass

class policy_page_fetcher:
    """ This class is responsible for fetching arbitraty URLs. Performs retries, timeouts and content-detection in this class so 
    that higher-level modules can remain simple and testable."""

    def __init__(self, timeout: int=8, max_retries: int=2, backoff:float=0.5):
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff = backoff
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def fetch(self, url:str) -> Tuple[str, bytes]:
        """ This method fetches a URL and returns a tuple of content type and content bytes. 
        This method raises a FetchError or unrecoverable errors.
        """
        parsedURL = urlparse(url)
        if parsedURL.scheme not in ("http", "https"):
            raise FetchError(f"Unsupported URL scheme:{url}")
        
        last_exec = None
        for attempt in range(self.max_retries+1):
            try:
                response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "").lower()
                return content_type, response.content
            except requests.exceptions.RequestException as exec:
                last_exec = exec

                time.sleep(self.backoff * (1 + attempt))
                continue

        raise FetchError(f"Failed to fetch {url}: {last_exec}")
    
    def normalize_url(base:str, href:str) -> str:
        return urljoin(base, href)
    

    