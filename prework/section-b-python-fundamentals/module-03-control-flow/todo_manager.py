# coverage_list_manager.py — submitted as todo_manager.py equivalent
# Interactive coverage list for a buy-side analyst
# Demonstrates: lists, append(), pop(), try/except, f-strings

# --- Pre-populated coverage list — 3 starting names ---
coverage = ["NVDA - Buy", "ASML - Neutral", "AMAT - Buy"]

def display_list(items):
    # Print the current coverage list numbered from 1
    W = 40
    print("=" * W)
    print(f"{'My Coverage List':^{W}}")
    print("=" * W)
    for i, item in enumerate(items, start=1):
        print(f"{i}. {item}")
    print(f"\nTotal names: {len(items)}")

# --- Main program loop ---
display_list(coverage)

print("\nWhat would you like to do?")
print("1. Add a name")
print("2. Remove a name")

choice = input("Choice: ")

if choice == "1":
    # append() adds the new name to the end of the list
    new_name = input("Enter new name (e.g. LLY - Buy): ")
    coverage.append(new_name)
    print("\nUpdated list:")
    display_list(coverage)

elif choice == "2":
    try:
        # User sees 1-based numbers — subtract 1 for Python 0-based index
        num = int(input("Enter task number to remove: "))
        removed = coverage.pop(num - 1)
        print(f"Removed: {removed}")
        print("\nUpdated list:")
        display_list(coverage)
    except (ValueError, IndexError):
        print("Invalid number. Please enter a valid task number.")

else:
    print("Invalid choice. Please enter 1 or 2.")
