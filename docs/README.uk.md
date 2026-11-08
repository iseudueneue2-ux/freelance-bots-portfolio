# Три боти для фріланс-портфоліо

Це навчальні проєкти, які можна показувати замовникам як приклади роботи з Python, сайтами, Telegram API та базами даних. Це демонстрації, а не вигадані комерційні кейси.

## Запуск на Windows

Потрібен Python 3.11 або новіший. Відкрий PowerShell у папці репозиторію:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m bots.scraper --demo
.venv\Scripts\python.exe -m bots.price_monitor --demo
.venv\Scripts\python.exe -m bots.expense_bot --demo
```

Ці команди працюють без активації середовища та без Telegram-токена. Після встановлення залежностей деморежими не потребують інтернету.

## Що можна показати замовнику

1. **Парсер каталогу.** Збирає назви книжок, ціни, наявність, рейтинг та посилання. Зберігає CSV для Excel і JSON. Реальний запуск на двох сторінках: `.venv\Scripts\python.exe -m bots.scraper --pages 2`. Результат: `data/catalog/`.
2. **Монітор цін.** Запам'ятовує попередні ціни в SQLite й знаходить зміни. Запуск: `.venv\Scripts\python.exe -m bots.price_monitor --pages 2`. Перший запуск створює базу, наступні порівнюють ціни. Деморежим сам показує зниження ціни; навчальний сайт може не змінювати ціни. Звіт: `data/price-changes.json`.
3. **Telegram-бот витрат.** Приймає `/add 120.50 їжа`, показує `/summary` та `/list`, видаляє записи через `/delete 1`. Дані зберігаються локально. Валюта — гривня, межі місяця — UTC. Працює лише у приватному чаті для заданого власника.

## Як підключити Telegram

Створи бота через [@BotFather](https://t.me/BotFather). Потрібні токен і твій числовий Telegram ID — це різні значення. ID можна взяти з `message.from.id` відповіді `getUpdates` після приватного повідомлення боту. Подробиці та обмеження — в [основному README](../README.md#3-telegram-expense-bot).

```powershell
$env:TELEGRAM_BOT_TOKEN = 'ТВІЙ_ТОКЕН'
$env:TELEGRAM_OWNER_ID = 'ТВІЙ_ЧИСЛОВИЙ_ID'
.venv\Scripts\python.exe -m bots.expense_bot
```

Підстав справжні значення тільки у своєму терміналі. Токен не додавай у GitHub. Бот працює, доки запущена програма; зупинка — Ctrl+C. Файл `.env` автоматично не читається. Монітор цін запускається один раз; для перевірок за розкладом використай Планувальник завдань Windows із робочою папкою репозиторію.

## Перевірка

```powershell
.venv\Scripts\python.exe -m unittest discover -v
```

Після завантаження на GitHub тести також запускає GitHub Actions. Для нового сайту потрібно адаптувати HTML-селектори в `bots/catalog.py`; зараз джерело навмисно обмежене навчальним каталогом Books to Scrape.
