from .models import ScrapedData

def run_llm_checks(llm_client, data:ScrapedData) -> dict:
    return {
        "age_appropriate_language": llm_client.complete(
            f"Evaluate age-appropriateness of UI text:\n{data.visible_text[:3000]}"
        ),
        "policy_clarity_for_minors": llm_client.complete(
            f"Evaluate child safety clarity in policy:\n{data.policy_text[:3000]}"
        ),
        "ui_policy_consistency": llm_client.complete(
            f"Check consistency between UI and policy for minors.\n"
            f"UI:\n{data.visible_text[:1500]}\nPOLICY:\n{data.policy_text[:1500]}"
        )
    }