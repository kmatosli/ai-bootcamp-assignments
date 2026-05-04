# buggy_program.py — Fixed version
# All 4 bugs identified and corrected.

def calculate_stats(numbers):                    # BUG 1 FIX: added missing colon
    total = sum(numbers)
    count = len(numbers)
    average = total / count
    above_average = []
    for num in numbers:
        if num > average:                        # BUG 2 FIX: added missing colon
            above_average.append(num)
    return {
        "total": total,
        "average": average,
        "above_average": above_average,
        "above_count": len(above_average)
    }

# BUG 3 FIX: removed "70" string — replaced with integer 70
# str "70" causes TypeError in sum() because you cannot add str to int
scores = [85, 92, 78, 95, 88, 70, 93]

result = calculate_stats(scores)
print(f"Total: {result['total']}")
print(f"Average: {result['average']:.1f}")      # BUG 4 FIX: added quotes around average
print(f"Above average: {result['above_count']} scores")
