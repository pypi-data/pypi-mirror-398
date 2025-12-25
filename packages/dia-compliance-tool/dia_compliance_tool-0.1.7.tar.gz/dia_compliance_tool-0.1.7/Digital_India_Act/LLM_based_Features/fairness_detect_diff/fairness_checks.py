# fairness_checks.py

from groq_client import query_llm
from normalization import normalize_output, is_refusal
from config import BIAS_KEYWORDS


def generate_counterfactual_prompts(base_prompt, placeholder, values):
    return {v: base_prompt.replace(placeholder, v) for v in values}


def keyword_bias_check(text):
    lowered = text.lower()
    found = [k for k in BIAS_KEYWORDS if k in lowered]
    return {"status": "FAIL" if found else "PASS", "keywords": found}


def tone_length(text):
    return len(text.split())


def collect_llm_outputs(prompts):
    outputs = {}
    normalized = {}
    metrics = {}

    for group, prompt in prompts.items():
        raw = query_llm(prompt)
        norm = normalize_output(raw)

        outputs[group] = raw
        normalized[group] = norm

        metrics[group] = {
            "refusal": is_refusal(raw),
            "length": tone_length(raw),
            "keyword_check": keyword_bias_check(raw)
        }

    return outputs, normalized, metrics
