import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base import ScrapingStrategy


class ReplyStrategy(ScrapingStrategy):
    """
    Scraping strategy for Reply Careers (reply.com/en/about/careers).
    
    Structure:
    - Each job is an <a class="job-result"> element
    - Title is in <h3> inside the job-result
    - Location and Company are in <article> divs
    """
    
    def fetch(self, url):
        self.driver.get(url)
        
        # Wait for dynamic content to load
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.job-result"))
            )
            # Extra wait for all content to render
            time.sleep(2)
        except Exception as e:
            print(f"Warning: Timeout waiting for job listings: {e}")
        
        return self.driver.page_source

    def parse(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        offers = []
        
        # Find all job listing links
        job_elements = soup.select("a.job-result")
        
        for job_el in job_elements:
            try:
                # Title - inside <h3>
                title_el = job_el.find("h3")
                title = title_el.get_text(strip=True) if title_el else "Unknown Title"
                
                # Get the article section with location and company
                article = job_el.find("article")
                location = "Unknown"
                company = "Reply"
                
                if article:
                    # All divs inside article
                    divs = article.find_all("div", recursive=False)
                    
                    if len(divs) >= 1:
                        location = divs[0].get_text(strip=True)
                    if len(divs) >= 2:
                        company = divs[1].get_text(strip=True)
                
                # Link - href attribute
                relative_link = job_el.get("href", "")
                if relative_link:
                    # Remove query parameters for consistent deduplication
                    clean_relative_link = relative_link.split("?")[0]
                    if clean_relative_link.startswith("/"):
                        full_url = f"https://www.reply.com{clean_relative_link}"
                    else:
                        full_url = clean_relative_link
                else:
                    full_url = "Unknown"
                
                # Extract slug from URL (job ID)
                # Example: /en/about/careers/pl/job-details/JOB-11134?... -> JOB-11134
                slug = ""
                if "job-details/" in relative_link:
                    slug_part = relative_link.split("job-details/")[-1]
                    slug = slug_part.split("?")[0]
                
                # Tags: extract from title keywords or use area from URL
                tags = self._extract_tags(title)
                
                offers.append({
                    'title': title,
                    'company': company,
                    'location': location,
                    'tags': ", ".join(tags) if tags else "",
                    'link_slug': slug,
                    'full_url': full_url
                })
                
            except Exception as e:
                print(f"Error parsing Reply offer: {e}")
                continue
        
        return offers
    
    def _extract_tags(self, title):
        """Extract relevant technology tags from the title."""
        title_upper = title.upper()
        
        known_tags = [
            'AWS', 'AZURE', 'GCP', 'CLOUD', 'PYTHON', 'JAVA', 'JAVASCRIPT',
            'REACT', 'ANGULAR', 'VUE', 'NODE', 'SQL', 'NOSQL', 'KUBERNETES',
            'DOCKER', 'DEVOPS', 'ML', 'AI', 'DATA', 'ANALYST', 'ENGINEER',
            'DEVELOPER', 'CONSULTANT', 'ARCHITECT', '.NET', 'C#', 'GO',
            'SALESFORCE', 'SAP', 'ORACLE', 'POWER BI', 'TABLEAU'
        ]
        
        found_tags = []
        for tag in known_tags:
            if tag in title_upper:
                found_tags.append(tag)
        
        return found_tags[:5]  # Limit to 5 tags

    def run(self, url, save_dir="data"):
        html_content = self.fetch(url)
        return self.parse(html_content)
