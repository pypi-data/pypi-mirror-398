from Digital_India_Act import run_basic_fairness_detect

DATASET_SUMMARY = {
    "name": "Bharat-Lending-AI-V1",
    "metrics": {
        "gender_ratio": {"Male": 0.78, "Female": 0.21},
        "geo_split": {"Tier-1": 0.88, "Rural": 0.02},
        "approval_rates": {"Male": 0.65, "Female": 0.42} # Synthetic data for audit
    },
    "features": ["Annual Income", "Residential Pincode", "Smartphone Model"]
}
def main():
    run_basic_fairness_detect(DATASET_SUMMARY)

if __name__ == "__main__":
    main()