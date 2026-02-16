import re
from html import unescape

def html_to_markdown(html_content):
    """
    Converts basic HTML tags to Markdown.
    Supports: <br>, <p>, <ul>, <li>, <strong>, <b>, <em>, <i>, <a>
    """
    if not html_content:
        return ""
        
    text = unescape(html_content)
    
    # <br> -> newline
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    
    # <p> -> double newline
    text = re.sub(r'<p[^>]*>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '', text, flags=re.IGNORECASE)
    
    # <ul> -> newline
    text = re.sub(r'<ul[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</ul>', '\n', text, flags=re.IGNORECASE)
    
    # <li> -> bullet point
    text = re.sub(r'<li[^>]*>', '\n- ', text, flags=re.IGNORECASE)
    text = re.sub(r'</li>', '', text, flags=re.IGNORECASE)
    
    # <strong>, <b> -> **text**
    text = re.sub(r'<(strong|b)[^>]*>(.*?)</\1>', r'**\2**', text, flags=re.IGNORECASE)
    
    # <em>, <i> -> *text*
    text = re.sub(r'<(em|i)[^>]*>(.*?)</\1>', r'*\2*', text, flags=re.IGNORECASE)
    
    # <a> -> [text](href)
    # Simple regex, might need bs4 for robust parsing if complex
    def link_repl(match):
        href = match.group(1)
        content = match.group(2)
        return f"[{content}]({href})"
        
    text = re.sub(r'<a[^>]*href=["\'](.*?)["\'][^>]*>(.*?)</a>', link_repl, text, flags=re.IGNORECASE)
    
    # Remove remaining tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def sanitize_filename(name):
    """
    Removes illegal characters for filenames.
    """
    return re.sub(r'[<>:"/\\|?*]', '', name).strip()
