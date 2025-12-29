from playwright.sync_api import sync_playwright
import pathlib
import json
from typing import List
from .models import RuleViolation

class RuleBasedAccessbilityChecker:
    def __init__(self, url: str):
        self.url = url
        self.axe_path = pathlib.Path(__file__).parent/"axe.min.js"

        if not self.axe_path.exists():
            raise FileNotFoundError(
                f"axe.min.js not found at {self.axe_path}. "
                f"Download from https://unpkg.com/axe-core@4.9.1/axe.min.js"
            )
    
    def run(self) -> List[RuleViolation]:
        violations:List[RuleViolation] = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                page.goto(self.url, timeout=60000, wait_until="networkidle")
                page.add_script_tag(path=str(self.axe_path))

                results = page.evaluate(
                    """async () => {
                        try {
                            return await axe.run();
                        } catch (e) {
                            return { error: e.toString() };
                        }
                    }"""
                )

                if "error" in results:
                    raise RuntimeError(f"axe-core failed: {results['error']}")


                for v in results["violations"]:
                    for node in v["nodes"]:
                        violations.append(
                            RuleViolation(
                                id=v["id"],
                                description=v["description"],
                                impact=v.get("impact", "unknown"),
                                html=node.get("html", ""),
                                target=node.get("target", []),
                                wcag=v.get("tags", [])
                            )
                        )

            finally:
                browser.close()

        return violations