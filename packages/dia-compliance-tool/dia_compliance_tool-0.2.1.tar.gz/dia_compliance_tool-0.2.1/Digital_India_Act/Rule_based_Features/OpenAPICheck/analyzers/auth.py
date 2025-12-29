import re

AUTH_PATTERNS = [
    r"Authorization",
    r"jwt",
    r"oauth",
    r"Bearer\s"
]

def detect_authentication(files: list) -> bool:
    for file in files:
        try:
            content = open(file, encoding="utf-8", errors="ignore").read()
            for pattern in AUTH_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    return True
        except Exception:
            continue
    
    return False