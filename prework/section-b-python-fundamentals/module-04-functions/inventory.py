# kpi_tracker.py — submitted as inventory.py equivalent
# KPI tracker for a buy-side analyst coverage universe
# Demonstrates: nested dictionaries, .get(), sets, formatted output

# --- Coverage universe with price target and conviction score ---
# Each name has a price target (float) and position size in bps (int)
inventory = {
    "NVDA": {"price": 950.00, "quantity": 150},
    "ASML": {"price": 820.00, "quantity": 75},
    "AMAT": {"price": 210.00, "quantity": 8},
    "LRCX": {"price": 890.00, "quantity": 5},
    "KLAC": {"price": 750.00, "quantity": 120}
}

W = 52

def display_inventory(inv):
    # Print formatted table of all names with price and quantity
    print("=" * W)
    print(f"{'Coverage Universe — KPI Tracker':^{W}}")
    print("=" * W)
    print(f"{'Ticker':<12}{'Price Target':>16}{'Position (bps)':>18}")
    print("-" * W)
    for ticker, data in inv.items():
        print(f"{ticker:<12}${data['price']:>14.2f}{data['quantity']:>18}")
    print("=" * W)

def total_value(inv):
    # Calculate total portfolio exposure — price target x position size
    return sum(d["price"] * d["quantity"] for d in inv.values())

def low_stock_alert(inv, threshold=10):
    # Use a set to track names with low conviction (position < threshold)
    return {ticker for ticker, d in inv.items() if d["quantity"] < threshold}

# --- Display inventory ---
display_inventory(inventory)

# --- Total value ---
print(f"\nTotal portfolio exposure: ${total_value(inventory):,.2f}")

# --- Low stock alert ---
low = low_stock_alert(inventory)
if low:
    print(f"\nLow conviction alert (position < 10 bps):")
    for ticker in sorted(low):
        print(f"  {ticker} — {inventory[ticker]['quantity']} bps")

# --- Product lookup using .get() for safety ---
print()
lookup = input("Look up a ticker (e.g. NVDA): ").upper()
result = inventory.get(lookup)
if result:
    print(f"{lookup}: Price target ${result['price']:.2f} | Position {result['quantity']} bps")
else:
    print(f"{lookup} not found in coverage universe.")

# --- Update quantity (simulate add/trim) ---
print()
update = input("Update position for which ticker: ").upper()
if inventory.get(update):
    try:
        new_qty = int(input(f"Enter new position size (bps) for {update}: "))
        inventory[update]["quantity"] = new_qty
        print(f"Updated. {update} position is now {new_qty} bps.")
        display_inventory(inventory)
    except ValueError:
        print("Invalid input. Position size must be a whole number.")
else:
    print(f"{update} not found in coverage universe.")
