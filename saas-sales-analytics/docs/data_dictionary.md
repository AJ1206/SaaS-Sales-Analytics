# Data Dictionary

**Dataset:** Amazon AWS SaaS Sales — https://www.kaggle.com/datasets/nnthanh101/aws-saas-sales
**Grain:** one row per **order line**. One order can span several rows.

## Source columns (as delivered, 19)

| Column | Type | Business meaning | Notes |
|---|---|---|---|
| Row ID | integer | Surrogate row identifier | Dropped — no business meaning |
| Order ID | text | Identifier for a customer order | **COUNT DISTINCT** for order totals |
| Order Date | date | Date the order was placed | Parsed to datetime |
| Date Key | integer | `YYYYMMDD` encoding of Order Date | Join key to a date dimension in SQL |
| Contact Name | text | Client-side person who ordered | High cardinality; detail only |
| Country | text | Country of the order | Geographic dimension |
| City | text | City of the order | Lowest geographic grain |
| Region | text | AMER / EMEA / APJ | Primary slicer |
| Subregion | text | Sub-grouping within a region | Mid-level geography |
| Customer | text | Client company name | Concentration analysis |
| Customer ID | text | Stable client identifier | Preferred grouping key |
| Industry | text | Client's industry | Segmentation dimension |
| Segment | text | SMB / Strategic / Enterprise | Client tier |
| Product | text | SaaS product sold | Product-line profitability |
| License | text | Licence key issued | Dropped — near-unique |
| Sales | float | Revenue for the line (USD) | Measure; reflects the discount |
| Quantity | integer | Units / licences sold | Measure |
| Discount | float | Discount as a 0–1 decimal | 0.10 = 10% |
| Profit | float | Profit for the line (USD) | **Can be negative** — real signal |

## Engineered columns (added by `src/pipeline.py`)

| Column | Type | Definition | Why it exists |
|---|---|---|---|
| `year`, `month`, `quarter` | integer | Extracted from `order_date` | Time-based grouping |
| `month_name` | text | Abbreviated month | Chart labelling |
| `year_month` | text | `YYYY-MM` period | Monthly trend axis |
| `profit_margin` | float | `profit / sales` (row level) | Row-level diagnostics only — **never average this** for an overall margin |
| `is_loss` | boolean | `profit < 0` | Flags loss-making lines |
| `discount_pct` | float | `discount * 100` | Display-friendly percentage |
| `revenue_per_unit` | float | `sales / quantity` | **Realised** revenue per unit, not list price — `sales` already reflects the discount |
| `revenue_band` | category | `<250`, `250-1K`, `1K-5K`, `5K+` | Turns a continuous measure into a slicer |

## Derived tables

| Table | Grain | Built by | Purpose |
|---|---|---|---|
| Order-level rollup | one row per `order_id` | `build_order_level()` | Correct grain for order counts and Average Order Value |

## Metric definitions

| Metric | Definition | Correctness note |
|---|---|---|
| Total Sales | `SUM(sales)` | |
| Total Profit | `SUM(profit)` | |
| Profit Margin % | `SUM(profit) / SUM(sales)` | **Not** the mean of `profit_margin`. Averaging ratios is wrong. |
| Total Orders | `COUNT(DISTINCT order_id)` | **Not** a row count. The grain is order-line. |
| Average Order Value | `SUM(sales) / COUNT(DISTINCT order_id)` | Denominator must be distinct orders |
| Average Discount % | `AVG(discount) * 100` | `discount` is stored 0–1 |
