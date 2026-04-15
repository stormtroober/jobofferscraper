"""Deep scraping strategy for builtin.com."""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from strategies.base_deep import DeepScrapingStrategy

_MIN_MEANINGFUL_LENGTH = 300

# Selectors in order of specificity — builtin.com React SPA
_JD_SELECTORS = [
    "[data-id='job-description']",
    "[data-testid='job-description']",
    "#job-description",
    ".job-description",
    "[class*='JobDescription']",
    "[class*='job-description']",
    "[class*='BcJdDesc']",
    "[class*='description']",
    "section.description",
    "article.description",
    "main",
    "[role='main']",
    "#main-content",
]

_JS_FIND_RICHEST = """
return Array.from(document.querySelectorAll('div, section, article, main'))
  .filter(el => {
    const t = (el.innerText || '').trim();
    return t.length > 400 && el.children.length > 0;
  })
  .reduce((best, el) => {
    const rect = el.getBoundingClientRect();
    if (rect.height < 150) return best;
    const t = (el.innerText || '').trim();
    return t.length > (best ? (best.innerText || '').trim().length : 0) ? el : best;
  }, null);
"""

_JD_MARKERS = [
    "The Role",
    "About the Role",
    "About the role",
    "Responsibilities",
    "Required Qualifications",
    "Requirements",
    "What you'll do",
    "What You'll Do",
    "Job description",
    "About the job",
    "About the position",
    "What we're looking for",
]


class BuiltInDeepStrategy(DeepScrapingStrategy):

    def extract(self, url: str) -> str:
        print(f"  [BuiltInDeepStrategy] Extracting JD from {url}")
        self.driver.get(url)

        wait = WebDriverWait(self.driver, 20)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        self._dismiss_cookies()
        time.sleep(0.5)

        self._expand_full_description()
        time.sleep(1)

        # 1. Try known CSS selectors
        for selector in _JD_SELECTORS:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                try:
                    txt = el.text.strip()
                    if len(txt) >= _MIN_MEANINGFUL_LENGTH:
                        trimmed = self._trim_to_jd(txt)
                        if len(trimmed) >= _MIN_MEANINGFUL_LENGTH:
                            print(f"  [BuiltInDeepStrategy] Found via '{selector}', {len(trimmed)} chars")
                            return self.cleanup(trimmed)
                except Exception:
                    continue

        # 2. JS richest-element fallback
        el = self.driver.execute_script(_JS_FIND_RICHEST)
        if el:
            txt = self._trim_to_jd(el.text.strip())
            if len(txt) >= _MIN_MEANINGFUL_LENGTH:
                print(f"  [BuiltInDeepStrategy] Found via JS richest-element, {len(txt)} chars")
                return self.cleanup(txt)

        # 3. Full body as last resort
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        trimmed = self._trim_to_jd(body_text)
        print(f"  [BuiltInDeepStrategy] Falling back to body text ({len(trimmed)} chars)")
        return self.cleanup(trimmed)

    def _trim_to_jd(self, text: str) -> str:
        """Cut nav/header noise before actual job content."""
        lower = text.lower()
        for marker in _JD_MARKERS:
            idx = lower.find(marker.lower())
            if idx != -1:
                start = max(0, idx - 300)
                snippet = text[start:idx]
                last_nl = snippet.rfind("\n")
                adjusted = start + last_nl + 1 if last_nl != -1 else idx
                return text[adjusted:]
        return text

    def _expand_full_description(self):
        """Click 'Read Full Description' button if present."""
        selectors = [
            "//button[contains(translate(text(),'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'READ FULL')]",
            "//a[contains(translate(text(),'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'READ FULL')]",
            "//span[contains(translate(text(),'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'READ FULL')]",
        ]
        for xpath in selectors:
            elements = self.driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if el.is_displayed():
                        self.driver.execute_script("arguments[0].click();", el)
                        print("  [BuiltInDeepStrategy] Clicked 'Read Full Description'")
                        return
                except Exception:
                    continue

    def _dismiss_cookies(self):
        selectors = [
            "button[id*='accept']",
            "button[class*='accept']",
            "button[data-testid*='accept']",
            "#onetrust-accept-btn-handler",
            "button[class*='cookie']",
            "[class*='CookieConsent'] button",
        ]
        for sel in selectors:
            for btn in self.driver.find_elements(By.CSS_SELECTOR, sel):
                try:
                    if btn.is_displayed():
                        btn.click()
                        return
                except Exception:
                    continue
