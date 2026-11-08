'use strict';
const repository = 'https://github.com/iseudueneue2-ux/freelance-bots-portfolio';
const projects = {
  scraper: {kind:'Парсинг даних',title:'Каталог без ручного копіювання',description:'Збирає назви книжок, ціни, рейтинги та посилання з Books to Scrape. Проходить кілька сторінок і зберігає дані у CSV та JSON.',features:['CSV, який зручно відкрити в Excel','Пагінація та захист від дублікатів','Тайм-аути й повторні спроби запитів'],file:'scraper.py'},
  monitor: {kind:'Моніторинг та звіти',title:'Помічай, коли змінюється ціна',description:'Зберігає ціни в SQLite та порівнює їх під час наступного запуску. Знаходить подорожчання і знижки, формує JSON-звіт зі старими й новими цінами.',features:['Перший запуск створює базову ціну','Точне порівняння сум через Decimal','Збереження історії останніх цін у SQLite'],file:'price_monitor.py'},
  expenses: {kind:'Telegram та бази даних',title:'Витрати — просто в повідомленнях',description:'Приватний Telegram-бот для обліку витрат у гривнях. Записує суму та категорію, рахує підсумок за місяць і дозволяє видаляти записи.',features:['Команди додавання, списку та видалення','Доступ лише для власника бота','Повторна доставка не дублює витрати'],file:'expense_bot.py'}
};
const status = document.getElementById('demo-status');
document.querySelectorAll('[data-project]').forEach(button => {
  button.addEventListener('click', () => {
    const key = button.dataset.project;
    const project = projects[key];
    document.querySelectorAll('[data-project]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    for (const name of Object.keys(projects)) document.getElementById(`demo-${name}`).hidden = name !== key;
    document.getElementById('project-kind').textContent = project.kind;
    document.getElementById('project-title').textContent = project.title;
    document.getElementById('project-description').textContent = project.description;
    document.getElementById('project-features').replaceChildren(...project.features.map(text => {
      const item = document.createElement('li'); item.textContent = text; return item;
    }));
    document.getElementById('project-source').href = `${repository}/blob/main/bots/${project.file}`;
    status.textContent = `Обрано: ${button.querySelector('strong').textContent}. Демо готове до запуску.`;
  });
});
document.getElementById('scrape-button').addEventListener('click', () => {
  document.getElementById('scrape-result').hidden = false;
  document.getElementById('scrape-button').textContent = 'Зібрати ще раз';
  status.textContent = 'Готово: 2 тестові книжки. Можна завантажити CSV.';
});
document.getElementById('download-csv').addEventListener('click', () => {
  const csv = '\uFEFFtitle,price,currency,rating\r\nDemo Python Book,24.50,GBP,4\r\nAutomation & Bots,18.00,GBP,5\r\n';
  const url = URL.createObjectURL(new Blob([csv], {type:'text/csv;charset=utf-8'}));
  const link = document.createElement('a'); link.href = url; link.download = 'demo-books.csv';
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  status.textContent = 'CSV-файл підготовлено для завантаження.';
});
document.getElementById('price-form').addEventListener('submit', event => {
  event.preventDefault();
  const cents = Math.round(Number(document.getElementById('new-price').value) * 100);
  if (!Number.isSafeInteger(cents) || cents < 1) return;
  const difference = cents - 2450;
  const output = document.getElementById('price-result'); output.hidden = false;
  output.textContent = difference === 0 ? 'Ціна не змінилась: £24.50.' :
    `£24.50 → £${(cents / 100).toFixed(2)}. ${difference < 0 ? 'Зниження' : 'Зростання'} на £${(Math.abs(difference) / 100).toFixed(2)} (${(Math.abs(difference) / 2450 * 100).toFixed(1)}%).`;
  status.textContent = 'Порівняння тестової ціни завершено.';
});
const expenses = [];
const messages = document.getElementById('expense-messages');
function bubble(text, user = false) {
  const item = document.createElement('p'); item.className = `chat-bubble${user ? ' user' : ''}`; item.textContent = text;
  messages.append(item);
  while (messages.children.length > 12) messages.firstElementChild.remove();
  messages.parentElement.scrollTop = messages.parentElement.scrollHeight;
}
document.getElementById('expense-form').addEventListener('submit', event => {
  event.preventDefault();
  const amount = document.getElementById('expense-amount');
  const category = document.getElementById('expense-category');
  const cents = Math.round(Number(amount.value) * 100);
  if (!Number.isSafeInteger(cents) || cents <= 0 || !category.value.trim()) {
    status.textContent = 'Введи додатну суму та категорію витрати.'; return;
  }
  expenses.push({cents, category:category.value.trim()});
  bubble(`/add ${(cents / 100).toFixed(2)} ${category.value.trim()}`, true);
  bubble(`Додано #${expenses.length}: ${(cents / 100).toFixed(2)} грн · ${category.value.trim()}`);
  status.textContent = `Витрату додано. Записів у демо: ${expenses.length}.`;
  amount.value = ''; category.value = ''; amount.focus();
});
document.getElementById('expense-summary').addEventListener('click', () => {
  bubble('/summary', true);
  const grouped = new Map();
  expenses.forEach(item => grouped.set(item.category, (grouped.get(item.category) || 0) + item.cents));
  const total = expenses.reduce((sum, item) => sum + item.cents, 0);
  bubble(expenses.length ? [...grouped].map(([category, cents]) => `${category}: ${(cents / 100).toFixed(2)} грн`).join('\n') + `\nРазом: ${(total / 100).toFixed(2)} грн` : 'Витрат ще немає. Додай першу витрату.');
  status.textContent = `Підсумок: ${(total / 100).toFixed(2)} грн.`;
});
