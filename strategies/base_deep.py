from abc import ABC, abstractmethod
from selenium.webdriver.remote.webdriver import WebDriver


class DeepScrapingStrategy(ABC):
    """
    Abstract base class for site-specific job description (deep) scraping strategies.

    Each concrete subclass targets a single site and knows how to:
      - wait for the right element to appear (Selenium waits, JS execution, etc.)
      - locate the job-description container
      - extract and clean the text

    The `deep_scraper.py` orchestrator owns the WebDriver lifecycle; strategies
    receive an already-navigated driver and return plain text.
    """

    def __init__(self, driver: WebDriver):
        self.driver = driver

    @abstractmethod
    def extract(self, url: str) -> str:
        """
        Navigate to *url* (driver.get is allowed here) and return the
        plain-text job description.  Return an empty string on failure.
        """
        pass

    # ------------------------------------------------------------------
    # Optional hook – subclasses may override for site-specific cleanup
    # ------------------------------------------------------------------
    def cleanup(self, text: str) -> str:
        """Light post-processing shared across strategies (strip blank lines, etc.)."""
        lines = [line for line in text.splitlines() if line.strip()]
        return "\n".join(lines).strip()
