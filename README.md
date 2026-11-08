# Freelance Bots Portfolio

Three working Python automation demos: a website scraper, a price change monitor, and a private Telegram expense bot. Built to demonstrate practical freelance tasks with readable code, persistent storage, offline examples, and automated tests.

**[Visit the portfolio website](https://iseudueneue2-ux.github.io/freelance-bots-portfolio/)** — Ukrainian project showcase with interactive browser demos. The static website lives in `site/` and is deployed through GitHub Pages.

[Українська інструкція](docs/README.uk.md) · [Demo output](examples/demo-output.md)

| Project | Client task | What it delivers |
| --- | --- | --- |
| [Catalog scraper](bots/scraper.py) | Collect product data from a website | Paginated extraction to Excel-friendly CSV and JSON |
| [Price monitor](bots/price_monitor.py) | Detect price changes between runs | SQLite baseline and a JSON report of increases/decreases |
| [Telegram expense bot](bots/expense_bot.py) | Record expenses through chat | Private commands, monthly totals, recent entries and deletion |

## Quick start

Requires Python 3.11 or newer. Run commands from this repository's root.

```sh
python -m venv .venv
```

Activate on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Or on macOS/Linux:

```sh
source .venv/bin/activate
```

Install dependencies and run all demos (no token or internet needed after installation):

```sh
python -m pip install -r requirements.txt
python -m bots.scraper --demo
python -m bots.price_monitor --demo
python -m bots.expense_bot --demo
python -m unittest discover -v
```

## 1. Catalog scraper

```sh
python -m bots.scraper --pages 2 --output data/catalog
```

Extracts title, GBP price, availability, rating and absolute product URL. Writes `books.csv` (UTF-8 with BOM for Excel) and `books.json`. Includes a one-second delay between pages, bounded GET retries, request timeouts, and URL deduplication. The adapter deliberately supports only Books to Scrape; adapting a client website requires updating selectors and access rules.

The source, [Books to Scrape](https://books.toscrape.com/), is a scraping practice website. Its prices and ratings are synthetic. Offline fixtures in this repository are invented examples, not a copy of the full catalog.

## 2. Price monitor

Run the same command again later to compare against its previous snapshot:

```sh
python -m bots.price_monitor --pages 2
```

The first run establishes `data/prices.sqlite3` and reports no changes. Later runs write changed prices to `data/price-changes.json`; an unchanged catalog produces `[]`. Prices are compared with `Decimal`. Only products included in the current scrape are checked; missing products are retained in the baseline and are not removal alerts. The report is overwritten on each successful run.

```sh
python -m bots.price_monitor --demo
```

The demo simulates a drop from £24.50 to £9.99 using an in-memory database, so it works even when live prices never change. This is a one-shot job: schedule it with cron or Windows Task Scheduler if you need repeated checks. Set the working directory to the repository root and use the virtual environment's Python executable. It reports locally and does not send notifications.

## 3. Telegram expense bot

1. Create a bot using [@BotFather](https://t.me/BotFather) and obtain a token.
2. Find your numeric Telegram user ID. One method is to send a private message to your new bot and inspect `message.from.id` in the official API's `getUpdates` result before starting polling. Keep the token private and avoid sharing token-bearing URLs.
3. Set these environment variables for the current terminal, then start polling:

```powershell
# Windows PowerShell — replace the placeholder values locally
$env:TELEGRAM_BOT_TOKEN = 'YOUR_BOT_TOKEN'
$env:TELEGRAM_OWNER_ID = 'YOUR_NUMERIC_USER_ID'
python -m bots.expense_bot
```

```sh
# macOS / Linux
export TELEGRAM_BOT_TOKEN='YOUR_BOT_TOKEN'
export TELEGRAM_OWNER_ID='YOUR_NUMERIC_USER_ID'
python -m bots.expense_bot
```

The application reads process environment variables; it does not automatically load `.env` files. Only the configured owner can use it, and only in a private chat. Stop with Ctrl+C. Run one instance per bot token and remove an existing webhook before using long polling.

| Command | Example | Result |
| --- | --- | --- |
| `/start`, `/help` | `/help` | Ukrainian command guide |
| `/add amount category` | `/add 120.50 їжа` | Add a UAH expense |
| `/summary` | `/summary` | Current calendar month by category (UTC) |
| `/list` | `/list` | Latest ten expenses with IDs |
| `/delete id` | `/delete 1` | Delete your expense |

Amounts are stored as integer kopecks; decimal commas are accepted. SQLite stores expenses, polling offset and processed update IDs. Retried updates reuse the saved reply instead of adding the expense twice. Replies can still be delivered twice if a network interruption happens after Telegram accepted a message. Data stays in local, unencrypted `data/expenses.sqlite3`; choose a trusted machine and back up the database. The process must remain running to receive messages.

API reference: [Telegram Bot API](https://core.telegram.org/bots/api).

## Repository layout

```text
bots/
  catalog.py         Shared website adapter
  scraper.py         CSV/JSON export CLI
  price_monitor.py   SQLite comparison CLI
  expense_bot.py     Telegram API adapter and expense commands
examples/            Offline HTML fixture and sample results
tests/               Network-free unittest suite
docs/                Ukrainian setup guide
.github/workflows/   CI on Python 3.11, 3.12 and 3.13
```

## Scope

These are educational portfolio projects, not paid client case studies. The scraper and monitor are terminal automation bots; the expense tracker is a Telegram chatbot. The Telegram workflow can be demonstrated offline, but a real chat needs your own bot token and user ID. No paid API keys are required. Test suite covers parsing, exports, pagination, price baselines, money precision, invalid input, user isolation, persistence and duplicate updates. CI does not contact external services.
