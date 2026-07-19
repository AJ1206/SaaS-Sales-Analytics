# Assumptions and Limitations

Stating these plainly is part of the analysis. An interviewer will ask; a reviewer will
check.

## Assumptions

| # | Assumption | Basis / risk if wrong |
|---|---|---|
| 1 | `Sales` is net of the discount | The column behaves as realised revenue. If it were a list figure, `revenue_per_unit` and every margin would be wrong. This is why the derived column is named "revenue per unit", not "unit price". |
| 2 | One `Order ID` = one commercial order, spanning multiple product lines | Consistent with the data's structure. All order metrics use `COUNT(DISTINCT order_id)`. |
| 3 | Negative `Profit` values are genuine loss-making deals, not data errors | They form a coherent pattern by product and discount level rather than appearing randomly. |
| 4 | `Discount` is stored as a 0–1 decimal | Verified at load; the pipeline detects and rescales percent-form input rather than assuming. |
| 5 | Large `Sales` values are real enterprise deals, not errors | Standard in B2B sales. They are reported, not trimmed. |
| 6 | `Customer ID` is stable and reliable for grouping | Preferred over the display name, which is more prone to variation. |

## Limitations

### Dataset
- **The data is fictitious.** It is not a real company's records, so findings demonstrate
  method, not market truth. See [`data/dataset_source.md`](../data/dataset_source.md) for the
  full provenance discussion, including the official-source alternative.
- **No cost data.** Profit is given, so margin cannot be decomposed into its drivers
  (delivery cost, support cost, acquisition cost). We can see *that* margin erodes, not the
  full mechanism.
- **Licence and update date are not clearly stated upstream.**

### Analytical
- **Not true SaaS metrics.** The dataset is transactional software sales with no
  subscription lifecycle: no renewals, no churn dates, no contract terms. MRR, ARR, net
  revenue retention, and churn — the metrics a real SaaS business runs on — **cannot** be
  computed. This project is sales performance analytics on SaaS data, which is a different
  and narrower thing. Claiming otherwise would be misleading.
- **Correlation, not causation.** The discount-margin relationship is strong and consistent,
  but the data cannot prove that discounting *causes* the margin loss. Plausible confounders
  exist: larger deals may attract larger discounts and also carry different cost structures.
  Establishing causation would need an experiment or cost data.
- **No customer-level history.** Without acquisition dates or contract states, concentration
  risk can be measured but customer lifetime value and retention cannot.
- **Fixed time window.** Trends describe the period in the file. They are not a forecast.

### Scope
- Forecasting, predictive modelling, and real-time pipelines are out of scope by design.
- The Power BI dashboard is delivered as a complete build specification rather than a
  `.pbix` — see [`dashboards/`](../dashboards/) for why and how.

## What would resolve these

Cost breakdowns per transaction, subscription and renewal records, customer acquisition
dates, and a controlled discount policy change to test the causal claim.
