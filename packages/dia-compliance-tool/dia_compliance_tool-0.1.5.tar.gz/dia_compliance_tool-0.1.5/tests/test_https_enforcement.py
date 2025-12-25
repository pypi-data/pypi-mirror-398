from Digital_India_Act import HTTPSEnfocementChecker

def main():
    test_cases = [
        "https://google.com",
        "https://github.com",
        "http://neverssl.com",
        "https://example.com", 
        "https://expired.badssl.com",
        "https://self-signed.badssl.com",
        "https://interiit-iittp-sports-2025-72224499903.asia-south1.run.app/matches",
        "https://interiit-iittp-sports-2025-72224499903.asia-south1.run.app/auth/me",
        "https://thisdomaindoesnotexist12345678.com",
    ]

    print("Final HTTPS Enforcement Check Results")

    for case in test_cases:
        url = case
        print(f"Testing URL:{url}")

        try:
            checker = HTTPSEnfocementChecker(url)
            result = checker.run()

            print("Result:")
            print(result)

        except Exception as e:
            print(f"Error occurred: {str(e)}")



if __name__ == "__main__":
    main()
