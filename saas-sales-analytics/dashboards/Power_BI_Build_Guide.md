# Power BI Build Guide — SaaS Sales Performance Dashboard

**Dataset source:** Amazon AWS SaaS Sales — https://www.kaggle.com/datasets/nnthanh101/aws-saas-sales
**Goal:** a recruiter-ready, 3-page interactive dashboard for a fictitious B2B SaaS company.

Follow this top to bottom. Every DAX measure is copy-paste ready. Build order matters — data model first, measures second, visuals last.

---

## 0. Prerequisites

Run the Python pipeline first so you have `outputs/saas_sales_clean.csv`. That file is your source.

**Two ways to load (pick one):**

- **Quick path (recommended for the build):** Get Data → **Text/CSV** → `saas_sales_clean.csv` → **Load**. Rename the table to `Sales`. This guide assumes this.
- **Production path (stronger story):** Get Data → **PostgreSQL database** → import `fact_sales` + the four `dim_*` tables from your SQL layer. Relationships auto-detect on the surrogate keys. Use this if you want to show the full SQL→BI pipeline live. (Measures below still work; just point column refs at the fact/dim tables.)

Either is legitimate. Loading the flat table is simpler and won't cost you interview points — your SQL star schema already proves the modeling.

---

## 1. Build the Date Table (do this before anything else)

Time-intelligence DAX (YoY, YTD, MoM) needs a dedicated, continuous date table. Don't skip this.

**Modeling view → New Table:**

```dax
Date =
VAR BaseCalendar = CALENDARAUTO()
RETURN
ADDCOLUMNS(
    BaseCalendar,
    "Year", YEAR([Date]),
    "Month", MONTH([Date]),
    "Month Name", FORMAT([Date], "MMM"),
    "Month Year", FORMAT([Date], "MMM YYYY"),
    "Quarter", "Q" & FORMAT([Date], "Q"),
    "Year-Month Sort", YEAR([Date]) * 100 + MONTH([Date])
)
```

Then:
- Select the **Month Name** column → Column tools → **Sort by column** → `Month` (so months read Jan→Dec, not alphabetically).
- Select **Month Year** → Sort by column → `Year-Month Sort`.
- Select the `Date` table → Table tools → **Mark as date table** → date column = `Date`. *(This unlocks proper time intelligence.)*

**On calculated columns generally:** you barely need any. Your Python export already contains `profit_margin`, `is_loss`, `discount_pct`, and `revenue_band`. Don't recreate them — reusing that work is the right call and a good thing to mention ("I did feature engineering once, in the pipeline, not scattered across layers").

---

## 2. Relationships

If you loaded the flat CSV, create one relationship:

- **`Sales[order_date]` → `Date[Date]`** — Model view, drag `order_date` onto `Date[Date]`. Cardinality **Many-to-one (\*:1)**, cross-filter **Single**.

That's it for the single-table setup. (Production path: fact→dim relationships on the `*_key` columns, all Many-to-one, Single direction.)

---

## 3. DAX Measures

Create a dedicated home for these: New Table → `_Measures = {BLANK()}`, hide the column, and put every measure there so they're easy to find. Create each via **New measure**.

### Core measures

```dax
Total Sales = SUM(Sales[sales])
```
```dax
Total Profit = SUM(Sales[profit])
```
```dax
Total Orders = DISTINCTCOUNT(Sales[order_id])
```
> **The most important measure in the whole file.** One order spans multiple rows, so `COUNT` would overstate orders. `DISTINCTCOUNT` is correct. Expect this exact question in an interview.

```dax
Total Quantity = SUM(Sales[quantity])
```
```dax
Total Customers = DISTINCTCOUNT(Sales[customer_id])
```
```dax
Profit Margin % = DIVIDE([Total Profit], [Total Sales])
```
> Use a **measure**, never the row-level `profit_margin` column. Averaging row margins ≠ overall margin. `DIVIDE` also handles divide-by-zero safely. Format as Percentage.

```dax
Avg Order Value = DIVIDE([Total Sales], [Total Orders])
```
```dax
Avg Discount % = AVERAGE(Sales[discount])
```
> `discount` is stored 0–1, so format this measure as Percentage.

### Time-intelligence measures

```dax
Sales LY = CALCULATE([Total Sales], SAMEPERIODLASTYEAR('Date'[Date]))
```
```dax
Sales YoY % = DIVIDE([Total Sales] - [Sales LY], [Sales LY])
```
```dax
Sales YTD = TOTALYTD([Total Sales], 'Date'[Date])
```
```dax
Sales MoM % =
VAR PrevMonth = CALCULATE([Total Sales], DATEADD('Date'[Date], -1, MONTH))
RETURN DIVIDE([Total Sales] - PrevMonth, PrevMonth)
```

### Advanced measures

```dax
Loss-Making Sales = CALCULATE([Total Sales], Sales[profit] < 0)
```
> Computed straight from `profit < 0` — avoids any ambiguity in how `is_loss` imported.

```dax
% of Total Sales = DIVIDE([Total Sales], CALCULATE([Total Sales], ALLSELECTED(Sales)))
```
> Powers "share of total" and the Pareto view. `ALLSELECTED` respects slicers but ignores the visual's own row context.

```dax
Running Total Sales =
CALCULATE(
    [Total Sales],
    FILTER(ALLSELECTED('Date'[Date]), 'Date'[Date] <= MAX('Date'[Date]))
)
```
```dax
Product Rank = RANKX(ALL(Sales[product]), [Total Sales], , DESC)
```

---

## 4. Apply the Theme

View → Themes → **Browse for themes** → select `powerbi_theme.json`. This sets the palette, card styling, rounded borders, and a light page background so you're not fighting formatting on every visual.

---

## 5. Page 1 — Executive Overview

Canvas: 16:9 (1280×720). Think in horizontal bands.

**Band 1 — Header (top, full width, ~60px tall)**
- Text box: **"SaaS Sales Performance"** (left), and a smaller subtitle "B2B Software · AMER / EMEA / APJ". Add a thin colored rectangle behind it as a header bar.

**Band 2 — KPI cards (row of 5, directly under header)**
Use **Card** visuals, one measure each, left to right:
1. Total Sales
2. Total Profit
3. Profit Margin %
4. Total Orders
5. Avg Order Value

Keep them equal width. These are the "answer in 3 seconds" row recruiters look for first.

**Band 3 — Slicers (thin strip under cards, or docked left)**
- Slicer: **Region** (as buttons/tiles — horizontal orientation looks clean)
- Slicer: **Segment** (tiles)
- Slicer: **Date[Year]** (dropdown) or a Date range slicer

**Band 4 — Two charts side by side (60/40 split)**
- **Left (wider):** Line chart — **Sales trend**. Axis = `Date[Month Year]`, Value = `Total Sales`. Add `Total Profit` as a second line for contrast.
- **Right:** Clustered bar — **Sales & Profit by Region**. Axis = `region`, Values = `Total Sales`, `Total Profit`.

**Band 5 — Two charts side by side (bottom)**
- **Left:** Bar chart — **Profit by Product** (this is your money chart). Axis = `product`, Value = `Total Profit`, sorted ascending. Apply conditional formatting (Section 8) so losses go red.
- **Right:** Bar chart — **Top 10 Customers** by `Total Sales`. Add a Top-N filter (Filters pane → `customer` → Top N → Top 10 by Total Sales).

---

## 6. Page 2 — Product & Discount Deep Dive

**Header:** "Product & Discount Analysis"

**Visual A — Discount vs Margin (the headline insight).** Clustered column. This needs a discount-bucket field. Easiest: use the `revenue_band` pattern — but for discount, add one calculated column on `Sales`:
```dax
Discount Bucket =
SWITCH(
    TRUE(),
    Sales[discount] = 0, "0%",
    Sales[discount] <= 0.10, "1-10%",
    Sales[discount] <= 0.20, "11-20%",
    Sales[discount] <= 0.30, "21-30%",
    "30%+"
)
```
Then: Column chart, Axis = `Discount Bucket`, Value = `Profit Margin %`. Watch it go negative past ~20% — that's your story on screen.

**Visual B — Scatter.** X = `Avg Discount %`, Y = `Total Profit`, Legend = `segment`, Details = `product`. Shows the discount–profit relationship per product.

**Visual C — Product table with conditional formatting.** Table visual: `product`, `Total Sales`, `Total Profit`, `Profit Margin %`. Format the margin column with a red-white-green color scale (Section 8).

**Visual D — Matrix.** Rows = `product`, Columns = `region`, Values = `Total Profit`. Quickly spots which product loses money in which region.

---

## 7. Page 3 — Customer Analysis

**Header:** "Customer Analysis"

**Visual A — Top 10 Customers** bar (by `Total Sales`, Top-N filter).

**Visual B — Revenue concentration (Pareto).** Line and clustered column chart: Axis = `customer` (sorted by sales desc, Top 15), Column = `Total Sales`, Line = a cumulative % measure. Add:
```dax
Cumulative % of Sales =
VAR CurrentCustomerSales = [Total Sales]
VAR AllCustomers =
    ADDCOLUMNS(ALLSELECTED(Sales[customer]), "@sales", [Total Sales])
VAR RankedAbove =
    FILTER(AllCustomers, [@sales] >= CurrentCustomerSales)
RETURN
DIVIDE(SUMX(RankedAbove, [@sales]), CALCULATE([Total Sales], ALLSELECTED(Sales)))
```
Format as %. This visualizes how few customers drive most revenue.

**Visual C — Industry × Segment matrix.** Rows = `industry`, Columns = `segment`, Values = `Total Sales` + `Profit Margin %`.

**Visual D — Customer detail table** (this becomes your drill-through source — see Section 9).

---

## 8. Conditional Formatting

**Profit-by-product bar (Page 1):** select the visual → Format → Bars → Colors → **fx** → Format by **Rules** → if value `< 0` → red (`#C0504D`), else green (`#70AD47`).

**Margin column in tables (Pages 2 & 3):** table → Format → Cell elements → **Background color** on `Profit Margin %` → **fx** → Color scale: min red `#C0504D`, center white, max green `#70AD47`. Red instantly flags loss-makers.

**KPI cards:** optionally add an fx font color on Profit Margin % — red below a threshold, green above.

---

## 9. Drill-Through Page

1. Add a new page, name it **"Customer Detail"**, and **hide** it (right-click tab → Hide page).
2. On that page, in the Filters pane, drag `customer` into the **Drill-through** well.
3. Build detail visuals filtered to whatever customer the user drills into: KPI cards (their Sales/Profit/Orders), a line of their monthly sales, a table of their orders/products.
4. Add a **Back button** (Insert → Buttons → Back). Power BI adds this automatically when you set up drill-through.
5. Now on any page, right-click a customer in a chart → **Drill through → Customer Detail**.

Do the same pattern for a **Product Detail** page if you want product drill-through too.

---

## 10. Slicers, Sync & Filters

- **Sync slicers across pages:** select a slicer → View → **Sync slicers** pane → tick the pages you want it to apply to. Sync Region and Segment across all three pages so filters carry through.
- **Filters pane:** use page-level filters for page-specific scope, and the Top-N filters mentioned above. Keep the pane clean — hide it from end users if you want (Format → Filter pane).

---

## 11. Bookmarks & Navigation

**Page navigation buttons:**
- Insert → Buttons → **Blank**, add three, label them "Overview", "Products", "Customers".
- For each: Format button → Action → Type = **Page navigation** → Destination = the matching page. Put this button strip at the top of every page for a nav bar.

**A "Reset Filters" bookmark:**
- Clear all slicers to your default state → View → Bookmarks → **Add**. Name it "Reset".
- Add a button → Action → **Bookmark** → Reset. Gives users a one-click clear.

**Optional show/hide bookmarks:** toggle between, say, a "Sales view" and "Profit view" of the same chart using two bookmarks and a button — a nice touch if you want to show off, but not required.

---

## 12. Recruiter-Ready Polish Checklist

Before you screenshot or record it:

- [ ] Every visual has a clear, plain-English title ("Profit by Product", not "Sum of profit by product").
- [ ] Numbers formatted: currency with no excessive decimals, % to 1 decimal, thousands separators.
- [ ] Consistent colors (the theme handles most of this). Profit red/green is intuitive.
- [ ] Aligned visuals — use the alignment tools; nothing overlapping or ragged.
- [ ] A short insight callout (text box) on Page 1: e.g., "Discounts above 20% erase margin." Recruiters love that you *interpreted*, not just charted.
- [ ] Tooltips make sense (hover a bar — does it show useful fields?).
- [ ] Nav buttons work on every page; drill-through works; Reset works.
- [ ] Filename: `SaaS_Sales_Dashboard.pbix`. Export a PDF snapshot for portfolios that can't open .pbix.

---

## 13. Interview Talking Points (about the dashboard specifically)

- "I used **`DISTINCTCOUNT`** for order counts because the grain is order-line, not order — counting rows would inflate the number."
- "Profit Margin is a **measure** (`DIVIDE(SUM, SUM)`), not an average of row margins — averaging ratios gives the wrong answer."
- "I built a **dedicated Date table** and marked it as such so time-intelligence functions like `SAMEPERIODLASTYEAR` behave correctly."
- "The discount-bucket view surfaced the core finding: **deals discounted above ~20% turn unprofitable** — so the recommendation is a discount-approval threshold."
- "Feature engineering lives **once in the Python layer**, not duplicated in DAX — one source of truth for derived fields."

Build it, then tell me if any visual or DAX line misbehaves and I'll debug that specific piece.
