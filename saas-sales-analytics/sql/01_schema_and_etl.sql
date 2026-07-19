-- ============================================================================
-- 01_schema_and_etl.sql
-- Dimensional (star) schema + ETL for the AWS SaaS Sales dataset
-- Dataset source: https://www.kaggle.com/datasets/nnthanh101/aws-saas-sales
-- Target: PostgreSQL (notes inline for MySQL / SQL Server / DuckDB differences)
--
-- ARCHITECTURE
--   Python pipeline  ->  outputs/saas_sales_clean.csv  (clean, flat)
--        |                        |
--        v                        v
--   stg_saas_sales (landing) -> star schema (dim_* + fact_sales)
--
--   The Python layer does the cleaning; SQL does the dimensional modeling.
--   The star schema is what the Power BI layer will connect to.
--
-- WHY A STAR SCHEMA (interview point)
--   * One central FACT table (measures: sales, quantity, discount, profit)
--   * Several DIMENSION tables (the "by what?" -- customer, product, date, geo)
--   * Fast to query, easy to slice, and the exact shape BI tools expect.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 0. STAGING TABLE  (flat landing zone -- mirrors the cleaned CSV exactly)
--    We land the data as-is first, then transform. Never model straight off a
--    raw file: staging gives you a place to validate before it hits the model.
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS stg_saas_sales CASCADE;
CREATE TABLE stg_saas_sales (
    order_id          VARCHAR(20),
    order_date        DATE,
    date_key          INTEGER,
    contact_name      VARCHAR(100),
    country           VARCHAR(60),
    city              VARCHAR(60),
    region            VARCHAR(10),
    subregion         VARCHAR(40),
    customer          VARCHAR(120),
    customer_id       VARCHAR(20),
    industry          VARCHAR(60),
    segment           VARCHAR(30),
    product           VARCHAR(60),
    sales             NUMERIC(12,2),
    quantity          INTEGER,
    discount          NUMERIC(5,4),
    profit            NUMERIC(12,2),
    year              INTEGER,
    month             INTEGER,
    month_name        VARCHAR(12),
    quarter           INTEGER,
    year_month        VARCHAR(10),
    profit_margin     NUMERIC(10,6),
    is_loss           BOOLEAN,
    discount_pct      NUMERIC(5,2),
    revenue_per_unit  NUMERIC(12,4),
    revenue_band      VARCHAR(12)
);

-- Load the cleaned CSV produced by saas_sales_analysis.py.
-- PostgreSQL (psql client). The \copy runs client-side, no superuser needed:
\copy stg_saas_sales FROM 'outputs/saas_sales_clean.csv' WITH (FORMAT csv, HEADER true);
-- MySQL      : LOAD DATA LOCAL INFILE 'outputs/saas_sales_clean.csv' INTO TABLE ...
-- SQL Server : BULK INSERT stg_saas_sales FROM '...' WITH (FORMAT='CSV', FIRSTROW=2);
-- DuckDB     : CREATE TABLE stg_saas_sales AS SELECT * FROM read_csv_auto('...');


-- ----------------------------------------------------------------------------
-- 1. DIMENSION TABLES
--    Surrogate keys (customer_key, etc.) are auto-generated integers. We use
--    them (not the business IDs) as the join keys because they're compact,
--    stable, and decouple the model from source-system quirks.
-- ----------------------------------------------------------------------------

-- Date dimension. date_key (YYYYMMDD) is its own natural key, so no IDENTITY.
DROP TABLE IF EXISTS dim_date CASCADE;
CREATE TABLE dim_date (
    date_key   INTEGER PRIMARY KEY,
    full_date  DATE NOT NULL,
    year       INTEGER,
    quarter    INTEGER,
    month      INTEGER,
    month_name VARCHAR(12)
);

DROP TABLE IF EXISTS dim_customer CASCADE;
CREATE TABLE dim_customer (
    customer_key  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id   VARCHAR(20) UNIQUE NOT NULL,   -- natural/business key
    customer_name VARCHAR(120),
    industry      VARCHAR(60),
    segment       VARCHAR(30)
);
-- MySQL: customer_key INT AUTO_INCREMENT PRIMARY KEY
-- SQL Server: customer_key INT IDENTITY(1,1) PRIMARY KEY

DROP TABLE IF EXISTS dim_product CASCADE;
CREATE TABLE dim_product (
    product_key  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_name VARCHAR(60) UNIQUE NOT NULL
);

DROP TABLE IF EXISTS dim_geography CASCADE;
CREATE TABLE dim_geography (
    geography_key INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    country   VARCHAR(60),
    city      VARCHAR(60),
    region    VARCHAR(10),
    subregion VARCHAR(40),
    UNIQUE (country, city, region, subregion)
);


-- ----------------------------------------------------------------------------
-- 2. FACT TABLE  (grain = ONE ORDER LINE)
--    order_id is a DEGENERATE DIMENSION: an ID we keep in the fact with no
--    dimension table of its own. Keeping it lets us COUNT(DISTINCT order_id)
--    for true order counts even though one order spans multiple fact rows.
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS fact_sales CASCADE;
CREATE TABLE fact_sales (
    sale_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id      VARCHAR(20) NOT NULL,
    date_key      INTEGER REFERENCES dim_date(date_key),
    customer_key  INTEGER REFERENCES dim_customer(customer_key),
    product_key   INTEGER REFERENCES dim_product(product_key),
    geography_key INTEGER REFERENCES dim_geography(geography_key),
    sales     NUMERIC(12,2),
    quantity  INTEGER,
    discount  NUMERIC(5,4),
    profit    NUMERIC(12,2)
);


-- ----------------------------------------------------------------------------
-- 3. POPULATE DIMENSIONS  (SELECT DISTINCT -> identity keys auto-assigned)
-- ----------------------------------------------------------------------------
INSERT INTO dim_date (date_key, full_date, year, quarter, month, month_name)
SELECT DISTINCT date_key, order_date, year, quarter, month, month_name
FROM stg_saas_sales;

INSERT INTO dim_customer (customer_id, customer_name, industry, segment)
SELECT DISTINCT customer_id, customer, industry, segment
FROM stg_saas_sales;

INSERT INTO dim_product (product_name)
SELECT DISTINCT product FROM stg_saas_sales;

INSERT INTO dim_geography (country, city, region, subregion)
SELECT DISTINCT country, city, region, subregion FROM stg_saas_sales;


-- ----------------------------------------------------------------------------
-- 4. POPULATE FACT  (resolve each natural key to its surrogate key via JOINs)
--    This lookup step is the heart of dimensional ETL.
-- ----------------------------------------------------------------------------
INSERT INTO fact_sales (order_id, date_key, customer_key, product_key,
                        geography_key, sales, quantity, discount, profit)
SELECT s.order_id,
       s.date_key,
       c.customer_key,
       p.product_key,
       g.geography_key,
       s.sales, s.quantity, s.discount, s.profit
FROM stg_saas_sales s
JOIN dim_customer  c ON s.customer_id = c.customer_id
JOIN dim_product   p ON s.product     = p.product_name
JOIN dim_geography g ON s.country   = g.country
                    AND s.city      = g.city
                    AND s.region    = g.region
                    AND s.subregion = g.subregion;


-- ----------------------------------------------------------------------------
-- 5. INDEXES  (speed up the dimension joins and date-range filters)
--    Rule of thumb: index the FK columns on the fact table + any column you
--    filter on a lot. The PKs are already indexed automatically.
-- ----------------------------------------------------------------------------
CREATE INDEX idx_fact_date     ON fact_sales(date_key);
CREATE INDEX idx_fact_customer ON fact_sales(customer_key);
CREATE INDEX idx_fact_product  ON fact_sales(product_key);
CREATE INDEX idx_fact_geo      ON fact_sales(geography_key);


-- ----------------------------------------------------------------------------
-- 6. VALIDATION  (fact rows must equal staging rows -- proves no rows were
--    dropped or duplicated by the joins above)
-- ----------------------------------------------------------------------------
SELECT
    (SELECT COUNT(*) FROM stg_saas_sales) AS staging_rows,
    (SELECT COUNT(*) FROM fact_sales)     AS fact_rows,
    (SELECT COUNT(*) FROM dim_customer)   AS customers,
    (SELECT COUNT(*) FROM dim_product)    AS products,
    (SELECT COUNT(*) FROM dim_geography)  AS geographies;
