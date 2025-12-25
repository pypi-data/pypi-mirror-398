import os
import re
import pandas as pd
import numpy as np
from groq import Groq
from dotenv import load_dotenv

# ==========================================================
# 1. DISCOVERY ENGINE (The "Detective")
# ==========================================================
class DiscoveryEngine:
    """Infers the purpose and risks of code when metadata is missing."""
    
    @staticmethod
    def extract_features_from_code(code_snippet):
        # Look for list definitions or dataframe column assignments
        feature_pattern = r"\[['\"](.+?)['\"]\]"
        found_features = list(set(re.findall(feature_pattern, code_snippet)))
        
        # Risk Mapping for India-specific context
        risk_map = {
            "pincode": "Proxy for Caste/Socio-economic status (Redlining)",
            "phone": "Proxy for Wealth (Digital Divide)",
            "gender": "Protected Class (Direct Discrimination)",
            "marital": "Proxy for Gender/Age bias",
            "religion": "Protected Class (Direct Discrimination)",
            "age": "Protected Class (Ageism)"
        }
        
        detected_risks = {f: risk_map[f.lower()] for f in found_features if f.lower() in risk_map}
        return found_features, detected_risks

# ==========================================================
# 2. SYNTHETIC STRESS TESTER
# ==========================================================
class StressTester:
    """Generates synthetic data to 'stress test' inferred models."""
    
    @staticmethod
    def generate_shadow_data(features, n_samples=100):
        data = {}
        for feat in features:
            f_low = feat.lower()
            if 'age' in f_low:
                data[feat] = np.random.randint(18, 70, n_samples)
            elif 'pincode' in f_low:
                # Simulating a bias: 90% Tier-1, 10% Rural
                data[feat] = np.random.choice(['110001', '400001', ' rural_001'], n_samples, p=[0.45, 0.45, 0.1])
            elif 'gender' in f_low:
                data[feat] = np.random.choice(['Male', 'Female'], n_samples, p=[0.7, 0.3])
            else:
                data[feat] = np.random.rand(n_samples) * 1000 # Default numerical
        return pd.DataFrame(data)

# ==========================================================
# 3. CORE AUDIT CONTROLLER
# ==========================================

def run_autonomous_audit(user_code):
    load_dotenv()
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    # --- PHASE 1: CODE DISCOVERY ---
    discovery = DiscoveryEngine()
    features, risks = discovery.extract_features_from_code(user_code)
    
    # --- PHASE 2: SYNTHETIC PROBING ---
    stress_tester = StressTester()
    shadow_df = stress_tester.generate_shadow_data(features)
    
    # Summary for the LLM
    discovery_summary = f"""
    DETECTED FEATURES: {features}
    IDENTIFIED PROXY RISKS: {risks}
    DATA DISTRIBUTION (SYNTHETIC):
    {shadow_df.describe(include='all').to_string()}
    """

    # --- PHASE 3: ETHICAL REASONING (The Auditor) ---
    system_prompt = (
        "You are the Lead Auditor for the Digital India AI Ethics Committee. "
        "Analyze the following code-inferred data against the AI Bill 2025."
        "\n\nTASKS:\n"
        "1. Identify 'Invisible Bias'—how features like Pincode or Phone Model create exclusion in India.\n"
        "2. Evaluate the 'Shadow Data' distribution for representation gaps.\n"
        "3. Provide a Technical Compliance Verdict.\n"
        "\nFORMAT: [VERDICT: PASS/FAIL], [RISK SCORE 1-10], [VIOLATIONS], [REQUIRED FIXES]."
    )

    try:
        print("... Infiltrating Code Logic & Generating Stress Tests ...")
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": discovery_summary}],
            temperature=0.1
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Audit Execution Error: {str(e)}"

def run_advance_fairness_detect(raw_untrusted_code: str):
    
    final_report = run_autonomous_audit(raw_untrusted_code)
    
    print("\n" + "═"*60)
    print("      ZERO-KNOWLEDGE AI ETHICS AUDIT (INDIA 2025)      ")
    print("═"*60 + "\n")
    print(final_report)
# ==========================================================
# 4. EXECUTION EXAMPLE
# ==========================================================
if __name__ == "__main__":
    # The user provides ONLY code. No data summary, no documentation.
    run_advance_fairness_detect()