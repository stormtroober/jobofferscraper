import time
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base import ScrapingStrategy


class BulldogJobStrategy(ScrapingStrategy):
    """
    Scraping strategy for BulldogJob (bulldogjob.com).
    """
    
    def fetch(self, url):
        self.driver.get(url)
        
        # Wait for dynamic content to load
        try:
            # Wait for at least one job item to appear
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[class*='JobListItem_item']"))
            )
            # Extra wait to ensure list is populated
            time.sleep(2)
        except Exception as e:
            print(f"Warning: Timeout waiting for BulldogJob listings: {e}")
        
        return self.driver.page_source

    def parse(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        offers = []
        
        # Find all job listing links using regex for the class name
        # The class name observed was "JobListItem_item__fYh8y" but hash might change
        job_elements = soup.find_all("a", class_=re.compile(r"JobListItem_item"))
        
        for job_el in job_elements:
            try:
                # Title - inside <h3>
                title_el = job_el.find("h3")
                title = title_el.get_text(strip=True) if title_el else "Unknown Title"
                
                tags = [] # Initialize tags list

                
                # Company & Location extraction
                # Structure:
                # <div>
                #   <h3>Title</h3>
                #   <div><div>Company</div></div>  <-- Optional?
                #   <div class="flex items-center"> <button>Location</button> ... </div>
                # </div>
                
                # Company - Sibling of h3
                company = "Unknown"
                company_container = title_el.find_next_sibling("div")
                if company_container:
                    company = company_container.get_text(strip=True)

                # Navigate Up to find Location and Details
                # title_el.parent is the Title Container
                title_container = title_el.parent
                location = "Unknown"
                
                # Details container (Location, Type)
                # Look for sibling of title_container that has 'details' in class or just next sibling
                # Based on HTML: TitleContainer -> DetailsContainer -> Salary -> Tags
                
                if title_container:
                    details_container = title_container.find_next_sibling("div")
                    # If the immediate sibling is not details (e.g. maybe check class), search or assume structure
                    # But verifying class is safer if possible. The class contains 'JobListItem_item__details'
                    
                    if details_container:
                        # Location is usually in a button
                        loc_btn = details_container.find("button")
                        if loc_btn:
                            location = loc_btn.get_text(strip=True)
                        
                        # Extract meta tags (Part-time, Internship)
                        # Divs inside details_container
                        meta_divs = details_container.find_all("div", recursive=False)
                        for div in meta_divs:
                            # If it has spans but no button, it's a tag line (Internship, Part-time)
                            if not div.find("button"):
                                spans = div.find_all("span")
                                for span in spans:
                                    tags.append(span.get_text(strip=True).upper())

                # Tags container (Tech stack) - look for div with class 'tags' inside the main job element
                tags_container = job_el.find("div", class_=re.compile(r"JobListItem_item__tags"))
                if tags_container:
                    spans = tags_container.find_all("span")
                    for span in spans:
                        tags.append(span.get_text(strip=True).upper())
                
                # Link - href attribute
                relative_link = job_el.get("href", "")
                if relative_link:
                    # Remove query parameters
                    clean_relative_link = relative_link.split("?")[0]
                    if clean_relative_link.startswith("/"):
                        full_url = f"https://bulldogjob.com{clean_relative_link}"
                    else:
                        full_url = clean_relative_link
                else:
                    full_url = "Unknown"
                
                # Tags: extract from title keywords
                tags.extend(self._extract_tags(title))
                
                # Deduplicate tags
                tags = list(set(tags))

                offers.append({
                    'title': title,
                    'company': company,
                    'location': location,
                    'tags': ", ".join(tags),
                    'link_slug': full_url,
                    'full_url': full_url
                })
                
            except Exception as e:
                print(f"Error parsing BulldogJob offer: {e}")
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
            'SALESFORCE', 'SAP', 'ORACLE', 'POWER BI', 'TABLEAU',
            'FULLSTACK', 'BACKEND', 'FRONTEND', 'TESTER', 'QA', 'MOBILE',
            'AUTOMATION', 'PHP', 'RUBY', 'SCALA', 'KOTLIN', 'SWIFT', 'FLUTTER'
        ]
        
        found_tags = []
        for tag in known_tags:
            # Check for exact word match or substring depending on tag
            if tag in title_upper:
                found_tags.append(tag)
        
        return found_tags[:5]  # Limit to 5 tags

    def run(self, url):
        html_content = self.fetch(url)
        return self.parse(html_content)
