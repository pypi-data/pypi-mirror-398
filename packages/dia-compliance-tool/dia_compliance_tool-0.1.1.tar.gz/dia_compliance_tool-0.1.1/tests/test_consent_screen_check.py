from Digital_India_Act import WebConsentChecker
import json
def main():
    checker = WebConsentChecker()
    url = "https://www.iittp.ac.in/"
    url1 = "https://kalavriddhi-frontend-6cyz.onrender.com/"
    result = checker.run(url1)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__=="__main__":
    main()

# Sample test response is presented below
# For URL: https://kalavriddhi-frontend-6cyz.onrender.com/
# The response is
"""
{
  "site": "https://kalavriddhi-frontend-6cyz.onrender.com/",
  "pages_scanned": 11,
  "violating_pages": [
    "https://kalavriddhi-frontend-6cyz.onrender.com/",
    "https://kalavriddhi-frontend-6cyz.onrender.com/index.html",
    "https://kalavriddhi-frontend-6cyz.onrender.com/signin/signin.html",
    "https://kalavriddhi-frontend-6cyz.onrender.com/loginPage/index.html",
    "https://kalavriddhi-frontend-6cyz.onrender.com/RequestFeature/rf.html",
    "https://kalavriddhi-frontend-6cyz.onrender.com/ContributeToQuiz/index.html",
    "https://kalavriddhi-frontend-6cyz.onrender.com/map-of-india/index.html",
    "https://kalavriddhi-frontend-6cyz.onrender.com/bharatnatyam-page/index.html",
    "https://kalavriddhi-frontend-6cyz.onrender.com/game/index.html",
    "https://kalavriddhi-frontend-6cyz.onrender.com/Culture-map-quiz/index.html"
  ],
  "details": [
    {
      "url": "https://kalavriddhi-frontend-6cyz.onrender.com/",
      "score": 20,
      "severity": "high",
      "issues": [
        "No explicit consent mechanism for collecting user data",
        "Lack of clear and specific explanation of data collection and usage",
        "No informed purpose for collecting user data",
        "No ability for users to refuse data collection",
        "No clear and unambiguous permission for data collection",
        "Potential dark pattern: 'Got it!' button may be misleading and not provide actual consent"
      ],
      "recommendation": "Add a clear and explicit consent mechanism, such as a checkbox or button, that requires users to actively opt-in to data collection. Provide a clear and specific explanation of what data is being collected, how it will be used, and for what purpose. Ensure that users have the ability to refuse data collection and that the permission is unambiguous and not misleading. Consider adding a privacy policy and terms of service that outline data collection and usage practices."
    },
    {
      "url": "https://kalavriddhi-frontend-6cyz.onrender.com/index.html",
      "score": 0,
      "severity": "high",
      "issues": [
        "No explicit consent mechanism for collecting user data",
        "No clear and specific explanation of data collection and usage",
        "No informed purpose for collecting user data",
        "No ability for users to refuse data collection",
        "Potential dark pattern: 'Got it!' button may be misleading as it does not provide a clear option to refuse or opt-out",
        "No unambiguous permission for collecting user data"
      ],
      "recommendation": "Add a prominent and explicit consent mechanism, such as a checkbox or button, that allows users to opt-in or opt-out of data collection. Provide a clear and specific explanation of what data is being collected, how it will be used, and for what purpose. Ensure that users have the ability to refuse data collection and that the 'Got it!' button is replaced with a clear and unambiguous opt-in or opt-out option."
    },
    {
      "url": "https://kalavriddhi-frontend-6cyz.onrender.com/about.html",
      "score": 100,
      "severity": "low",
      "issues": [],
      "recommendation": "No changes required, as the provided UI text does not contain any consent mechanisms or personal data collection elements."
    },
    {
      "url": "https://kalavriddhi-frontend-6cyz.onrender.com/signin/signin.html",
      "score": 20,
      "severity": "high",
      "issues": [
        "Lack of explicit consent for collecting personal data",
        "Unclear purpose of collecting data, such as full name, email, and art form interest", 
        "No option to refuse data collection",
        "No clear explanation of how data will be used and shared",
        "No unambiguous permission for processing sensitive information"
      ],
      "recommendation": "Add a clear and specific consent statement, such as 'By signing up, you agree to our terms and conditions, and consent to the collection and use of your personal data for the purpose of providing and improving our services.' Provide an option to opt-out of data collection and specify how data will be used, shared, and protected. Consider adding a checkbox or similar mechanism to obtain explicit consent."
    },
    {
      "url": "https://kalavriddhi-frontend-6cyz.onrender.com/loginPage/index.html",
      "score": 20,
      "severity": "high",
      "issues": [
        "Lack of explicit consent mechanism for processing user data",
        "No clear and specific explanation of data processing purposes",
        "Informed purpose of data collection is not provided",
        "No ability to refuse data collection and processing",
        "Presence of potentially misleading 'Remember me' option without clear consent",       
        "No unambiguous permission for data processing"
      ],
      "recommendation": "Add a clear and specific consent mechanism, such as a checkbox or separate agreement page, that explains the purpose of data collection and processing. Provide users with the ability to refuse data collection and processing. Ensure that the 'Remember me' option is accompanied by a clear explanation of its implications on user data. Implement a separate and explicit consent mechanism for admin users, if applicable."
    },
    {
      "url": "https://kalavriddhi-frontend-6cyz.onrender.com/RequestFeature/rf.html",
      "score": 0,
      "severity": "high",
      "issues": [
        "No consent mechanism present",
        "No explicit consent obtained",
        "No clear and specific explanation provided",
        "No informed purpose stated",
        "No ability to refuse or opt-out",
        "No unambiguous permission granted"
      ],
      "recommendation": "Implement a clear and transparent consent mechanism that includes explicit consent, a clear and specific explanation of the purpose, informed purpose, ability to refuse or opt-out, and unambiguous permission. The UI text should be revised to include a consent request with a specific purpose, such as 'We use cookies to improve your experience. Do you consent to our cookie policy?' with options to accept or decline."
    },
    {
      "url": "https://kalavriddhi-frontend-6cyz.onrender.com/ContributeToQuiz/index.html",     
      "score": 0,
      "severity": "low",
      "issues": [
        "No consent mechanism present",
        "No explanation of data collection or usage",
        "No option to refuse data collection"
      ],
      "recommendation": "Implement a clear and specific consent mechanism that provides an informed purpose for data collection, allows users to refuse data collection, and avoids dark patterns. The consent mechanism should be unambiguous and provide explicit consent. Since the current UI text does not contain any information related to consent, a complete overhaul of the consent mechanism is required."
    },
    {
      "url": "https://kalavriddhi-frontend-6cyz.onrender.com/map-of-india/index.html",
      "score": 0,
      "severity": "high",
      "issues": [
        "No explicit consent mechanism is present",
        "No clear and specific explanation of data collection and usage is provided",
        "No informed purpose for data collection is stated",
        "No ability to refuse data collection is offered",
        "No unambiguous permission is requested from users"
      ],
      "recommendation": "Add a prominent and explicit consent mechanism, such as a checkbox or button, that requires users to affirmatively opt-in to data collection. Provide a clear and specific explanation of what data is being collected, how it will be used, and for what purpose. Ensure that users have the ability to refuse data collection and that no dark patterns are used to manipulate user consent. Consider adding a privacy policy link and a terms of service link to the webpage."
    },
    {
      "url": "https://kalavriddhi-frontend-6cyz.onrender.com/bharatnatyam-page/index.html",    
      "score": 0,
      "severity": "high",
      "issues": [
        "No consent mechanism is present",
        "No explicit consent is obtained from the user",
        "No clear and specific explanation of data collection and usage is provided",
        "No informed purpose of data collection is stated",
        "No ability to refuse data collection is provided",
        "No unambiguous permission is obtained from the user"
      ],
      "recommendation": "Add a prominent and explicit consent mechanism that provides a clear and specific explanation of data collection and usage, informs the user of the purpose of data collection, allows the user to refuse data collection, and obtains unambiguous permission from the user. This can be achieved by adding a checkbox or a button that requires the user to actively consent to data collection, along with a link to a privacy policy that explains data collection and usage in detail."
    },
    {
      "url": "https://kalavriddhi-frontend-6cyz.onrender.com/game/index.html",
      "score": 0,
      "severity": "high",
      "issues": [
        "No explicit consent mechanism is present",
        "No clear and specific explanation of data collection and usage is provided",
        "No informed purpose for data collection is stated",
        "No ability to refuse data collection is offered",
        "No unambiguous permission is requested from the user"
      ],
      "recommendation": "Add a prominent and explicit consent mechanism that clearly explains the purpose of data collection, provides specific details on what data will be collected and how it will be used, and offers users the ability to refuse or opt-out of data collection. Ensure that the consent mechanism is unambiguous, free from dark patterns, and compliant with the Digital India Act's consent requirements."
    },
    {
      "url": "https://kalavriddhi-frontend-6cyz.onrender.com/Culture-map-quiz/index.html",     
      "score": 0,
      "severity": "high",
      "issues": [
        "No explicit consent mechanism for collecting user data",
        "No clear and specific explanation of how user data will be used",
        "No informed purpose for collecting user data",
        "No ability for users to refuse data collection",
        "Potential dark pattern: requiring users to enter their name without explaining why it's necessary",
        "Ambiguous permission: no clear indication of what users are agreeing to by participating in the quiz"
      ],
      "recommendation": "Add a clear and explicit consent mechanism, such as a checkbox or button, that requires users to affirmatively agree to data collection and use. Provide a specific explanation of how user data will be used, including any potential sharing with third parties. Offer users the ability to refuse data collection and provide an option to participate in the quiz anonymously. Remove any potential dark patterns, such as requiring users to enter their name without a clear explanation. Ensure that users are fully informed and provide unambiguous permission for data collection and use."
    }
  ]
}
"""