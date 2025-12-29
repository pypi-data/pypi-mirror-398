import os
import sys
from groq import Groq
from dotenv import load_dotenv

# ==========================================================
# 1. CONFIGURATION
# ==========================================================
# This line looks for a file named .env and loads the variables inside it
load_dotenv()

# Now we pull the key from the environment
API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "llama-3.3-70b-versatile"

# ==========================================================
# 2. SAMPLE DATA
# ==========================================================
DATASET_SUMMARY = """
Project: Bharat-Lending-AI-V1
Demographics: 78% Male, 21% Female. 
Geography: 88% data from Tier-1 metros (Bengaluru, Delhi, Mumbai). 
Rural representation: < 2%.
Features: Annual Income, Residential Pincode, Smartphone Model (iOS/Android).
Language: Data collected via English-only mobile application.
"""

MODEL_DOCS = """
Architecture: XGBoost Classifier for credit eligibility.
Fairness: 'Gender' and 'Caste' features were removed to prevent bias.
Spatial Logic: 'Pincode' is retained to assess regional economic risks.
Economic Indicators: 'Smartphone Model' is used as a proxy for disposable income.
Validation: Tested on a 15% random holdout set. No sub-group analysis for states.
Language: Only processes English inputs.
"""

# ==========================================================
# 3. AUDIT ENGINE
# ==========================================================
def run_compliance_audit(dataset, docs):
    # Error handling if the API key is missing
    if not API_KEY:
        return "ERROR: API Key not found. Ensure your .env file has GROQ_API_KEY=your_key_here"

    client = Groq(api_key=API_KEY)
    
    system_prompt = (
        "You are a Senior Compliance Officer for the Digital India AI Ethics Committee. "
        "Audit the following AI system against the AI (Ethics and Accountability) Bill, 2025. "
        "\n\nCRITICAL CHECKLIST:\n"
        "1. ALGORITHMIC BIAS: Identify if removing labels (Gender/Caste) is insufficient due to proxy variables (Pincode/Smartphone).\n"
        "2. GEOGRAPHIC EXCLUSION: Flag lack of rural/Tier-2 data as a violation of 'Inclusion' mandates.\n"
        "3. LINGUISTIC BARRIERS: Note if English-only systems create a 'Digital Divide' in the Indian context.\n"
        "4. LEGAL CONSEQUENCES: Mention that non-compliance can lead to penalties up to ₹5 Crore.\n\n"
        "Provide a formal report in Markdown with: [STATUS], [VIOLATIONS], and [REQUIRED REMEDIATION]."
    )

    user_prompt = f"### DATASET SUMMARY\n{dataset}\n\n### MODEL DOCUMENTATION\n{docs}"

    try:
        print("... Analyzing compliance via Groq ...")
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error executing audit: {str(e)}"

# ==========================================================
# 4. EXECUTION
# ==========================================================
if __name__ == "__main__":
    print("=== AI FAIRNESS & BIAS COMPLIANCE CHECK (INDIA 2025) ===")
    
    report = run_compliance_audit(DATASET_SUMMARY, MODEL_DOCS)
    
    print("\n" + "="*50)
    print(report)
    print("="*50)
    
    with open("compliance_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("\nAudit complete. Detailed report saved to 'compliance_report.md'")