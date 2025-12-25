from Digital_India_Act import AIDisclosureChecker


def main():
    # Simulated publicly visible text extracted from webpages
    pages = [
        {
            "url": "https://counselnavi.com/about-us",
            "text": "Ask me anything to summarize your document.",
            "section": "main"
        },
        {
            "url": "https://gemini.google/about/",
            "text": "Generate image using text to image prompts.",
            "section": "main"
        },
    ]

    checker = AIDisclosureChecker(pages)
    result = checker.run_check()

    print("AI Disclosure Check Results")
    print(f"Check           : {result['Check']}")
    print(f"Status          : {result['status']}")
    print(f"Confidence      : {result['confidence_score']}")
    print(f"Reason          : {result['reason']}")

    print("Summary")
    print(f"Pages analyzed                  : {result['summary']['page_analyzed']}")
    print(f"Pages with strong AI signals    : {result['summary']['pages with strong ai usage signals']}")
    print(f"Pages with weak AI signals      : {result['summary']['pages with weak ai usage signals']}")
    print(f"Pages with AI disclosure text   : {result['summary']['pages with ai disclosure text']}")

    print("Evidence")

    for p in result["evidence"]["strong ai pages"]:
        print(
            f"[STRONG AI] {p['url']} | Section: {p['section']} | "
            f"Hits: {p['Strong Hits']}"
        )

    for p in result["evidence"]["weak ai pages"]:
        print(
            f"[WEAK AI] {p['url']} | Section: {p['section']} | "
            f"Hits: {p['Weak Hits']}"
        )

    for p in result["evidence"]["disclosure pages"]:
        print(
            f"[DISCLOSURE] {p['url']} | Section: {p['section']} | "
            f"Hits: {p['Disclosure Hits']}"
        )


if __name__ == "__main__":
    main()
