from Digital_India_Act import ContentModerationChecker
import json

def main():
    checker = ContentModerationChecker()

    result = checker.run(
        url="http://localhost:3000",   
        backend_path="./test_backend_cmf"           
    )

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

"""
Results when the selection of files if put in the hands of LLM:
{
  "ugc_detected": false,
  "moderation_present": false,
  "severity": "low",
  "files_analyzed": [],
  "human_inspection_recommended": [],
  "details": [],
  "recommendation": "No user-generated content was detected. Content moderation obligations under the Digital India Act are not applicable for the analyzed system."
}

Results when all files are scanned:
{
  "ugc_detected": true,
  "moderation_present": true,
  "severity": "medium",
  "files_analyzed": [
    "./test_backend_cmf\\server.py",
    "./test_backend_cmf\\routes\\createComments.py",
    "./test_backend_cmf\\routes\\posts.py",
    "./test_backend_cmf\\routes\\utils\\profanity_filter.py"
  ],
  "human_inspection_recommended": [],
  "details": [
    {
      "file": "./test_backend_cmf\\server.py",
      "analysis": [
        {
          "ugc_present": true,
          "moderation_present": false,
          "moderation_type": "none",
          "issues": [
            "No content moderation mechanism is implemented in the provided code.",
            "The code only sets up routes for comments and posts, but does not include any functionality for moderating user-generated content.",
            "There is no indication of frontend, backend, AI, or human review moderation being used."
          ]
        }
      ]
    },
    {
      "file": "./test_backend_cmf\\routes\\createComments.py",
      "analysis": [
        {
          "ugc_present": true,
          "moderation_present": false,
          "moderation_type": "none",
          "issues": [
            "No content moderation is performed on user-generated comments",
            "Comments are posted without any review or filtering",
            "Potential for abusive or harmful content to be published"
          ]
        }
      ]
    },
    {
      "file": "./test_backend_cmf\\routes\\posts.py",
      "analysis": [
        {
          "ugc_present": true,
          "moderation_present": true,
          "moderation_type": "backend",
          "issues": [
            "The code only checks for profanity, it may not cover other types of inappropriate content",
            "The code does not provide any information about the criteria used to determine 'bad words'",
            "The code does not have a mechanism for users to appeal or report false positives",
            "The code does not have a mechanism for updating the list of 'bad words' over time"
          ]
        }
      ]
    },
    {
      "file": "./test_backend_cmf\\routes\\utils\\profanity_filter.py",
      "analysis": [
        {
          "ugc_present": true,
          "moderation_present": true,
          "moderation_type": "backend",
          "issues": [
            "The moderation is case-sensitive only in the sense that it converts the input text to lowercase, but it does not handle word variations or misspellings.",
            "The list of bad words is hardcoded and may not be comprehensive or up-to-date.",
            "The function only checks for exact word matches and does not account for context or word combinations."
          ]
        }
      ]
    }
  ],
  "recommendation": "Based on the provided content moderation findings, I recommend the following actions to ensure compliance with the Digital India Act:\n\n1. Backend moderation is required, and it appears to be partially implemented. The presence of a profanity filter in the utils directory is a good start. However, to enhance the moderation capabilities, it is recommended to implement a more comprehensive backend moderation system that can detect and flag potentially harmful or objectionable content.\n\n2. The findings indicate that the moderation types detected include \"backend\" and \"none\". To improve the moderation process, it is suggested to implement a combination of automated and human moderation techniques. The automated system can flag potentially problematic content, which can then be reviewed by human moderators.\n\n3. The absence of reporting or flagging mechanisms for users to report objectionable content is a significant concern. To address this, it is recommended to add a reporting or flagging feature that allows users to report suspicious or harmful content. This can be achieved by adding a \"report\" button next to each post or comment, which will send a notification to the moderation team for review.\n\n4. Human review is essential for ensuring that the content moderation process is effective. It is recommended to implement a system where human moderators can review flagged content and make decisions on whether it complies with the community guidelines. The files analyzed, such as server.py, createComments.py, posts.py, and profanity_filter.py, should be reviewed by human moderators to ensure that they are functioning correctly and effectively moderating user-generated content.\n\n5. To enhance transparency and accountability, it is recommended to maintain a record of all moderation actions, including the date, time, and reason for the action. This will help to ensure that the moderation process is fair, unbiased, and compliant with the Digital India Act.\n\nIn concrete terms, the following changes are recommended:\n\n- Add a reporting or flagging feature for users to report objectionable content\n- Implement a comprehensive backend moderation system that can detect and flag potentially harmful content\n- Review and enhance the profanity filter to ensure it is effective in detecting and blocking objectionable content\n- Implement a human review process for flagged content\n- Maintain a record of all moderation actions, including the date, time, and reason for the action."
}
"""