from strategies.nofluff import NoFluffJobsStrategy
from strategies.builtin import BuiltInStrategy
from strategies.pracuj import PracujStrategy
from strategies.hitachi import HitachiStrategy
from strategies.pepsico import PepsiCoStrategy
from strategies.fedex import FedExStrategy


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
    elif "careers.hitachi.com" in url:
        return HitachiStrategy(driver)
    elif "pepsicojobs.com" in url:
        return PepsiCoStrategy(driver)
    elif "careers.fedex.com" in url:
        return FedExStrategy(driver)
    else:
        raise ValueError(f"No scraping strategy available for URL: {url}")
