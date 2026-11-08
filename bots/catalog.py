"""Books to Scrape adapter shared by the scraper and price monitor."""
from dataclasses import asdict, dataclass
from decimal import Decimal
from urllib.parse import urljoin, urlsplit
import time

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://books.toscrape.com/"


@dataclass(frozen=True)
class Book:
    title: str
    price: str
    currency: str
    available: bool
    rating: int
    url: str

    def to_dict(self):
        return asdict(self)


def checked_url(url):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "books.toscrape.com":
        raise ValueError("Only https://books.toscrape.com URLs are supported")
    return url


def parse_page(html, page_url=BASE_URL):
    soup = BeautifulSoup(html, "html.parser")
    books = []
    ratings = {name: i for i, name in enumerate(
        ["Zero", "One", "Two", "Three", "Four", "Five"])}
    for card in soup.select("article.product_pod"):
        link = card.select_one("h3 a")
        price = card.select_one(".price_color").get_text(strip=True)
        rating = card.select_one(".star-rating")
        books.append(Book(
            title=link["title"],
            price=str(Decimal(price.removeprefix("£"))),
            currency="GBP",
            available="In stock" in card.select_one(".availability").get_text(),
            rating=next((ratings[c] for c in rating.get("class", []) if c in ratings), 0),
            url=checked_url(urljoin(page_url, link["href"])),
        ))
    if not books:
        raise ValueError("No products found; the catalog markup may have changed")
    next_link = soup.select_one("li.next a")
    next_url = checked_url(urljoin(page_url, next_link["href"])) if next_link else None
    return books, next_url


def scrape(pages=1, delay=1.0):
    if pages < 1 or delay < 0:
        raise ValueError("pages must be positive and delay nonnegative")
    retry = Retry(total=3, backoff_factor=0.5,
                  status_forcelist=[429, 500, 502, 503, 504])
    with requests.Session() as session:
        session.headers["User-Agent"] = "FreelancePortfolioDemo/1.0"
        session.mount("https://", HTTPAdapter(max_retries=retry))
        url, seen, result = BASE_URL, set(), []
        for index in range(pages):
            if not url or url in seen:
                break
            seen.add(url)
            if index:
                time.sleep(delay)
            response = session.get(checked_url(url), timeout=20, allow_redirects=False)
            response.raise_for_status()
            if response.status_code != 200:
                raise ValueError("Unexpected catalog response")
            books, url = parse_page(response.content.decode("utf-8"), url)
            result.extend(books)
    return list({book.url: book for book in result}.values())
