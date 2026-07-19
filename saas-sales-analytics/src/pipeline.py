"""
saas_sales_analysis.py
======================
End-to-end analysis pipeline for the Amazon AWS SaaS Sales dataset
(a fictitious B2B SaaS company selling sales & marketing software).

PIPELINE STAGES
    1. Load & inspect
    2. Clean (standardize names, parse dates, validate, de-duplicate)
    3. Feature engineering (margin, loss flag, date parts, order rollups)
    4. Exploratory Data Analysis (KPIs + segment breakdowns)
    5. Visualizations -- Matplotlib (static PNGs) and Plotly (interactive HTML)
    6. Export the cleaned dataset for the SQL and Power BI layers

HOW TO RUN
    # Option A -- real data (recommended for your portfolio):
    #   1. Download from Kaggle: nnthanh101/aws-saas-sales
    #   2. Save it as  data/raw/aws_saas_sales.csv
    #
    # Option B -- test immediately with synthetic data:
    #   python generate_sample_data.py     # writes data/sample/aws_saas_sales_SAMPLE.csv
    #
    # Then:
    #   python saas_sales_analysis.py

    The script auto-detects the real file and falls back to the sample.

DESIGN NOTES (the "why", for interviews)
    * We count DISTINCT order_id for order-level metrics -- one order can
      span several rows, so counting rows would overstate order counts.
    * Negative profit is NEVER dropped. Loss-making deals are a real finding,
      not dirty data. Removing them would delete the most useful insight.
    * Charts are saved to disk (not shown interactively) so the script runs
      headless and leaves reproducible artifacts.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless backend -> save figures without a display
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px

# --------------------------------------------------------------------------
# CONFIGURATION -- all paths and constants live in config.py
# --------------------------------------------------------------------------
from config import (  # noqa: E402  (import after matplotlib backend is set)
    CLEAN_CSV,
    DROP_COLUMNS,
    FIG_DIR,
    RAW_CSV,
    SAMPLE_CSV,
)
from utils import get_logger, read_csv_safe, write_csv_safe  # noqa: E402

log = get_logger("saas_pipeline")

plt.rcParams.update({"figure.autolayout": True, "axes.grid": True, "grid.alpha": 0.3})


# ==========================================================================
# STAGE 1 -- LOAD & INSPECT
# ==========================================================================
def load_data() -> pd.DataFrame:
    """Load the dataset, preferring the real file and falling back to sample.

    Returns
    -------
    pd.DataFrame
        Raw dataset with original column names.
    """
    if RAW_CSV.exists():
        source = RAW_CSV
    elif SAMPLE_CSV.exists():
        source = SAMPLE_CSV
        log.info("NOTE: using SYNTHETIC sample data. Numbers are not real findings.")
    else:
        raise FileNotFoundError(
            "No data found. Download the real CSV to data/raw/aws_saas_sales.csv, "
            "or run `python src/generate_sample_data.py` to create sample data."
        )

    return read_csv_safe(source, log)


def inspect_data(df: pd.DataFrame) -> None:
    """Print a quick structural profile. Purely informational (no mutation)."""
    log.info("\n--- SHAPE ---")
    log.info(df.shape)
    log.info("\n--- DTYPES ---")
    log.info(df.dtypes)
    log.info("\n--- MISSING VALUES PER COLUMN ---")
    log.info(df.isna().sum())
    log.info("\n--- DUPLICATE ROWS ---")
    log.info(f"{df.duplicated().sum():,} fully-duplicated rows")
    log.info("\n--- NUMERIC SUMMARY ---")
    log.info(df.select_dtypes("number").describe().round(2))


# ==========================================================================
# STAGE 2 -- CLEAN
# ==========================================================================
def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names to snake_case (lower, underscores, no spaces)."""
    df = df.copy()
    df.columns = (
        df.columns.str.strip().str.lower().str.replace(" ", "_", regex=False)
    )
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Parse types, validate measures, and remove exact duplicates.

    Cleaning is deliberately conservative: we fix formats and drop only
    genuine duplicates. We do NOT drop negative profit or large values --
    those are real business events.
    """
    df = df.copy()

    # Parse the order date; anything unparseable becomes NaT so we can catch it.
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    n_bad_dates = df["order_date"].isna().sum()
    if n_bad_dates:
        log.info(f"WARNING: {n_bad_dates} rows had unparseable order_date")

    # Validate discount is a 0-1 decimal. If it looks like whole percents
    # (e.g. 10 instead of 0.10), rescale so downstream math is correct.
    if df["discount"].max() > 1:
        log.info("NOTE: discount appears to be in percent form -> dividing by 100")
        df["discount"] = df["discount"] / 100

    # Remove exact duplicate rows (report how many, for transparency).
    before = len(df)
    df = df.drop_duplicates()
    removed = before - len(df)
    if removed:
        log.info(f"Removed {removed:,} exact duplicate rows")

    # Sanity checks -- surfaced as warnings, not silently altered.
    if (df["sales"] < 0).any():
        log.info("WARNING: negative sales values present -- investigate")
    if (df["quantity"] <= 0).any():
        log.info("WARNING: non-positive quantity present -- investigate")

    return df


# ==========================================================================
# STAGE 3 -- FEATURE ENGINEERING
# ==========================================================================
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create derived columns used across EDA, SQL, and the dashboard."""
    df = df.copy()

    # Date parts for time-based analysis.
    df["year"] = df["order_date"].dt.year
    df["month"] = df["order_date"].dt.month
    df["month_name"] = df["order_date"].dt.strftime("%b")
    df["quarter"] = df["order_date"].dt.quarter
    df["year_month"] = df["order_date"].dt.to_period("M").astype(str)

    # Profit margin = profit / sales. Guard against divide-by-zero.
    df["profit_margin"] = np.where(
        df["sales"] != 0, df["profit"] / df["sales"], np.nan
    )

    # Boolean flag for loss-making lines -- powers the "where are we leaking
    # margin" analysis and a Power BI conditional-format rule later.
    df["is_loss"] = df["profit"] < 0

    # Discount as a display-friendly percentage.
    df["discount_pct"] = (df["discount"] * 100).round(1)

    # Effective revenue per unit. NOTE: labelled "effective" on purpose --
    # Sales already reflects discount, so this is realized revenue/unit,
    # NOT list price. Naming it honestly avoids a misleading metric.
    df["revenue_per_unit"] = np.where(
        df["quantity"] > 0, df["sales"] / df["quantity"], np.nan
    )

    # Revenue band -- turns a continuous measure into an interpretable
    # category for segmentation and slicers.
    df["revenue_band"] = pd.cut(
        df["sales"],
        bins=[-np.inf, 250, 1000, 5000, np.inf],
        labels=["<250", "250-1K", "1K-5K", "5K+"],
    )

    return df


def build_order_level(df: pd.DataFrame) -> pd.DataFrame:
    """Roll line-level rows up to one row per order.

    This is the correct grain for order counts and Average Order Value.
    Aggregating here (instead of on raw rows) is what prevents the
    multi-line double-counting trap.
    """
    order_df = (
        df.groupby("order_id")
        .agg(
            order_date=("order_date", "first"),
            customer=("customer", "first"),
            region=("region", "first"),
            segment=("segment", "first"),
            order_sales=("sales", "sum"),
            order_profit=("profit", "sum"),
            n_lines=("product", "count"),
        )
        .reset_index()
    )
    return order_df


# ==========================================================================
# STAGE 4 -- EXPLORATORY DATA ANALYSIS
# ==========================================================================
def _margin(sales: float, profit: float) -> float:
    """Safe overall margin as a percentage."""
    return (profit / sales * 100) if sales else float("nan")


def headline_kpis(df: pd.DataFrame, order_df: pd.DataFrame) -> dict:
    """Compute the top-line KPIs shown on the dashboard cards."""
    total_sales = df["sales"].sum()
    total_profit = df["profit"].sum()
    n_orders = df["order_id"].nunique()  # DISTINCT, not row count
    kpis = {
        "total_sales": total_sales,
        "total_profit": total_profit,
        "profit_margin_pct": _margin(total_sales, total_profit),
        "n_orders": n_orders,
        "n_customers": df["customer_id"].nunique(),
        "avg_discount_pct": df["discount"].mean() * 100,
        "avg_order_value": total_sales / n_orders if n_orders else float("nan"),
    }
    return kpis


def breakdown(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """Aggregate sales/profit/margin/discount by a categorical dimension."""
    grp = (
        df.groupby(dimension)
        .agg(
            sales=("sales", "sum"),
            profit=("profit", "sum"),
            avg_discount_pct=("discount_pct", "mean"),
            orders=("order_id", "nunique"),
        )
        .reset_index()
    )
    grp["margin_pct"] = (grp["profit"] / grp["sales"] * 100).round(1)
    return grp.sort_values("sales", ascending=False).round(2)


def top_customers(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top-N customers by revenue plus their share of total revenue."""
    total = df["sales"].sum()
    grp = (
        df.groupby("customer")["sales"].sum().sort_values(ascending=False).head(n)
    ).reset_index()
    grp["pct_of_total"] = (grp["sales"] / total * 100).round(1)
    return grp


def run_eda(df: pd.DataFrame, order_df: pd.DataFrame) -> None:
    """Print the full EDA narrative to the console."""
    log.info("\n" + "=" * 60)
    log.info("HEADLINE KPIs")
    log.info("=" * 60)
    kpis = headline_kpis(df, order_df)
    log.info(f"Total Sales      : ${kpis['total_sales']:,.0f}")
    log.info(f"Total Profit     : ${kpis['total_profit']:,.0f}")
    log.info(f"Profit Margin    : {kpis['profit_margin_pct']:.1f}%")
    log.info(f"Orders (distinct): {kpis['n_orders']:,}")
    log.info(f"Customers        : {kpis['n_customers']:,}")
    log.info(f"Avg Discount     : {kpis['avg_discount_pct']:.1f}%")
    log.info(f"Avg Order Value  : ${kpis['avg_order_value']:,.0f}")

    for dim in ["region", "segment", "industry", "product"]:
        log.info("\n" + "-" * 60)
        log.info(f"BY {dim.upper()}")
        log.info("-" * 60)
        log.info(breakdown(df, dim).to_string(index=False))

    log.info("\n" + "-" * 60)
    log.info("TOP 10 CUSTOMERS (revenue concentration)")
    log.info("-" * 60)
    tc = top_customers(df, 10)
    log.info(tc.to_string(index=False))
    log.info(f"\nTop 10 customers = {tc['pct_of_total'].sum():.1f}% of total revenue")

    log.info("\n" + "-" * 60)
    log.info("LOSS-MAKING LINES")
    log.info("-" * 60)
    loss = df[df["is_loss"]]
    log.info(f"{len(loss):,} of {len(df):,} lines are unprofitable "
          f"({len(loss) / len(df) * 100:.1f}%)")
    log.info("Loss $ by product:")
    log.info(loss.groupby("product")["profit"].sum().sort_values().round(0).to_string())

    log.info("\n" + "-" * 60)
    log.info("DISCOUNT vs PROFIT (correlation)")
    log.info("-" * 60)
    corr = df["discount"].corr(df["profit_margin"])
    log.info(f"Pearson corr(discount, profit_margin) = {corr:.3f}")


# ==========================================================================
# STAGE 5 -- VISUALIZATIONS
# ==========================================================================
def save_matplotlib_charts(df: pd.DataFrame) -> None:
    """Create and save static PNG charts (good for README / print)."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Sales & profit by region (grouped bars).
    reg = breakdown(df, "region")
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(reg))
    ax.bar(x - 0.2, reg["sales"], width=0.4, label="Sales")
    ax.bar(x + 0.2, reg["profit"], width=0.4, label="Profit")
    ax.set_xticks(x)
    ax.set_xticklabels(reg["region"])
    ax.set_title("Sales vs Profit by Region")
    ax.set_ylabel("USD")
    ax.legend()
    fig.savefig(FIG_DIR / "01_sales_profit_by_region.png", dpi=120)
    plt.close(fig)

    # 2. Profit by product -- red bars flag loss-makers (the money chart).
    prod = breakdown(df, "product").sort_values("profit")
    colors = ["#d62728" if p < 0 else "#2ca02c" for p in prod["profit"]]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(prod["product"], prod["profit"], color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_title("Profit by Product (red = loss-making)")
    ax.set_xlabel("Total Profit (USD)")
    fig.savefig(FIG_DIR / "02_profit_by_product.png", dpi=120)
    plt.close(fig)

    # 3. Discount vs profit margin (the margin-leak story).
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(df["discount_pct"], df["profit_margin"] * 100,
               alpha=0.15, s=10)
    ax.axhline(0, color="red", linewidth=0.8, linestyle="--")
    ax.set_title("Discount % vs Profit Margin %")
    ax.set_xlabel("Discount %")
    ax.set_ylabel("Profit Margin %")
    fig.savefig(FIG_DIR / "03_discount_vs_margin.png", dpi=120)
    plt.close(fig)

    # 4. Monthly sales trend.
    trend = df.groupby("year_month")["sales"].sum().reset_index()
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(trend["year_month"], trend["sales"], marker="o", markersize=3)
    ax.set_title("Monthly Sales Trend")
    ax.set_ylabel("Sales (USD)")
    ax.tick_params(axis="x", rotation=90, labelsize=7)
    fig.savefig(FIG_DIR / "04_monthly_sales_trend.png", dpi=120)
    plt.close(fig)

    # 5. Correlation heatmap of the numeric measures.
    measures = df[["sales", "quantity", "discount", "profit", "profit_margin"]]
    corr = measures.corr()
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(corr)))
    ax.set_yticklabels(corr.columns)
    for i in range(len(corr)):
        for j in range(len(corr)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center",
                    fontsize=8)
    fig.colorbar(im, ax=ax)
    ax.set_title("Correlation of Measures")
    fig.savefig(FIG_DIR / "05_correlation_heatmap.png", dpi=120)
    plt.close(fig)

    log.info(f"Saved 5 Matplotlib charts to {FIG_DIR}/")


def save_plotly_charts(df: pd.DataFrame) -> None:
    """Create and save interactive HTML charts (good for exploration)."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Sunburst: region -> industry contribution to sales.
    sun = px.sunburst(
        df, path=["region", "industry"], values="sales",
        title="Sales Breakdown: Region -> Industry",
    )
    sun.write_html(FIG_DIR / "p1_sales_sunburst.html", include_plotlyjs="cdn")

    # 2. Interactive discount vs profit, coloured by segment.
    scat = px.scatter(
        df, x="discount_pct", y="profit", color="segment",
        hover_data=["product", "customer"], opacity=0.5,
        title="Discount % vs Profit by Segment",
    )
    scat.write_html(FIG_DIR / "p2_discount_profit_scatter.html", include_plotlyjs="cdn")

    # 3. Top 10 customers by revenue.
    tc = top_customers(df, 10)
    bar = px.bar(
        tc, x="sales", y="customer", orientation="h",
        title="Top 10 Customers by Revenue",
    )
    bar.update_layout(yaxis={"categoryorder": "total ascending"})
    bar.write_html(FIG_DIR / "p3_top_customers.html", include_plotlyjs="cdn")

    # 4. Monthly sales trend (interactive).
    trend = df.groupby("year_month")["sales"].sum().reset_index()
    line = px.line(
        trend, x="year_month", y="sales", markers=True,
        title="Monthly Sales Trend (interactive)",
    )
    line.write_html(FIG_DIR / "p4_monthly_trend.html", include_plotlyjs="cdn")

    log.info(f"Saved 4 Plotly charts to {FIG_DIR}/")


# ==========================================================================
# STAGE 6 -- EXPORT
# ==========================================================================
def export_clean(df: pd.DataFrame) -> None:
    """Write the cleaned, feature-rich dataset for the SQL / Power BI layers."""
    write_csv_safe(df, CLEAN_CSV, log)


# ==========================================================================
# ORCHESTRATION
# ==========================================================================
def main() -> None:
    """Run the full pipeline in order."""
    raw = load_data()
    inspect_data(raw)

    df = clean_column_names(raw)
    df = clean_data(df)
    df = df.drop(columns=[c for c in DROP_COLUMNS if c in df.columns])
    df = engineer_features(df)

    order_df = build_order_level(df)

    run_eda(df, order_df)
    save_matplotlib_charts(df)
    save_plotly_charts(df)
    export_clean(df)

    log.info("\nPipeline complete.")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as exc:
        log.error("Pipeline aborted -- missing input: %s", exc)
        raise SystemExit(1)
    except Exception:  # noqa: BLE001 -- log the traceback before exiting
        log.exception("Pipeline failed with an unexpected error")
        raise SystemExit(1)
