from Digital_India_Act import Authentication_checker

#one test case as an object with url parameter
class ApiEndpoint:
    def __init__(self,url,method="GET"):
        self.url = url
        self.method = method


def main():
    checker = Authentication_checker()

    results = checker.check([
        "https://httpstat.us/401",              # plain string case
        ApiEndpoint("https://httpstat.us/200"), # object case
        "https://interiit-iittp-sports-2025-72224499903.asia-south1.run.app/matches/upcoming",
        "https://interiit-iittp-sports-2025-72224499903.asia-south1.run.app/gallery?checkpoint=1970-01-01T00:00:00Z",
        "https://interiit-iittp-sports-2025-72224499903.asia-south1.run.app/auth/me",
        "https://interiit-iittp-sports-2025-72224499903.asia-south1.run.app/matches",
        "https://github.com/SrikrishnaKidambi/Digital-India-Act-Compliance-Checker-Tool.git",
        "https://api.nexmo.com/v1/messages"

    ])

    print("--Authentication check results---")
    for r in results:
        print(f"Endpoint: {r['endpoint']}, Secure: {r['secure']}, Api Working: {r['Api Working']}")

if __name__ == "__main__":
    main()


#Sample output for the urls tested is presented below
"""
--Authentication check results---
Endpoint: https://httpstat.us/401, Secure: False, Api Working: False
Endpoint: https://httpstat.us/200, Secure: False, Api Working: False
Endpoint: https://interiit-iittp-sports-2025-72224499903.asia-south1.run.app/matches/upcoming, Secure: False, Api Working: True
Endpoint: https://interiit-iittp-sports-2025-72224499903.asia-south1.run.app/gallery?checkpoint=1970-01-01T00:00:00Z, Secure: False, Api Working: True
Endpoint: https://interiit-iittp-sports-2025-72224499903.asia-south1.run.app/auth/me, Secure: False, Api Working: True
Endpoint: https://interiit-iittp-sports-2025-72224499903.asia-south1.run.app/matches, Secure: True, Api Working: True
Endpoint: https://github.com/SrikrishnaKidambi/Digital-India-Act-Compliance-Checker-Tool.git, Secure: True, Api Working: True
Endpoint: https://api.nexmo.com/v1/messages, Secure: True, Api Working: True
"""