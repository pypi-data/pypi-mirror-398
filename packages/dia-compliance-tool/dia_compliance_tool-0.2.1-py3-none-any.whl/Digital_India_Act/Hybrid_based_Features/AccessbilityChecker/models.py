from pydantic import BaseModel
from typing import List, Optional

class RuleViolation(BaseModel):
    id: str
    description: str
    impact: str
    html: str
    target: List[str]
    wcag: List[str]

class SemanticFinding(BaseModel):
    component: str
    issue: str
    severity: str
    explanation: str

class AccessbilityReport(BaseModel):
    url: str
    rule_based_violations: List[RuleViolation]
    semantic_findings: List[SemanticFinding]
    overall_status: str