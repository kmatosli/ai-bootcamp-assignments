"""
pipeline.py — Caduceus DataPipeline class.

Bootcamp Module 2 Capstone (Data Processing Pipeline). Re-framed onto
Caduceus's actual operational problem: ingest a messy pre-load CSV of
SEC EDGAR observations, clean it, analyze it, visualize it, and export
the cleaned product ready for the loader to ingest into Postgres.

This is a real Caduceus module — it sits at `data-foundation/extractors/`
in the repo and is the canonical first-pass cleaner that runs before
observations hit the loader.

Architecture:
    DataPipeline.__init__(filepath)   -> load raw CSV
    DataPipeline.clean()              -> all cleaning steps; returns self
    DataPipeline.analyze()            -> return summary dict
    DataPipeline.visualize(out_path)  -> save PNG with 3 charts
    DataPipeline.export(out_path)     -> save cleaned CSV
    DataPipeline.run()                -> chain: clean -> analyze -> viz -> export

The cleaning logic mirrors what a production Caduceus pre-load step does:
filer-tag normalization, unit harmonization, sentinel-value handling, etc.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


# ──────────────────────────────────────────────────────────────────────────────
# Normalization tables — these encode the cross-filer variants we see in EDGAR
# ──────────────────────────────────────────────────────────────────────────────

#: Different XBRL concept tags used by different filers for the same fact.
CONCEPT_NORMALIZATION: Dict[str, str] = {
    "Revenues":                          "Revenue",
    "Revenue":                           "Revenue",
    "SalesRevenueNet":                   "Revenue",
    "RevenueFromContractWithCustomerExcludingAssessedTax": "Revenue",
    "NetSales":                          "Revenue",
    "NetIncomeLoss":                     "NetIncome",
    "NetIncome":                         "NetIncome",
    "ProfitLoss":                        "NetIncome",
    "ResearchAndDevelopmentExpense":     "RandDExpense",
    "RnDExpense":                        "RandDExpense",
    "RDExpense":                         "RandDExpense",
}

#: Ticker-case normalization map for the 8 Phase 1 names (defensive).
PHASE_1_TICKERS = {"PFE", "MRK", "JNJ", "ABBV", "BMY", "LLY", "AMGN", "GILD"}

#: Acceptable unit strings, mapped to a canonical name.
UNIT_NORMALIZATION = {
    "usd":      "USD",
    "USD":      "USD",
    "u.s.d.":   "USD",
    "dollars":  "USD",
    "$":        "USD",
}


# ──────────────────────────────────────────────────────────────────────────────
# The pipeline
# ──────────────────────────────────────────────────────────────────────────────

class DataPipeline:
    """A reusable data processing pipeline for messy SEC observations.

    Usage:
        pipeline = DataPipeline("data/messy_observations.csv")
        results = pipeline.run()

    Or step-by-step:
        pipeline = DataPipeline("data/messy_observations.csv")
        pipeline.clean()
        summary = pipeline.analyze()
        pipeline.visualize("out/charts.png")
        pipeline.export("out/clean.csv")
    """

    def __init__(self, filepath: str | Path) -> None:
        self.filepath = Path(filepath)
        self.raw: pd.DataFrame = pd.DataFrame()
        self.clean_df: pd.DataFrame = pd.DataFrame()
        self.cleaning_log: list[str] = []

        try:
            self.raw = pd.read_csv(self.filepath, dtype=str, keep_default_na=False)
            print(f"  Loaded {len(self.raw)} raw rows from {self.filepath.name}")
        except FileNotFoundError:
            print(f"  ✗ File not found: {self.filepath}")
            raise
        except pd.errors.EmptyDataError:
            print(f"  ✗ File is empty: {self.filepath}")
            raise
        except Exception as e:
            print(f"  ✗ Unexpected load error: {type(e).__name__}: {e}")
            raise

    # ── Public API ───────────────────────────────────────────────────────────

    def clean(self) -> "DataPipeline":
        """Run every cleaning step. Returns self so calls can chain."""
        if self.raw.empty:
            print("  ⚠ No data loaded — nothing to clean")
            return self

        df = self.raw.copy()
        start = len(df)

        df = self._strip_whitespace(df)
        df = self._normalize_tickers(df)
        df = self._normalize_concepts(df)
        df = self._normalize_units(df)
        df = self._coerce_value(df)
        df = self._coerce_period_end(df)
        df = self._drop_invalid_rows(df)
        df = self._drop_duplicates(df)

        self.clean_df = df.reset_index(drop=True)
        kept = len(self.clean_df)

        print(f"\n  Cleaning summary:")
        for line in self.cleaning_log:
            print(f"    • {line}")
        print(f"    • Started with {start} rows, kept {kept} ({start - kept} dropped)")
        return self

    def analyze(self) -> Dict[str, Any]:
        """Return a summary dictionary with the headline metrics."""
        df = self.clean_df
        if df.empty:
            print("  ⚠ Nothing to analyze — clean() first")
            return {}

        results: Dict[str, Any] = {}

        # 1. Average value by concept
        avg_by_concept = (
            df.groupby("concept")["value"]
              .mean()
              .round(2)
              .sort_values(ascending=False)
              .to_dict()
        )
        results["avg_value_by_concept_usd"] = avg_by_concept

        # 2. Total revenue by ticker (Caduceus-meaningful aggregate)
        revenue_rows = df[df["concept"] == "Revenue"]
        if not revenue_rows.empty:
            results["total_revenue_by_ticker_usd"] = (
                revenue_rows.groupby("ticker")["value"]
                            .sum()
                            .round(2)
                            .sort_values(ascending=False)
                            .to_dict()
            )

        # 3. Observation count by ticker (coverage check)
        results["observations_by_ticker"] = (
            df["ticker"].value_counts().to_dict()
        )

        # 4. Correlation between revenue and R&D where both are present
        results["revenue_rd_correlation"] = self._compute_revenue_rd_correlation(df)

        # 5. Caduceus-specific insight: R&D intensity (R&D as % of revenue)
        results["rd_intensity_pct_by_ticker"] = self._compute_rd_intensity(df)

        # Print summary
        print(f"\n  Analysis summary:")
        for k, v in results.items():
            if isinstance(v, dict):
                print(f"    {k}:")
                for kk, vv in list(v.items())[:5]:
                    print(f"      {kk:30s} -> {vv}")
            else:
                print(f"    {k}: {v}")

        return results

    def visualize(self, output_path: str | Path = "output/charts.png") -> None:
        """Save a 3-panel chart: by-concept bar / by-ticker bar / value distribution."""
        df = self.clean_df
        if df.empty:
            print("  ⚠ Nothing to visualize — clean() first")
            return

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        fig, axes = plt.subplots(1, 3, figsize=(18, 5))

        # 1. Total value by concept
        by_concept = df.groupby("concept")["value"].sum().sort_values(ascending=False)
        axes[0].bar(by_concept.index, by_concept.values / 1e9, color="#1f5fa3")
        axes[0].set_title("Total value by concept (USD B)")
        axes[0].set_ylabel("USD Billions")
        axes[0].tick_params(axis="x", rotation=20)

        # 2. Revenue by ticker
        rev = df[df["concept"] == "Revenue"]
        if not rev.empty:
            r_by_t = rev.groupby("ticker")["value"].sum().sort_values(ascending=False)
            axes[1].bar(r_by_t.index, r_by_t.values / 1e9, color="#3a8e3a")
            axes[1].set_title("Revenue by ticker (USD B)")
            axes[1].set_ylabel("USD Billions")

        # 3. Distribution of all numeric values (log-scaled because revenue
        #    and R&D differ by an order of magnitude)
        positive = df[df["value"] > 0]["value"]
        if not positive.empty:
            axes[2].hist(positive / 1e9, bins=20, color="#a35a1f", edgecolor="black")
            axes[2].set_title("Distribution of observation values")
            axes[2].set_xlabel("USD Billions")
            axes[2].set_ylabel("Frequency")

        plt.tight_layout()
        plt.savefig(out, dpi=120, bbox_inches="tight")
        plt.close(fig)
        print(f"\n  Charts saved -> {out}")

    def export(self, output_path: str | Path = "output/clean_observations.csv") -> None:
        """Write the cleaned DataFrame to disk in load-ready form."""
        if self.clean_df.empty:
            print("  ⚠ Nothing to export — clean() first")
            return
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.clean_df.to_csv(out, index=False, encoding="utf-8-sig")
            print(f"  Cleaned CSV saved -> {out}  ({len(self.clean_df)} rows)")
        except (OSError, PermissionError) as e:
            print(f"  ✗ Failed to write {out}: {e}")

    def run(
        self,
        charts_path: str | Path = "output/charts.png",
        export_path: str | Path = "output/clean_observations.csv",
    ) -> Dict[str, Any]:
        """Execute the full pipeline. Returns the analysis dict."""
        self.clean()
        results = self.analyze()
        self.visualize(charts_path)
        self.export(export_path)
        return results

    # ── Private cleaning steps ───────────────────────────────────────────────

    def _strip_whitespace(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype("string").str.strip()
        self.cleaning_log.append("Stripped whitespace from all string columns")
        return df

    def _normalize_tickers(self, df: pd.DataFrame) -> pd.DataFrame:
        df["ticker"] = df["ticker"].str.upper()
        # Drop rows whose normalized ticker isn't a Phase 1 name
        before = len(df)
        df = df[df["ticker"].isin(PHASE_1_TICKERS)]
        dropped = before - len(df)
        if dropped:
            self.cleaning_log.append(
                f"Dropped {dropped} rows with off-universe tickers"
            )
        return df

    def _normalize_concepts(self, df: pd.DataFrame) -> pd.DataFrame:
        before = df["concept"].nunique()
        df["concept"] = df["concept"].map(CONCEPT_NORMALIZATION).fillna(df["concept"])
        after = df["concept"].nunique()
        if before != after:
            self.cleaning_log.append(
                f"Normalized concept names ({before} distinct -> {after} distinct)"
            )
        return df

    def _normalize_units(self, df: pd.DataFrame) -> pd.DataFrame:
        if "unit" not in df.columns:
            return df
        df["unit"] = df["unit"].str.strip().map(
            lambda u: UNIT_NORMALIZATION.get(u, UNIT_NORMALIZATION.get(u.lower() if isinstance(u, str) else u, u))
        )
        # After normalization, only keep USD rows (the canonical unit for the loader)
        before = len(df)
        df = df[df["unit"] == "USD"]
        dropped = before - len(df)
        if dropped:
            self.cleaning_log.append(f"Dropped {dropped} rows with non-USD units")
        return df

    def _coerce_value(self, df: pd.DataFrame) -> pd.DataFrame:
        # Handle sentinels: "$1,234.5M", "1.2B", "1234", "N/A", "-"
        def parse(v: Any) -> float | None:
            if pd.isna(v) or v in ("", "N/A", "-", "None"):
                return None
            s = str(v).strip().replace("$", "").replace(",", "")
            multiplier = 1.0
            if s.endswith(("M", "m")):
                multiplier = 1e6
                s = s[:-1]
            elif s.endswith(("B", "b")):
                multiplier = 1e9
                s = s[:-1]
            elif s.endswith(("K", "k")):
                multiplier = 1e3
                s = s[:-1]
            try:
                return float(s) * multiplier
            except ValueError:
                return None

        before = len(df)
        df["value"] = df["value"].map(parse)
        df = df.dropna(subset=["value"])
        dropped = before - len(df)
        if dropped:
            self.cleaning_log.append(
                f"Dropped {dropped} rows with non-parseable values"
            )
        return df

    def _coerce_period_end(self, df: pd.DataFrame) -> pd.DataFrame:
        if "period_end" not in df.columns:
            return df

        # Try multiple common formats. SEC filings and analyst-entered data
        # use ISO, US, and abbreviated month forms — we try them in order.
        formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d"]
        parsed = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
        for fmt in formats:
            mask = parsed.isna()
            if not mask.any():
                break
            attempt = pd.to_datetime(df.loc[mask, "period_end"], format=fmt, errors="coerce")
            parsed.loc[mask] = attempt
        # Final fallback — let pandas guess for anything still unparsed
        mask = parsed.isna()
        if mask.any():
            parsed.loc[mask] = pd.to_datetime(df.loc[mask, "period_end"], errors="coerce")

        df["period_end"] = parsed
        before = len(df)
        df = df.dropna(subset=["period_end"])
        dropped = before - len(df)
        if dropped:
            self.cleaning_log.append(f"Dropped {dropped} rows with unparseable dates")
        return df

    def _drop_invalid_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        # Revenue and R&D can't be negative; net income can be
        impossibly_negative = df[
            (df["concept"].isin(["Revenue", "RandDExpense"])) & (df["value"] < 0)
        ]
        if not impossibly_negative.empty:
            self.cleaning_log.append(
                f"Dropped {len(impossibly_negative)} rows with negative revenue/R&D"
            )
            df = df.drop(impossibly_negative.index)

        # Obvious magnitude error: any value > $10T is fat-finger
        big = df[df["value"].abs() > 1e13]
        if not big.empty:
            self.cleaning_log.append(
                f"Dropped {len(big)} rows with implausibly large values (> $10T)"
            )
            df = df.drop(big.index)

        return df

    def _drop_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        before = len(df)
        df = df.drop_duplicates(subset=["ticker", "concept", "period_end"], keep="first")
        dropped = before - len(df)
        if dropped:
            self.cleaning_log.append(
                f"Dropped {dropped} duplicate (ticker, concept, period) rows"
            )
        return df

    # ── Analysis helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _compute_revenue_rd_correlation(df: pd.DataFrame) -> float | str:
        pivot = df.pivot_table(
            index=["ticker", "period_end"],
            columns="concept",
            values="value",
            aggfunc="first",
        )
        if "Revenue" not in pivot.columns or "RandDExpense" not in pivot.columns:
            return "n/a (need both Revenue and RandDExpense)"
        both = pivot.dropna(subset=["Revenue", "RandDExpense"])
        if len(both) < 2:
            return "n/a (insufficient paired observations)"
        return round(both["Revenue"].corr(both["RandDExpense"]), 4)

    @staticmethod
    def _compute_rd_intensity(df: pd.DataFrame) -> Dict[str, float]:
        pivot = df.pivot_table(
            index="ticker",
            columns="concept",
            values="value",
            aggfunc="sum",
        )
        if "Revenue" not in pivot.columns or "RandDExpense" not in pivot.columns:
            return {}
        intensity = (pivot["RandDExpense"] / pivot["Revenue"] * 100).round(2)
        return intensity.dropna().sort_values(ascending=False).to_dict()
