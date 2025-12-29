from Digital_India_Act import Encryption_libraries_checker
import os

def main():
    checker = Encryption_libraries_checker()

    # base_path = os.path.dirname(__file__)
    base_path = r"C:\Users\srikr\OneDrive\Documents\GitHub\DesiBazaar\Culture-map-quiz"
    res_full = checker.full_scan(base_path)
    print("\n--- Full Scan Result ---")
    print(res_full)

    res_llm = checker.llm_scan(base_path)
    print("\n --- LLM Scan Result ---")
    print(res_llm)

if __name__ == "__main__":
    main()


# Output for Path: C:\Users\srikr\OneDrive\Documents\GitHub\DesiBazaar\Culture-map-quiz
"""
--- Full Scan Result ---
{
  'method': 'full_scan',
  'total_used': 0,
  'total_needed': 0,
  'score': 0,
  'violations:': 0,
  'violating_files': []
}




--- LLM Scan Result ---
{
  'method': 'llm_based_heuristic_scan',
  'heuristic_scanned_files': [
    'C:\\Users\\srikr\\OneDrive\\Documents\\GitHub\\DesiBazaar\\Culture-map-quiz\\auth.js',
    'C:\\Users\\srikr\\OneDrive\\Documents\\GitHub\\DesiBazaar\\Culture-map-quiz\\backend/user.py'
  ],
  'total_used': 0,
  'total_needed': 0,
  'score': 0,
  'violations': 0,
  'violating_files': []
}
"""
