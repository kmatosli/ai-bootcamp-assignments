# grade_tracker.py
# Pre-Work Section C — Python Fundamentals Capstone
# Applied to Premia: same pattern as the forecast accuracy reporting pipeline

import csv
import os
from datetime import date


def load_students(filepath: str) -> list[dict]:
    """Read students.csv and return a list of row dicts."""
    try:
        students = []
        with open(filepath, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                students.append(dict(row))
        return students
    except FileNotFoundError:
        print(f"  ERROR: Data file not found: {filepath}")
        print(f"  Expected location: {os.path.abspath(filepath)}")
        return []


def calculate_average(grades: list) -> float | None:
    """Return average of grade values, skipping empty strings. Returns None if all missing."""
    valid_grades = []
    for g in grades:
        if g == "" or g is None:
            continue
        try:
            valid_grades.append(float(g))
        except (ValueError, TypeError):
            continue
    if not valid_grades:
        return None
    return round(sum(valid_grades) / len(valid_grades), 1)


def get_letter_grade(average: float | None) -> str:
    """Convert numeric average to letter grade. Returns N/A if average is None."""
    if average is None:
        return "N/A"
    if average >= 90:
        return "A"
    elif average >= 80:
        return "B"
    elif average >= 70:
        return "C"
    elif average >= 60:
        return "D"
    else:
        return "F"


def generate_report(students: list[dict]) -> dict:
    """Process full student list and return summary dict."""
    SUBJECTS = ["math", "science", "english", "history"]
    student_results = []
    valid_averages = []
    grade_dist = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0, "N/A": 0}

    for student in students:
        raw_grades = [student.get(s, "") for s in SUBJECTS]
        present = [g for g in raw_grades if g != "" and g is not None]
        missing = len(SUBJECTS) - len(present)
        avg = calculate_average(raw_grades)
        letter = get_letter_grade(avg)

        if avg is not None:
            valid_averages.append(avg)

        grade_dist[letter] = grade_dist.get(letter, 0) + 1
        student_results.append({
            "name": student.get("student_name", "Unknown"),
            "average": avg,
            "letter_grade": letter,
            "grades_present": len(present),
            "grades_missing": missing,
        })

    class_avg = round(sum(valid_averages) / len(valid_averages), 1) if valid_averages else None
    highest = max(valid_averages) if valid_averages else None
    lowest = min(valid_averages) if valid_averages else None

    student_results.sort(
        key=lambda s: s["average"] if s["average"] is not None else -1,
        reverse=True
    )

    return {
        "total_students": len(students),
        "class_average": class_avg,
        "highest_average": highest,
        "lowest_average": lowest,
        "grade_distribution": grade_dist,
        "student_results": student_results,
    }


def write_report(report: dict, filepath: str) -> None:
    """Write formatted summary report to a text file."""
    W = 60
    div = "=" * W
    sep = "-" * W

    def fmt_avg(val):
        return f"{val:.1f}" if val is not None else "N/A"

    lines = [
        div,
        f"{'GRADE REPORT':^{W}}",
        f"{'Generated: ' + str(date.today()):^{W}}",
        div, "",
        "  CLASS SUMMARY", sep,
        f"  {'Total students:':<28}{report['total_students']}",
        f"  {'Class average:':<28}{fmt_avg(report['class_average'])}",
        f"  {'Highest average:':<28}{fmt_avg(report['highest_average'])}",
        f"  {'Lowest average:':<28}{fmt_avg(report['lowest_average'])}",
        "", "  GRADE DISTRIBUTION", sep,
    ]

    for letter in ["A", "B", "C", "D", "F", "N/A"]:
        count = report["grade_distribution"].get(letter, 0)
        if count > 0:
            bar = "█" * count
            lines.append(f"  {letter:<5} {bar}  {count}")

    lines += ["", "  INDIVIDUAL RESULTS", sep,
              f"  {'Name':<22}{'Average':>8}  {'Grade':<6}  {'Subjects'}"]
    lines.append(sep)

    for s in report["student_results"]:
        present = s["grades_present"]
        missing = s["grades_missing"]
        sub_note = f"{present}/4" + (f"  ({missing} missing)" if missing else "")
        lines.append(
            f"  {s['name']:<22}{fmt_avg(s['average']):>8}  "
            f"{s['letter_grade']:<6}  {sub_note}"
        )

    lines += ["", div]

    try:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"  Report written to {filepath}")
    except OSError as e:
        print(f"  ERROR writing report: {e}")


def main():
    print("\nLoading student data...")
    students = load_students("prework/section-b-python-fundamentals/section-c-capstone/data/students.csv")

    if not students:
        print("  No students loaded. Exiting.")
        return

    print(f"  Loaded {len(students)} students.")
    print("\nGenerating report...")

    report = generate_report(students)

    print("\n--- Summary ---")
    print(f"Total students:   {report['total_students']}")
    print(f"Class average:    {report['class_average']}")
    print(f"Highest average:  {report['highest_average']}")
    print(f"Lowest average:   {report['lowest_average']}")

    print("\nGrade Distribution:")
    for letter in ["A", "B", "C", "D", "F", "N/A"]:
        count = report["grade_distribution"].get(letter, 0)
        if count > 0:
            print(f"  {letter}: {count}")

    print("\nTop 5 students:")
    for s in report["student_results"][:5]:
        avg = f"{s['average']:.1f}" if s["average"] is not None else "N/A"
        print(f"  {s['name']:<22} {avg:>5}  ({s['letter_grade']})")

    write_report(report, "prework/section-b-python-fundamentals/section-c-capstone/grade_report.txt")
    print()


if __name__ == "__main__":
    main()
