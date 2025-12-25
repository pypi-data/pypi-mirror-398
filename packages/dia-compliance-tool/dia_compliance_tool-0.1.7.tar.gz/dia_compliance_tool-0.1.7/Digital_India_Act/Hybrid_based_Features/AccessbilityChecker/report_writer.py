import json
from .models import AccessbilityReport

def write_report(report: AccessbilityReport, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=4)