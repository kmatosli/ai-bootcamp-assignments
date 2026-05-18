"""
main.py — Module 2 Capstone entry point.

Runs the Caduceus DataPipeline against a messy SEC observations CSV.
"""
from __future__ import annotations

from pathlib import Path

from pipeline import DataPipeline


def main() -> None:
    print("=" * 70)
    print("  CADUCEUS DATA PIPELINE — Module 2 Capstone")
    print("=" * 70)

    here = Path(__file__).parent
    raw_csv = here / "data" / "messy_observations.csv"

    pipeline = DataPipeline(raw_csv)
    results = pipeline.run(
        charts_path=here / "output" / "charts.png",
        export_path=here / "output" / "clean_observations.csv",
    )

    print("\n" + "=" * 70)
    print("  ANALYSIS RESULTS")
    print("=" * 70)
    for key, value in results.items():
        print(f"\n  {key}:")
        if isinstance(value, dict):
            for k, v in value.items():
                if isinstance(v, float):
                    print(f"    {k:30s}  {v:,.2f}")
                else:
                    print(f"    {k:30s}  {v}")
        else:
            print(f"    {value}")


if __name__ == "__main__":
    main()
