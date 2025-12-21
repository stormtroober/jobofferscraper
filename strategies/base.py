from abc import ABC, abstractmethod

class ScrapingStrategy(ABC):
    def __init__(self, driver):
        self.driver = driver

    @abstractmethod
    def fetch(self, url):
        """Fetches the page and returns raw content (usually HTML)"""
        pass

    @abstractmethod
    def parse(self, content):
        """Parses the content and returns a list of standardized offer objects"""
        pass
        
    @abstractmethod
    def run(self, url):
        """Executes the full scraping logic for a given URL"""
        pass
