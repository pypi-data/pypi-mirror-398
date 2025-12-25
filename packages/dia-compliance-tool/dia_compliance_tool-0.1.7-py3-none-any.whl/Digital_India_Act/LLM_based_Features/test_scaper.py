import requests
from bs4 import BeautifulSoup

def extract_html_and_text(url: str):
    print("=" * 80)
    print(f"Fetching URL: {url}")
    print("=" * 80)

    headers = {
        "User-Agent": "Digital-India-Act-Compliance-Checker/1.0",
        "Accept-Language": "en-IN,en;q=0.9"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
    except Exception as e:
        print(f"[REQUEST ERROR] {e}")
        return

    print("\n--- HTTP STATUS ---")
    print(response.status_code)

    print("\n--- RAW HTML (first 5000 chars) ---")
    print(response.text[:5000])

    print("\n--- CLEANED VISIBLE TEXT ---")

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove non-visible / non-content elements
    for tag in soup([
        "script", "style", "meta", "iframe", "svg", "canvas", "noscript"
    ]):
        tag.decompose()

    for form in soup.find_all("form"):
        for t in form(["input", "textarea", "select", "button"]):
            t.decompose()

    for tag in soup.find_all(True):
        if tag.has_attr("aria-hidden") and tag["aria-hidden"] == "true":
            tag.decompose()
        if tag.has_attr("style") and "display:none" in tag["style"].replace(" ", "").lower():
            tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    text = " ".join(text.split())

    if text:
        print(text[:5000])
    else:
        print("[NO VISIBLE TEXT EXTRACTED]")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    url = input("Enter URL to analyze: ").strip()
    extract_html_and_text(url)
