-- ============================================================================
-- 02_analysis_queries.sql
-- Analytical query library for the AWS SaaS Sales star schema
-- Dataset source: https://www.kaggle.com/datasets/nnthanh101/aws-saas-sales
-- Ordered beginner -> advanced. Every query has a note on WHAT it answers.
-- Run 01_schema_and_etl.sql first.
-- ============================================================================


-- ############################################################################
-- SECTION A -- BEGINNER  (aggregation, GROUP BY, ORDER BY, DISTINCT)
-- ############################################################################

-- A1. Headline KPIs for the whole business.
--     NOTE: COUNT(DISTINCT order_id), not COUNT(*). One order = many rows,
--     so counting rows would overstate orders. This is THE classic gotcha.
SELECT
    ROUND(SUM(sales), 2)                          AS total_sales,
    ROUND(SUM(profit), 2)                         AS total_profit,
    ROUND(100.0 * SUM(profit) / SUM(sales), 1)    AS profit_margin_pct,
    COUNT(DISTINCT order_id)                      AS total_orders,
    ROUND(SUM(sales) / COUNT(DISTINCT order_id), 2) AS avg_order_value,
    ROUND(AVG(discount) * 100, 1)                 AS avg_discount_pct
FROM fact_sales;


-- A2. Sales & profit by region (first JOIN to a dimension).
SELECT
    g.region,
    ROUND(SUM(f.sales), 2)                       AS sales,
    ROUND(SUM(f.profit), 2)                      AS profit,
    ROUND(100.0 * SUM(f.profit) / SUM(f.sales), 1) AS margin_pct
FROM fact_sales f
JOIN dim_geography g ON f.geography_key = g.geography_key
GROUP BY g.region
ORDER BY sales DESC;


-- A3. Top 10 customers by revenue.
SELECT
    c.customer_name,
    ROUND(SUM(f.sales), 2) AS revenue,
    COUNT(DISTINCT f.order_id) AS orders
FROM fact_sales f
JOIN dim_customer c ON f.customer_key = c.customer_key
GROUP BY c.customer_name
ORDER BY revenue DESC
LIMIT 10;


-- ############################################################################
-- SECTION B -- INTERMEDIATE  (CASE, HAVING, subqueries, multi-dimension)
-- ############################################################################

-- B1. Product profitability with a CASE health flag.
--     CASE turns a raw margin number into a label a manager can act on.
SELECT
    p.product_name,
    ROUND(SUM(f.sales), 2)                        AS sales,
    ROUND(SUM(f.profit), 2)                       AS profit,
    ROUND(100.0 * SUM(f.profit) / SUM(f.sales), 1) AS margin_pct,
    CASE
        WHEN SUM(f.profit) < 0                       THEN 'LOSS-MAKING'
        WHEN SUM(f.profit) / SUM(f.sales) < 0.10     THEN 'THIN MARGIN'
        ELSE                                              'HEALTHY'
    END AS status
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.product_name
ORDER BY margin_pct;


-- B2. Only loss-making products (HAVING filters AFTER aggregation).
--     WHERE can't be used here -- the condition is on an aggregate.
SELECT
    p.product_name,
    ROUND(SUM(f.profit), 2) AS total_profit
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.product_name
HAVING SUM(f.profit) < 0
ORDER BY total_profit;


-- B3. Segments that discount above the company average (correlated with a
--     scalar subquery). The subquery computes the global average once.
SELECT
    c.segment,
    ROUND(AVG(f.discount) * 100, 1) AS avg_discount_pct
FROM fact_sales f
JOIN dim_customer c ON f.customer_key = c.customer_key
GROUP BY c.segment
HAVING AVG(f.discount) > (SELECT AVG(discount) FROM fact_sales)
ORDER BY avg_discount_pct DESC;


-- B4. Industry x Segment revenue matrix (grouping by two dimensions).
SELECT
    c.industry,
    c.segment,
    ROUND(SUM(f.sales), 2) AS sales,
    ROUND(100.0 * SUM(f.profit) / SUM(f.sales), 1) AS margin_pct
FROM fact_sales f
JOIN dim_customer c ON f.customer_key = c.customer_key
GROUP BY c.industry, c.segment
ORDER BY c.industry, sales DESC;


-- B5. Monthly sales trend (JOIN to the date dimension).
SELECT
    d.year,
    d.month,
    d.month_name,
    ROUND(SUM(f.sales), 2) AS sales
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month;


-- ############################################################################
-- SECTION C -- ADVANCED  (CTEs + window functions)
-- These are what push an interview from "junior" to "hire".
-- ############################################################################

-- C1. Revenue concentration / Pareto (CTE + running-total window).
--     Answers "how much of our revenue rides on our biggest customers?"
--     SUM(...) OVER (ORDER BY rev DESC) gives a cumulative running total;
--     dividing by the grand total gives the cumulative % (the Pareto curve).
WITH customer_rev AS (
    SELECT c.customer_name, SUM(f.sales) AS revenue
    FROM fact_sales f
    JOIN dim_customer c ON f.customer_key = c.customer_key
    GROUP BY c.customer_name
)
SELECT
    customer_name,
    ROUND(revenue, 2) AS revenue,
    ROUND(100.0 * revenue / SUM(revenue) OVER (), 1) AS pct_of_total,
    ROUND(100.0 * SUM(revenue) OVER (ORDER BY revenue DESC)
                / SUM(revenue) OVER (), 1)           AS cumulative_pct
FROM customer_rev
ORDER BY revenue DESC;


-- C2. Best-selling product IN EACH region (RANK with PARTITION BY).
--     PARTITION BY restarts the ranking for every region.
WITH product_region AS (
    SELECT
        g.region,
        p.product_name,
        SUM(f.sales) AS sales,
        RANK() OVER (PARTITION BY g.region ORDER BY SUM(f.sales) DESC) AS rnk
    FROM fact_sales f
    JOIN dim_geography g ON f.geography_key = g.geography_key
    JOIN dim_product  p ON f.product_key   = p.product_key
    GROUP BY g.region, p.product_name
)
SELECT region, product_name, ROUND(sales, 2) AS sales
FROM product_region
WHERE rnk = 1
ORDER BY sales DESC;


-- C3. Month-over-month growth (LAG pulls the previous month's value).
WITH monthly AS (
    SELECT d.year, d.month, SUM(f.sales) AS sales
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY d.year, d.month
)
SELECT
    year, month,
    ROUND(sales, 2) AS sales,
    ROUND(sales - LAG(sales) OVER (ORDER BY year, month), 2) AS mom_change,
    ROUND(100.0 * (sales - LAG(sales) OVER (ORDER BY year, month))
                / NULLIF(LAG(sales) OVER (ORDER BY year, month), 0), 1) AS mom_pct
FROM monthly
ORDER BY year, month;


-- C4. Each customer's share of their OWN industry's revenue
--     (SUM OVER PARTITION BY industry -- an aggregate without collapsing rows).
WITH cust AS (
    SELECT c.industry, c.customer_name, SUM(f.sales) AS revenue
    FROM fact_sales f
    JOIN dim_customer c ON f.customer_key = c.customer_key
    GROUP BY c.industry, c.customer_name
)
SELECT
    industry,
    customer_name,
    ROUND(revenue, 2) AS revenue,
    ROUND(100.0 * revenue / SUM(revenue) OVER (PARTITION BY industry), 1)
        AS pct_of_industry
FROM cust
ORDER BY industry, revenue DESC;


-- C5. Cumulative (running) sales over time -- the "how are we tracking YTD?" view.
WITH monthly AS (
    SELECT d.year, d.month, SUM(f.sales) AS sales
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY d.year, d.month
)
SELECT
    year, month,
    ROUND(sales, 2) AS monthly_sales,
    ROUND(SUM(sales) OVER (PARTITION BY year ORDER BY month), 2) AS running_total_ytd
FROM monthly
ORDER BY year, month;


-- C6. THE MONEY QUERY -- discount bucket vs margin (CASE + aggregation).
--     Shows the exact discount level where deals stop being profitable.
SELECT
    CASE
        WHEN discount = 0      THEN '0%'
        WHEN discount <= 0.10  THEN '1-10%'
        WHEN discount <= 0.20  THEN '11-20%'
        WHEN discount <= 0.30  THEN '21-30%'
        ELSE                        '30%+'
    END AS discount_bucket,
    COUNT(*)                                      AS line_count,
    ROUND(SUM(sales), 2)                          AS sales,
    ROUND(SUM(profit), 2)                         AS profit,
    ROUND(100.0 * SUM(profit) / SUM(sales), 1)    AS margin_pct
FROM fact_sales
GROUP BY discount_bucket
ORDER BY discount_bucket;


-- ############################################################################
-- SECTION D -- VIEWS  (save complex logic as reusable objects)
-- ############################################################################

-- D1. "One Big Table" view: fact joined to every dimension + derived margin.
--     Point Power BI / Tableau / ad-hoc analysts at THIS instead of raw joins.
CREATE OR REPLACE VIEW vw_sales_enriched AS
SELECT
    f.sale_id,
    f.order_id,
    d.full_date,
    d.year,
    d.quarter,
    d.month_name,
    c.customer_name,
    c.industry,
    c.segment,
    p.product_name,
    g.region,
    g.subregion,
    g.country,
    f.sales,
    f.quantity,
    f.discount,
    f.profit,
    ROUND(100.0 * f.profit / NULLIF(f.sales, 0), 2) AS profit_margin_pct,
    CASE WHEN f.profit < 0 THEN TRUE ELSE FALSE END AS is_loss
FROM fact_sales f
JOIN dim_date      d ON f.date_key      = d.date_key
JOIN dim_customer  c ON f.customer_key  = c.customer_key
JOIN dim_product   p ON f.product_key   = p.product_key
JOIN dim_geography g ON f.geography_key = g.geography_key;


-- D2. Pre-aggregated monthly KPIs view (handy for a trend page).
CREATE OR REPLACE VIEW vw_monthly_kpis AS
SELECT
    d.year,
    d.month,
    ROUND(SUM(f.sales), 2)                        AS sales,
    ROUND(SUM(f.profit), 2)                       AS profit,
    ROUND(100.0 * SUM(f.profit) / SUM(f.sales), 1) AS margin_pct,
    COUNT(DISTINCT f.order_id)                    AS orders
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.year, d.month;


-- ############################################################################
-- SECTION E -- STORED PROCEDURE / FUNCTION  (PostgreSQL-specific)
-- NOTE: This uses PL/pgSQL and runs in PostgreSQL. It will NOT run in DuckDB.
--       MySQL/SQL Server use CREATE PROCEDURE with their own syntax.
-- Parameterizing a query like this avoids copy-pasting the same SQL per region.
-- ############################################################################
CREATE OR REPLACE FUNCTION get_region_kpis(p_region VARCHAR)
RETURNS TABLE (
    metric VARCHAR,
    value  NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 'total_sales'::VARCHAR, ROUND(SUM(f.sales), 2)
        FROM fact_sales f JOIN dim_geography g ON f.geography_key = g.geography_key
        WHERE g.region = p_region
    UNION ALL
    SELECT 'total_profit', ROUND(SUM(f.profit), 2)
        FROM fact_sales f JOIN dim_geography g ON f.geography_key = g.geography_key
        WHERE g.region = p_region
    UNION ALL
    SELECT 'margin_pct', ROUND(100.0 * SUM(f.profit) / NULLIF(SUM(f.sales), 0), 1)
        FROM fact_sales f JOIN dim_geography g ON f.geography_key = g.geography_key
        WHERE g.region = p_region
    UNION ALL
    SELECT 'orders', COUNT(DISTINCT f.order_id)::NUMERIC
        FROM fact_sales f JOIN dim_geography g ON f.geography_key = g.geography_key
        WHERE g.region = p_region;
END;
$$ LANGUAGE plpgsql;

-- Call it like:   SELECT * FROM get_region_kpis('AMER');


-- ############################################################################
-- SECTION F -- OPTIMIZATION NOTES (talking points, not runnable statements)
-- ############################################################################
-- 1. INDEX the fact FK columns (done in 01) so dimension JOINs use index scans
--    instead of full-table scans. Also index columns you filter on heavily.
-- 2. Use EXPLAIN ANALYZE <query> to see the actual plan and spot slow scans:
--       EXPLAIN ANALYZE SELECT ... ;
-- 3. Filter EARLY. Push WHERE conditions before big JOINs/aggregations so the
--    engine handles fewer rows.
-- 4. SELECT only the columns you need -- SELECT * drags extra I/O into memory.
-- 5. For dashboards hitting the same heavy aggregation repeatedly, promote the
--    view to a MATERIALIZED VIEW and refresh on a schedule:
--       CREATE MATERIALIZED VIEW mv_monthly_kpis AS SELECT ... ;
--       REFRESH MATERIALIZED VIEW mv_monthly_kpis;
-- 6. Keep the fact table NARROW (keys + measures). Descriptive text belongs in
--    dimensions -- it keeps the fact small and fast.
