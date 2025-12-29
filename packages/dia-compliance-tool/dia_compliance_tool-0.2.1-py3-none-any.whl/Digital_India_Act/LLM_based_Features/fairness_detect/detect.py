import os
import pandas as pd
import numpy as np
from groq import Groq
from dotenv import load_dotenv

# ==========================================================
# 1. ADVANCED FAIRNESS ENGINE (Next-Level Detection)
# ==========================================================
class BiasDetectionEngine:
    """
    Simulates quantitative fairness checks (Disparate Impact, Proxy Analysis)
    that modern regulators require alongside qualitative reports.
    """
    @staticmethod
    def calculate_disparate_impact(selection_rate_group_a, selection_rate_group_b):
        """The 4/5th Rule: Ratio of selection rates should be > 0.8"""
        ratio = min(selection_rate_group_a, selection_rate_group_b) / max(selection_rate_group_a, selection_rate_group_b)
        status = "PASS" if ratio >= 0.8 else "FAIL"
        return ratio, status

    @staticmethod
    def detect_proxy_risk(features):
        """Checks if features like 'Pincode' or 'Smartphone' act as proxies for protected classes."""
        proxies = {
            "Pincode": "High Risk: Likely proxy for Caste/Socio-economic status (Redlining).",
            "Smartphone Model": "Medium Risk: Proxy for Wealth/Disposable Income (Digital Divide)."
        }
        found = [v for k, v in proxies.items() if k in features]
        return found

# ==========================================================
# 2. CONFIGURATION & SAMPLE DATA
# ==========================================
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "llama-3.3-70b-versatile"

DATASET_SUMMARY = {
    "name": "Bharat-Lending-AI-V1",
    "metrics": {
        "gender_ratio": {"Male": 0.78, "Female": 0.21},
        "geo_split": {"Tier-1": 0.88, "Rural": 0.02},
        "approval_rates": {"Male": 0.65, "Female": 0.42} # Synthetic data for audit
    },
    "features": ["Annual Income", "Residential Pincode", "Smartphone Model"]
}

# ==========================================================
# 3. IMPROVISED AUDIT ENGINE
# ==========================================================
def run_compliance_audit(data_summary):
    if not API_KEY:
        return "ERROR: API Key not found."

    # --- STEP 1: QUANTITATIVE ANALYSIS ---
    bias_engine = BiasDetectionEngine()
    
    # Calculate Disparate Impact (Ratio of approval rates)
    di_ratio, di_status = bias_engine.calculate_disparate_impact(
        data_summary["metrics"]["approval_rates"]["Male"],
        data_summary["metrics"]["approval_rates"]["Female"]
    )
    
    proxy_warnings = bias_engine.detect_proxy_risk(data_summary["features"])

    # --- STEP 2: LLM POLICY REASONING ---
    client = Groq(api_key=API_KEY)
    
    system_prompt = (
        "You are the Lead Auditor for the Digital India AI Ethics Committee. "
        "Analyze the provided Quantitative Bias Data and Model Specs against the AI Bill 2025."
        "\n\nFOCUS AREAS:\n"
        f"1. DISPARATE IMPACT: The calculated ratio is {di_ratio:.2f} ({di_status}).\n"
        "2. PROXY REDLINING: Analyze if 'Pincode' is being used to bypass Caste/Religion protections.\n"
        "3. EXCLUSION: Evaluate the impact of 88% Tier-1 data on India's 'Inclusion' mandate.\n"
        "Provide a technical report: [RISK SCORE 1-10], [VIOLATIONS], [MANDATORY RECTIFICATION]."
    )

    user_input = f"""
    Dataset: {data_summary['name']}
    Detected Proxies: {proxy_warnings}
    Demographics: {data_summary['metrics']['gender_ratio']}
    Geographic Split: {data_summary['metrics']['geo_split']}
    """

    try:
        print(f"... Analyzing {data_summary['name']} for Compliance & Bias ...")
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_input}],
            temperature=0.1
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Audit Failure: {str(e)}"
def run_basic_fairness_detect(dataset_summary: dict):
    report = run_compliance_audit(dataset_summary)
    
    print("\n" + "═"*60)
    print("      OFFICIAL AI COMPLIANCE REPORT (INDIA 2025)     ")
    print("═"*60 + "\n")
    print(report)
    
    # Save as Markdown
    with open("enhanced_compliance_report.md", "w") as f:
        f.write(report)
# ==========================================================
# 4. EXECUTION
# ==========================================================
if __name__ == "__main__":
    run_basic_fairness_detect()