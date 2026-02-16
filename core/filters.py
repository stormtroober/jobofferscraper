import re

def is_recent(offer, days_limit=10):
    """Returns True if offer is recent (<= days_limit) or age is unknown/Fresh."""
    age_str = offer.get('posted_age', '').lower()
    
    if "new" in age_str:
        return True
        
    if "left" in age_str:
        # "27d left" -> typical validity is 30 days. So posted approx 3 days ago.
        # If "10d left" -> posted 20 days ago.
        # Wait, if validity is 30 days:
        # > 20d left = posted < 10 days ago.
        # checks: "11d left" (posted 19 days ago) -> False
        # checks: "21d left" (posted 9 days ago) -> True
        
        # Regex to find number
        match = re.search(r'(\d+)d', age_str)
        if match:
            days_left = int(match.group(1))
            days_posted_ago = 30 - days_left
            if days_posted_ago > days_limit:
                return False
            # Also if it says "1d left" -> posted 29 days ago -> False
            return True
            
    # For "1w ago" type strings if they exist (JustJoin usually shows "Xd left")
    return True

def is_polish_title(title):
    """
    Detects if the title is in Polish based on diacritics and keywords.
    Excludes 'ó' from diacritic check to avoid flagging city names like 'Kraków'.
    """
    title_lower = title.lower()
    
    # 1. Polish diacritics (excluding ó)
    # ą, ć, ę, ł, ń, ś, ź, ż
    if re.search(r'[ąćęłńśźż]', title_lower):
        return True
        
    # 2. Polish specific words (ASCII or with ó)
    polish_keywords = [
        'programista', 'starszy', 'specjalista', 'kierownik', 'analityk', 
        'architekt', 'konsultant', 'serwisant', 'doradca', 'praktykant', 
        'praca', 'zdalna', 'hybrydowa', 'stacjonarna', 'zespołu', r'ds\.',
        'asystent', 'ekspert', 'referent', 'koordynator'
    ]
    
    # Simple word bound check
    for keyword in polish_keywords:
        # \b matches word boundary
        if re.search(r'\b' + keyword + r'\b', title_lower):
            return True
            
    return False
