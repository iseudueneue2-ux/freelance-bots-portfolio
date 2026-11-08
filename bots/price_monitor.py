"""Compare catalog prices against a persistent SQLite snapshot."""
import argparse
from contextlib import closing
from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path
import sqlite3

import requests
from bots.catalog import parse_page, scrape


def compare_and_save(db, books):
    """Return changes; first sightings establish a baseline, not an alert."""
    db.execute("CREATE TABLE IF NOT EXISTS prices (url TEXT PRIMARY KEY, title TEXT, price TEXT)")
    changes = []
    with db:
        for book in books:
            old = db.execute("SELECT price FROM prices WHERE url=?", (book.url,)).fetchone()
            if old and Decimal(old[0]) != Decimal(book.price):
                changes.append({"title": book.title, "url": book.url,
                                "old_price": old[0], "new_price": book.price,
                                "currency": book.currency,
                                "direction": "down" if Decimal(book.price) < Decimal(old[0]) else "up"})
            db.execute("INSERT INTO prices VALUES (?, ?, ?) ON CONFLICT(url) DO UPDATE SET "
                       "title=excluded.title, price=excluded.price", (book.url, book.title, book.price))
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--db", default="data/prices.sqlite3")
    parser.add_argument("--output", default="data/price-changes.json")
    parser.add_argument("--demo", action="store_true", help="Simulate a price drop in memory")
    args = parser.parse_args()
    if args.pages < 1:
        parser.error("--pages must be positive")
    try:
        if args.demo:
            fixture = Path(__file__).resolve().parents[1] / "examples/catalog.html"
            books, _ = parse_page(fixture.read_text(encoding="utf-8"))
            with closing(sqlite3.connect(":memory:")) as db:
                compare_and_save(db, books)
                changes = compare_and_save(db, [replace(books[0], price="9.99"), *books[1:]])
        else:
            books = scrape(args.pages)
            Path(args.db).parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(args.db)) as db:
                changes = compare_and_save(db, books)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(changes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(changes, ensure_ascii=False, indent=2))
        print(f"Found {len(changes)} price changes. Report: {output}")
    except (OSError, ValueError, sqlite3.Error, requests.RequestException) as exc:
        parser.exit(1, f"Monitor failed: {exc}\n")


if __name__ == "__main__":
    main()
