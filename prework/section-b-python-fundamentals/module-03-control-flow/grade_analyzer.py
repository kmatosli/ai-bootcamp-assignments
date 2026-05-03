# grade_analyzer.py — forecast accuracy tracker applied to Premia
# Analyzes analyst estimate accuracy scores across a coverage universe
# Demonstrates: for loops, while loops, conditionals, lists, formatted output

# --- Starting accuracy scores for 15 covered names ---
scores = [88, 45, 92, 67, 73, 95, 81, 56, 78, 100, 62, 85, 90, 38, 71]

def get_grade(score):
    # Categorize each accuracy score into a letter grade
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"

def analyze(scores):
    # Count grade distribution using a dictionary
    distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    passing = 0
    failing = 0

    for score in scores:
        grade = get_grade(score)
        distribution[grade] += 1
        if score >= 60:
            passing += 1
        else:
            failing += 1

    total = len(scores)
    average = sum(scores) / total
    highest = max(scores)
    lowest = min(scores)

    print("\n=== Grade Analyzer ===")
    print(f"Total scores:   {total}")
    print(f"Average:        {average:.1f}")
    print(f"Highest:        {highest}")
    print(f"Lowest:         {lowest}")
    print(f"Passing:        {passing} ({passing/total*100:.1f}%)")
    print(f"Failing:        {failing} ({failing/total*100:.1f}%)")
    print("\nGrade Distribution:")
    for grade, count in distribution.items():
        print(f"  {grade}: {count} students")

# --- Initial analysis ---
analyze(scores)

# --- While loop to add more scores ---
print("\n--- Add More Scores ---")
while True:
    entry = input("Enter a score (or 'done' to finish): ")
    if entry.lower() == "done":
        print(f"Final average: {sum(scores)/len(scores):.1f}")
        break
    try:
        new_score = int(entry)
        scores.append(new_score)
        print(f"Updated average: {sum(scores)/len(scores):.1f}")
    except ValueError:
        print("Invalid input. Enter a number or 'done'.")
