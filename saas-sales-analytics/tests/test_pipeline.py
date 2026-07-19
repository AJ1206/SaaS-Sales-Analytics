"""Tests for the SaaS sales pipeline.

These cover the correctness rules the analysis depends on -- especially the
order-grain rule, which is the easiest thing to get silently wrong.
"""

import numpy as np
import pandas as pd
import pytest

from pipeline import (
    breakdown,
    build_order_level,
    clean_column_names,
    clean_data,
    engineer_features,
    headline_kpis,
    top_customers,
)


@pytest.fixture()
def raw_df() -> pd.DataFrame:
    """A tiny frame mirroring the real schema: 2 orders, 3 lines."""
    return pd.DataFrame({
        "Order ID": ["ORD-1", "ORD-1", "ORD-2"],   # ORD-1 spans two lines
        "Order Date": ["2023-01-15", "2023-01-15", "2023-02-20"],
        "Customer ID": ["C1", "C1", "C2"],
        "Customer": ["Acme", "Acme", "Globex"],
        "Region": ["AMER", "AMER", "EMEA"],
        "Segment": ["SMB", "SMB", "Enterprise"],
        "Industry": ["Finance", "Finance", "Energy"],
        "Product": ["FinanceHub", "Support", "FinanceHub"],
        "Sales": [1000.0, 500.0, 2000.0],
        "Quantity": [2, 1, 4],
        "Discount": [0.10, 0.0, 0.20],
        "Profit": [200.0, -50.0, 400.0],           # one loss-making line
    })


def test_clean_column_names_makes_snake_case(raw_df):
    out = clean_column_names(raw_df)
    assert "order_id" in out.columns
    assert "customer_id" in out.columns
    assert not any(" " in c for c in out.columns)


def test_clean_data_rescales_percent_discounts(raw_df):
    df = clean_column_names(raw_df)
    df["discount"] = df["discount"] * 100        # simulate percent-form input
    out = clean_data(df)
    assert out["discount"].max() <= 1.0


def test_clean_data_removes_exact_duplicates(raw_df):
    df = clean_column_names(pd.concat([raw_df, raw_df.iloc[[0]]], ignore_index=True))
    out = clean_data(df)
    assert len(out) == len(raw_df)


def test_engineer_features_adds_expected_columns(raw_df):
    df = engineer_features(clean_data(clean_column_names(raw_df)))
    for col in ["profit_margin", "is_loss", "year", "month", "discount_pct"]:
        assert col in df.columns
    assert df["is_loss"].sum() == 1               # exactly one negative-profit line


def test_order_level_rollup_collapses_multiline_orders(raw_df):
    """3 line rows must roll up to 2 orders -- the core grain rule."""
    df = engineer_features(clean_data(clean_column_names(raw_df)))
    orders = build_order_level(df)
    assert len(orders) == 2
    assert orders.loc[orders.order_id == "ORD-1", "order_sales"].iloc[0] == 1500.0


def test_kpis_count_distinct_orders_not_rows(raw_df):
    """Total orders must be 2 (distinct), not 3 (rows)."""
    df = engineer_features(clean_data(clean_column_names(raw_df)))
    kpis = headline_kpis(df, build_order_level(df))
    assert kpis["n_orders"] == 2
    assert kpis["total_sales"] == 3500.0
    # AOV uses distinct orders as the denominator
    assert kpis["avg_order_value"] == pytest.approx(3500.0 / 2)


def test_margin_is_ratio_of_sums_not_mean_of_ratios(raw_df):
    """Overall margin = SUM(profit)/SUM(sales); never the average of row margins."""
    df = engineer_features(clean_data(clean_column_names(raw_df)))
    kpis = headline_kpis(df, build_order_level(df))
    expected = 550.0 / 3500.0 * 100
    assert kpis["profit_margin_pct"] == pytest.approx(expected)
    assert kpis["profit_margin_pct"] != pytest.approx(df["profit_margin"].mean() * 100)


def test_breakdown_returns_margin_per_dimension(raw_df):
    df = engineer_features(clean_data(clean_column_names(raw_df)))
    out = breakdown(df, "region")
    assert set(out["region"]) == {"AMER", "EMEA"}
    assert "margin_pct" in out.columns


def test_top_customers_share_sums_sensibly(raw_df):
    df = engineer_features(clean_data(clean_column_names(raw_df)))
    out = top_customers(df, n=10)
    assert out["pct_of_total"].sum() == pytest.approx(100.0, abs=0.1)
