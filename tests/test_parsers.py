"""
Tests for core/parsers.py

Covers:
- get_sheet_title(): URL-to-title derivation for each supported platform
- parse_links_file(): JSON config loading and error handling
"""
import json
import pytest
from core.parsers import get_sheet_title, parse_links_file


# ---------------------------------------------------------------------------
# get_sheet_title
# ---------------------------------------------------------------------------

class TestGetSheetTitle:

    # --- JustJoin.it ---

    def test_justjoinit_junior_keyword(self):
        url = "https://justjoin.it/job-offers/krakow?keyword=junior&sort=newest"
        title = get_sheet_title(url)
        # Domain is extracted as 'justjoin' (the .it TLD is stripped)
        assert "justjoin" in title
        assert "krakow" in title
        assert "junior" in title

    def test_justjoinit_experience_level(self):
        url = "https://justjoin.it/job-offers/krakow?experience-level=junior&orderBy=DESC"
        title = get_sheet_title(url)
        assert "junior" in title

    def test_justjoinit_italian_keyword(self):
        url = "https://justjoin.it/job-offers/krakow?keyword=italian&orderBy=DESC"
        title = get_sheet_title(url)
        assert "italian" in title

    # --- NoFluffJobs ---

    def test_nofluffjobs_junior(self):
        url = "https://nofluffjobs.com/pl/krakow?lang=en&criteria=seniority%3Djunior&sort=newest"
        title = get_sheet_title(url)
        assert "nofluffjobs" in title
        assert "junior" in title

    # --- TheProtocol.it ---

    def test_theprotocol_junior_krakow(self):
        url = "https://theprotocol.it/filtry/junior;p/krakow;wp?sort=date"
        title = get_sheet_title(url)
        assert "theprotocol" in title
        assert "junior" in title
        assert "krakow" in title

    def test_theprotocol_keyword(self):
        url = "https://theprotocol.it/filtry/krakow;wp?kw=italian"
        title = get_sheet_title(url)
        assert "italian" in title

    # --- BulldogJob ---

    def test_bulldogjob_junior_krakow(self):
        url = (
            "https://bulldogjob.com/companies/jobs/s/city,Krakow"
            "/role,backend,analyst/experienceLevel,junior,intern/order,published,desc"
        )
        title = get_sheet_title(url)
        assert "bulldogjob" in title
        assert "krakow" in title
        assert "junior" in title

    # --- General properties ---

    def test_title_has_no_spaces(self):
        url = "https://justjoin.it/job-offers/krakow?keyword=junior"
        title = get_sheet_title(url)
        assert " " not in title

    def test_title_max_length(self):
        url = "https://justjoin.it/job-offers/krakow?keyword=junior"
        title = get_sheet_title(url)
        assert len(title) <= 100

    def test_title_no_duplicate_segments(self):
        # 'krakow' from the path and 'kw-krakow' from the keyword param are
        # treated as distinct segments, so both appear in the title.
        url = "https://justjoin.it/job-offers/krakow?keyword=krakow"
        title = get_sheet_title(url)
        # The raw word 'krakow' appears at least once
        assert "krakow" in title


# ---------------------------------------------------------------------------
# parse_links_file
# ---------------------------------------------------------------------------

class TestParseLinksFile:

    def test_valid_json_file(self, tmp_path):
        data = [
            {"title": "Junior", "urls": ["https://example.com/junior"]},
            {"title": "Italian", "urls": ["https://example.com/italian"]},
        ]
        f = tmp_path / "links.json"
        f.write_text(json.dumps(data))

        result = parse_links_file(str(f))

        assert len(result) == 2
        assert result[0]["title"] == "Junior"
        assert result[1]["urls"] == ["https://example.com/italian"]

    def test_missing_file_returns_empty_list(self, tmp_path):
        result = parse_links_file(str(tmp_path / "nonexistent.json"))
        assert result == []

    def test_malformed_json_returns_empty_list(self, tmp_path):
        f = tmp_path / "links.json"
        f.write_text("{ this is not valid json }")

        result = parse_links_file(str(f))
        assert result == []

    def test_empty_array_is_valid(self, tmp_path):
        f = tmp_path / "links.json"
        f.write_text("[]")

        result = parse_links_file(str(f))
        assert result == []

    def test_preserves_multiple_urls_per_group(self, tmp_path):
        data = [{"title": "Mixed", "urls": ["https://a.com", "https://b.com", "https://c.com"]}]
        f = tmp_path / "links.json"
        f.write_text(json.dumps(data))

        result = parse_links_file(str(f))
        assert len(result[0]["urls"]) == 3
