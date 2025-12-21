import re
import os
from .base import ScrapingStrategy
from utils.converter import html_to_markdown, sanitize_filename

class JustJoinITStrategy(ScrapingStrategy):
    def fetch(self, url):
        print(f"Fetching {url}")
        self.driver.get(url)
        return self.driver.page_source

    def parse(self, markdown_content):
        offers = []
        
        # New Regex Strategy: Capture the entire block from "### Title" specific structure
        # Structure:
        # ### Title
        # Salary
        # ...
        # ---
        # Company
        # Location
        # ... (Tags, Age)
        # ](/job-offer/slug)
        
        # We look for the start "### " and the end "](/job-offer/"
        
        offer_pattern = re.compile(r'### (.*?)\n(.*?)(?=\]\(/job-offer/(.*?)\))', re.DOTALL)
        # Note: We need to capture the slug too, so let's adjust:
        offer_pattern = re.compile(r'### (.*?)\n(.*?)]\(/job-offer/(.*?)\)', re.DOTALL)
        
        matches = offer_pattern.findall(markdown_content)
        
        for match in matches:
            title = match[0].strip()
            block_content = match[1].strip()
            slug = match[2].strip()
            
            lines = [l.strip() for l in block_content.split('\n') if l.strip()]
            
            # Defaults
            salary = "Undisclosed Salary"
            company = "Unknown"
            location = "Unknown"
            posted_age = "Unknown"
            tags = []
            
            # Simple State Machine / Line Text Analysis
            # Usually:
            # 0: Salary (e.g. "12 - 14 EUR/h" or "Undisclosed Salary")
            # 1: duplicated salary often?
            # Find "---" separator
            
            # Let's try to identify by content
            # Salary usually contains numbers or "Undisclosed"
            # Company is usually early after separator
            
            # Let's split by "---" separator which is prevalent in markdown for horizontal rules
            block_parts = block_content.split('---')
            
            if len(block_parts) >= 2:
                # Part 0 is usually Salary
                salary_part = block_parts[0].strip()
                salary_lines = [l.strip() for l in salary_part.split('\n') if l.strip()]
                if salary_lines:
                    salary = salary_lines[0] # First line usually
                
                # Part 1 is Company, Location, Age, Tags
                details_part = block_parts[1].strip()
                details_lines = [l.strip() for l in details_part.split('\n') if l.strip()]
                
                if len(details_lines) >= 1:
                    company = details_lines[0]
                if len(details_lines) >= 2:
                    location = details_lines[1]
                
                # Remaining lines could be Age or Tags
                remaining = details_lines[2:]
                
                for line in remaining:
                    # Check for Age
                    if ("left" in line and any(c.isdigit() for c in line)) or "New" in line:
                         posted_age = line
                    elif "1-click Apply" in line:
                        continue
                    elif len(line) < 30: # Tag heuristic
                        tags.append(line)
            else:
                # Fallback if no separator
                if lines:
                    salary = lines[0]
            
            # Safety cleanup
            exclude_terms = [location, posted_age, company, "1-click Apply", "Undisclosed Salary", "EUR", "PLN", "USD"]
            tags = [t for t in tags if t not in exclude_terms]

            offer = {
                'title': title,
                'salary': salary,
                'company': company,
                'location': location,
                'posted_age': posted_age,
                'tags': ", ".join(tags[:5]),
                'link_slug': slug,
                'full_url': f"https://justjoin.it/job-offer/{slug}"
            }
            offers.append(offer)

        return offers

    def run(self, url, save_dir="data"):
        # 1. Fetch
        html = self.fetch(url)
        
        # 2. Convert to Markdown
        md_content = html_to_markdown(html)
        
        # 3. Save Markdown (Optional but useful for debugging/storage)
        filename = f"{sanitize_filename(url)}.md"
        filepath = os.path.join(save_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"Saved markdown to {filepath}")
        
        # 4. Parse
        offers = self.parse(md_content)
        return offers
