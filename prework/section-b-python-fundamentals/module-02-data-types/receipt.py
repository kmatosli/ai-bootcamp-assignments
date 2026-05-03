# receipt.py
# Simulates a simple store receipt
# Demonstrates: type conversion, arithmetic, f-strings, string formatting

# --- Variables defined as strings, simulating data from a file or form ---
item1_name = "Notebook"
item1_price = "4.99"
item1_qty = "2"

item2_name = "Pen Pack"
item2_price = "7.50"
item2_qty = "1"

item3_name = "Backpack"
item3_price = "34.99"
item3_qty = "1"

tax_rate = "0.075"   # 7.5% sales tax

# --- Type conversion: strings must become numbers before arithmetic ---
# float() converts price strings to decimals for dollar calculations
# int() converts quantity strings to whole numbers
p1 = float(item1_price)
q1 = int(item1_qty)

p2 = float(item2_price)
q2 = int(item2_qty)

p3 = float(item3_price)
q3 = int(item3_qty)

# float() converts tax_rate string so we can multiply against subtotal
tax = float(tax_rate)

# --- Calculations ---
line1 = p1 * q1
line2 = p2 * q2
line3 = p3 * q3

subtotal = line1 + line2 + line3
tax_amount = subtotal * tax
grand_total = subtotal + tax_amount

# --- Print formatted receipt using f-strings ---
# :.2f formats all dollar amounts to exactly 2 decimal places
W = 40
print("=" * W)
print(f"{'STORE RECEIPT':^{W}}")
print("=" * W)
print(f"{item1_name:<16}${p1:.2f} x {q1:<5}  ${line1:.2f}")
print(f"{item2_name:<16}${p2:.2f} x {q2:<5}  ${line2:.2f}")
print(f"{item3_name:<16}${p3:.2f} x {q3:<5}  ${line3:.2f}")
print("-" * W)
print(f"{'Subtotal:':<28}${subtotal:.2f}")
print(f"{'Tax (7.5%):':<28}${tax_amount:.2f}")
print("=" * W)
print(f"{'TOTAL:':<28}${grand_total:.2f}")
print("=" * W)
