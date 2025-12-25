import re

JSON_HEADERS = re.compile(r"application/json")

def detect_json_usage(files: list) -> bool:
    for file in files:
        try:
            content = open(file, encoding="utf-8", errors="ignore").read()
            if JSON_HEADERS.search(content):
                return True
        except Exception:
            continue
    return False