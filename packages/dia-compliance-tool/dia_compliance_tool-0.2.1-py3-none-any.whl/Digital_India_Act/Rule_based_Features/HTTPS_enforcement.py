import requests
from urllib.parse import urlparse

class HTTPSEnfocementChecker:
    """
    Docstring for HTTPSEnfocementCheck

    This class checks if the URL has the HTTPS enforced or not. This is done in three levels.
    1. Simple check: If the URL starts with HTTPS
    2. If all the HTTP requests are re-directed to HTTPS
    3. If the header-HSTS is present that is checking the presence of Stric-Transport-Security
    """

    def __init__(self, url:str, timeout: int=5):
        self.url = url.strip()
        self.timeout = timeout

        parsedURL = urlparse(self.url)

        if not parsedURL.scheme:
            raise ValueError("URL must be following the scheme(Must begin with http:// or https://).")
        
        if not parsedURL.netloc:
            raise ValueError("Invalid URL format.")
        
        self.domain = parsedURL.netloc  # extracting the domain present in the URL


    def _safe_request_sender(self, url:str, allow_redirects:bool):
        """Utility function to make network calls safely"""

        try:
            return requests.get(
                url,
                allow_redirects=allow_redirects,
                timeout=self.timeout,
                headers={"User-Agent": "DIA-Compliance-Checker/1.0"}
            )
        except requests.exceptions.RequestException:
            return None
    
    def check_url_with_https(self):
        url_starts_with_https = self.url.lower().startswith("https://")
        return {
            "status": "Supported" if url_starts_with_https else "Not Supported",
            "value": url_starts_with_https,
            "reason": "URL supports HTTPS." if url_starts_with_https else "URL does not being with HTTPS"
        }
    
    def check_http_redirection_to_https(self):
        http_url = f"http://{self.domain}"

        response = self._safe_request_sender(http_url, allow_redirects=False)

        if response is None:
            return {
                "status": "Warning",
                "value": None,
                "reason": "HTTP request failed, site may be blocking HTTP entirely (secure behaviour)."
            }
        
        redirect_status = response.status_code in (301, 302)
        location = response.headers.get("Location", "")

        if redirect_status and location.startswith("https://"):
            return {
                "status": "Supported",
                "value": True,
                "reason": "Re-direction to HTTPS attempted making it HTTPS enforced"
            }
        
        return {
            "status": "Not Supported",
            "value": False,
            "reason": "HTTP URL does not redirect to HTTPS"
        }
    
    def check_hsts_header(self):
        https_url = f"https://{self.domain}"

        response = self._safe_request_sender(https_url, allow_redirects=True)

        if response is None:
            return {
                "status": "Not Supported",
                "value": False,
                "reason": "HTTPS request failed, invalid HTTPS configuration"
            }
        
        hsts = response.headers.get("Strict-Transport-Security")
        if hsts:
            return{
                "status": "Supported",
                "value": True,
                "hsts_value": hsts
            }
        
        return {
            "status": "Not Supported",
            "value": False,
            "reason": "HSTS header is missing"
        }
    
    def run(self):
        """Run all the above defined HTTPS checks and then return the structured result"""
        url_starts_with_https = self.check_url_with_https()
        http_redirects_to_https = self.check_http_redirection_to_https()
        hsts_header_is_present = self.check_hsts_header()

        final_result = (
            url_starts_with_https["status"] == "Supported" and 
            hsts_header_is_present["status"] == "Supported" and 
            http_redirects_to_https["status"] in ("Supported", "Warning")
        )

        return {
            "Input URL": self.url,
            "URL starts with HTTPS": url_starts_with_https,
            "HTTP Re-direction to HTTPS": http_redirects_to_https,
            "HSTS Enabled or not": hsts_header_is_present,
            "Overall HTTPS Enforcement Checking Result": "Complies with the HTTPS Enforcement" if final_result else "Does not comply with the HTTPS Enforcement"
        }
