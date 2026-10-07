"""Generate a deliberately messy sales export for the demo (sample_data/raw_sales.csv).

All data is synthetic. The mess imitates what a real export tends to contain:
mixed date formats, stray spaces and casing, currency symbols, blanks, duplicates.
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

PRODUCTS = {
    "Wireless Mouse": 24.99,
    "Laptop Stand": 39.5,
    "Desk Lamp": 32.0,
    "Monitor Arm": 89.0,
    "Standing Desk": 1249.0,
}
REGIONS = ["North", "South", "East", "West"]
CUSTOMERS = ["Acme Corp", "Blue Ocean Ltd", "Greenfield Inc", "Nova Trading", "Summit Supplies", "Harbor Foods"]
DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%d %b %Y", "%B %d, %Y"]


def messy_text(value):
    roll = random.random()
    if roll < 0.10:
        return value.upper()
    if roll < 0.20:
        return value.lower()
    if roll < 0.30:
        return f"  {value} "
    return value


def messy_price(price):
    roll = random.random()
    if roll < 0.30:
        return f"${price:,.2f}"
    if roll < 0.40:
        return f" {price} "
    return f"{price:.2f}"


def main():
    rows = []
    start = date(2026, 1, 1)
    for i in range(1, 301):
        product = random.choice(list(PRODUCTS))
        day = start + timedelta(days=random.randint(0, 180))
        quantity = str(random.randint(1, 12))
        roll = random.random()
        if roll < 0.03:
            quantity = ""
        elif roll < 0.06:
            quantity = f"{quantity} pcs"
        elif roll < 0.08:
            quantity = f"-{quantity}"
        rows.append(
            {
                "Order ID": f"SO-{i:04d}",
                "Order Date": "" if random.random() < 0.03 else day.strftime(random.choice(DATE_FORMATS)),
                "Customer": messy_text(random.choice(CUSTOMERS)),
                "Region": messy_text(random.choice(REGIONS)),
                "Product": messy_text(product),
                "Quantity": quantity,
                "Unit Price": "" if random.random() < 0.02 else messy_price(PRODUCTS[product]),
            }
        )

    # exact duplicates, as happens when an export is run twice
    rows.extend(random.sample(rows, 12))
    random.shuffle(rows)

    out = Path(__file__).parent / "sample_data" / "raw_sales.csv"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()
