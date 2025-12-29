from .rule_engine import RuleBasedAccessbilityChecker
from .llm_engine import SemanticAccessibilityChecker_LLM
from .groq_client import GroqLLMClient
from .report_writer import write_report
from .models import AccessbilityReport


def run_accessbility_check(urls):
    if isinstance(urls, str):
        urls = [urls]

    results = []

    llm_client = GroqLLMClient(
        model="llama-3.3-70b-versatile"
    )

    for url in urls:
        rule_checker = RuleBasedAccessbilityChecker(url)
        semantic_checker = SemanticAccessibilityChecker_LLM(url, llm_client)

        rule_violations = rule_checker.run()
        semantic_findings = semantic_checker.run()

        status = "PASS"
        if rule_violations:
            status = "FAIL"
        elif semantic_findings:
            status = "PARTIAL"

        report = AccessbilityReport(
            url=url,
            rule_based_violations=rule_violations,
            semantic_findings=semantic_findings,
            overall_status=status
        )

        write_report(report, "accessbility_report.json")

        results.append({
            "url": url,
            "overall_status": status,
            "rule_violation_count": len(rule_violations),
            "semantic_issue_count": len(semantic_findings),
            "rule_violations": [
                {
                    "description": v.description,
                    "impact": v.impact,
                    "wcag": v.wcag
                }
                for v in rule_violations
            ],
            "semantic_findings": [
                {
                    "component": s.component,
                    "issue": s.issue,
                    "severity": s.severity
                }
                for s in semantic_findings
            ]
        })

    return results
