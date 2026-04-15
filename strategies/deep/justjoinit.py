"""
Deep scraping strategy for justjoin.it job offers.

JustJoin uses Next.js App Router with React Server Components (RSC).
The job description is NOT rendered into the visible DOM in headless mode —
it is embedded as unicode-escaped HTML inside inline <script> tags that
contain `self.__next_f.push(...)` RSC payloads.

Strategy:
  1. Load the page and grab the raw page_source.
  2. Parse all <script> tags for __next_f.push payloads.
  3. Concatenate the payloads and find the HTML fragment (starts with <p> or <ul>).
  4. Parse that HTML with BeautifulSoup to get plain text.

Confirmed on:
  https://justjoin.it/job-offer/relativity-administrative-assistant-krakow-support
"""

import time
import re
from bs4 import BeautifulSoup

from strategies.base_deep import DeepScrapingStrategy


# RSC payloads carry HTML fragments as strings like:  "47:T1246,<p><strong>..."
# We look for any string that starts with an HTML tag after the payload header.
_RSC_PAYLOAD_RE = re.compile(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', re.DOTALL)
_HTML_FRAGMENT_RE = re.compile(r'\\u003c(?:p|ul|ol|h[1-6]|div)\\u003e.{100,}', re.DOTALL)


def _decode_unicode_escapes(s: str) -> str:
    """Convert \\uXXXX sequences to real characters."""
    return s.encode("raw_unicode_escape").decode("unicode_escape", errors="replace")


def _extract_jd_from_rsc(page_source: str) -> str:
    """
    Walk through all RSC script payloads and return the largest HTML
    fragment that looks like a job description body.
    """
    candidates = []

    for match in _RSC_PAYLOAD_RE.finditer(page_source):
        payload = match.group(1)
        # Check if this payload contains an HTML fragment
        if _HTML_FRAGMENT_RE.search(payload):
            # Extract the HTML part: everything after the first < until end
            html_start = payload.find("\\u003c")
            if html_start == -1:
                continue
            html_escaped = payload[html_start:]
            html = _decode_unicode_escapes(html_escaped)
            candidates.append(html)

    if not candidates:
        return ""

    # Pick the longest candidate (most content)
    best = max(candidates, key=len)
    soup = BeautifulSoup(best, "html.parser")
    return soup.get_text(separator="\n").strip()


class JustJoinITDeepStrategy(DeepScrapingStrategy):
    """
    Extracts JustJoin job descriptions by parsing the Next.js RSC payload
    embedded in <script> tags, bypassing the client-side rendering entirely.
    """

    def extract(self, url: str) -> str:
        print(f"  [JustJoinITDeepStrategy] Extracting JD from {url}")
        self.driver.get(url)

        # Wait for the page to load (RSC payloads are injected by SSR,
        # so they're present immediately after DOMContentLoaded)
        for _ in range(20):
            if self.driver.execute_script("return document.readyState") == "complete":
                break
            time.sleep(0.5)
        time.sleep(2)

        page_source = self.driver.page_source
        text = _extract_jd_from_rsc(page_source)

        if not text:
            print("  [JustJoinITDeepStrategy] RSC parse failed, no JD fragment found.")

        return self.cleanup(text)
