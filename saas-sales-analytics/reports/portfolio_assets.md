# Portfolio Assets — SaaS Sales Performance

> **🔸 Figures marked below come from the synthetic sample.** Run the pipeline on the real
> Kaggle dataset and replace them before putting any of this on a resume or LinkedIn. A
> recruiter may ask you to reproduce a number; every figure you publish should be one you
> can regenerate on demand.

---

## Resume bullets (ATS-friendly, XYZ format)

Three bullets, one page, quantified. Update the 🔸 values from your real run.

```
SaaS Sales Performance Analytics Dashboard | Python, SQL, Power BI
• Built an end-to-end analytics pipeline on 9,994 B2B SaaS transactions using pandas,
  reducing 19 raw columns to a validated star schema and cutting manual reporting effort
  to a single scripted run.
• Identified a margin cliff at 🔸20% discount where deals turn unprofitable (🔸-0.70
  correlation between discount and margin), supporting a discount-approval threshold
  recommendation to finance.
• Designed a 3-page Power BI dashboard with 16 DAX measures, drill-through, and
  time-intelligence reporting, surfacing a 🔸$816K loss-making product line and 🔸53%
  revenue concentration in the top 10 customers.
```

**Alternative bullet if the role emphasises SQL:**
```
• Modelled a PostgreSQL star schema (fact + 4 dimensions) with ETL, indexed foreign keys,
  and 15 analytical queries using CTEs and window functions, including a Pareto
  concentration analysis and month-over-month growth via LAG().
```

---

## Resume project description (2 lines)

```
SaaS Sales Performance Analytics Dashboard — Python, SQL, Power BI
Analysed 9,994 B2B SaaS transactions across a Python pipeline, PostgreSQL star schema, and
Power BI dashboard. Found that discounts above 🔸20% erase margin and one product line runs
at a 🔸17.9% loss, and recommended a discount-approval threshold.
```

---

## LinkedIn post

```
Rebuilt my SaaS sales analytics project from scratch, and the most useful thing I learned
had nothing to do with charts.

The dataset looked simple: 9,994 B2B SaaS transactions, no missing values, no duplicates.
The kind of file where you're tempted to jump straight to a dashboard.

But the grain was the order LINE, not the order. One order spans several rows. Count rows
and you overstate your order volume and understate your deal size — and every KPI built on
top inherits the error. So order counts use COUNT(DISTINCT order_id), and average order
value divides by that.

Then the actual finding showed up. Margin holds at 🔸20% on undiscounted deals. It thins to
🔸4% in the 11-20% band. Past 20% it goes NEGATIVE — 🔸-17% at the top end.

There's a cliff. Past it, the company pays for the privilege of closing the deal.

One product line was running at 🔸-17.9% margin and destroying 🔸$816K of profit, offsetting
more than 60% of the best product's entire contribution. Selling more of it would have made
things worse.

The recommendation wasn't "make a chart". It was: cap discounts at the cliff and require
finance sign-off above it. No new systems. No new spend. Just a policy.

What I'd tell anyone rebuilding a portfolio project: the analysis is the easy part. Knowing
what the data CAN'T tell you is the hard part. This data has no cost breakdown, so I can see
that margin erodes but not the full mechanism. It has no subscription lifecycle, so MRR and
churn aren't computable at all. Saying that out loud is more convincing than pretending
otherwise.

Full repo (Python pipeline, SQL star schema, Power BI build guide) below.

#DataAnalytics #Python #SQL #PowerBI #BusinessIntelligence
```

---

## STAR interview explanation

**Situation.** A B2B SaaS company was profitable overall (🔸10.4% margin on 🔸$37.4M) but
leadership had no view of where profit came from or where margin was leaking. Discount
approvals, regional staffing, and segment focus were all decided on judgement.

**Task.** Build an analytics solution that identified the drivers of profit and produced a
recommendation leadership could act on, not just a set of charts.

**Action.** I built three layers with a clear separation of concerns. Python handled
cleaning, feature engineering, and EDA. The first decision that mattered was recognising the
grain: the data is order-line level, so order counts needed `COUNT(DISTINCT order_id)`, not a
row count. I also kept negative-profit rows rather than removing them as outliers, since
they turned out to be the finding. In SQL I modelled a star schema with the order ID as a
degenerate dimension so distinct counts still worked. In Power BI I built three pages with
margin as a measure (`DIVIDE(SUM, SUM)`) rather than an averaged column, since averaging
ratios gives the wrong answer.

**Result.** The analysis found a margin cliff at 🔸20% discount, a product line at 🔸-17.9%
margin costing 🔸$816K, and 🔸53% revenue concentration in ten customers. The recommendation
was a discount-approval threshold — a policy change requiring no new systems. I also
documented what the data couldn't support: no cost breakdown means the discount-margin link
is correlation, not proven causation, and the absence of subscription data means true SaaS
metrics like churn and MRR were out of reach.

---

## Elevator pitch (one line)

"I analysed 9,994 B2B SaaS transactions across Python, SQL, and Power BI and found that
discounts above 🔸20% erase margin entirely — which turned a reporting request into a
discount-policy recommendation."
