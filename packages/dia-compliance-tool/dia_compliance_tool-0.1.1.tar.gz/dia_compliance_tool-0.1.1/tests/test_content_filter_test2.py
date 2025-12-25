from Digital_India_Act import ContentModerationChecker
import json

def main():
    checker = ContentModerationChecker()

    result = checker.run(
        url="https://iittp.plumerp.co.in/prod/iittirupati/",
        backend_path=None           
    )

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

"""
Result:

{
  "ugc_detected": false,
  "moderation_present": false,
  "severity": "low",
  "files_analyzed": [],
  "human_inspection_recommended": [],
  "details": [],
  "recommendation": "No user-generated content was detected. Content moderation obligations under the Digital India Act are not applicable for the analyzed system."
}
"""