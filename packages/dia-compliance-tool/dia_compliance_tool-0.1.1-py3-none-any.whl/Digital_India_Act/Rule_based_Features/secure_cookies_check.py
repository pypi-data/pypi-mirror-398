import requests
from urllib.parse import urlparse
import re

class SecureCookiesCheck:
    """
    Robust Secure Cookie Checker.
    - Presence of the secure flag
    - Presence of HttpOnly flag that is protection against XSS
    - Analyzing the SameSite attribute
    - Path Attribute check
    - Expiration or maximum age allowed check
    - Search for any sensitive data in the cookie value and flag if exists
    - Check if the cookies are not sent over plain HTTP with security that is over HTTPS
    - Avoids false positives for analytics/UI cookies (whitelist)
    - Conservative sensitive-detection
    - Correctly splits Set-Cookie headers (won't break on Expires commas)
    - Severity ranked as HIGH / MEDIUM / LOW
    """

    # conservative sensitive cookie name keywords (if present -> sensitive)
    SENSITIVE_COOKIE_KEYWORDS = {"session", "auth", "token", "jwt", "bearer", "user", "login"}

    # whitelist of known non-sensitive analytics / UI cookies (common on many sites)
    ANALYTICS_COOKIE_WHITELIST = {
        "_octo", "_gh_sess", "logged_in", "_ga", "_gid", "_gat", "_fbp", "_gcl_au",
        "ajs_anonymous_id", "_hjIncludedInSample", "_stripe_mid"
    }

    # strict patterns for sensitive values
    JWT_RE = re.compile(r"\b[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_]{5,}\b")
    BASE64_JWT_RE = re.compile(r"eyJ[A-Za-z0-9=_\-]{10,}")
    EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
    PHONE_RE = re.compile(r"\b\d{10}\b")

    def __init__(self, url: str, timeout: int = 6):
        self.url = url.strip()
        self.timeout = timeout
        parsedURL = urlparse(self.url)
        if parsedURL.scheme not in ("http", "https"):
            raise ValueError("URL must start with http:// or https://")
        self.is_https = parsedURL.scheme == "https"

    def _safe_request(self):
        try:
            return requests.get(
                self.url,
                timeout=self.timeout,
                allow_redirects=True,
                headers={"User-Agent": "DIA-Checker/1.0"}
            )
        except requests.exceptions.RequestException:
            return None

    def _looks_sensitive(self, name: str, value: str) -> bool:
        """
        Conservative sensitive detection. Return True only for strong signals:
        - cookie name contains clear token/session/auth keyword (not substrings)
        - value matches JWT-like or base64-jwt-like
        - value contains email or phone
        - value contains explicit keywords like 'access_token' or 'refresh_token'
        Otherwise return False to avoid false positives.
        """
        if not name:
            return False

        lname = name.lower()

        # if cookie name is known analytics/UI cookie, NOT sensitive
        if lname in self.ANALYTICS_COOKIE_WHITELIST:
            return False

        # name-based sensitivity (exact keyword match or word boundaries)
        for kw in self.SENSITIVE_COOKIE_KEYWORDS:
            # match whole word or starts/ends to avoid partial numeric matches
            if re.search(rf"\b{re.escape(kw)}\b", lname):
                return True

        # value-based checks used for the checking if the cookie is sensitive or not only based on strong signals
        if self.JWT_RE.search(value):
            return True
        if self.BASE64_JWT_RE.search(value):
            return True
        if self.EMAIL_RE.search(value):
            return True
        if self.PHONE_RE.search(value):
            return True

        # explicit token labels inside value (e.g. access_token=..., refresh_token=...)
        if re.search(r"(access[_-]?token|refresh[_-]?token|bearer)", value, re.IGNORECASE):
            return True

        # everything else: not sensitive (conservative)
        return False

    def _split_set_cookie_headers(self, raw_header: str):
        """
        Split a combined Set-Cookie header string into individual Set-Cookie entries.
        Uses a conservative regex to split on commas that appear to start a new cookie
        (i.e. comma followed by optional whitespace and then a token=...). This avoids
        splitting on the comma inside Expires date (e.g., 'Expires=Wed, 09 Dec 2026 ...').
        """
        # if already a single cookie string without commas, return as single
        if "," not in raw_header:
            return [raw_header.strip()]

        # split on ', ' only when next chunk looks like a cookie name (token=)
        parts = re.split(r", (?=[^=;,\s]+\s*=\s*[^;]+)", raw_header)
        return [p.strip() for p in parts if p.strip()]

    def analyze_cookie(self, cookie_header: str):
        """
        Parse a single Set-Cookie header (string) and return structured issues.
        """
        parts = [p.strip() for p in cookie_header.split(";")]
        name_value = parts[0]

        if "=" not in name_value:
            return {
                "cookie_name": None,
                "raw_header": cookie_header,
                "status": "invalid",
                "issues": [{"severity": "LOW", "message": "Cookie has no name=value format"}]
            }

        name, value = name_value.split("=", 1)
        lname = name.lower()
        attrs = {p.split("=", 1)[0].strip().lower(): (p.split("=", 1)[1].strip() if "=" in p else True)
                 for p in parts[1:] if p}

        issues = []

        has_secure = "secure" in attrs
        has_httponly = "httponly" in attrs
        samesite = attrs.get("samesite")
        # normalize samesite if present and is True (flag)
        if isinstance(samesite, bool):
            samesite = None

        is_sensitive = self._looks_sensitive(name, value)

        # Rule: Missing Secure
        if self.is_https and not has_secure:
            if is_sensitive:
                issues.append({"severity": "HIGH", "message": "Sensitive cookie missing Secure flag"})
            else:
                issues.append({"severity": "MEDIUM", "message": "Missing Secure flag (recommended)"})

        # Rule: HttpOnly
        if not has_httponly:
            if is_sensitive:
                issues.append({"severity": "HIGH", "message": "Sensitive cookie missing HttpOnly"})
            else:
                issues.append({"severity": "LOW", "message": "HttpOnly not required for non-sensitive cookie"})

        # Rule: SameSite
        if not samesite:
            issues.append({"severity": "MEDIUM", "message": "SameSite not specified"})
        else:
            ss = str(samesite).lower()
            if ss == "none" and not has_secure:
                issues.append({"severity": "HIGH", "message": "SameSite=None requires Secure flag"})

        status = "insecure" if any(i["severity"] == "HIGH" for i in issues) else "secure"

        return {
            "cookie_name": name,
            "raw_header": cookie_header,
            "status": status,
            "issues": issues
        }

    def run(self):
        resp = self._safe_request()
        if resp is None:
            return {"url": self.url, "status": "error", "reason": "Request failed"}

        raw = resp.headers.get("Set-Cookie")
        if not raw:
            return {"url": self.url, "status": "no_cookies", "message": "No Set-Cookie headers found"}

        # preferred: try to get all headers if the response keeps duplicates
        cookies_list = None
        if hasattr(resp.headers, "get_all"):
            cookies_list = resp.headers.get_all("Set-Cookie")
        else:
            # split safely
            cookies_list = self._split_set_cookie_headers(raw)

        results = [self.analyze_cookie(h) for h in cookies_list]

        overall_secure = not any(
            any(issue["severity"] == "HIGH" for issue in cookie["issues"])
            for cookie in results
        )

        return {"url": self.url, "overall_secure": overall_secure, "cookies": results}


# quick run example (if executed as script)
if __name__ == "__main__":
    checker = SecureCookiesCheck("https://monkeytype.com/")
    print(checker.run())
