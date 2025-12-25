from Digital_India_Act import ContentModerationChecker
import json

def main():
    checker = ContentModerationChecker()

    result = checker.run(
        url="https://kalavriddhi-frontend-6cyz.onrender.com/",  
        backend_path=r"C:\Users\srikr\OneDrive\Documents\GitHub\DesiBazaar"         
    )

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

"""
This is a real-time software testcase and results are as follows:

groq api is unable to handle such high limit
"""