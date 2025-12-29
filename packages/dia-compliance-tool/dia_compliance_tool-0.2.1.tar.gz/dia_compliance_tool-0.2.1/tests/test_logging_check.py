from Digital_India_Act import LoggingChecker
import json

def main():
    checker = LoggingChecker()
    result = checker.run("test_repo_logging")

    print(json.dumps(result,indent=2))

if __name__ == "__main__":
    main()

"""
Sample output for the test_repo_logging given in Tests folder:

{
  "files_scanned_count": 7,
  "files_scanned": [
    "app.py",
    "audit.rb",
    "auth.js",
    "main.go",
    "Service.cs",
    "UserService.java",
    "utils.py"
  ],
  "files_not_scanned": [],
  "violations": 4,
  "details": [
    {
      "file": "test_repo_logging\\auth.js",
      "language": "node",
      "severity": "high",
      "issues": [
        "Sensitive data may be logged",
        "Console-based/teminal-based logging detected (non-persistent)",
        "Audit-relevant event without corresponding log"
      ],
      "recommendation": "Do not log passwords, tokens, secrets, or API keys. Mask or remove sensitive fields before logging. Log access, update, and delete events for auditability"
    },
    {
      "file": "test_repo_logging\\main.go",
      "language": "go",
      "severity": "medium",
      "issues": [
        "No logging framework detected",
        "Console-based/teminal-based logging detected (non-persistent)"
      ],
      "recommendation": "Introduce a standard logging framework in go"
    },
    {
      "file": "test_repo_logging\\Service.cs",
      "language": "dotnet",
      "severity": "medium",
      "issues": [
        "No logging framework detected"
      ],
      "recommendation": "Introduce a standard logging framework in dotnet"
    },
    {
      "file": "test_repo_logging\\utils.py",
      "language": "python",
      "severity": "medium",
      "issues": [
        "No logging framework detected",
        "Console-based/teminal-based logging detected (non-persistent)"
      ],
      "recommendation": "Introduce a standard logging framework in python"
    }
  ]
}
"""