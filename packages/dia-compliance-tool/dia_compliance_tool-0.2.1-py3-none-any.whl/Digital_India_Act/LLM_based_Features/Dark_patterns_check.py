# The below are the some of the dark patterns that are extracted online sources like wikipedia:
# 1) Confirmshaming - Undermines free and informed consent - Ex: "I prefer missing out updates", "No, I don't care about my privacy", 
# 2) Privacy Zuckering - Violates data minimization and consent principles - Ex: Sharing more data (Similar to Data minimization check)
# 3) Roach Motel - Consent withdrawal must be easy as content giving - Ex: Easy account creation but bad tough account deletion process
# 4) Misdirection - Manipulative UI (can be seen through css files and jsx files) - Ex: Prominant "Accept" button, hidden "Decline" etc
# 5) Pre-selected opt-in - consent must be explicit - Ex: having preselected checkboxes etc.
# 6) AI Training Consent Dark Patterns - can be integral part of 2,3,4
# Future extensions - Drip pricing, Bait-and-Switch

from bs4 import BeautifulSoup
import re
from typing import Dict, List
import os
import time,json
from groq import Groq
import requests
from Digital_India_Act.config import get_api_key

LLM_BACKEND = "groq"
GROQ_API_KEY = get_api_key("GROQ_API_KEY")

class DarkPatternsChecker:
    name = "Dark Patterns checker"
    description = """ It looks for the dark patterns listed below in the UI
     1) Confirmshaming - Undermines free and informed consent - Ex: "I prefer missing out updates", "No, I don't care about my privacy", 
     2) Privacy Zuckering - Violates data minimization and consent principles - Ex: Sharing more data (Similar to Data minimization check)
     3) Roach Motel - Consent withdrawal must be easy as content giving - Ex: Easy account creation but bad tough account deletion process
     4) Misdirection - Manipulative UI (can be seen through css files and jsx files) - Ex: Prominant "Accept" button, hidden "Decline" etc
     5) Pre-selected opt-in - consent must be explicit - Ex: having preselected checkboxes etc.
     6) AI Training Consent Dark Patterns - can be integral part of 2,3,4

     This is a combination of both Rule based + LLM based and some places also uses some other compliances internally
"""

    def __init__(
        self,
        url: str = None,
        html: str = None,
        frontend_path: str = None,
        model: str = "llama-3.3-70b-versatile",
    ):
        inputs = [url, html, frontend_path]
        if sum(x is not None for x in inputs) != 1:
            raise ValueError("Provide exactly one of: url, html, frontend_path")

        self.url = url
        self.model = model
        self.client = Groq(api_key=GROQ_API_KEY)

        if url:
            self.html = self._fetch_html(url)
        elif html:
            self.html = html
        else:
            self.html = self._load_frontend_folder(frontend_path)

        self.soup = BeautifulSoup(self.html, "html.parser")

    # html fetcher
    def _fetch_html(self, url: str) -> str:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    
    def _load_frontend_folder(self, path: str) -> str:
        if not os.path.isdir(path):
            raise ValueError("frontend_path must be a directory")

        combined_html = []

        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".html"):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            combined_html.append(f.read())
                    except Exception:
                        pass

        if not combined_html:
            raise ValueError("No HTML files found in frontend folder")

        return "\n".join(combined_html)

    def check_preselected_opt_ins(self)->bool:
        """Detect checked checkboxes / enabled toggles by default"""
        inputs = self.soup.find_all("input",{"type": ["checkbox","radio"]})
        return any(inp.has_attr("checked") for inp in inputs)
    
    def check_missing_reject_button(self)->bool:
        """Detect absence of reject/decline option"""
        reject_keywords = ['reject',"decline","deny","opt out","no thanks"]
        buttons = self.soup.find_all("button")

        for btn in buttons:
            text = btn.get_text(strip=True).lower()
            if any(k in text for k in reject_keywords):
                return False
        
        return True
    
    def check_forced_consent(self) -> bool:
        """Detect blocking modals with only accept actions"""
        modals = self.soup.find_all(
            lambda tag: tag.name == "div"
            and tag.get("role") in ["dialog","alertdialog"]
        )
        reject_keywords = ['reject',"decline","deny","opt out","no thanks"]
        for modal in modals:
            buttons = modal.find_all("button")
            if not buttons:
                continue
            has_reject = False
            for btn in buttons:
                txt = btn.get_text(strip=True).lower()
                if any(k in txt for k in reject_keywords):
                    has_reject = True
            
            if not has_reject:
                return True
            
        return False
    
    def check_asymmetric_choice(self) -> bool:
        """Detect visual or structural imbalance in accept vs reject"""
        buttons = self.soup.find_all("button")
        accept_buttons = []
        reject_buttons = []

        for btn in buttons:
            text = btn.get_text(strip=True).lower()
            style = btn.get("style","").lower()

            if "accept" in text:
                accept_buttons.append(style)
            if "reject" in text or "decline" in text:
                reject_buttons.append(style)

        if accept_buttons and not reject_buttons:
            return True
        
        # defining some helper functions
        def has_prominent_color(style: str) -> bool:
            return any(
                check in style
                for check in ['background:',"background-color:","color:","rgb","#"]
            ) 
        
        def get_font_size(style: str)-> int:
            for part in style.split(";"):
                if "font-size" in part:
                    try:
                        return int(part.split(":")[1].replace("px","").strip())
                    except:
                        pass
            return 0
        

        def get_font_weight(style:str) -> int:
            for part in style.split(";"):
                if "font-weight" in part:
                    try:
                        return int(part.split(":")[1].strip())
                    except:
                        pass
            return 400 # this is the default value
        
        for a_button in accept_buttons:
            for r_button in reject_buttons:
                dominance_score = 0

                if has_prominent_color(a_button) and not has_prominent_color(r_button):
                    dominance_score+=1

                if get_font_size(a_button) > get_font_size(r_button):
                    dominance_score+=1
                
                if get_font_weight(a_button) > get_font_weight(r_button):
                    dominance_score+=1

                if dominance_score >=2:
                    return True
        
        return False
    
    # helper function to invoke the llm
    def _query_llm(self, prompt: str) -> str:
        """Internal helper to query Groq LLM"""
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert in digital regulation compliance, "
                        "UI dark patterns, and user consent analysis."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        return completion.choices[0].message.content.strip()
    
    def check_roach_motel(self) -> bool:
        """Detect easy opt-in but hidden or missing opt-out"""
        
        # collect the opt-in related UI text
        opt_in_elements = self.soup.find_all(
            ["button","a"],
            string = lambda s: s and any(
                k in s.lower() for k in ["accept","agree","sign up","enable","allow"]
            )
        )

        opt_in_text = [el.get_text(strip=True) for el in opt_in_elements]

        # collecting potential opt-out/settings related UI text
        opt_out_elements = self.soup.find_all(
            ['a','button','label'],
            string = lambda s: s and any(
                k in s.lower()
                for k in ["opt out","unsubscribe","disable","cancel","withdraw","settings","preferences"]
            )
        )

        opt_out_text = [el.get_text(strip=True) for el in opt_out_elements]

        # Invoking llm to get results
        prompt = f"""
You are analyzing a website UI for dark patterns under the "Roach Motel" category.

Definition:
Roach Motel means users can easily opt in to a feature, service, or data usage,
but opting out is hidden, unclear, requires extra effort, or is not equivalently presented.

Opt-in UI text:
{opt_in_text}

Opt-out / settings UI text:
{opt_out_text}

Question:
Does this UI exhibit a Roach Motel dark pattern?
Answer ONLY as one of: YES or NO.
"""
        
        response = self._query_llm(prompt)
        return response.upper().startswith("YES")
    
    def check_confirmshaming(self) -> bool:
        """Detect shame or guilt-inducing consent language"""
        ui_text = self.extract_ui_text()

        if not ui_text:
            return False

        prompt = f"""
Confirmshaming is a dark pattern that uses guilt, shame, or ridicule
to pressure users into accepting.

UI TEXT:
{ui_text}

QUESTION:
Does this UI use confirmshaming?

Answer strictly in this format:
YES - <short reason>
or
NO - <short reason>
"""
        response = self._query_llm(prompt)
        return response.upper().startswith("YES")
    
    def check_misdirection_language(self) -> bool:
        """Detect misleading, confusing, or double-negative wording"""
        ui_text = self.extract_ui_text()

        if not ui_text:
            return False

        prompt = f"""
Misdirection is a dark pattern where wording is confusing, misleading,
or uses double negatives to trick users into consenting.

UI TEXT:
{ui_text}

QUESTION:
Is there misleading or confusing consent language?

Answer strictly in this format:
YES - <short reason>
or
NO - <short reason>
"""
        response = self._query_llm(prompt)
        return response.upper().startswith("YES")
    
    def extract_ui_text(self) -> str:
        """Extract visible UI text relevant to consent"""
        texts = []

        for tag in self.soup.find_all(["p","span","label","button"]):
            txt = tag.get_text(strip=True)
            if txt:
                texts.append(txt)
        return "\n".join(texts)
    
    # Finals results out
    def run(self) -> Dict[str,bool]:
        results = {}

        def add_result(name,detected,recommendation):
            results[name] = {
                "detected": detected,
                "recommendation": recommendation if detected else None
            }

        add_result(
            "forced_consent",
            self.check_forced_consent(),
            "Provide a clear Reject or Continue-without-accepting option."
        )

        add_result(
            "preselected_opt_in",
            self.check_preselected_opt_ins(),
            "Ensure consent checkboxes are unchecked by default."
        )

        add_result(
            "missing_reject_option",
            self.check_missing_reject_button(),
            "Add a visible Reject or Decline button equal to Accept."
        )

        add_result(
            "asymmetric_choice",
            self.check_asymmetric_choice(),
            "Present Accept and Reject options with equal visual prominence and accept should not dominate over reject."
        )

        add_result(
            "roach_motel",
            self.check_roach_motel(),
            "Make opt-out or cancellation as easy as opt-in."
        )

        add_result(
            "confirmshaming",
            self.check_confirmshaming(),
            "Remove guilt-inducing or shaming language from consent flows."
        )

        add_result(
            "misdirection_language",
            self.check_misdirection_language(),
            "Rewrite consent text to be clear, direct and non-misleading."
        )

        results["dark_pattern_detected"] = any(
            v['detected'] for v in results.values()
            if isinstance(v,dict)
        )

        return results