# Dataset Source

## Recommended dataset: Amazon AWS SaaS Sales

| Field | Detail |
|---|---|
| **Name** | Amazon AWS SaaS Sales |
| **Official dataset website** | https://www.kaggle.com/datasets/nnthanh101/aws-saas-sales |
| **Official download link** | https://www.kaggle.com/datasets/nnthanh101/aws-saas-sales (Download button; requires a free Kaggle account) |
| **Official documentation** | The dataset description on the page above. No separate documentation site exists. |
| **Published data dictionary** | None published upstream. This repository provides one at [`docs/data_dictionary.md`](../docs/data_dictionary.md), derived from the column semantics. |
| **Kaggle mirror** | Kaggle **is** the primary distribution point (see below). |
| **GitHub mirror** | None known. |
| **License** | Not clearly stated upstream. **Check the current terms on the dataset page before redistributing or publishing derived data.** This repository does not commit the raw file. |
| **Citation** | None required — the dataset is fictitious and has no associated publication. Credit the Kaggle publisher (`nnthanh101`) when referencing it. |
| **Last updated** | Not clearly stated. Check the dataset page for the current value. |
| **Rows** | 9,994 (one row per **order line**, not per order) |
| **Columns** | 19 |
| **Target column** | None — this is a descriptive/diagnostic analytics project, not supervised learning. The measures are `Sales`, `Quantity`, `Discount`, and `Profit`. |

### Description

Transaction records from a **fictitious** B2B SaaS company that sells sales and marketing
software (products such as *Marketing Suite* and *ContactMatcher*) to business customers
across three global regions (AMER, EMEA, APJ). Each row is a single order line; one order
can span several rows.

### Feature descriptions

| # | Feature | Type | Description |
|---|---|---|---|
| 1 | `Row ID` | integer | Surrogate row identifier. No business meaning — drop for analysis. |
| 2 | `Order ID` | text | Identifier for a customer order. **Count DISTINCT for order totals** — one order spans multiple rows. |
| 3 | `Order Date` | date | Date the order was placed. Source of all time-based analysis. |
| 4 | `Date Key` | integer | `YYYYMMDD` encoding of `Order Date`. Redundant in pandas; a join key to a date dimension in SQL. |
| 5 | `Contact Name` | text | Person at the client who placed the order. High cardinality — detail only, not for aggregation. |
| 6 | `Country` | text | Country of the order. |
| 7 | `City` | text | City of the order. Lowest geographic grain. |
| 8 | `Region` | text | AMER / EMEA / APJ. The top-level geographic rollup and primary slicer. |
| 9 | `Subregion` | text | Sub-grouping within a region. |
| 10 | `Customer` | text | Client company name. Used for top-customer and concentration analysis. |
| 11 | `Customer ID` | text | Stable client identifier. Group by this rather than the name. |
| 12 | `Industry` | text | Client's industry (Finance, Energy, Manufacturing, and others). |
| 13 | `Segment` | text | Client tier: SMB / Strategic / Enterprise. |
| 14 | `Product` | text | SaaS product sold. Drives product-line profitability. |
| 15 | `License` | text | License key issued for the sale. Near-unique — drop for analysis. |
| 16 | `Sales` | float | Revenue from the transaction, in USD. |
| 17 | `Quantity` | integer | Units / licences sold. |
| 18 | `Discount` | float | Discount applied, stored as a **0–1 decimal** (0.10 = 10%). |
| 19 | `Profit` | float | Profit from the transaction, in USD. **Can be negative** — loss-making deals are real signal, not errors. |

### Why this is the best choice for this project

The project's business framing is B2B SaaS sales performance, and this is the only readily
available dataset that is SaaS-native: it carries the dimensions the analysis needs
(region, industry, customer segment, product line) alongside a discount and a profit
figure on every line. That combination is what makes the central finding — margin eroding
as discounts rise, and a product line running at a loss — possible at all. Retail
alternatives can support similar mechanics but require the story to be re-framed away from
SaaS.

### An honest note on source priority

The preferred source order for this repository is government/open-data portals → UCI →
World Bank → WHO → OECD → IMF → AWS Open Data → Google Dataset Search → official company
datasets → **Kaggle only if no official dataset exists**.

This dataset sits at the bottom of that order, and it is worth being explicit about why:

- It is **fictitious**, not a real company's records, so no official upstream exists to prefer.
- Despite the name, it is **not** an official Amazon or AWS release and is not part of the
  AWS Open Data programme. The name reflects the publisher's framing, not provenance.
- Its licence and update date are not clearly stated upstream.

**If official provenance matters more than the SaaS framing**, use *Online Retail* from the
UCI Machine Learning Repository instead (see below). It ranks second in the priority order,
is properly documented and licensed, and contains real transactions. The trade-off is that
the project becomes retail sales analytics rather than SaaS sales analytics, and the
discount/profit columns central to the margin story are not present — that analysis would
need re-scoping.

This repository keeps the SaaS dataset because the business narrative and the discount-margin
finding are the point of the project. The trade-off is documented here rather than hidden.

---

## Alternatives considered

### Online Retail (UCI Machine Learning Repository) — the official-source alternative
- **Official website:** https://archive.ics.uci.edu/dataset/352/online+retail
- **Rows / columns:** ~541,909 × 8
- **Licence:** Documented on the UCI page (Creative Commons — verify current terms).
- **Citation:** Chen, D. (2015). *Online Retail.* UCI Machine Learning Repository.
- **Strengths:** real transactions, official repository, clear documentation and licence, well above Kaggle in the source priority order.
- **Not chosen:** it is UK e-commerce retail, not SaaS, and carries **no discount or profit
  columns** — the discount-versus-margin analysis at the centre of this project cannot be
  reproduced from it without inventing those fields.

### Sample Superstore
- **Link:** https://www.kaggle.com/datasets/vivek468/superstore-dataset-final
- **Rows / columns:** ~9,994 × 21
- **Strengths:** structurally near-identical (same grain, has Discount and Profit), so the
  analysis transfers almost unchanged.
- **Not chosen:** also Kaggle-only, also fictitious, and retail rather than SaaS — it offers
  no provenance advantage over the chosen dataset while losing the SaaS framing.

---

## How to obtain the data

1. Create a free Kaggle account.
2. Download from https://www.kaggle.com/datasets/nnthanh101/aws-saas-sales
3. Save the file as `data/raw/aws_saas_sales.csv`.
4. Run `python src/pipeline.py` — it detects the real file automatically.

**No account?** Run `python src/generate_sample_data.py` first. It writes a schema-matched
synthetic file to `data/sample/` so the pipeline runs end to end. Numbers produced from the
sample are illustrative only and must never be presented as findings.

The raw data is **not** committed to this repository (see `.gitignore`) — fetch it from the
source above.
