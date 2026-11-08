from dataclasses import replace
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock

from bots.catalog import checked_url, parse_page
from bots.expense_bot import TelegramError, api, initialize, process
from bots.price_monitor import compare_and_save
from bots.scraper import export

FIXTURE = Path(__file__).resolve().parents[1] / "examples/catalog.html"


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.books, _ = parse_page(FIXTURE.read_text(encoding="utf-8"))

    def test_parse_prices_titles_and_ratings(self):
        self.assertEqual(self.books[0].price, "24.50")
        self.assertEqual(self.books[0].rating, 4)
        self.assertTrue(self.books[0].available)
        self.assertEqual(self.books[1].title, "Automation & Bots")

    def test_pagination(self):
        html = FIXTURE.read_text(encoding="utf-8") + '<li class="next"><a href="page-2.html">next</a></li>'
        _, next_url = parse_page(html, "https://books.toscrape.com/catalogue/page-1.html")
        self.assertEqual(next_url, "https://books.toscrape.com/catalogue/page-2.html")

    def test_empty_catalog_fails(self):
        with self.assertRaises(ValueError):
            parse_page("<html></html>")

    def test_external_urls_rejected(self):
        with self.assertRaises(ValueError):
            checked_url("https://example.com/catalogue")

    def test_export_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            export(self.books, directory)
            rows = json.loads((Path(directory) / "books.json").read_text(encoding="utf-8"))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["price"], "24.50")
            self.assertIn("Automation & Bots", (Path(directory) / "books.csv").read_text(encoding="utf-8-sig"))

    def test_baseline_change_and_repeat(self):
        with closing(sqlite3.connect(":memory:")) as db:
            self.assertEqual(compare_and_save(db, self.books), [])
            changed = [replace(self.books[0], price="10.00"), self.books[1]]
            changes = compare_and_save(db, changed)
            self.assertEqual(changes[0]["direction"], "down")
            self.assertEqual(changes[0]["old_price"], "24.50")
            self.assertEqual(compare_and_save(db, changed), [])
            self.assertEqual(compare_and_save(db, self.books)[0]["direction"], "up")


class ExpenseTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        initialize(self.db)

    def tearDown(self):
        self.db.close()

    def test_decimal_precision_and_comma(self):
        process(self.db, 1, 7, "/add 0.10 їжа")
        process(self.db, 2, 7, "/add 0,20 їжа")
        self.assertIn("Разом: 0.30", process(self.db, 3, 7, "/summary"))

    def test_replayed_update_does_not_duplicate(self):
        first = process(self.db, 1, 7, "/add 10 їжа")
        self.assertEqual(first, process(self.db, 1, 7, "/add 10 їжа"))
        self.assertEqual(self.db.execute("SELECT count(*) FROM expenses").fetchone()[0], 1)

    def test_user_isolation_and_delete(self):
        process(self.db, 1, 7, "/add 10 їжа")
        self.assertEqual(process(self.db, 2, 8, "/list"), "Витрат ще немає.")
        self.assertEqual(process(self.db, 3, 8, "/delete 1"), "Такої витрати немає.")
        self.assertEqual(process(self.db, 4, 7, "/delete 1"), "Витрату видалено.")

    def test_invalid_amounts_do_not_write(self):
        for i, amount in enumerate(["0", "-1", "NaN", "1e5", "1.001", "10000000"]):
            process(self.db, i, 7, f"/add {amount} їжа")
        self.assertEqual(self.db.execute("SELECT count(*) FROM expenses").fetchone()[0], 0)

    def test_telegram_errors_never_expose_token(self):
        import requests
        session = Mock()
        session.post.side_effect = requests.ConnectionError("secret-token-in-url")
        with self.assertRaises(TelegramError) as caught:
            api(session, "secret-token", "getUpdates", {})
        self.assertNotIn("secret-token", str(caught.exception))

    def test_expenses_persist_across_connections(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "expenses.sqlite3"
            with closing(sqlite3.connect(path)) as db:
                initialize(db)
                process(db, 1, 7, "/add 42 кава")
            with closing(sqlite3.connect(path)) as db:
                self.assertIn("42.00", process(db, 2, 7, "/list"))


if __name__ == "__main__":
    unittest.main()
