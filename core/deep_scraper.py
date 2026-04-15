"""
deep_scraper.py – orchestratore del deep scraping delle Job Description.

Delegaa la logica di estrazione a una DeepScrapingStrategy per-sito,
recuperata tramite get_deep_strategy() (strategies/deep_factory.py).
"""

from services.browser import get_driver
from urllib.parse import urlparse

from strategies.deep_factory import get_deep_strategy


def get_domain(url: str) -> str:
    """Estrae il dominio (es. uber.com) da una URL."""
    return urlparse(url).netloc.replace("www.", "")


def fetch_full_description(url: str) -> str:
    """
    Esegue il deep scraping della Job Description per *url*.

    Crea un driver Selenium, delega l'estrazione alla strategia
    specifica del sito (o al fallback generico) e restituisce
    il testo pulito della JD.
    """
    domain = get_domain(url)
    print(f"Deep scraping (Strategy: {domain}) per: {url}")

    driver = get_driver(headless=True)
    try:
        strategy = get_deep_strategy(url, driver)
        raw_text = strategy.extract(url)
        return cleanup_text(raw_text)
    except Exception as e:
        print(f"  [Error] Fallimento scraping per {url}: {e}")
        return ""
    finally:
        driver.quit()


def cleanup_text(text: str) -> str:
    """Rimuove boilerplate comune che potrebbe inquinare la JD."""
    noise_indicators = [
        "cookie", "privacy policy", "all rights reserved",
        "nasza witryna", "zgodę na", "apply now", "aplikuj",
    ]
    lines = text.split("\n")
    filtered = [
        line for line in lines
        if not (any(ind in line.lower() for ind in noise_indicators) and len(line) < 100)
    ]
    return "\n".join(filtered).strip()


if __name__ == "__main__":
    url = (
        "https://theprotocol.it/szczegoly/praca/"
        "data-scientist-warszawa-aleje-jerozolimskie-44,"
        "oferta,dc570000-1d37-3e55-45dd-08de9abff320"
    )
    print(fetch_full_description(url))
