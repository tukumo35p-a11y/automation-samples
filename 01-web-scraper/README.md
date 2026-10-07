# Web scraper: product listings to CSV / Excel

Collects every book listed on [books.toscrape.com](https://books.toscrape.com/), a public site made for scraping practice, and saves the result as a spreadsheet-ready file.

## What you get

One row per product: title, price, star rating (1 to 5), stock status, and the product URL.

A full run collects 1,000 products across 50 pages in about a minute. See [sample_output/product_listings.csv](sample_output/product_listings.csv) and [sample_output/product_listings.xlsx](sample_output/product_listings.xlsx).

## Run it

```
python scrape_books.py                    # all pages -> output/product_listings.csv
python scrape_books.py --pages 3 --xlsx   # first 3 pages, also write Excel
```

| Option | Meaning | Default |
|---|---|---|
| `--pages N` | Number of pages to collect | all |
| `--delay S` | Seconds to wait between requests | 0.5 |
| `--out PATH` | CSV output path | `output/product_listings.csv` |
| `--xlsx` | Also write an Excel file | off |

## How it behaves

- Waits between requests so it does not put load on the site.
- Retries a failed request up to three times, waiting longer each time.
- Stops cleanly at the last page instead of relying on a fixed page count.
- Writes the CSV so that it opens correctly in Excel, including the currency values.
- Warns if the same product appears twice.

## Adapting it

The page URL and the fields to extract are defined in one place each (`PAGE_URL` and `parse_page`). Pointing the tool at another listing site means changing those two parts. For any real site I check its terms of use and robots.txt first and collect public data only.
