// ============================================================================
// Power Query (M) — load & type the cleaned SaaS Sales data
// Dataset source: https://www.kaggle.com/datasets/nnthanh101/aws-saas-sales
//
// HOW TO USE
//   Power BI Desktop -> Get Data -> Blank Query -> Advanced Editor ->
//   paste this whole script -> Done. Rename the query to "Sales".
//
//   >>> EDIT THE FILE PATH on the File.Contents line to point at YOUR copy
//       of saas_sales_clean.csv (produced by saas_sales_analysis.py). <<<
// ============================================================================
let
    // --- Point this at your local cleaned CSV -------------------------------
    Source = Csv.Document(
        File.Contents("C:\Users\YOU\path\to\outputs\saas_sales_clean.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),

    // Use the first row as column headers
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),

    // Set explicit data types (never leave Power BI to guess -- wrong types
    // break aggregations, date logic, and relationships)
    Typed = Table.TransformColumnTypes(Promoted, {
        {"order_id", type text},
        {"order_date", type date},
        {"date_key", Int64.Type},
        {"contact_name", type text},
        {"country", type text},
        {"city", type text},
        {"region", type text},
        {"subregion", type text},
        {"customer", type text},
        {"customer_id", type text},
        {"industry", type text},
        {"segment", type text},
        {"product", type text},
        {"sales", type number},
        {"quantity", Int64.Type},
        {"discount", type number},
        {"profit", type number},
        {"year", Int64.Type},
        {"month", Int64.Type},
        {"month_name", type text},
        {"quarter", Int64.Type},
        {"year_month", type text},
        {"profit_margin", type number},
        {"is_loss", type logical},
        {"discount_pct", type number},
        {"revenue_per_unit", type number},
        {"revenue_band", type text}
    })
in
    Typed
