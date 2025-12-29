from .scraper import scrape_site
from .rule_engine import run_rule_checks
from .llm_engine import run_llm_checks
from .groq_llm_client import GroqLLMClient
from .evaluator import evaluate

def run_child_safety_check(url: str):
    llm_client = GroqLLMClient()
    scraped = scrape_site(url)
    rule_results = run_rule_checks(scraped)
    llm_results = run_llm_checks(llm_client, scraped)
    return evaluate(url, rule_results, llm_results)

if __name__ == "__main__":
    result = run_child_safety_check("input url")
    print(result)