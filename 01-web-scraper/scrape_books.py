"""Collect book listings from books.toscrape.com and save them as CSV (and optionally Excel).

books.toscrape.com is a public sandbox site built for scraping practice.

Usage:
    python scrape_books.py                      # all pages -> output/product_listings.csv
    python scrape_books.py --pages 3 --xlsx     # first 3 pages, also write Excel
"""

import argparse
import csv
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

PAGE_URL = "https://books.toscrape.com/catalogue/page-{}.html"
HEADERS = {"User-Agent": "portfolio-sample-scraper/1.0"}
RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
FIELDS = ["title", "price_gbp", "rating", "in_stock", "url"]


def fetch(session, url, retries=3, timeout=20):
    """Return the page HTML, or None when the page does not exist (404)."""
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, timeout=timeout)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            resp.encoding = "utf-8"
            return resp.text
        except requests.RequestException as exc:
            if attempt == retries:
                raise
            wait = 2**attempt
            print(f"  request failed ({exc}); retrying in {wait}s", file=sys.stderr)
            time.sleep(wait)


def parse_page(html, page_url):
    """Extract one dict per book from a listing page."""
    soup = BeautifulSoup(html, "html.parser")
    books = []
    for card in soup.select("article.product_pod"):
        link = card.select_one("h3 a")
        price_text = card.select_one("p.price_color").get_text(strip=True)
        rating_word = next(
            (c for c in card.select_one("p.star-rating")["class"] if c in RATINGS), None
        )
        availability = card.select_one("p.availability").get_text(strip=True)
        books.append(
            {
                "title": link["title"],
                "price_gbp": float(re.sub(r"[^\d.]", "", price_text)),
                "rating": RATINGS.get(rating_word),
                "in_stock": "in stock" in availability.lower(),
                "url": urljoin(page_url, link["href"]),
            }
        )
    return books


def scrape(max_pages=None, delay=0.5):
    books = []
    page = 1
    with requests.Session() as session:
        session.headers.update(HEADERS)
        while max_pages is None or page <= max_pages:
            url = PAGE_URL.format(page)
            html = fetch(session, url)
            if html is None:
                break
            found = parse_page(html, url)
            if not found:
                break
            books.extend(found)
            print(f"page {page}: {len(found)} books (total {len(books)})")
            page += 1
            time.sleep(delay)
    return books


def write_csv(books, path):
    # utf-8-sig so the file opens correctly in Excel
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(books)


def write_xlsx(books, path):
    from openpyxl import Workbook
    from openpyxl.styles import Font

    wb = Workbook()
    ws = wb.active
    ws.title = "products"
    ws.append(FIELDS)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for book in books:
        ws.append([book[f] for f in FIELDS])
    ws.freeze_panes = "A2"
    ws.column_dimensions["A"].width = 60
    ws.column_dimensions["E"].width = 70
    wb.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pages", type=int, default=None, help="number of pages to collect (default: all)")
    parser.add_argument("--delay", type=float, default=0.5, help="seconds to wait between requests")
    parser.add_argument("--out", default="output/product_listings.csv", help="CSV output path")
    parser.add_argument("--xlsx", action="store_true", help="also write an Excel file next to the CSV")
    args = parser.parse_args()

    books = scrape(max_pages=args.pages, delay=args.delay)
    if not books:
        sys.exit("No books found. The site layout may have changed.")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_csv(books, out)
    print(f"saved {len(books)} rows -> {out}")
    if args.xlsx:
        xlsx_path = out.with_suffix(".xlsx")
        write_xlsx(books, xlsx_path)
        print(f"saved {len(books)} rows -> {xlsx_path}")

    duplicates = len(books) - len({b["url"] for b in books})
    if duplicates:
        print(f"warning: {duplicates} duplicate URLs", file=sys.stderr)


if __name__ == "__main__":
    main()
