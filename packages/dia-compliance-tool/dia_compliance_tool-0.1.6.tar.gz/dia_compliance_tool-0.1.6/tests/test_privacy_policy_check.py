from Digital_India_Act import PrivacyPolicyChecker


def test(url):
    checker = PrivacyPolicyChecker()
    result = checker.run_check(url)

    print("Final result")
    print(f"Input URL: {result['input_url']}")
    print(f"Policy Found: {result['policy_found']}")
    print(f"Policy URL: {result['policy_url']}")
    print(f"Overall Score: {result['overall_score']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Human Review Recommended: {result['human_review_recommended']}")
    print("\nChecks:")

    for k,v in result["checks"].items():
        print(f"- {k}: {v['status']}")

    print("Text Snippet :\n", result["extracted_text_snippet"][:500])

if __name__ == "__main__":
    test("https://www.github.com")