from Digital_India_Act import DataMinimizationChecker
import json

def main():
    checker = DataMinimizationChecker()

    frontend_path1 = "./test_datamin_frontend1"
    backend_path1 = "./test_datamin_backend1"
    frontend_path2 ="./test_datamin_frontend2"
    backend_path2 = "./test_datamin_backend2"
    print("Rule based check for frontend1 and backend1:")
    result1 = checker.run(backend_path=backend_path1,frontend_path=frontend_path1,backend_mode="rule")
    print(json.dumps(result1, indent=2))
    print("-------------------------------------")
    print("LLM based check for frontend2 and backend2")
    result2 = checker.run(backend_path=backend_path2,frontend_path=frontend_path2,backend_mode="llm")
    print(json.dumps(result2, indent=2))

if __name__=="__main__":
    main()


"""
Rule based check for frontend1 and backend1:
{
  "frontend_collected_fields": [
    "age",
    "email",
    "phone"
  ],
  "backend_analysis_mode": "rule",
  "backend_result": {
    "field_usage": {
      "phone": [
        "api"
      ],
      "email": [
        "db"
      ],
      "age": [
        "logs"
      ]
    },
    "unused_fields": [],
    "over_shared_fields": {
      "db": [
        "email"
      ],
      "api": [
        "phone"
      ],
      "logs": [
        "age"
      ]
    }
  },
  "severity": "medium",
  "recommendation": "Remove unnecessary fields and avoid forwarding personal data unless strictly required for business purposes."
}
-------------------------------------
LLM based check for frontend2 and backend2
{
  "frontend_collected_fields": [
    "email",
    "password"
  ],
  "backend_analysis_mode": "llm",
  "backend_result": {
    "method": "llm_based",
    "llm_provider": "groq",
    "analysis": {
      "field_analysis": {
        "email": {
          "necessity": "required",
          "backend_usage": [
            "unknown"
          ],
          "justification": "Email is necessary for user authentication"
        },
        "password": {
          "necessity": "required",
          "backend_usage": [
            "unknown"
          ],
          "justification": "Password is necessary for user authentication"
        }
      },
      "over_sharing_detected": [],
      "unused_or_excessive_fields": [],
      "overall_compliance_risk": "LOW",
      "summary": "The backend code appears to be compliant with data minimization principles as it only uses the collected fields for authentication purposes." 
    },
    "note": "Semantic analysis based on backend behavior and data minimization principles"
  },
  "severity": "low",
  "recommendation": "Data minimization principles are followed."
}
"""