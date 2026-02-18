# JobOfferScraper

A personal tool to aggregate junior job offers from multiple Polish tech job boards into a single Google Sheets spreadsheet. Built to avoid the daily grind of checking five different sites manually.

## What it does

The scraper visits a configurable list of URLs, extracts job listings, filters out duplicates and stale posts, and writes the results to a Google Sheet — one tab per search group. It runs in parallel across all configured URLs and skips anything already present, so re-running it is safe and fast.

Supported platforms:

- [JustJoin.it](https://justjoin.it)
- [NoFluffJobs](https://nofluffjobs.com)
- [TheProtocol.it](https://theprotocol.it)
- [BulldogJob](https://bulldogjob.com)
- [Reply Careers](https://www.reply.com)

## Project structure

```
.
├── core/
│   ├── app.py          # Main orchestration logic
│   ├── filters.py      # Recency and language filters
│   ├── parsers.py      # Config and data parsing
│   └── worker.py       # Per-URL scraping worker
├── services/
│   ├── browser.py      # Selenium driver setup
│   ├── converter.py    # Data normalization
│   └── sheets/         # Google Sheets integration
├── strategies/
│   ├── base.py         # Abstract scraping strategy
│   ├── factory.py      # URL-to-strategy routing
│   ├── justjoinit.py
│   ├── nofluff.py
│   ├── theprotocol.py
│   ├── bulldogjob.py
│   └── reply.py
├── links.json          # Search URLs configuration
├── main.py
├── Dockerfile
└── docker-compose.yml
```

## Configuration

Edit `links.json` to define your search groups. Each group maps to a separate sheet tab:

```json
[
  {
    "title": "Junior",
    "urls": [
      "https://justjoin.it/job-offers/krakow?experience-level=junior&orderBy=DESC&sortBy=newest",
      "https://nofluffjobs.com/pl/krakow?criteria=seniority%3Djunior&sort=newest"
    ]
  },
  {
    "title": "Italian",
    "urls": [
      "https://justjoin.it/job-offers/krakow?keyword=italian&orderBy=DESC&sortBy=newest"
    ]
  }
]
```

## Setup

### Prerequisites

- Python 3.11+
- Firefox (used by Selenium in headless mode)
- A Google Cloud project with the Sheets and Drive APIs enabled
- OAuth2 credentials saved as `credentials.json`

### Install dependencies

```bash
pip install -r requirements.txt
```

### Authenticate with Google

Run this once to generate `token.json`:

```bash
python generate_token.py
```

### Run

```bash
python main.py
```

To skip scraping and only reorganize existing sheets:

```bash
python main.py --organize-only
```

## Docker

If you prefer to run it containerized:

```bash
docker-compose up --build
```

The `token.json` and `credentials.json` files are mounted as volumes so you don't need to rebuild after re-authenticating.

## How duplicates are handled

Before writing anything, the scraper loads all existing entries from the spreadsheet and checks each new offer against two criteria: the full URL and the combination of title, company, and tags. If either matches, the offer is skipped. This means you can run the scraper daily without accumulating noise.

## Filters

- **Recency**: offers older than 10 days are discarded (based on the platform's own "posted X days ago" label)
- **Language**: Polish-language job titles are filtered out automatically, keeping results in English

## Testing

The project includes a pytest suite covering the core business logic — no browser or Google Sheets connection required to run it.

```bash
python -m pytest tests/ -v
```

Test coverage:

| Module | What is tested |
|---|---|
| `tests/test_filters.py` | Recency detection and Polish title filtering |
| `tests/test_parsers.py` | URL-to-sheet-title derivation and JSON config loading |
| `tests/test_deduplication.py` | Duplicate detection logic (by URL and by content) |

External dependencies (Selenium, Google Sheets API) are intentionally excluded from the test scope and would require integration tests with proper mocking or a live environment.

## License

MIT
