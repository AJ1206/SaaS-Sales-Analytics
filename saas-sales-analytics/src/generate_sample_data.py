"""
generate_sample_data.py
------------------------
Generates a SYNTHETIC dataset that matches the exact schema of the
Amazon AWS SaaS Sales dataset (Kaggle: nnthanh101/aws-saas-sales).

WHY THIS EXISTS
    You lost the original file. This lets the analysis pipeline run
    immediately so you can test everything end-to-end. For your actual
    portfolio, download the real CSV from Kaggle and point the pipeline
    at it instead -- the real data is what you should present and defend.

    This generator intentionally bakes in the same "shape" as the real
    data so the pipeline exercises every code path:
        - multiple line-rows per order (the double-counting trap)
        - genuinely negative profit on one product line (real signal)
        - varied discounts stored as 0-1 decimals
        - dates spanning multiple years (for time-trend analysis)

    Numbers here are RANDOM, not the real dataset's numbers. Never quote
    figures produced from this file as if they were real findings.
"""

from __future__ import annotations

import random
import string
from pathlib import Path

import numpy as np
import pandas as pd

# Reproducibility -- same seed => same file every run.
RNG_SEED = 42
random.seed(RNG_SEED)
np.random.seed(RNG_SEED)

N_ORDERS = 5000          # distinct orders; rows will exceed this (multi-line)
from config import SAMPLE_CSV

OUTPUT = SAMPLE_CSV

# --- Reference dimensions (mirror the real dataset's categories) ----------
REGION_MAP = {
    "AMER": {
        "subregions": ["NAMER", "LATAM"],
        "countries": {
            "United States": ["New York City", "San Francisco", "Chicago", "Austin"],
            "Canada": ["Toronto", "Vancouver"],
            "Brazil": ["Sao Paulo"],
            "Mexico": ["Mexico City"],
        },
    },
    "EMEA": {
        "subregions": ["Western Europe", "Eastern Europe", "Middle East", "Africa"],
        "countries": {
            "United Kingdom": ["London", "Manchester"],
            "France": ["Paris"],
            "Germany": ["Berlin", "Munich"],
            "Finland": ["Helsinki"],
            "Egypt": ["Cairo"],
        },
    },
    "APJ": {
        "subregions": ["ANZ", "ASEAN", "East Asia"],
        "countries": {
            "Japan": ["Tokyo"],
            "Australia": ["Sydney"],
            "Singapore": ["Singapore"],
            "India": ["Bengaluru", "Mumbai"],
        },
    },
}

INDUSTRIES = [
    "Finance", "Manufacturing", "Energy", "Healthcare", "Tech",
    "Communications", "Consumer Products", "Retail", "Transportation", "Misc",
]
SEGMENTS = ["SMB", "Strategic", "Enterprise"]

# Product -> (base_margin_rate, price_scale). Marketing Suite runs negative
# on purpose so the pipeline surfaces a loss-making line (a real insight in
# the actual dataset).
PRODUCTS = {
    "Marketing Suite": (-0.08, 900),
    "ContactMatcher": (0.28, 450),
    "FinanceHub": (0.31, 1200),
    "Site Analytics": (0.22, 600),
    "Support": (0.18, 300),
    "Big Ol Database": (0.25, 1500),
    "Data Smasher": (0.20, 700),
    "Storage": (0.15, 400),
    "OneView": (0.24, 800),
    "ChatBot Plus": (0.19, 350),
}

CUSTOMERS = [
    "Apple", "Amazon", "Wells Fargo", "BNP Paribas", "United Parcel Service",
    "Toyota", "Siemens", "HSBC", "Nestle", "Samsung", "Pfizer", "Shell",
    "Vodafone", "Unilever", "Sony", "Airbus", "Tata Group", "Rakuten",
    "Deutsche Bank", "Maersk",
]

FIRST_NAMES = ["Aaron", "Bianca", "Chen", "Divya", "Ella", "Farid", "Grace",
               "Hiro", "Ines", "Jonas", "Kavya", "Liam", "Mei", "Noah", "Omar"]
LAST_NAMES = ["Smith", "Garcia", "Wang", "Patel", "Muller", "Rossi", "Kim",
              "Silva", "Johnson", "Nakamura", "Dubois", "Ahmed", "Novak"]


def _license_key() -> str:
    """Return a random alphanumeric license key (high-cardinality ID column)."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=10))


def _random_date() -> pd.Timestamp:
    """Random order date across a 4-year window (2020-2023)."""
    start = pd.Timestamp("2020-01-01")
    end = pd.Timestamp("2023-12-31")
    span_days = (end - start).days
    return start + pd.Timedelta(days=int(np.random.randint(0, span_days + 1)))


def generate() -> pd.DataFrame:
    """Build the synthetic dataset row by row and return it as a DataFrame."""
    rows: list[dict] = []
    row_id = 1

    # Pre-assign each customer to a stable region/industry/segment so the
    # data behaves like a real book of business (not fully random noise).
    customer_profile = {}
    for cust in CUSTOMERS:
        region = random.choice(list(REGION_MAP))
        rmeta = REGION_MAP[region]
        country = random.choice(list(rmeta["countries"]))
        customer_profile[cust] = {
            "customer_id": f"CUST-{1000 + CUSTOMERS.index(cust)}",
            "region": region,
            "subregion": random.choice(rmeta["subregions"]),
            "country": country,
            "city": random.choice(rmeta["countries"][country]),
            "industry": random.choice(INDUSTRIES),
            "segment": random.choices(SEGMENTS, weights=[0.5, 0.2, 0.3])[0],
        }

    for order_num in range(1, N_ORDERS + 1):
        order_id = f"ORD-{order_num:06d}"
        order_date = _random_date()
        cust = random.choice(CUSTOMERS)
        prof = customer_profile[cust]
        contact = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

        # An order contains 1-4 product lines -> multiple rows share order_id.
        n_lines = random.choices([1, 2, 3, 4], weights=[0.6, 0.25, 0.1, 0.05])[0]
        products_in_order = random.sample(list(PRODUCTS), k=n_lines)

        for product in products_in_order:
            base_margin, price_scale = PRODUCTS[product]
            quantity = int(np.random.randint(1, 15))
            discount = random.choices(
                [0.0, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5],
                weights=[0.35, 0.2, 0.15, 0.15, 0.08, 0.05, 0.02],
            )[0]

            # Sales = revenue for the line (already reflects the discount).
            unit_rev = price_scale * (1 - discount) * np.random.uniform(0.7, 1.3)
            sales = round(unit_rev * quantity, 2)

            # Profit rate falls as discount rises -> heavy discounts can
            # push a line into the red (the core margin-leak story).
            margin_rate = base_margin - discount * 0.9 + np.random.normal(0, 0.05)
            profit = round(sales * margin_rate, 2)

            rows.append({
                "Row ID": row_id,
                "Order ID": order_id,
                "Order Date": order_date.strftime("%Y-%m-%d"),
                "Date Key": int(order_date.strftime("%Y%m%d")),
                "Contact Name": contact,
                "Country": prof["country"],
                "City": prof["city"],
                "Region": prof["region"],
                "Subregion": prof["subregion"],
                "Customer": cust,
                "Customer ID": prof["customer_id"],
                "Industry": prof["industry"],
                "Segment": prof["segment"],
                "Product": product,
                "License": _license_key(),
                "Sales": sales,
                "Quantity": quantity,
                "Discount": discount,
                "Profit": profit,
            })
            row_id += 1

    return pd.DataFrame(rows)


def main() -> None:
    df = generate()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT, index=False)
    print(f"Wrote {len(df):,} rows ({df['Order ID'].nunique():,} orders) -> {OUTPUT}")
    print(f"Columns: {list(df.columns)}")


if __name__ == "__main__":
    main()
