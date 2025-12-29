import re

HTTP_METHODS = re.compile(r"\b(GET|POST|PUT|DELETE|PATCH)\b")
VERSION_PATTERN = re.compile(r"/(v[0-9]+|api/v[0-9]+)")

def analyze_rest_patterns(files: list) -> dict:
    methods_found = set()
    versioned = False

    for file in files:
        try:
            content = open(file, encoding="utf-8", errors="ignore").read()
            methods_found.update(HTTP_METHODS.findall(content))
            if VERSION_PATTERN.search(content):
                versioned = True
        except Exception:
            continue

    return {
        "methods_used": list(methods_found),
        "versioning": versioned
    }