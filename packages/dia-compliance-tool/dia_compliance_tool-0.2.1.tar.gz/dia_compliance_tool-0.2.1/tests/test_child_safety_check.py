from Digital_India_Act import run_child_safety_check

def main():
    report = run_child_safety_check("https://www.reddit.com")
    print("====== The obtained result ======")
    print(report)

if __name__ == "__main__":
    main()