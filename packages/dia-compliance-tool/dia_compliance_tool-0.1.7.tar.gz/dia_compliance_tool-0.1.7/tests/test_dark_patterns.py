from Digital_India_Act import DarkPatternsChecker
import json

def main():
    checker = DarkPatternsChecker(frontend_path="test_case_dark1")
    result = checker.run()

    checker1 = DarkPatternsChecker(frontend_path="test_case_dark2")
    result1 = checker1.run()

    checker2 = DarkPatternsChecker(frontend_path="test_case_dark3")
    result2 = checker2.run()

    checker3 = DarkPatternsChecker(url="https://www.iittp.ac.in/")
    result3 = checker3.run()

    print("Result for first test case:")
    print(json.dumps(result,indent=2))

    print("----------------------------")
    print("Result for second test case:")
    print(json.dumps(result1,indent=2))

    print("----------------------------")
    print("Result for third test case:")
    print(json.dumps(result2,indent=2))

    print("--------------------------")
    print("Result for fourth test case:")
    print(json.dumps(result3,indent=2))

if __name__ == "__main__":
    main()

"""
Results for the above test cases:

Result for first test case:
{
  "forced_consent": {
    "detected": true,
    "recommendation": "Provide a clear Reject or Continue-without-accepting option."
  },
  "preselected_opt_in": {
    "detected": false,
    "recommendation": null
  },
  "missing_reject_option": {
    "detected": true,
    "recommendation": "Add a visible Reject or Decline button equal to Accept."
  },
  "asymmetric_choice": {
    "detected": true,
    "recommendation": "Present Accept and Reject options with equal visual prominence and accept should not dominate over reject."
  },
  "roach_motel": {
    "detected": true,
    "recommendation": "Make opt-out or cancellation as easy as opt-in."
  },
  "confirmshaming": {
    "detected": true,
    "recommendation": "Remove guilt-inducing or shaming language from consent flows."
  },
  "misdirection_language": {
    "detected": true,
    "recommendation": "Rewrite consent text to be clear, direct and non-misleading."
  },
  "dark_pattern_detected": true
}
----------------------------
Result for second test case:
{
  "forced_consent": {
    "detected": false,
    "recommendation": null
  },
  "preselected_opt_in": {
    "detected": true,
    "recommendation": "Ensure consent checkboxes are unchecked by default."
  },
  "missing_reject_option": {
    "detected": true,
    "recommendation": "Add a visible Reject or Decline button equal to Accept."
  },
  "asymmetric_choice": {
    "detected": true,
    "recommendation": "Present Accept and Reject options with equal visual prominence and accept should not dominate over reject."
  },
  "roach_motel": {
    "detected": true,
    "recommendation": "Make opt-out or cancellation as easy as opt-in."
  },
  "confirmshaming": {
    "detected": false,
    "recommendation": null
  },
  "misdirection_language": {
    "detected": false,
    "recommendation": null
  },
  "dark_pattern_detected": true
}
----------------------------
Result for third test case:
{
  "forced_consent": {
    "detected": false,
    "recommendation": null
  },
  "preselected_opt_in": {
    "detected": false,
    "recommendation": null
  },
  "missing_reject_option": {
    "detected": true,
    "recommendation": "Add a visible Reject or Decline button equal to Accept."
  },
  "asymmetric_choice": {
    "detected": false,
    "recommendation": null
  },
  "roach_motel": {
    "detected": true,
    "recommendation": "Make opt-out or cancellation as easy as opt-in."
  },
  "confirmshaming": {
    "detected": false,
    "recommendation": null
  },
  "misdirection_language": {
    "detected": true,
    "recommendation": "Rewrite consent text to be clear, direct and non-misleading."
  },
  "dark_pattern_detected": true
}
--------------------------
Result for fourth test case:
{
  "forced_consent": {
    "detected": false,
    "recommendation": null
  },
  "preselected_opt_in": {
    "detected": false,
    "recommendation": null
  },
  "missing_reject_option": {
    "detected": true,
    "recommendation": "Add a visible Reject or Decline button equal to Accept."
  },
  "asymmetric_choice": {
    "detected": false,
    "recommendation": null
  },
  "roach_motel": {
    "detected": true,
    "recommendation": "Make opt-out or cancellation as easy as opt-in."
  },
  "confirmshaming": {
    "detected": false,
    "recommendation": null
  },
  "misdirection_language": {
    "detected": false,
    "recommendation": null
  },
  "dark_pattern_detected": true
}
"""