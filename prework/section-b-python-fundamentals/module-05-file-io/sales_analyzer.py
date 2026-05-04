# sales_analyzer.py — applied to Premia as an earnings data analyzer
# Reads CSV data, calculates revenue metrics, writes summary files
# Demonstrates: csv.DictReader, file I/O, dictionaries, formatted output

import csv
from collections import defaultdict

# --- File paths ---
INPUT_FILE  = "prework/section-b-python-fundamentals/module-05-file-io/sales_data.csv"
REPORT_FILE = "prework/section-b-python-fundamentals/module-05-file-io/sales_report.txt"
SUMMARY_CSV = "prework/section-b-python-fundamentals/module-05-file-io/product_summary.csv"

# --- Read and process the CSV ---
product_qty     = defaultdict(float)
product_revenue = defaultdict(float)
date_revenue    = defaultdict(float)
total_revenue   = 0.0

try:
    # utf-8-sig strips the BOM character PowerShell adds to UTF-8 files
    with open(INPUT_FILE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            qty        = float(row["quantity"])
            price      = float(row["price"])
            product    = row["product"]
            date       = row["date"]
            line_total = qty * price

            product_qty[product]     += qty
            product_revenue[product] += line_total
            date_revenue[date]       += line_total
            total_revenue            += line_total

except FileNotFoundError:
    print(f"ERROR: {INPUT_FILE} not found.")
    exit()

# --- Find best day ---
best_day = max(date_revenue, key=date_revenue.get)

# --- Write sales_report.txt ---
W = 44
with open(REPORT_FILE, "w", encoding="utf-8") as f:
    f.write("=" * W + "\n")
    f.write(f"{'SALES REPORT':^{W}}\n")
    f.write("=" * W + "\n")
    f.write(f"{'Total Revenue:':<28}${total_revenue:>10.2f}\n")
    f.write(f"{'Best Day:':<28}{best_day} (${date_revenue[best_day]:.2f})\n")
    f.write("-" * W + "\n")
    f.write(f"{'Product':<16}{'Qty':>8}{'Revenue':>14}\n")
    f.write("-" * W + "\n")
    for product in sorted(product_revenue):
        f.write(f"{product:<16}{int(product_qty[product]):>8}  ${product_revenue[product]:>10.2f}\n")
    f.write("=" * W + "\n")

print(f"Report written to {REPORT_FILE}")

# --- Write product_summary.csv ---
with open(SUMMARY_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["product", "total_quantity", "total_revenue"])
    writer.writeheader()
    for product in sorted(product_revenue):
        writer.writerow({
            "product":        product,
            "total_quantity": int(product_qty[product]),
            "total_revenue":  round(product_revenue[product], 2)
        })

print(f"Summary CSV written to {SUMMARY_CSV}")

# --- Print summary to terminal ---
print("\n" + "=" * W)
print(f"{'SALES REPORT':^{W}}")
print("=" * W)
print(f"{'Total Revenue:':<28}${total_revenue:>10.2f}")
print(f"{'Best Day:':<28}{best_day} (${date_revenue[best_day]:.2f})")
print("-" * W)
print(f"{'Product':<16}{'Qty':>8}{'Revenue':>14}")
print("-" * W)
for product in sorted(product_revenue):
    print(f"{product:<16}{int(product_qty[product]):>8}  ${product_revenue[product]:>10.2f}")
print("=" * W)
