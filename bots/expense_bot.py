"""Private Telegram expense tracker with SQLite and an offline conversation demo."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
from decimal import Decimal
import os
from pathlib import Path
import re
import sqlite3
import time

import requests

HELP = ("Облік витрат у гривнях\n/add 120.50 їжа — додати витрату\n"
        "/summary — підсумок за поточний місяць (UTC)\n"
        "/list — останні 10 витрат\n/delete 1 — видалити свою витрату")


def initialize(db):
    db.executescript("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, cents INTEGER NOT NULL,
            category TEXT NOT NULL, created TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS processed (update_id INTEGER PRIMARY KEY, reply TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value INTEGER NOT NULL);
    """)


def money(cents):
    return f"{Decimal(cents) / 100:.2f}"


def command(db, user_id, text):
    parts = text.strip().split(maxsplit=2)
    action = parts[0].split("@")[0].lower() if parts else ""
    if action in ("/start", "/help"):
        return HELP
    if action == "/add":
        if len(parts) < 3 or not re.fullmatch(r"[0-9]{1,7}([.,][0-9]{1,2})?", parts[1]):
            return "Приклад: /add 120.50 їжа. Сума: від 0.01 до 9999999.99 грн."
        cents = int(Decimal(parts[1].replace(",", ".")) * 100)
        category = parts[2].strip()
        if cents <= 0 or not category or len(category) > 50:
            return "Сума має бути більшою за нуль, категорія — до 50 символів."
        cursor = db.execute("INSERT INTO expenses(user_id,cents,category,created) VALUES (?,?,?,?)",
                            (user_id, cents, category, datetime.now(timezone.utc).isoformat()))
        return f"Додано #{cursor.lastrowid}: {money(cents)} грн · {category}"
    if action == "/summary":
        month = datetime.now(timezone.utc).strftime("%Y-%m")
        rows = db.execute("SELECT category,SUM(cents) FROM expenses WHERE user_id=? "
                          "AND substr(created,1,7)=? GROUP BY category ORDER BY SUM(cents) DESC",
                          (user_id, month)).fetchall()
        if not rows:
            return "Цього місяця витрат ще немає."
        return f"Витрати за {month} (UTC)\n" + "\n".join(
            f"{category}: {money(total)} грн" for category, total in rows
        ) + f"\nРазом: {money(sum(total for _, total in rows))} грн"
    if action == "/list":
        rows = db.execute("SELECT id,cents,category FROM expenses WHERE user_id=? "
                          "ORDER BY id DESC LIMIT 10", (user_id,)).fetchall()
        return "\n".join(f"#{i}: {money(c)} грн · {cat}" for i, c, cat in rows) or "Витрат ще немає."
    if action == "/delete":
        if len(parts) != 2 or not re.fullmatch(r"[0-9]{1,18}", parts[1]):
            return "Приклад: /delete 1"
        deleted = db.execute("DELETE FROM expenses WHERE id=? AND user_id=?", (int(parts[1]), user_id))
        return "Витрату видалено." if deleted.rowcount else "Такої витрати немає."
    return "Невідома команда. /help — список команд."


def process(db, update_id, user_id, text):
    """Persist command and reply together so retries never duplicate an expense."""
    with db:
        cached = db.execute("SELECT reply FROM processed WHERE update_id=?", (update_id,)).fetchone()
        if cached:
            return cached[0]
        reply = command(db, user_id, text)
        db.execute("INSERT INTO processed VALUES (?,?)", (update_id, reply))
    return reply


class TelegramError(Exception):
    pass


def api(session, token, method, payload):
    try:
        response = session.post(f"https://api.telegram.org/bot{token}/{method}",
                                json=payload, timeout=40)
        if response.status_code != 200:
            raise TelegramError(f"Telegram returned HTTP {response.status_code}")
        data = response.json()
        if not data.get("ok"):
            raise TelegramError("Telegram rejected the request")
        return data["result"]
    except (requests.RequestException, ValueError):
        # requests exceptions may contain the token-bearing URL. Never log them.
        raise TelegramError("Telegram connection failed") from None


def run(db, token, owner_id):
    with requests.Session() as session:
        while True:
            row = db.execute("SELECT value FROM state WHERE key='offset'").fetchone()
            offset = row[0] if row else 0
            try:
                updates = api(session, token, "getUpdates", {
                    "offset": offset, "timeout": 25, "allowed_updates": ["message"]})
                for update in updates:
                    message = update.get("message", {})
                    chat = message.get("chat", {})
                    if (chat.get("type") == "private" and
                            message.get("from", {}).get("id") == owner_id and
                            isinstance(message.get("text"), str)):
                        reply = process(db, update["update_id"], owner_id, message["text"])
                        # Chunk large summaries to respect sendMessage's text limit.
                        for start in range(0, len(reply), 3000):
                            api(session, token, "sendMessage", {
                                "chat_id": chat["id"], "text": reply[start:start + 3000]})
                    with db:
                        db.execute("INSERT INTO state VALUES ('offset',?) "
                                   "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                                   (update["update_id"] + 1,))
            except TelegramError as exc:
                print(f"{exc}; retrying in 5 seconds", flush=True)
                time.sleep(5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="data/expenses.sqlite3")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if args.demo:
        with closing(sqlite3.connect(":memory:")) as db:
            initialize(db)
            for i, text in enumerate(["/start", "/add 120.50 їжа", "/add 45 транспорт", "/summary", "/list"]):
                print(f"> {text}\n{process(db, i, 1, text)}\n")
        return
    token, owner = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_OWNER_ID", "")
    if not token or not owner.isdecimal() or int(owner) < 1 or len(owner) > 18:
        parser.error("Set TELEGRAM_BOT_TOKEN and a positive TELEGRAM_OWNER_ID in your environment")
    try:
        Path(args.db).parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(args.db)) as db:
            initialize(db)
            print("Expense bot started. Ctrl+C to stop.", flush=True)
            run(db, token, int(owner))
    except KeyboardInterrupt:
        print("Stopped.")
    except (OSError, sqlite3.Error):
        parser.exit(1, "Could not open or update the expense database.\n")


if __name__ == "__main__":
    main()
