# number_collector.py
# Crash-proof input program — Prework Section C
# Demonstrates: input(), try/except ValueError, type conversion, arithmetic

# --- Collect 3 numbers with error handling ---
# try/except catches ValueError if the user types something non-numeric
# instead of crashing, we print a helpful message and default to 0

numbers = []

for i in range(1, 4):
    try:
        value = int(input(f"Enter number {i}: "))
    except ValueError:
        print("That's not a valid number. Using 0 instead.")
        value = 0
    numbers.append(value)

# --- Calculate results ---
total = sum(numbers)
average = total / len(numbers)

# --- Print summary ---
print(f"\nYour numbers: {numbers[0]}, {numbers[1]}, {numbers[2]}")
print(f"Sum: {total}")
print(f"Average: {average:.2f}")
