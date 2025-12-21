from selenium import webdriver
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import re



def sanitize_filename(url):
    # Remove protocol and replace non-alphanumeric chars with underscore
    name = re.sub(r'https?://', '', url)
    name = re.sub(r'[^\w\-_\. ]', '_', name)
    return name[:100]  # Limit length

def get_page_content(url):
    print(f"Fetching {url}")
    
    options = webdriver.FirefoxOptions()
    options.add_argument("-headless")
    driver = webdriver.Firefox(options=options)

    try:
        driver.get(url)
        html_content = driver.page_source
    finally:
        driver.quit()

    # Parse and clean with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove scripts and styles for cleaner content
    for script in soup(["script", "style", "noscript"]):
        script.extract()

    # Convert to Markdown
    markdown_content = md(str(soup), heading_style="ATX")
    
    # Clean up excessive newlines
    markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)

    filename = f"{sanitize_filename(url)}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"Saved content to {filename}")
    return markdown_content

get_page_content("https://theprotocol.it/filtry/junior;p/krakow;wp?sort=date")