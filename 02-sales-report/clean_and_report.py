"""Clean a messy sales export and build an Excel summary report.

Usage:
    python clean_and_report.py sample_data/raw_sales.csv
    python clean_and_report.py raw.csv --out-dir results

Outputs:
    cleaned_sales.csv   one clean row per order
    sales_report.xlsx   Summary / By Month / By Product / By Region / Issues
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

REQUIRED = ["order_id", "order_date", "customer", "region", "product", "quantity", "unit_price"]
MONEY_COLUMNS = {"unit_price", "revenue", "avg_order_value"}


def load(path):
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        sys.exit(f"Missing columns in {path}: {', '.join(missing)}")
    return df[REQUIRED]


def clean(raw):
    """Return (clean rows, issues). Every removed row is listed in issues with the reason."""
    df = raw.copy()
    issues = []

    def drop(mask, reason):
        nonlocal df
        for order_id in df.loc[mask, "order_id"]:
            issues.append({"order_id": order_id, "issue": reason, "action": "row removed"})
        df = df[~mask]

    for col in ("order_id", "customer", "region", "product"):
        df[col] = df[col].str.strip().str.replace(r"\s+", " ", regex=True)
    for col in ("customer", "region", "product"):
        df[col] = df[col].str.title()

    drop(df.duplicated(subset="order_id", keep="first"), "duplicate order ID")

    df["order_date"] = pd.to_datetime(df["order_date"].str.strip(), format="mixed", errors="coerce")
    drop(df["order_date"].isna(), "missing or unreadable date")

    df["quantity"] = pd.to_numeric(df["quantity"].str.extract(r"(-?\d+)")[0], errors="coerce")
    drop(df["quantity"].isna(), "missing quantity")
    drop(df["quantity"] <= 0, "quantity is zero or negative")

    df["unit_price"] = pd.to_numeric(
        df["unit_price"].str.replace(r"[^\d.\-]", "", regex=True), errors="coerce"
    )
    drop(df["unit_price"].isna(), "missing or unreadable price")

    df["quantity"] = df["quantity"].astype(int)
    df["revenue"] = (df["quantity"] * df["unit_price"]).round(2)
    df = df.sort_values(["order_date", "order_id"]).reset_index(drop=True)
    return df, pd.DataFrame(issues, columns=["order_id", "issue", "action"])


def group(df, key):
    out = (
        df.groupby(key)
        .agg(orders=("order_id", "count"), units=("quantity", "sum"), revenue=("revenue", "sum"))
        .reset_index()
    )
    out["revenue"] = out["revenue"].round(2)
    return out


def build_tables(raw, df, issues):
    summary = pd.DataFrame(
        [
            ("Rows in source file", len(raw)),
            ("Rows removed", len(raw) - len(df)),
            ("Clean orders", len(df)),
            ("First order date", df["order_date"].min().date().isoformat()),
            ("Last order date", df["order_date"].max().date().isoformat()),
            ("Total units", int(df["quantity"].sum())),
            ("Total revenue", round(float(df["revenue"].sum()), 2)),
            ("Average order value", round(float(df["revenue"].mean()), 2)),
        ],
        columns=["metric", "value"],
    )
    by_month = group(df.assign(month=df["order_date"].dt.strftime("%Y-%m")), "month")
    by_product = group(df, "product").sort_values("revenue", ascending=False)
    by_region = group(df, "region").sort_values("revenue", ascending=False)
    return {
        "Summary": summary,
        "By Month": by_month,
        "By Product": by_product,
        "By Region": by_region,
        "Issues": issues,
    }


def write_report(tables, path):
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, table in tables.items():
            table.to_excel(writer, sheet_name=name, index=False)
            ws = writer.sheets[name]
            ws.freeze_panes = "A2"
            for idx, column in enumerate(table.columns, start=1):
                header = ws.cell(row=1, column=idx)
                header.font = Font(bold=True, color="FFFFFF")
                header.fill = PatternFill("solid", fgColor="2F5597")
                longest = max([len(str(column))] + [len(str(v)) for v in table[column]])
                ws.column_dimensions[get_column_letter(idx)].width = min(longest + 4, 50)
                if column in MONEY_COLUMNS:
                    for row in range(2, len(table) + 2):
                        ws.cell(row=row, column=idx).number_format = "#,##0.00"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", help="path to the raw sales CSV")
    parser.add_argument("--out-dir", default="output", help="folder for the cleaned CSV and report")
    args = parser.parse_args()

    raw = load(args.source)
    df, issues = clean(raw)
    if df.empty:
        sys.exit("No usable rows after cleaning. See the reasons above or check the source file.")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cleaned_path = out_dir / "cleaned_sales.csv"
    report_path = out_dir / "sales_report.xlsx"

    df.assign(order_date=df["order_date"].dt.date).to_csv(cleaned_path, index=False, encoding="utf-8-sig")
    write_report(build_tables(raw, df, issues), report_path)

    print(f"source rows:  {len(raw)}")
    print(f"clean orders: {len(df)}")
    print(f"removed:      {len(issues)}")
    for reason, count in issues["issue"].value_counts().items():
        print(f"  - {reason}: {count}")
    print(f"total revenue: {df['revenue'].sum():,.2f}")
    print(f"saved -> {cleaned_path}")
    print(f"saved -> {report_path}")


if __name__ == "__main__":
    main()
