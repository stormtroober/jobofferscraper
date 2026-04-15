"""Deep scraping strategy for justjoin.it (React SPA)."""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from strategies.base_deep import DeepScrapingStrategy

_MIN_MEANINGFUL_LENGTH = 300

# JS: walk all divs/sections/articles and return the one with most innerText
_JS_FIND_RICHEST = """
return Array.from(document.querySelectorAll('div, section, article'))
  .filter(el => {
    const t = (el.innerText || '').trim();
    return t.length > 400 && el.children.length > 0;
  })
  .reduce((best, el) => {
    const rect = el.getBoundingClientRect();
    // Ignore elements that are not taking meaningful vertical space
    if (rect.height < 200) return best;
    const t = (el.innerText || '').trim();
    return t.length > (best ? (best.innerText || '').trim().length : 0) ? el : best;
  }, null);
"""

_JS_FIND_BY_MARKER = """
// Look for the element that contains "JOB DESCRIPTION" or similar markers
// and is a meaningful container
const markers = ['JOB DESCRIPTION', 'Job Description', 'About the role', 'About this role'];
for (const marker of markers) {
    const all = Array.from(document.querySelectorAll('*'));
    for (const el of all) {
        if (el.children.length === 0) continue; // skip leaves
        const t = (el.innerText || '').trim();
        if (t.includes(marker) && t.length > 400) {
            return el;
        }
    }
}
return null;
"""


class JustJoinITDeepStrategy(DeepScrapingStrategy):

    def extract(self, url: str) -> str:
        print(f"  [JustJoinITDeepStrategy] Extracting JD from {url}")
        self.driver.get(url)

        wait = WebDriverWait(self.driver, 20)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(5)  # SPA hydration

        self._dismiss_cookies()
        time.sleep(0.5)

        # 1. Try JS-based: find container with "JOB DESCRIPTION" marker
        el = self.driver.execute_script(_JS_FIND_BY_MARKER)
        if el:
            txt = self._trim_to_jd(el.text.strip())
            if len(txt) >= _MIN_MEANINGFUL_LENGTH:
                print(f"  [JustJoinITDeepStrategy] Found via marker, {len(txt)} chars")
                return self.cleanup(txt)

        # 2. Try JS-based: find richest visible container
        el = self.driver.execute_script(_JS_FIND_RICHEST)
        if el:
            txt = self._trim_to_jd(el.text.strip())
            if len(txt) >= _MIN_MEANINGFUL_LENGTH:
                print(f"  [JustJoinITDeepStrategy] Found via richest-element JS, {len(txt)} chars")
                return self.cleanup(txt)

        # 3. Body text – trim everything before "JOB DESCRIPTION" marker
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        print(f"  [JustJoinITDeepStrategy] Falling back to body text ({len(body_text)} chars)")
        return self.cleanup(self._trim_to_jd(body_text))

    def _trim_to_jd(self, body_text: str) -> str:
        """Cut the nav/header noise by starting from known JD markers."""
        markers = ["JOB DESCRIPTION", "Job Description", "About the role", "About this role"]
        lower = body_text.lower()
        for marker in markers:
            idx = lower.find(marker.lower())
            if idx != -1:
                return body_text[idx:]
        return body_text

    def _dismiss_cookies(self):
        selectors = [
            "button[id*='accept']",
            "button[class*='accept']",
            "button[data-testid*='accept']",
            "#onetrust-accept-btn-handler",
        ]
        for sel in selectors:
            for btn in self.driver.find_elements(By.CSS_SELECTOR, sel):
                try:
                    if btn.is_displayed():
                        btn.click()
                        return
                except Exception:
                    continue
