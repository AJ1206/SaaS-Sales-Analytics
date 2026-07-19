# Presentation — SaaS Sales Performance
**Format:** 10 slides, ~10 minutes. Built for a recruiter walkthrough or a stakeholder readout.

> Figures are from the synthetic sample — update from the real data run before presenting.

---

### Slide 1 — Title
**SaaS Sales Performance Analytics**
Akshay Juluru · Python · SQL · Power BI
*Say:* "A B2B SaaS company profitable on paper, but leadership couldn't see where the profit came from."

### Slide 2 — The business problem
Profitable overall (10.4% margin) but flying blind. Regional staffing, discount approvals, and segment focus decided on gut feel.
*Visual:* the five KPI cards.
*Say:* "The question isn't 'how are we doing' — it's 'why'."

### Slide 3 — Approach
`images/` → architecture diagram from [`docs/architecture.md`](../docs/architecture.md).
Python (clean + analyse) → SQL (star schema) → Power BI (dashboard).
*Say:* "Cleaning happens once, in Python. SQL owns the model. Power BI presents. One source of truth for every derived field."

### Slide 4 — The data, and the trap
9,994 rows, 19 columns, grain = **order line**, not order.
*Say:* "One order spans several rows. Count rows and you overstate orders. Everything downstream depends on catching that."

### Slide 5 — Finding 1: the margin cliff ⭐ **the money slide**
*Visual:* `images/03_discount_vs_margin.png` + the discount-band table.
20% margin at no discount → **−17% past 30%**. Correlation −0.70.
*Say:* "Past roughly 20% discount, we pay for the privilege of closing the deal."

### Slide 6 — Finding 2: a loss-making product
*Visual:* `images/02_profit_by_product.png` (red bar).
Marketing Suite: −17.9% margin, −$816K.
*Say:* "It offsets more than 60% of our best product's entire contribution. Selling more of it makes things worse."

### Slide 7 — Finding 3: concentration risk
Top 10 customers = 53% of revenue.
*Say:* "One lost account is material. Two is a bad year. That's a risk register item, not a sales stat."

### Slide 8 — What we recommend
1. Discount-approval threshold at the cliff.
2. Reprice / bundle / retire the loss-making line.
3. Concentration target + deliberate account coverage.
*Say:* "All three are policy changes. No new systems, no new spend."

### Slide 9 — The dashboard
*Visual:* dashboard screenshots (see `images/` once captured).
Three pages: executive health, discount deep-dive, customer analysis. Drill-through to customer detail.

### Slide 10 — Limitations & next steps
No cost data, no subscription lifecycle (so no MRR/churn), correlation not causation.
Next: cost breakdown to decompose margin; test the discount policy change.
*Say:* "Knowing what the data can't tell you is part of the analysis."

---

## Q&A preparation
| Likely question | Answer |
|---|---|
| "How many orders?" | 5,000 distinct — not 8,043 rows. The grain is order-line. |
| "Is it really the discounting?" | Strong correlation (−0.70) and a consistent pattern, but no cost data — so correlation, not proven causation. |
| "Why not just drop the negative-profit rows?" | They're the finding. Cleaning them away deletes the result. |
| "Is this real SaaS data?" | No — it's fictitious, and it has no subscription lifecycle, so true SaaS metrics (MRR, churn, NRR) aren't computable. It's sales performance analytics on SaaS-shaped data. |
