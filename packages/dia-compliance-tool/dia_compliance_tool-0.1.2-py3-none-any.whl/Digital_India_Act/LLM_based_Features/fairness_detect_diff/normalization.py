# normalization.py

from config import REFUSAL_PATTERNS

def is_refusal(text: str) -> bool:
    lowered = text.lower()
    return any(p in lowered for p in REFUSAL_PATTERNS)


def normalize_output(text: str) -> str:
    """
    Convert all refusals to a canonical form
    to avoid stylistic false positives.
    """
    if is_refusal(text):
        return "REFUSAL: Decision based on protected attribute is not provided."
    return text.strip()
