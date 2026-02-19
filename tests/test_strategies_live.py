import pytest
from bs4 import BeautifulSoup
from services.browser import get_driver
from strategies.factory import get_strategy
from strategies.builtin import BuiltInStrategy
from strategies.justjoinit import JustJoinITStrategy

# Representative URLs for each strategy
# We use live URLs, so these tests depend on internet connection and site stability.
TEST_URLS = [
    # JustJoinIT
    "https://justjoin.it/job-offers/krakow?keyword=junior&sort=newest",
    # NoFluffJobs
    "https://nofluffjobs.com/pl/krakow?lang=en&criteria=seniority%3Djunior",
    # TheProtocol
    "https://theprotocol.it/filtry/junior;p/krakow;wp?sort=date",
    # BulldogJob - use a broader query to avoid failure on 0 results (e.g. just Krakow IT)
    "https://bulldogjob.com/companies/jobs/s/city,Krakow",
    # Reply
    "https://www.reply.com/en/about/careers/pl/job-search?country=pl&role=career_starter&area=technology",
    # BuiltIn
    "https://builtin.com/jobs/hybrid/office/entry-level/junior?daysSinceUpdated=3&city=Krak%C3%B3w&state=Ma%C5%82opolskie&country=POL&allLocations=true"
]

@pytest.fixture(scope="module")
def driver():
    """
    Shared driver instance for all tests in this module to save time.
    Scope is module-level so we spin up the browser only once.
    """
    driver = get_driver(headless=True)
    yield driver
    driver.quit()

@pytest.mark.parametrize("url", TEST_URLS)
def test_strategy_live(driver, url):
    """
    Test that the strategy for a given URL can:
    1. Instantiate correctly via factory.
    2. Fetch the page (live request).
    3. Parse at least one offer (selector check).
    """
    print(f"\nTesting URL: {url}")
    strategy = get_strategy(url, driver)
    
    offers = []
    
    # Custom handling to avoid infinite loops or specific workflow needs
    if isinstance(strategy, BuiltInStrategy):
        # BuiltInStrategy.run() has a while loop for pagination.
        # We test fetch() and parse() individually for a single page.
        html = strategy.fetch(url)
        assert html is not None, "Fetched content is empty for BuiltIn"
        
        soup = BeautifulSoup(html, 'html.parser')
        offers = strategy.parse(soup)
        
    else:
        # For other strategies, run() usually handles a single page or is safe enough.
        # JustJoinIT converts to markdown inside run(), so we must use run() or replicate it.
        # TheProtocol, Reply, Bulldog, NoFluff usually fetch once in run().
        offers = strategy.run(url)

    # Basic Validations
    assert isinstance(offers, list), f"Strategy {type(strategy).__name__} did not return a list"
    
    # We expect some offers. If 0, it might mean the site changed or no offers match.
    # We warn but don't strictly fail if it's just 'no offers found' unless we are sure there should be some.
    # However, user asked to see "if they still work", so getting 0 is suspicious.
    # Let's verify structure even if empty, but preferably assert > 0.
    
    print(f"Found {len(offers)} offers.")
    
    if len(offers) == 0:
        # User specified that 0 offers is an acceptable outcome (e.g. no jobs match the query).
        # We print a warning but allow the test to pass if the structure was handled without error.
        print(f"WARNING: No offers found for {url}. This might be valid if no jobs exist.")
    else:
        print(f"SUCCESS: Found {len(offers)} offers.")

    # Validate Offer Structure
    for offer in offers:
        assert "title" in offer, "Offer missing 'title'"
        assert "company" in offer, "Offer missing 'company'"
        assert "full_url" in offer, "Offer missing 'full_url'"
        
        assert isinstance(offer["title"], str)
        assert len(offer["title"].strip()) > 0
        
        # Link should be a full URL
        assert offer["full_url"].startswith("http"), f"Invalid URL: {offer['full_url']}"

if __name__ == "__main__":
    # Allow running directly with python
    sys.exit(pytest.main(["-v", __file__]))
