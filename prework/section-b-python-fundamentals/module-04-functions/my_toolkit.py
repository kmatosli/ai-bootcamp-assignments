# my_toolkit.py — reusable utility functions for Premia analyst workbench
# Demonstrates: functions, docstrings, loops, tuples, string manipulation

def calculate_average(numbers):
    """
    Takes a list of numbers and returns the average as a float.
    Returns 0 if the list is empty to avoid division by zero.
    Used in Premia to calculate average accuracy scores and KPI hit rates.
    """
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)


def find_max_and_min(numbers):
    """
    Takes a list of numbers and returns a tuple (max_value, min_value).
    Implements the logic manually without using built-in max() or min().
    Used in Premia to find highest and lowest analyst accuracy scores.
    """
    if not numbers:
        return (None, None)

    current_max = numbers[0]
    current_min = numbers[0]

    for value in numbers[1:]:
        if value > current_max:
            current_max = value
        if value < current_min:
            current_min = value

    return (current_max, current_min)


def count_occurrences(items, target):
    """
    Takes a list and a target value, returns how many times target appears.
    Implements the logic manually without using built-in .count() method.
    Used in Premia to count how many times a KPI status appears in a list.
    """
    count = 0
    for item in items:
        if item == target:
            count += 1
    return count


def is_palindrome(text):
    """
    Takes a string and returns True if it reads the same forward and backward.
    Case-insensitive and ignores spaces.
    Examples: "racecar" -> True, "hello" -> False,
    "A man a plan a canal Panama" -> True
    """
    if not text or not text.strip():
        return False
    cleaned = text.lower().replace(" ", "")
    return cleaned == cleaned[::-1]


def create_report(title, scores):
    """
    Takes a report title and a list of scores.
    Uses calculate_average and find_max_and_min internally.
    Returns a formatted string report — does not print directly.
    Used in Premia to generate analyst accuracy summary reports.
    """
    avg = calculate_average(scores)
    high, low = find_max_and_min(scores)
    W = 44
    divider = "=" * W
    sep = "-" * W

    report = f"{divider}\n"
    report += f"{title:^{W}}\n"
    report += f"{divider}\n"
    report += f"{'Total scores:':<28}{len(scores)}\n"
    report += f"{'Average:':<28}{avg:.1f}\n"
    report += f"{'Highest:':<28}{high}\n"
    report += f"{'Lowest:':<28}{low}\n"
    report += f"{divider}"

    return report


if __name__ == "__main__":
    # Test each function with sample analyst accuracy scores
    test_scores = [85, 92, 78, 95, 88, 70, 93]

    print(f"Average: {calculate_average(test_scores)}")
    print(f"Max/Min: {find_max_and_min(test_scores)}")
    print(f"Count of 85: {count_occurrences(test_scores, 85)}")
    print(f"'racecar' palindrome: {is_palindrome('racecar')}")
    print(f"'hello' palindrome: {is_palindrome('hello')}")
    print()
    print(create_report("Class Scores", test_scores))
