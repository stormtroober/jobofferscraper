"""
Tests for core/filters.py

Covers:
- is_recent(): recency detection based on age strings
- is_polish_title(): Polish language detection in job titles
"""
import pytest
from core.filters import is_recent, is_polish_title


# ---------------------------------------------------------------------------
# is_recent
# ---------------------------------------------------------------------------

class TestIsRecent:
    """Offers with 'new' label or unknown age should always pass."""

    def test_new_label_is_recent(self):
        assert is_recent({"posted_age": "new"}) is True

    def test_new_label_case_insensitive(self):
        assert is_recent({"posted_age": "New"}) is True

    def test_missing_age_is_recent(self):
        # Unknown age -> we assume it's fine
        assert is_recent({"posted_age": ""}) is True

    def test_no_age_key_is_recent(self):
        assert is_recent({}) is True

    # --- "X days left" logic (validity window = 30 days) ---

    def test_25d_left_is_recent(self):
        # 30 - 25 = 5 days ago -> recent
        assert is_recent({"posted_age": "25d left"}) is True

    def test_21d_left_is_recent(self):
        # 30 - 21 = 9 days ago -> recent (boundary)
        assert is_recent({"posted_age": "21d left"}) is True

    def test_20d_left_is_not_recent(self):
        # 30 - 20 = 10 days ago -> exactly at limit, should be excluded
        assert is_recent({"posted_age": "20d left"}, days_limit=9) is False

    def test_5d_left_is_not_recent(self):
        # 30 - 5 = 25 days ago -> too old
        assert is_recent({"posted_age": "5d left"}) is False

    def test_1d_left_is_not_recent(self):
        # 30 - 1 = 29 days ago -> definitely too old
        assert is_recent({"posted_age": "1d left"}) is False

    def test_custom_days_limit(self):
        # With a stricter limit of 5 days:
        # "24d left" -> posted 6 days ago -> older than limit -> False
        assert is_recent({"posted_age": "24d left"}, days_limit=5) is False
        # "26d left" -> posted 4 days ago -> within limit -> True
        assert is_recent({"posted_age": "26d left"}, days_limit=5) is True


# ---------------------------------------------------------------------------
# is_polish_title
# ---------------------------------------------------------------------------

class TestIsPolishTitle:
    """English titles should pass; Polish titles should be detected."""

    # --- Should NOT be flagged as Polish ---

    def test_english_title_passes(self):
        assert is_polish_title("Junior Python Developer") is False

    def test_english_with_krakow_passes(self):
        # 'ó' in Kraków should not trigger Polish detection
        assert is_polish_title("Backend Developer - Kraków") is False

    def test_english_with_numbers_passes(self):
        assert is_polish_title("Data Engineer L2 (Remote)") is False

    def test_empty_string_passes(self):
        assert is_polish_title("") is False

    # --- Should BE flagged as Polish ---

    def test_polish_diacritic_ą(self):
        assert is_polish_title("Programistą Python") is True

    def test_polish_diacritic_ę(self):
        assert is_polish_title("Inżynier danych") is True

    def test_polish_diacritic_ł(self):
        assert is_polish_title("Młodszy programista") is True

    def test_polish_keyword_programista(self):
        assert is_polish_title("Programista Java") is True

    def test_polish_keyword_starszy(self):
        assert is_polish_title("Starszy Developer") is True

    def test_polish_keyword_specjalista(self):
        assert is_polish_title("Specjalista ds. IT") is True

    def test_polish_keyword_analityk(self):
        assert is_polish_title("Analityk Biznesowy") is True

    def test_polish_keyword_case_insensitive(self):
        assert is_polish_title("PROGRAMISTA Backend") is True
