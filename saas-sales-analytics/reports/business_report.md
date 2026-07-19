# Business Report — SaaS Sales Performance

**Dataset:** Amazon AWS SaaS Sales — https://www.kaggle.com/datasets/nnthanh101/aws-saas-sales
**Prepared by:** Akshay Juluru

> ### ⚠️ Read before quoting any figure
> Every number below was produced by running `python src/pipeline.py` against the
> **synthetic sample** (`src/generate_sample_data.py`), so this repository is runnable
> without a Kaggle account. The *shape* of each finding holds on the real data, but the
> exact values will differ.
>
> **Before publishing or presenting:** download the real CSV to `data/raw/`, re-run the
> pipeline, and replace the figures marked 🔸 below. Never present sample-derived numbers
> as findings.

---

## 1. Context

A B2B SaaS company selling sales and marketing software to business customers across AMER,
EMEA, and APJ is profitable overall but has no clear view of where that profit comes from
or where margin is leaking. Regional staffing, discount approvals, and segment
prioritisation are decided on judgement rather than evidence.

## 2. Headline position 🔸

| KPI | Value |
|---|---|
| Total Sales | $37,419,761 |
| Total Profit | $3,903,748 |
| Profit Margin | 10.4% |
| Orders (distinct) | 5,000 |
| Average Order Value | $7,484 |
| Average Discount | 12.6% |

The business is profitable, but a 10.4% margin on $37.4M of revenue is thin for software.
The rest of this report explains where it goes.

## 3. Finding 1 — Discounting is destroying margin 🔸

This is the central result. Margin does not decline gently as discounts rise; it collapses
and turns negative.

| Discount band | Profit margin |
|---|---|
| 0% | 20.0% |
| 1–10% | 11.4% |
| 11–20% | 4.2% |
| 21–30% | **−6.3%** |
| 30%+ | **−17.1%** |

The correlation between discount and line-level margin is **−0.70** — strong and negative.

**The margin cliff sits between 20% and 30%.** Past roughly 20%, deals stop contributing
profit and start consuming it. Every deal closed at 30%+ actively costs the company money.

**Recommendation:** introduce a discount-approval threshold. Deals above the cliff require
sign-off from finance with a documented justification. This is the single highest-value
change available and requires no new data or systems.

## 4. Finding 2 — One product line runs at a loss 🔸

| Product | Profit | Margin |
|---|---|---|
| FinanceHub | $1,305,520 | 20.8% |
| Big Ol Database | $1,099,237 | 14.8% |
| OneView | $638,756 | 14.6% |
| ContactMatcher | $428,673 | 18.0% |
| Site Analytics | $415,967 | 13.7% |
| Data Smasher | $409,360 | 11.3% |
| ChatBot Plus | $167,575 | 9.0% |
| Support | $147,659 | 9.0% |
| Storage | $107,543 | 4.8% |
| **Marketing Suite** | **−$816,544** | **−17.9%** |

Marketing Suite loses money on every dollar it sells. It is not a small drag: its loss
offsets more than 60% of FinanceHub's entire contribution. Storage, at 4.8%, is thin enough
to warrant a look too.

**Recommendation:** a pricing review of Marketing Suite. Three options in order of
preference — reprice it, bundle it with a high-margin product to make the attachment
profitable, or retire it. Do not simply sell more of it.

## 5. Finding 3 — Revenue is concentrated 🔸

The **top 10 customers account for 53.0% of total revenue**. Losing any one of them would
be material; losing two would be a bad year.

**Recommendation:** treat this as a risk register item, not just a sales statistic. Set a
target for revenue share outside the top 10, and ensure account management coverage on the
largest accounts is deliberate rather than incidental.

## 6. Finding 4 — Regions and segments perform evenly 🔸

| Region | Sales | Profit | Margin |
|---|---|---|---|
| APJ | $15,027,816 | $1,579,274 | 10.5% |
| AMER | $13,643,171 | $1,423,877 | 10.4% |
| EMEA | $8,748,774 | $900,597 | 10.3% |

| Segment | Sales | Margin | Avg discount |
|---|---|---|---|
| SMB | $24,339,699 | 10.3% | 12.8% |
| Strategic | $7,362,981 | 10.5% | 12.4% |
| Enterprise | $5,717,082 | 10.8% | 12.4% |

Margins are near-identical across regions (10.3–10.5%) and segments (10.3–10.8%). This is
worth stating plainly: **there is no regional or segment story here.** The margin problem
is not concentrated in one geography or customer tier — it is a product and discounting
problem that runs through the whole book.

> **Note on the sample:** this evenness is partly an artefact of how the synthetic generator
> assigns customers to regions. On the real data, expect more variation between regions —
> check whether a genuine regional story emerges before repeating this conclusion.

## 7. Recommendations, in priority order

| # | Action | Owner | Why it is first |
|---|---|---|---|
| 1 | Introduce a discount-approval threshold at the margin cliff | Finance / RevOps | Largest, fastest margin recovery; no new systems needed |
| 2 | Pricing review of the loss-making product line | Product / Finance | Removes a structural loss rather than managing around it |
| 3 | Set a revenue-concentration target and cover top accounts deliberately | Sales leadership | Reduces a single-point-of-failure risk |
| 4 | Re-test the regional and segment picture on real data | Analytics | Confirms whether prioritisation should shift at all |

## 8. How to read the numbers

- **Order counts are distinct.** The data's grain is the order *line*; one order spans
  several rows. Counting rows would overstate order volume.
- **Margin is a ratio of sums** (`SUM(profit) / SUM(sales)`), never the average of row-level
  margins — averaging ratios gives the wrong answer.
- **Negative profit is preserved**, not cleaned away. It is the finding.

## 9. Limitations

The data is fictitious, contains no cost breakdown, and has no subscription lifecycle — so
true SaaS metrics (MRR, ARR, churn, net revenue retention) cannot be computed, and the
discount-margin relationship is correlation rather than proven causation. See
[`docs/assumptions_and_limitations.md`](../docs/assumptions_and_limitations.md) for the full
treatment.
