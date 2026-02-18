"""
Tests for the deduplication logic in core/app.py

JobScraperApp._filter_offers() is the core business logic that decides
which scraped offers are genuinely new. We test it in isolation by
instantiating the app with mocked args and no real services.
"""
import pytest
from unittest.mock import MagicMock, patch
from core.app import JobScraperApp


@pytest.fixture
def app():
    """Return a JobScraperApp instance without triggering argparse or services."""
    with patch("argparse.ArgumentParser.parse_args", return_value=MagicMock(organize_only=False)):
        instance = JobScraperApp()
    return instance


@pytest.fixture
def base_offer():
    return {
        "title": "Junior Python Developer",
        "company": "Acme Corp",
        "tags": "Python, Django",
        "full_url": "https://example.com/jobs/123",
    }


class TestFilterOffers:

    def test_new_offer_is_accepted(self, app, base_offer):
        new_offers, skipped = app._filter_offers([base_offer], set(), [])
        assert len(new_offers) == 1
        assert skipped == 0

    def test_duplicate_url_is_skipped(self, app, base_offer):
        existing_slugs = {base_offer["full_url"]}
        new_offers, skipped = app._filter_offers([base_offer], existing_slugs, [])
        assert len(new_offers) == 0
        assert skipped == 1

    def test_duplicate_content_is_skipped(self, app, base_offer):
        existing_records = [{
            "title": base_offer["title"],
            "company": base_offer["company"],
            "tags": base_offer["tags"],
        }]
        new_offers, skipped = app._filter_offers([base_offer], set(), existing_records)
        assert len(new_offers) == 0
        assert skipped == 1

    def test_same_title_different_company_is_accepted(self, app, base_offer):
        existing_records = [{
            "title": base_offer["title"],
            "company": "Different Company",
            "tags": base_offer["tags"],
        }]
        new_offers, skipped = app._filter_offers([base_offer], set(), existing_records)
        assert len(new_offers) == 1

    def test_same_company_different_title_is_accepted(self, app, base_offer):
        existing_records = [{
            "title": "Senior Python Developer",
            "company": base_offer["company"],
            "tags": base_offer["tags"],
        }]
        new_offers, skipped = app._filter_offers([base_offer], set(), existing_records)
        assert len(new_offers) == 1

    def test_accepted_offer_is_added_to_existing_slugs(self, app, base_offer):
        existing_slugs = set()
        app._filter_offers([base_offer], existing_slugs, [])
        # After processing, the slug should be tracked to prevent re-adding
        assert base_offer["full_url"] in existing_slugs

    def test_accepted_offer_is_added_to_existing_records(self, app, base_offer):
        existing_records = []
        app._filter_offers([base_offer], set(), existing_records)
        assert len(existing_records) == 1
        assert existing_records[0]["title"] == base_offer["title"]

    def test_multiple_offers_mixed(self, app, base_offer):
        offer_new = {
            "title": "DevOps Engineer",
            "company": "NewCo",
            "tags": "Docker, K8s",
            "full_url": "https://example.com/jobs/999",
        }
        existing_slugs = {base_offer["full_url"]}

        new_offers, skipped = app._filter_offers(
            [base_offer, offer_new], existing_slugs, []
        )
        assert len(new_offers) == 1
        assert new_offers[0]["title"] == "DevOps Engineer"
        assert skipped == 1

    def test_empty_input_returns_empty(self, app):
        new_offers, skipped = app._filter_offers([], set(), [])
        assert new_offers == []
        assert skipped == 0
