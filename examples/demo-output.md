# Offline demo results

Illustrative output from the bundled synthetic fixture. Month headings in the expense bot depend on the current UTC month.

## Catalog scraper

```text
Exported 2 books to data/catalog
```

CSV data:

```csv
title,price,currency,available,rating,url
Demo Python Book,24.50,GBP,True,4,https://books.toscrape.com/catalogue/demo-book_1/index.html
Automation & Bots,18.00,GBP,True,5,https://books.toscrape.com/catalogue/automation_2/index.html
```

## Price monitor

```json
[
  {
    "title": "Demo Python Book",
    "url": "https://books.toscrape.com/catalogue/demo-book_1/index.html",
    "old_price": "24.50",
    "new_price": "9.99",
    "currency": "GBP",
    "direction": "down"
  }
]
```

## Expense bot

```text
> /add 120.50 їжа
Додано #1: 120.50 грн · їжа

> /add 45 транспорт
Додано #2: 45.00 грн · транспорт

> /summary
Витрати за 2026-11 (UTC)
їжа: 120.50 грн
транспорт: 45.00 грн
Разом: 165.50 грн
```
