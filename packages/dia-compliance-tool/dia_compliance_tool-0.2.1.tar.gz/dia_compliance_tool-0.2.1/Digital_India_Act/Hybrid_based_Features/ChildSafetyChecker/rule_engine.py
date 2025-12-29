import re
from .models import ScrapedData

def run_rule_checks(data: ScrapedData) -> dict:
    ui_text = (
        data.visible_text + 
        " ".join(data.inputs) +
        " ".join(data.buttons) +
        " ".join(data.modals)
    ).lower()

    policy = data.policy_text.lower()

    return {
        "age_gate_present": bool(re.search(r"dob|date of birth|age|above\s*18|under\s*18", ui_text)),
        "minimum_age_declared": bool(re.search(r"minimum age|at least\s*\d+", policy)),
        "child_policy_section": bool(re.search(r"children|minors|child safety", policy)),
        "parental_consent": bool(re.search(r"parental consent|guardian approval", policy)),
        "child_reporting_mechanism": bool(re.search(r"report.*child|child abuse|minor safety", policy))
    }