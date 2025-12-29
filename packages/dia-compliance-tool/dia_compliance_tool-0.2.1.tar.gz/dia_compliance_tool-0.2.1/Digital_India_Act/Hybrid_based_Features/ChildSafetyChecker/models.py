from dataclasses import dataclass
from typing import Dict, List

@dataclass
class ScrapedData:
    visible_text: str
    inputs: List[str]
    buttons: List[str]
    modals: List[str]
    policy_text: str

@dataclass
class EvaluationResult:
    url: str
    final_score: float
    overall_status: str
    risk_level: str
    rule_findings: Dict[str, bool]
    llm_findings: Dict[str, Dict]