from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from typing import List
from .models import ScrapedData

def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    return soup.get_text(separator=" ", strip=True)

def _discovery_policy_links(page) -> List[str]:
    keywords = ["privacy", "terms", "safety", "children", "community"]
    urls = set()

    for link in page.query_selector_all("a"):
        href = link.get_attribute("href")
        text = (link.inner_text() or "").lower()

        if href and any(k in text for k in keywords):
            if href.startswith("/"):
                base = page.url.split("/", 3)[0]
                urls.add(base + href)
            elif href.startswith("http"):
                urls.add(href)
    return list(urls)

def scrape_site(url: str) -> ScrapedData:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page  = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=60000)

        visible_text = _clean_html(page.content())
        inputs = [el.inner_text() for el in page.query_selector_all("input, select, label")]
        buttons = [el.inner_text() for el in page.query_selector_all("button")]
        modals = [el.inner_text() for el in page.query_selector_all("[role='dialog'], .modal, .popup")]

        policy_text = ""

        for link in _discovery_policy_links(page)[:3]:
            try:
                page.goto(link, wait_until="networkidle", timeout=30000)
                policy_text += _clean_html(page.content()) + "\n"
            except:
                continue
        
        browser.close()

        return ScrapedData(
            visible_text=visible_text,
            inputs=inputs,
            buttons=buttons,
            modals=modals,
            policy_text=policy_text
        )
