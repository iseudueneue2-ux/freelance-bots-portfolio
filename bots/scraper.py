"""Export a paginated book catalog to CSV and JSON."""
import argparse
import csv
import json
from pathlib import Path
import requests

from bots.catalog import parse_page, scrape


def export(books, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    rows = [book.to_dict() for book in books]
    (directory / "books.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (directory / "books.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=[
            "title", "price", "currency", "available", "rating", "url"])
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--output", default="data/catalog")
    parser.add_argument("--demo", action="store_true", help="Use an offline HTML fixture")
    args = parser.parse_args()
    if args.pages < 1:
        parser.error("--pages must be positive")
    try:
        if args.demo:
            fixture = Path(__file__).resolve().parents[1] / "examples/catalog.html"
            books, _ = parse_page(fixture.read_text(encoding="utf-8"))
        else:
            books = scrape(args.pages)
        export(books, args.output)
        print(f"Exported {len(books)} books to {args.output}")
    except (OSError, ValueError, requests.RequestException) as exc:
        parser.exit(1, f"Scraper failed: {exc}\n")


if __name__ == "__main__":
    main()
