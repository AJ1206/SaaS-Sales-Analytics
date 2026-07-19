# Executive Summary — SaaS Sales Performance

> **Figures are from the synthetic sample.** Re-run the pipeline on the real Kaggle dataset
> and update before presenting. See [`business_report.md`](business_report.md).

## The situation

The business generates **$37.4M in revenue** but keeps only **10.4%** of it as profit — thin
for software. Leadership could see the totals but not the drivers.

## What we found

**Discounting is the problem.** Margin holds at 20% on undiscounted deals, thins to 4% in
the 11–20% band, and turns **negative past 20%**. Deals discounted above 30% run at −17%
margin: the company pays for the privilege of closing them. The correlation between discount
and margin is −0.70.

**One product line loses money.** Marketing Suite runs at −17.9% margin and destroys
$816K of profit — offsetting more than 60% of the best product's entire contribution.

**Revenue is concentrated.** The top 10 customers are 53% of revenue. That is a
single-point-of-failure risk, not just a sales statistic.

**Geography and segment are not the story.** Margins sit within half a point of each other
across all regions and all customer tiers. The problem runs through the whole book rather
than hiding in one corner of it.

## What we recommend

1. **Cap discounts at the margin cliff.** Require finance sign-off above it. Largest and
   fastest margin recovery available; needs no new systems.
2. **Reprice, bundle, or retire the loss-making product.** Selling more of it makes things
   worse, not better.
3. **Set a revenue-concentration target** and cover the largest accounts deliberately.

## What this would be worth

Moving deals currently closed above the cliff back under it converts a negative-margin
transaction into a positive one. Fixing the loss-making line removes a structural drag
rather than managing around it. Both are policy changes, not investments.

## What we could not determine

The data contains no cost breakdown, so we can see *that* margin erodes but not the full
mechanism. It has no subscription lifecycle, so churn and retention are out of reach. And
the discount-margin link is a strong correlation, not proven causation — a controlled
policy change would be needed to establish that.
