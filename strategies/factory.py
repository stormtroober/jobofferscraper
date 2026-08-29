from strategies.nofluff import NoFluffJobsStrategy
from strategies.builtin import BuiltInStrategy
from strategies.pracuj import PracujStrategy


def get_strategy(url, driver):
    """
    Returns the appropriate strategy instance for the given URL.
    """
    if "nofluffjobs.com" in url:
        return NoFluffJobsStrategy(driver)
    elif "builtin.com" in url:
        return BuiltInStrategy(driver)
    elif "pracuj.pl" in url:
        return PracujStrategy(driver)
    else:
        raise ValueError(f"No scraping strategy available for URL: {url}")
