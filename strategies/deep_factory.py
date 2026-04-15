"""
Factory for deep-scraping (job description) strategies.

Each site that appears in links.json as a source of individual job offer
URLs needs a corresponding DeepScrapingStrategy subclass registered here.

Supported sites (mirrors links.json):
  - theprotocol.it
  - justjoin.it
  - nofluffjobs.com
  - bulldogjob.com
  - builtin.com
  - reply.com
  - uber.com
  - accenture.com
  - reversegroup.io   (careers.reversegroup.io)
  - myworkdayjobs.com (Motorola)

Usage:
    from strategies.deep_factory import get_deep_strategy
    strategy = get_deep_strategy(job_url, driver)
    description = strategy.extract(job_url)
"""

from urllib.parse import urlparse
from selenium.webdriver.remote.webdriver import WebDriver

from strategies.base_deep import DeepScrapingStrategy


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _domain(url: str) -> str:
    """Return the bare domain (without 'www.') for a URL."""
    return urlparse(url).netloc.replace("www.", "")


# ---------------------------------------------------------------------------
# Lazy imports – each strategy module is imported only when actually needed
# so that missing optional dependencies don't break the whole factory.
# ---------------------------------------------------------------------------

def get_deep_strategy(url: str, driver: WebDriver) -> DeepScrapingStrategy:
    """
    Return the appropriate DeepScrapingStrategy instance for *url*.

    Falls back to a generic heuristic strategy when no site-specific
    implementation exists yet.
    """
    domain = _domain(url)

    if "theprotocol.it" in domain:
        from strategies.deep.theprotocol import TheProtocolDeepStrategy
        return TheProtocolDeepStrategy(driver)

    if "justjoin.it" in domain:
        from strategies.deep.justjoinit import JustJoinITDeepStrategy
        return JustJoinITDeepStrategy(driver)

    if "nofluffjobs.com" in domain:
        from strategies.deep.nofluff import NoFluffDeepStrategy
        return NoFluffDeepStrategy(driver)

    if "bulldogjob.com" in domain:
        from strategies.deep.bulldogjob import BulldogJobDeepStrategy
        return BulldogJobDeepStrategy(driver)

    if "builtin.com" in domain:
        from strategies.deep.builtin import BuiltInDeepStrategy
        return BuiltInDeepStrategy(driver)

    if "reply.com" in domain:
        from strategies.deep.reply import ReplyDeepStrategy
        return ReplyDeepStrategy(driver)

    if "uber.com" in domain:
        from strategies.deep.uber import UberDeepStrategy
        return UberDeepStrategy(driver)

    if "accenture.com" in domain:
        from strategies.deep.accenture import AccentureDeepStrategy
        return AccentureDeepStrategy(driver)

    if "reversegroup.io" in domain:
        from strategies.deep.reversegroup import ReverseGroupDeepStrategy
        return ReverseGroupDeepStrategy(driver)

    if "myworkdayjobs.com" in domain:
        from strategies.deep.motorola import MotorolaDeepStrategy
        return MotorolaDeepStrategy(driver)

    # -----------------------------------------------------------------------
    # Generic fallback – used for unknown / future sites
    # -----------------------------------------------------------------------
    from strategies.deep.generic import GenericDeepStrategy
    return GenericDeepStrategy(driver)
