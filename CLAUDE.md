# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the scraper (full mode)
python main.py

# Run with custom worker count
python main.py --workers 4

# Skip scraping, only reorganize sheets
python main.py --organize-only

# Evaluate SAVE-status offers against master CV using local LLM
python main.py --eval

# Run all tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_filters.py -v

# Run live strategy tests (requires internet)
python -m pytest tests/test_strategies_live.py -v
```

Dependencies are managed via `uv` (`uv.lock` present) but `pip install -r requirements.txt` also works. Python 3.13 is used.

## Environment setup (uv)

`uv` gestisce il virtualenv automaticamente — non serve attivarlo manualmente per eseguire i comandi.

```bash
# Crea il venv
uv venv

# Attiva il venv (sempre necessario)
source .venv/bin/activate

# Installa le dipendenze
uv pip install -r requirements.txt
```

Il venv è in `.venv/` nella root del progetto. Attivarlo sempre con `source` prima di eseguire qualsiasi comando.

## Architecture

The app has three operational modes controlled by CLI flags, all routed through `core/app.py`:

1. **Full scrape** (default): scrapes all URLs in `links.json` in parallel, deduplicates against the spreadsheet, writes new offers.
2. **Organize-only** (`--organize-only`): skips scraping, only reorders/formats existing sheets.
3. **Eval** (`--eval`): reads offers marked `SAVE` from Sheets, deep-scrapes their individual job pages, runs the local LLM evaluator, and prints a match report.

### Scraping layer (`strategies/`)

Two parallel factory patterns exist:

- **Listing strategies** (`strategies/factory.py` → `strategies/*.py`): scrape job listing pages to extract offer summaries. Each strategy implements `ScrapingStrategy` (abstract base at `strategies/base.py`) with `fetch()`, `parse()`, and `run()`. The factory maps domain to strategy; unrecognized domains default to `JustJoinITStrategy`.

- **Deep strategies** (`strategies/deep_factory.py` → `strategies/deep/*.py`): scrape individual job offer pages to extract the full job description text. Each implements `DeepScrapingStrategy` (`strategies/base_deep.py`). Falls back to `GenericDeepStrategy` for unknown domains.

When adding support for a new site, you need entries in **both** factories and **both** strategy directories. Use `strategies/deep/_stub_template.py` as a starting point for deep strategies.

### Data flow

```
links.json → core/app.py → core/worker.py (ThreadPoolExecutor)
                                  ↓
                    strategies/factory.py → site strategy
                                  ↓
                    core/filters.py (Polish title filter, recency)
                                  ↓
                    services/sheets/ (dedup + write)
```

The `core/worker.py` creates one Selenium Firefox driver per URL and tears it down after. Default limit is 50 offers per URL (30 for theprotocol.it).

### Sheets layer (`services/sheets/`)

- `GoogleSheetsClient` (`client.py`): handles OAuth2 auth and spreadsheet connection.
- `SheetFormatter` (`formatter.py`): handles visual formatting, row reordering by Status.
- `SheetManager` (`manager.py`): high-level operations — deduplication (by URL and by title+company+tags), adding offers, moving DISCARD/OUT rows to Trash sheet, fetching SAVE offers.

Sheet columns: `Title | Company | Tags | Status | Link`. Status values in use: `NEW`, `SAVE`, `DISCARD`, `OUT`.

### Eval / LLM layer

`core/eval_runner.py` orchestrates eval mode: fetches SAVE offers from Sheets → calls `core/deep_scraper.py` to get full JDs → passes to `services/llm.py` (`LocalLLMEvaluator` using `llama-cpp-python` with a local GGUF model at `~/llama.cpp/models/gemma_e4b_q8.gguf`). The candidate background document is at `data/master_cv.md`.

## Configuration

- `links.json`: defines search groups. Each group has a `title` (→ sheet tab name) and a list of `urls` to scrape.
- `credentials.json` + `token.json`: Google OAuth2 credentials (not committed).

## Testing notes

`tests/test_strategies_live.py` hits live websites — it will fail without internet access and may break when site selectors change. Business logic tests (`test_filters.py`, `test_parsers.py`, `test_deduplication.py`) are offline-safe.
