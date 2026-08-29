import os
import json
from urllib.parse import urlparse, parse_qs
import re

def get_sheet_title(url):
    """Derives a readable sheet title from the URL parameters."""
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    
    parts = []
    
    # 1. Source (Domain)
    domain = parsed.netloc.replace("www.", "").split(".")[0]
    parts.append(domain)
    
    # 2. Extract keywords based on domain
    if "justjoin.it" in url:
        # /job-offers/krakow?keyword=junior...
        path_segments = parsed.path.split('/')
        if 'krakow' in path_segments:
            parts.append("krakow")
        elif len(path_segments) > 2:
             parts.append(path_segments[-1])
             
        keyword = qs.get("keyword", [""])[0]
        exp = qs.get("experience-level", [""])[0]
        if keyword: parts.append(f"kw-{keyword}")
        if exp: parts.append(f"exp-{exp}")
        
    elif "bulldogjob.com" in url:
        # /companies/jobs/s/city,Krakow/role,backend...
        # Extract meaningful parts from the long path
        path = parsed.path
        if "city,Krakow" in path:
            parts.append("krakow")
        
        # Example extracting role
        # /role,backend,analyst...
        role_start = path.find("role,")
        if role_start != -1:
            role_end = path.find("/", role_start)
            if role_end == -1: role_end = len(path)
            roles = path[role_start+5:role_end]
            # Just take the first one or "custom"
            first_role = roles.split(",")[0]
            parts.append(first_role)

        if "experienceLevel,junior" in path:
            parts.append("junior")

    elif "nofluffjobs.com" in url:
        # /pl/krakow?criteria=seniority%3Djunior
        # Extract location from path
        for segment in parsed.path.split('/'):
            if segment in ['pl', 'job']: continue
            if segment: parts.append(segment)
            
        # Extract criteria (e.g. seniority=junior)
        criteria = qs.get("criteria", [""])[0] # "seniority=junior"
        if criteria:
            cr_parts = criteria.split('=')
            if len(cr_parts) > 1:
                parts.append(cr_parts[1])
            else:
                parts.append(criteria)

    elif "theprotocol.it" in url:
        # /filtry/junior;p/krakow;wp
        # Splitting path: ['', 'filtry', 'junior;p', 'krakow;wp']
        # We need "junior", "krakow"
        path_segments = parsed.path.split('/')
        for seg in path_segments:
            if seg in ['', 'filtry']: continue
            # "junior;p" -> "junior"
            clean_seg = seg.split(';')[0]
            if clean_seg:
                parts.append(clean_seg)
        
        # Extract keyword (kw)
        kw = qs.get("kw", [""])[0]
        if kw:
            parts.append(f"kw-{kw}")
    else:
        # Fallback
        parts.append(parsed.path.replace('/', '-'))

    # Sanitize and join
    # Filter duplicates and empty
    clean_parts = []
    seen = set()
    for p in parts:
        p = p.lower().strip()
        if p and p not in seen:
            clean_parts.append(p)
            seen.add(p)
            
    title = "-".join(clean_parts)
    title = re.sub(r'[^\w\-]', '', title)
    return title[:100]

def parse_links_file(filepath):
    """
    Parses the links file from JSON format.
    Expected structure:
    [
      {"title": "Sheet Name", "urls": ["url1", "url2"],
       "disabled_urls": ["url3"]},
      ...
    ]
    """
    if not os.path.exists(filepath):
        # Fallback to old 'links' file if json doesn't exist
        old_links = "links"
        if os.path.exists(old_links):
            print(f"Warning: '{filepath}' not found. Falling back to legacy '{old_links}' format.")
            return parse_links_file_legacy(old_links)
        return []

    try:
        with open(filepath, "r") as f:
            data = json.load(f)
            # JSON has no comment syntax; disabled_urls keeps inactive sources
            # documented without sending them to the scraper.
            for group in data:
                disabled_urls = set(group.get("disabled_urls", []))
                group["urls"] = [url for url in group.get("urls", [])
                                 if url not in disabled_urls]
            return data
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {filepath}: {e}")
        return []

def parse_links_file_legacy(filepath):
    """
    Parses the legacy links file. Supports two formats:
    1. Legacy: List of URLs
    2. Grouped: INI-style sections
    """
    groups = []
    current_group = {'title': None, 'urls': []}
    
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
                
            # Check for Header [Title]
            if line.startswith("[") and line.endswith("]"):
                # Save previous group if it has URLs
                if current_group['urls']:
                    groups.append(current_group)
                
                # Start new group
                title = line[1:-1].strip()
                current_group = {'title': title, 'urls': []}
            else:
                # It's a URL
                current_group['urls'].append(line)
    
    # Add last group
    if current_group['urls']:
        groups.append(current_group)
        
    return groups
