from .models import EvaluationResult

def evaluate(url: str, rule_results:dict, llm_results:dict) -> EvaluationResult:
    rule_score = sum(rule_results.values()) / len(rule_results)
    llm_score = sum(v["score"] for v in llm_results.values()) / len(llm_results)

    final_score = round((0.6*rule_score) + (0.4*llm_score),2)

    if final_score >= 0.8:
        status, risk = "compliant", "low"
    elif final_score >= 0.5:
        status, risk = "partially_compliant", "medium"
    else:
        status, risk = "non_compliant", "high"

    return EvaluationResult(
        url=url,
        final_score=final_score,
        overall_status=status,
        risk_level=risk,
        rule_findings=rule_results,
        llm_findings=llm_results
    )