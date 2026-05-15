"""
sec_observations_cleaning.py — Clean and visualize real Caduceus EDGAR data.

Coding Temple AI Bootcamp · Module 2 · Data Cleaning + Visualization
Author: Kathy Matos

This is the Data Cleaning + matplotlib deliverable, applied to real SEC
EDGAR observations from the Caduceus healthcare equity platform. The data
originated from the SEC EDGAR XBRL API via the edgartools Python library,
landed in a Supabase Postgres instance, and a snapshot is bundled here for
the submission. See README.md for architecture.

Architecture:
    1. Connect — bundled CSV (default) or live Supabase if DATABASE_URL set
    2. Clean  — fiscal-period normalization, type coercion, dedup, classify
                quarterly/annual periods, drop nulls
    3. Validate — coverage by ticker × concept, period coverage, magnitude
                  sanity check on revenue (flags suspicious values)
    4. Visualize — branded 3-panel chart with legends below each panel and
                   inline analysis annotations
    5. Export   — refreshed CSV snapshot (when Supabase path is used)

Run:
    python sec_observations_cleaning.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


# Optional .env loader — only matters when running against live Supabase
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ──────────────────────────────────────────────────────────────────────────────
# Brand system — imported from sibling branding/ folder
# ──────────────────────────────────────────────────────────────────────────────

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from branding import (
    COLORS, TICKER_COLORS, FONTS, FONT_WEIGHTS,
    apply_matplotlib_style, annotation_box_style,
)


# ──────────────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────────────

#: Caduceus Phase 1 data universe — all 8 names whose financials are loaded.
PHASE_1_TICKERS = ["PFE", "MRK", "JNJ", "ABBV", "BMY", "LLY", "AMGN", "GILD"]

#: Chart universe — pharma-only.
#: JNJ is excluded from analytical charts because (a) its MedTech segment
#: dilutes pharma comparability, and (b) its scale (~$94B vs the cluster
#: at ~$30-65B) distorts axes and obscures the meaningful dispersion among
#: the actual pharma peers. JNJ remains in the data layer for cross-checks.
CHART_UNIVERSE = ["PFE", "MRK", "ABBV", "BMY", "LLY", "AMGN", "GILD"]

CHART_CONCEPTS = [
    "revenue", "net_income", "rd_expense", "capex",
    "cfo", "total_assets", "cash", "long_term_debt",
]

#: Bundled CSV snapshot path (relative to this script)
BUNDLED_CSV = HERE / "data" / "edgar_observations.csv"

#: Chart output path
CHART_OUTPUT = HERE / "output" / "sec_observations_charts.png"


# ──────────────────────────────────────────────────────────────────────────────
# Data acquisition — CSV-first, Supabase if DATABASE_URL is set
# ──────────────────────────────────────────────────────────────────────────────

def _find_db_url() -> Optional[str]:
    """Look for DATABASE_URL in environment. Used for live Supabase pull."""
    for key in ("DATABASE_URL_SESSION", "DATABASE_URL", "DATABASE_URL_TRANSACTION"):
        v = os.environ.get(key)
        if v:
            return v
    return None


def fetch_from_supabase(db_url: str) -> pd.DataFrame:
    """Live pull from the Caduceus Supabase Postgres instance."""
    import psycopg2

    sql = """
        SELECT
            e.current_ticker        AS ticker,
            c.name                  AS concept,
            o.value_numeric         AS value,
            o.period_start          AS period_start,
            o.period_end            AS period_end,
            o.form                  AS form,
            o.fiscal_year           AS fiscal_year,
            o.fiscal_period         AS fiscal_period,
            o.accession_number      AS accession_number,
            o.is_canonical          AS is_canonical
        FROM edgar_observations o
        JOIN entities e ON e.caduceus_uuid = o.caduceus_uuid
        JOIN concepts c ON c.concept_id     = o.concept_id
        WHERE e.current_ticker = ANY(%s)
          AND c.name           = ANY(%s)
          AND o.is_canonical   = TRUE
        ORDER BY ticker, concept, period_end DESC
    """
    with psycopg2.connect(db_url) as conn:
        return pd.read_sql(sql, conn, params=(PHASE_1_TICKERS, CHART_CONCEPTS))


def fetch_from_csv() -> pd.DataFrame:
    """Read the bundled CSV snapshot."""
    if not BUNDLED_CSV.exists():
        raise FileNotFoundError(
            f"Bundled CSV not found at {BUNDLED_CSV}. "
            f"This submission requires data/edgar_observations.csv "
            f"to ship alongside the script."
        )
    return pd.read_csv(BUNDLED_CSV, parse_dates=["period_start", "period_end"])


def fetch_observations() -> tuple[pd.DataFrame, str]:
    """
    Try Supabase first if DATABASE_URL is set; otherwise read the bundled CSV.
    Returns (DataFrame, source_label) where source_label is "supabase" or "csv".
    """
    db_url = _find_db_url()
    if db_url:
        try:
            df = fetch_from_supabase(db_url)
            print(f"  Connected to Supabase, fetched {len(df):,} rows (live).")
            return df, "supabase"
        except Exception as e:
            print(f"  ! Supabase fetch failed: {type(e).__name__}: {str(e)[:80]}")
            print(f"    Falling back to bundled CSV.")

    df = fetch_from_csv()
    print(f"  Read {len(df):,} rows from bundled CSV ({BUNDLED_CSV.name}).")
    return df, "csv"


# ──────────────────────────────────────────────────────────────────────────────
# Cleaning
# ──────────────────────────────────────────────────────────────────────────────

def clean_observations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the full cleaning pipeline to raw EDGAR observations.

    Steps:
      1. Type coercion (dates, numeric values)
      2. Drop rows with null/non-numeric values
      3. Normalize fiscal_period strings (uppercase, strip)
      4. Compute period length in days
      5. Classify period_kind as quarterly / annual / other
      6. Build a stable period_label for dedup
      7. Deduplicate by (ticker, concept, period_label), keeping the most
         recently filed (handles restatements — e.g., JNJ's 2024-filed
         restatement of FY2023 revenue after the Kenvue divestiture)
    """
    print(f"\n  Cleaning {len(df):,} raw rows:")
    df = df.copy()

    # 1. Type coercion
    df["period_end"] = pd.to_datetime(df["period_end"])
    df["period_start"] = pd.to_datetime(df["period_start"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # 2. Drop nulls
    before = len(df)
    df = df.dropna(subset=["value"])
    if before - len(df):
        print(f"    Dropped {before - len(df)} rows with null/non-numeric value")

    # 3. Normalize fiscal_period
    df["fiscal_period"] = (
        df["fiscal_period"].fillna("").astype(str).str.upper().str.strip()
    )

    # 4. Period length
    df["period_length_days"] = (df["period_end"] - df["period_start"]).dt.days

    # 5. Classify period_kind by length (quarterly ≈ 90 days, annual ≈ 365)
    def _classify(days):
        if pd.isna(days):
            return "unknown"
        if 80 <= days <= 100:
            return "quarterly"
        if 350 <= days <= 380:
            return "annual"
        return "other"

    df["period_kind"] = df["period_length_days"].apply(_classify)
    counts = df["period_kind"].value_counts().to_dict()
    print(f"    Period kind split: {counts}")

    # 6. Build dedup label
    def _label(row):
        if row["period_kind"] == "quarterly":
            fp = row["fiscal_period"]
            if fp in ("Q1", "Q2", "Q3", "Q4"):
                return f"{int(row['fiscal_year'])}-{fp}"
            q = ((row["period_end"].month - 1) // 3) + 1
            return f"{row['period_end'].year}-Q{q}"
        if row["period_kind"] == "annual":
            try:
                return f"{int(row['fiscal_year'])}-FY"
            except (ValueError, TypeError):
                return f"{row['period_end'].year}-FY"
        return None

    df["period_label"] = df.apply(_label, axis=1)

    # 7. Dedup — keep first when sorted by period_end DESC
    #    (after sort, "first" is the most recent filing → handles restatements)
    before = len(df)
    df = (
        df.sort_values("period_end", ascending=False)
          .drop_duplicates(subset=["ticker", "concept", "period_label"], keep="first")
    )
    print(f"    Deduplicated to {len(df):,} rows (removed {before - len(df)})")

    return df.reset_index(drop=True)


# ──────────────────────────────────────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────────────────────────────────────

def validate(df: pd.DataFrame) -> None:
    """Coverage and magnitude sanity checks."""
    print(f"\n  Validation summary:")

    # Coverage: every ticker × concept should have at least one row
    cov = df.groupby(["ticker", "concept"]).size().unstack(fill_value=0)
    missing = []
    for ticker in PHASE_1_TICKERS:
        if ticker not in cov.index:
            missing.append((ticker, "ALL CONCEPTS"))
            continue
        for concept in CHART_CONCEPTS:
            if concept not in cov.columns or cov.loc[ticker, concept] == 0:
                missing.append((ticker, concept))
    if missing:
        print(f"    Coverage gaps:")
        for t, c in missing:
            print(f"        {t} missing {c}")
    else:
        print(f"    All {len(PHASE_1_TICKERS)} tickers x {len(CHART_CONCEPTS)} concepts have data.")

    # Period coverage per ticker
    print(f"    Period coverage (annual rows):")
    ann = df[df["period_kind"] == "annual"]
    for t in PHASE_1_TICKERS:
        rows = ann[ann["ticker"] == t]
        if rows.empty:
            print(f"        {t}: no annual rows")
            continue
        years = sorted(rows["fiscal_year"].dropna().unique())
        print(f"        {t}: FYs {int(min(years))}-{int(max(years))}  ({len(years)} years)")

    # Magnitude sanity check on annual revenue (large pharma should be $1-300B)
    rev_ann = df[(df["concept"] == "revenue") & (df["period_kind"] == "annual")]
    if not rev_ann.empty:
        suspicious = rev_ann[(rev_ann["value"] < 1e9) | (rev_ann["value"] > 3e11)]
        if not suspicious.empty:
            print(f"    Revenue magnitude flags ({len(suspicious)}):")
            for _, r in suspicious.head(5).iterrows():
                print(f"        {r['ticker']} {int(r['fiscal_year'])}: ${r['value']/1e9:.1f}B")
        else:
            print(f"    All annual revenue values in $1B-$300B range.")


# ──────────────────────────────────────────────────────────────────────────────
# Branded visualization
# ──────────────────────────────────────────────────────────────────────────────

def make_charts(df: pd.DataFrame, out_path: Path) -> None:
    """Three branded panels: FY revenue / quarterly trend / R&D intensity.

    Pharma-only by design — JNJ is filtered out at the chart layer because
    its MedTech segment and scale make it not directly comparable to pure
    pharma peers. The underlying data still contains JNJ for cross-checks.
    """
    apply_matplotlib_style()

    # Filter to pharma-only universe — JNJ drops from all three panels
    df = df[df["ticker"].isin(CHART_UNIVERSE)].copy()

    fig, axes = plt.subplots(
        1, 3, figsize=(20, 7),
        gridspec_kw={"bottom": 0.22, "top": 0.88, "wspace": 0.28},
    )

    # Find the latest FY with most companies reporting
    ann_rev = (
        df[(df["concept"] == "revenue") & (df["period_kind"] == "annual")]
        .pivot_table(index="fiscal_year", columns="ticker", values="value", aggfunc="first")
        .sort_index()
    )
    complete_years = ann_rev.dropna(thresh=5).index  # 5 of 7 names reporting
    latest_year = int(complete_years.max()) if len(complete_years) else int(ann_rev.index.max())

    # ── PANEL 1 — FY revenue by ticker ────────────────────────────────────────
    ax = axes[0]
    latest_rev = ann_rev.loc[latest_year].dropna().sort_values(ascending=False)
    colors = [TICKER_COLORS[t] for t in latest_rev.index]
    ax.bar(
        latest_rev.index, latest_rev.values / 1e9, color=colors,
        edgecolor=COLORS["ink_slate"], linewidth=0.6,
    )
    # Give the top some headroom so value labels don't clip
    ax.set_ylim(0, latest_rev.iloc[0] / 1e9 * 1.12)
    ax.set_title(
        f"FY{latest_year} revenue by ticker",
        fontfamily=FONTS["serif"], pad=12,
    )
    ax.set_ylabel("USD billions")
    for i, (t, v) in enumerate(latest_rev.items()):
        ax.text(
            i, v / 1e9, f"${v/1e9:.1f}B",
            ha="center", va="bottom",
            fontsize=9, color=COLORS["ink_slate"],
            fontweight=FONT_WEIGHTS["emphasis"],
        )

    universe_total = latest_rev.sum() / 1e9
    top4_total = latest_rev.head(4).sum() / 1e9
    top4_share = top4_total / universe_total * 100
    top4_names = ", ".join(latest_rev.head(4).index.tolist())
    bottom3_avg = latest_rev.tail(3).mean() / 1e9
    ax.text(
        0.98, 0.97,
        f"Pharma universe: ${universe_total:.0f}B\n"
        f"Top-4 ({top4_names})\n"
        f"  cluster at $61-65B = {top4_share:.0f}% of total\n"
        f"Bottom-3 average: ${bottom3_avg:.0f}B  (sub-scale)",
        transform=ax.transAxes, va="top", ha="right",
        fontsize=9, color=COLORS["ink_slate"], bbox=annotation_box_style(),
    )

    legend_handles = [
        plt.Rectangle((0, 0), 1, 1, color=TICKER_COLORS[t]) for t in latest_rev.index
    ]
    ax.legend(
        legend_handles, list(latest_rev.index),
        loc="upper center", bbox_to_anchor=(0.5, -0.10),
        ncol=len(latest_rev), frameon=False, fontsize=8.5,
        handlelength=1.2, handletextpad=0.4, columnspacing=1.0,
    )

    # ── PANEL 2 — Quarterly revenue trend ────────────────────────────────────
    ax = axes[1]
    qtr = (
        df[(df["concept"] == "revenue") & (df["period_kind"] == "quarterly")]
        .sort_values("period_end")
    )
    recent_periods = sorted(qtr["period_label"].dropna().unique())[-8:]
    qtr = qtr[qtr["period_label"].isin(recent_periods)]

    first_period = qtr["period_end"].min() if not qtr.empty else None
    last_period = qtr["period_end"].max() if not qtr.empty else None

    growth_rows = []
    for t in sorted(CHART_UNIVERSE):
        sub = qtr[qtr["ticker"] == t].sort_values("period_end")
        if sub.empty:
            continue
        ax.plot(
            sub["period_end"], sub["value"] / 1e9,
            marker="o", markersize=5, linewidth=1.8, label=t,
            color=TICKER_COLORS[t],
        )
        if len(sub) >= 2:
            first_v = sub.iloc[0]["value"]
            last_v = sub.iloc[-1]["value"]
            if first_v:
                growth_rows.append((t, (last_v / first_v - 1) * 100))

    ax.set_title(
        f"Quarterly revenue — last {len(recent_periods)} quarters",
        fontfamily=FONTS["serif"], pad=12,
    )
    ax.set_ylabel("USD billions")
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, axis="y", color=COLORS["light_grey"], linewidth=0.6)

    # Add headroom so the highest line doesn't touch the frame or annotation
    if not qtr.empty:
        ymax = qtr["value"].max() / 1e9
        ymin = qtr["value"].min() / 1e9
        ax.set_ylim(ymin * 0.9, ymax * 1.15)

    # Panel 2 deliberately has no annotation — the LLY trajectory is
    # self-explanatory once you see the chart; over-annotating quarterly
    # revenue movements would attribute single-quarter spikes (Paxlovid
    # lump-sum recognition, Gardasil seasonality) as if they were
    # fundamentals.

    ax.legend(
        loc="upper center", bbox_to_anchor=(0.5, -0.18),
        ncol=len(CHART_UNIVERSE), frameon=False, fontsize=8.5,
        handlelength=1.5, handletextpad=0.5, columnspacing=1.0,
    )

    # ── PANEL 3 — R&D intensity ──────────────────────────────────────────────
    ax = axes[2]
    ann_rd = (
        df[(df["concept"] == "rd_expense") & (df["period_kind"] == "annual")]
        .pivot_table(index="fiscal_year", columns="ticker", values="value", aggfunc="first")
        .sort_index()
    )
    if latest_year in ann_rd.index:
        rd_latest = ann_rd.loc[latest_year]
        intensity = (rd_latest / latest_rev * 100).dropna().sort_values(ascending=False)
        colors3 = [TICKER_COLORS[t] for t in intensity.index]
        ax.bar(
            intensity.index, intensity.values, color=colors3,
            edgecolor=COLORS["ink_slate"], linewidth=0.6,
        )
        ax.set_ylim(0, intensity.iloc[0] * 1.15)
        ax.set_title(
            f"FY{latest_year} R&D intensity",
            fontfamily=FONTS["serif"], pad=12,
        )
        ax.set_ylabel("R&D / Revenue (%)")

        mean = intensity.mean()
        ax.axhline(mean, color=COLORS["monument"], linestyle="--", linewidth=1, alpha=0.7)
        ax.text(
            len(intensity) - 0.4, mean + 0.5, f" universe mean {mean:.0f}%",
            color=COLORS["monument"], fontsize=8,
            va="bottom", ha="left", fontweight=FONT_WEIGHTS["emphasis"],
        )
        for i, (t, v) in enumerate(intensity.items()):
            ax.text(
                i, v, f"{v:.0f}%", ha="center", va="bottom",
                fontsize=9, color=COLORS["ink_slate"],
                fontweight=FONT_WEIGHTS["emphasis"],
            )

        # Group names into R&D-heavy and R&D-light buckets relative to mean
        heavy = intensity[intensity >= mean].index.tolist()
        light = intensity[intensity < mean].index.tolist()
        ax.text(
            0.98, 0.97,
            f"R&D-heavy (>={mean:.0f}%): {', '.join(heavy)}\n"
            f"R&D-light (<{mean:.0f}%): {', '.join(light)}\n"
            f"{intensity.index[0]} top at {intensity.iloc[0]:.0f}%  "
            f"(patent cliff defense)\n"
            f"{intensity.index[-1]} low at {intensity.iloc[-1]:.0f}%  "
            f"(post-Humira recovery)",
            transform=ax.transAxes, va="top", ha="right",
            fontsize=9, color=COLORS["ink_slate"], bbox=annotation_box_style(),
        )

        legend_handles = [
            plt.Rectangle((0, 0), 1, 1, color=TICKER_COLORS[t]) for t in intensity.index
        ]
        ax.legend(
            legend_handles, list(intensity.index),
            loc="upper center", bbox_to_anchor=(0.5, -0.10),
            ncol=len(intensity), frameon=False, fontsize=8.5,
            handlelength=1.2, handletextpad=0.4, columnspacing=1.0,
        )

    # Figure title (serif, brand-styled)
    fig.suptitle(
        f"FY{latest_year} Headline Metrics — Across 7 Pure-Pharma Names",
        fontsize=15, fontweight=FONT_WEIGHTS["title"],
        fontfamily=FONTS["serif"], color=COLORS["ink_slate"],
        y=0.96,
    )

    # Footnote at the bottom of the figure
    fig.text(
        0.98, 0.04,
        "JNJ excluded for MedTech mix  ·  sourced from edgar_observations",
        ha="right", va="bottom",
        fontsize=9, color=COLORS["monument"], style="italic",
        fontfamily=FONTS["sans"],
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=140, bbox_inches="tight", facecolor=COLORS["off_white"])
    plt.close(fig)
    print(f"\n  Chart saved: {out_path.relative_to(HERE)}")


# ──────────────────────────────────────────────────────────────────────────────
# Export — refresh CSV snapshot when running live against Supabase
# ──────────────────────────────────────────────────────────────────────────────

def export_csv(df: pd.DataFrame, path: Path) -> None:
    """Export cleaned data to CSV (used when running live for snapshot refresh)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  Snapshot refreshed: {path.relative_to(HERE)}  ({len(df):,} rows)")


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 78)
    print("  CADUCEUS EDGAR OBSERVATIONS — clean + validate + visualize")
    print("=" * 78)

    print("\n  Fetching observations:")
    df, source = fetch_observations()

    df = clean_observations(df)
    validate(df)

    if source == "supabase":
        # Refresh the bundled snapshot when running live
        export_csv(df, BUNDLED_CSV)

    make_charts(df, CHART_OUTPUT)

    print(f"\n  Done. Source: {source}. Clean rows: {len(df):,}")


if __name__ == "__main__":
    main()
