# Methodology

## 1. Framing

The project is scoped as work for a fictitious B2B SaaS company's sales leadership. Every
visual and query must answer one of five questions: where profit concentrates, how
discounting affects margin, which products lose money, how concentrated revenue is, and
how performance trends. Anything that answers none of those is out.

## 2. Understanding the grain

The first analytical decision: the dataset's grain is the **order line**, not the order.
One order occupies several rows. Everything else follows from recognising that:

- Order counts use `COUNT(DISTINCT order_id)`.
- Average Order Value divides by distinct orders.
- An order-level rollup (`build_order_level()`) exists for order-grain analysis.

Counting rows instead would overstate order volume and understate deal size.

## 3. Cleaning

The dataset is clean — no missing values and no duplicates. Rather than invent cleaning
work, the pipeline **verifies and reports** honestly, and does the transformations that
genuinely matter:

- Column names standardised to `snake_case`.
- `order_date` parsed to datetime, with unparseable values surfaced as warnings.
- `discount` range validated. If the source ever delivers whole percents instead of 0–1
  decimals, the pipeline detects it and rescales rather than silently computing wrong margins.
- Exact duplicates removed and the count reported.
- Measures sanity-checked: sales non-negative, quantity positive.

**Negative profit is preserved.** Loss-making lines are the most interesting finding in the
data; removing them as "outliers" would delete the result.

## 4. Feature engineering

Done once, in Python, and reused by SQL and Power BI. Date parts, `profit_margin`,
`is_loss`, `discount_pct`, `revenue_band`, and `revenue_per_unit`.

`revenue_per_unit` is deliberately **not** called "unit price": `sales` already reflects the
discount, so the figure is realised revenue per unit. Naming it "price" would imply
something the data cannot support.

## 5. Analysis

Descriptive (what happened) then diagnostic (why). Headline KPIs, then breakdowns by
region, segment, industry, and product; discount-versus-margin; revenue concentration; and
time trends. The correlation between discount and row-level margin quantifies the central
finding.

## 6. Dimensional modelling

A star schema: `fact_sales` at order-line grain, surrounded by `dim_date`, `dim_customer`,
`dim_product`, and `dim_geography`. Surrogate integer keys join the fact to the dimensions;
`order_id` stays in the fact as a degenerate dimension. Data lands in a staging table first,
then ETL resolves natural keys to surrogates. A validation query proves no rows are lost.

## 7. Presentation

Three pages, one story each: executive health, discount deep-dive, customer analysis.
Measures — not calculated columns — carry every KPI so they respond to filter context.

## 8. Reproducibility

- A fixed seed (42) in the sample generator.
- All paths in `config.py`, derived from the repo root.
- `requirements.txt` pins minimum versions.
- Tests assert the correctness rules above rather than merely exercising the code.
