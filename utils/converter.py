import re
from bs4 import BeautifulSoup
from markdownify import markdownify as md

def sanitize_filename(url):
    # Remove protocol and replace non-alphanumeric chars with underscore
    name = re.sub(r'https?://', '', url)
    name = re.sub(r'[^\w\-_\. ]', '_', name)
    return name[:100]  # Limit length

def html_to_markdown(html_content):
    # Parse and clean with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove scripts and styles for cleaner content
    for script in soup(["script", "style", "noscript"]):
        script.extract()

    # Convert to Markdown
    markdown_content = md(str(soup), heading_style="ATX")
    
    # Clean up excessive newlines
    markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
    
    return markdown_content
