# Architecture

## Pipeline overview

Three layers with a clear separation of concerns: Python cleans and analyses, SQL models
and serves, Power BI presents. Each layer hands a well-defined artefact to the next.

```mermaid
flowchart TD
    A["Kaggle: AWS SaaS Sales<br/>9,994 rows x 19 cols"] --> B["data/raw/aws_saas_sales.csv"]
    G["src/generate_sample_data.py"] -.synthetic fallback.-> B2["data/sample/*_SAMPLE.csv"]
    B --> C
    B2 --> C
    C["src/pipeline.py<br/>load - clean - engineer - EDA - visualise"] --> D["data/processed/saas_sales_clean.csv"]
    C --> E["images/*.png, *.html"]
    D --> F["sql/01_schema_and_etl.sql<br/>star schema + ETL"]
    F --> H["sql/02_analysis_queries.sql<br/>+ vw_sales_enriched"]
    D --> I["Power BI<br/>dashboards/"]
    H -.production path.-> I
    I --> J["3-page dashboard<br/>+ drill-through"]
```

## Why this shape

- **Cleaning happens once, in Python.** Feature engineering is not duplicated in SQL or DAX,
  so there is a single source of truth for every derived field.
- **SQL owns the dimensional model.** The star schema is the serving layer; Power BI can
  connect to it directly in a production setup.
- **Power BI owns presentation only.** It consumes either the flat cleaned CSV (simple) or
  the star schema (production).

## Data model (star schema)

```mermaid
erDiagram
    dim_date ||--o{ fact_sales : "date_key"
    dim_customer ||--o{ fact_sales : "customer_key"
    dim_product ||--o{ fact_sales : "product_key"
    dim_geography ||--o{ fact_sales : "geography_key"

    fact_sales {
        bigint sale_id PK
        varchar order_id "degenerate dimension"
        int date_key FK
        int customer_key FK
        int product_key FK
        int geography_key FK
        numeric sales
        int quantity
        numeric discount
        numeric profit
    }
    dim_date {
        int date_key PK
        date full_date
        int year
        int quarter
        int month
    }
    dim_customer {
        int customer_key PK
        varchar customer_id
        varchar customer_name
        varchar industry
        varchar segment
    }
    dim_product {
        int product_key PK
        varchar product_name
    }
    dim_geography {
        int geography_key PK
        varchar country
        varchar city
        varchar region
        varchar subregion
    }
```

`order_id` is kept in the fact table as a **degenerate dimension** — an identifier with no
dimension table of its own. It is what makes `COUNT(DISTINCT order_id)` possible even
though a single order occupies several fact rows.

## Module structure

```mermaid
flowchart LR
    cfg["config.py<br/>paths + constants"] --> pipe["pipeline.py"]
    utils["utils.py<br/>logging + safe IO"] --> pipe
    cfg --> gen["generate_sample_data.py"]
    pipe --> out["images/ + data/processed/"]
    tests["tests/test_pipeline.py"] -.imports.-> pipe
```

| Module | Responsibility |
|---|---|
| `config.py` | Every path and constant. Derived from `PROJECT_ROOT`, so the pipeline runs from any working directory. |
| `utils.py` | Logger setup (console + file) and CSV read/write with actionable errors. |
| `pipeline.py` | The six pipeline stages, one function per concern. |
| `generate_sample_data.py` | Schema-matched synthetic data so the repo runs without the Kaggle download. |
