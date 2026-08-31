-- =====================================================================
-- Insight360 Executive BI Platform
-- Phase 4 — Data Engineering: validate_sql.sql
-- Post-Load Validation, Referential Integrity & Business Metrics Audit
-- =====================================================================

SET search_path TO insight360, public;

-- =====================================================================
-- 1. ROW COUNT AUDIT
-- =====================================================================

SELECT 'dim_date' AS table_name, COUNT(*) AS row_count FROM insight360.dim_date
UNION ALL
SELECT 'dim_store', COUNT(*) FROM insight360.dim_store
UNION ALL
SELECT 'dim_product', COUNT(*) FROM insight360.dim_product
UNION ALL
SELECT 'dim_customer', COUNT(*) FROM insight360.dim_customer
UNION ALL
SELECT 'fact_sales', COUNT(*) FROM insight360.fact_sales
UNION ALL
SELECT 'fact_returns', COUNT(*) FROM insight360.fact_returns
UNION ALL
SELECT 'fact_inventory_snapshot', COUNT(*) FROM insight360.fact_inventory_snapshot
UNION ALL
SELECT 'fact_staffing', COUNT(*) FROM insight360.fact_staffing
ORDER BY table_name;

-- =====================================================================
-- 2. REFERENTIAL INTEGRITY & ORPHAN CHECKS
-- =====================================================================

SELECT 'fact_sales_orphan_store_key' AS check_name, COUNT(*) AS orphan_count
FROM insight360.fact_sales fs
LEFT JOIN insight360.dim_store ds ON fs.store_key = ds.store_key
WHERE ds.store_key IS NULL;

SELECT 'fact_sales_orphan_product_key' AS check_name, COUNT(*) AS orphan_count
FROM insight360.fact_sales fs
LEFT JOIN insight360.dim_product dp ON fs.product_key = dp.product_key
WHERE dp.product_key IS NULL;

SELECT 'fact_sales_orphan_customer_key' AS check_name, COUNT(*) AS orphan_count
FROM insight360.fact_sales fs
LEFT JOIN insight360.dim_customer dc ON fs.customer_key = dc.customer_key
WHERE dc.customer_key IS NULL;

SELECT 'fact_sales_orphan_date_key' AS check_name, COUNT(*) AS orphan_count
FROM insight360.fact_sales fs
LEFT JOIN insight360.dim_date dd ON fs.date_key = dd.date_key
WHERE dd.date_key IS NULL;

SELECT 'fact_returns_orphan_sales_id' AS check_name, COUNT(*) AS orphan_count
FROM insight360.fact_returns fr
LEFT JOIN insight360.fact_sales fs ON fr.original_sales_id = fs.sales_id
WHERE fs.sales_id IS NULL;

SELECT 'fact_returns_orphan_store_key' AS check_name, COUNT(*) AS orphan_count
FROM insight360.fact_returns fr
LEFT JOIN insight360.dim_store ds ON fr.store_key = ds.store_key
WHERE ds.store_key IS NULL;

SELECT 'fact_returns_orphan_product_key' AS check_name, COUNT(*) AS orphan_count
FROM insight360.fact_returns fr
LEFT JOIN insight360.dim_product dp ON fr.product_key = dp.product_key
WHERE dp.product_key IS NULL;

SELECT 'fact_inventory_orphan_store_key' AS check_name, COUNT(*) AS orphan_count
FROM insight360.fact_inventory_snapshot fi
LEFT JOIN insight360.dim_store ds ON fi.store_key = ds.store_key
WHERE ds.store_key IS NULL;

SELECT 'fact_inventory_orphan_product_key' AS check_name, COUNT(*) AS orphan_count
FROM insight360.fact_inventory_snapshot fi
LEFT JOIN insight360.dim_product dp ON fi.product_key = dp.product_key
WHERE dp.product_key IS NULL;

SELECT 'fact_staffing_orphan_store_key' AS check_name, COUNT(*) AS orphan_count
FROM insight360.fact_staffing fst
LEFT JOIN insight360.dim_store ds ON fst.store_key = ds.store_key
WHERE ds.store_key IS NULL;

SELECT 'fact_sales' AS table_name, sales_id, COUNT(*) AS dup_count
FROM insight360.fact_sales
GROUP BY sales_id
HAVING COUNT(*) > 1;

-- =====================================================================
-- 3. KEY BUSINESS METRICS VERIFICATION
-- =====================================================================

SELECT
    ROUND(SUM(fs.quantity::numeric * fs.unit_price::numeric), 2)  AS total_gross_sales,
    ROUND(SUM(fs.discount_amount::numeric), 2)                   AS total_discounts,
    ROUND(SUM(fs.net_sales_amount::numeric), 2)                  AS total_net_sales,
    (SELECT ROUND(SUM(refund_amount::numeric), 2) FROM insight360.fact_returns) AS total_returns_refund_amount
FROM insight360.fact_sales fs;

SELECT
    ROUND(
        100.0 * (SELECT COALESCE(SUM(quantity_returned::numeric), 0) FROM insight360.fact_returns)
        / NULLIF((SELECT SUM(quantity::numeric) FROM insight360.fact_sales), 0)
    , 2) AS global_return_rate_pct;

WITH sales_by_channel AS (
    SELECT channel, SUM(quantity::numeric) AS units_sold
    FROM insight360.fact_sales
    GROUP BY channel
),
returns_by_channel AS (
    SELECT fs.channel, SUM(fr.quantity_returned::numeric) AS units_returned
    FROM insight360.fact_returns fr
    JOIN insight360.fact_sales fs ON fr.original_sales_id = fs.sales_id
    GROUP BY fs.channel
)
SELECT
    sbc.channel,
    sbc.units_sold,
    COALESCE(rbc.units_returned, 0) AS units_returned,
    ROUND(100.0 * COALESCE(rbc.units_returned, 0) / NULLIF(sbc.units_sold, 0), 2) AS return_rate_pct
FROM sales_by_channel sbc
LEFT JOIN returns_by_channel rbc ON sbc.channel = rbc.channel
ORDER BY sbc.channel;

-- 3d. Overall stockout rate (%) by region
SELECT
    ds.region,
    COUNT(*)                                                                                  AS total_snapshots,
    SUM(CASE WHEN fi.is_out_of_stock::text IN ('True', 'true', '1') THEN 1 ELSE 0 END)        AS stockout_snapshots,
    ROUND(
        100.0 * SUM(CASE WHEN fi.is_out_of_stock::text IN ('True', 'true', '1') THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)
    , 2) AS stockout_rate_pct
FROM insight360.fact_inventory_snapshot fi
JOIN insight360.dim_store ds ON fi.store_key = ds.store_key
GROUP BY ds.region
ORDER BY stockout_rate_pct DESC;

-- 3e. Overall stockout rate (%) by product division
SELECT
    dp.division,
    COUNT(*)                                                                                  AS total_snapshots,
    SUM(CASE WHEN fi.is_out_of_stock::text IN ('True', 'true', '1') THEN 1 ELSE 0 END)        AS stockout_snapshots,
    ROUND(
        100.0 * SUM(CASE WHEN fi.is_out_of_stock::text IN ('True', 'true', '1') THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)
    , 2) AS stockout_rate_pct
FROM insight360.fact_inventory_snapshot fi
JOIN insight360.dim_product dp ON fi.product_key = dp.product_key
GROUP BY dp.division
ORDER BY stockout_rate_pct DESC;

-- 3f. Combined stockout rate (%) by region AND division
SELECT
    ds.region,
    dp.division,
    COUNT(*)                                                                                  AS total_snapshots,
    SUM(CASE WHEN fi.is_out_of_stock::text IN ('True', 'true', '1') THEN 1 ELSE 0 END)        AS stockout_snapshots,
    ROUND(
        100.0 * SUM(CASE WHEN fi.is_out_of_stock::text IN ('True', 'true', '1') THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)
    , 2) AS stockout_rate_pct
FROM insight360.fact_inventory_snapshot fi
JOIN insight360.dim_store ds ON fi.store_key = ds.store_key
JOIN insight360.dim_product dp ON fi.product_key = dp.product_key
GROUP BY ds.region, dp.division
ORDER BY stockout_rate_pct DESC
LIMIT 20;

SELECT
    ds.store_format,
    ROUND(SUM(fst.labor_cost::numeric), 2)              AS total_labor_cost,
    ROUND(AVG(fst.sales_per_labor_hour::numeric), 2)    AS avg_sales_per_labor_hour,
    ROUND(SUM(fst.overtime_hours::numeric), 2)          AS total_overtime_hours
FROM insight360.fact_staffing fst
JOIN insight360.dim_store ds ON fst.store_key = ds.store_key
GROUP BY ds.store_format
ORDER BY total_labor_cost DESC;

-- =====================================================================
-- 4. AGGREGATED BI SUMMARY VIEWS (Data Mart Readiness)
-- =====================================================================

DROP VIEW IF EXISTS insight360.vw_executive_summary;

CREATE VIEW insight360.vw_executive_summary AS
WITH monthly_sales AS (
    SELECT
        dd.fiscal_year                                                AS year,
        dd.fiscal_month_number                                        AS month,
        dd.month_name                                                 AS month_name,
        SUM(fs.quantity::numeric * fs.unit_price::numeric)            AS gross_sales,
        SUM(fs.discount_amount::numeric)                              AS total_discounts,
        SUM(fs.net_sales_amount::numeric)                             AS net_sales,
        SUM(fs.quantity::numeric)                                     AS units_sold,
        COUNT(DISTINCT fs.customer_key)                               AS active_customers,
        COUNT(DISTINCT fs.sales_id)                                   AS total_transactions
    FROM insight360.fact_sales fs
    JOIN insight360.dim_date dd ON fs.date_key = dd.date_key
    GROUP BY dd.fiscal_year, dd.fiscal_month_number, dd.month_name
),
monthly_returns AS (
    SELECT
        dd.fiscal_year                                                AS year,
        dd.fiscal_month_number                                        AS month,
        SUM(fr.refund_amount::numeric)                                AS total_refund_amount,
        SUM(fr.quantity_returned::numeric)                            AS units_returned,
        COUNT(fr.return_id)                                           AS total_return_transactions
    FROM insight360.fact_returns fr
    JOIN insight360.dim_date dd ON fr.date_key = dd.date_key
    GROUP BY dd.fiscal_year, dd.fiscal_month_number
)
SELECT
    ms.year,
    ms.month,
    ms.month_name,
    ms.gross_sales,
    ms.total_discounts,
    ms.net_sales,
    ms.units_sold,
    ms.total_transactions,
    ms.active_customers,
    COALESCE(mr.total_refund_amount, 0)                                     AS total_refund_amount,
    COALESCE(mr.units_returned, 0)                                          AS units_returned,
    COALESCE(mr.total_return_transactions, 0)                               AS total_return_transactions,
    ROUND(ms.net_sales - COALESCE(mr.total_refund_amount, 0), 2)          AS net_revenue_after_returns,
    ROUND(
        100.0 * COALESCE(mr.units_returned, 0) / NULLIF(ms.units_sold, 0)
    , 2)                                                                    AS return_rate_pct
FROM monthly_sales ms
LEFT JOIN monthly_returns mr
    ON ms.year = mr.year AND ms.month = mr.month
ORDER BY ms.year, ms.month;

DROP VIEW IF EXISTS insight360.vw_inventory_health;

CREATE VIEW insight360.vw_inventory_health AS
SELECT
    dd.fiscal_year                                                                            AS year,
    dd.week_of_year                                                                           AS week_number,
    ds.region,
    dp.division,
    COUNT(*)                                                                                  AS total_snapshots,
    SUM(CASE WHEN fi.is_out_of_stock::text IN ('True', 'true', '1') THEN 1 ELSE 0 END)        AS stockout_snapshots,
    ROUND(
        100.0 * SUM(CASE WHEN fi.is_out_of_stock::text IN ('True', 'true', '1') THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)
    , 2)                                                                                      AS stockout_rate_pct,
    ROUND(AVG(fi.closing_stock::numeric), 2)                                                  AS avg_closing_stock,
    ROUND(AVG(fi.opening_stock::numeric), 2)                                                  AS avg_opening_stock,
    ROUND(AVG(fi.safety_stock::numeric), 2)                                                   AS avg_safety_stock,
    ROUND(AVG(fi.stockout_duration_days::numeric), 2)                                        AS avg_stockout_duration_days,
    SUM(fi.stockout_duration_days::numeric)                                                   AS total_stockout_duration_days
FROM insight360.fact_inventory_snapshot fi
JOIN insight360.dim_date dd ON fi.date_key = dd.date_key
JOIN insight360.dim_store ds ON fi.store_key = ds.store_key
JOIN insight360.dim_product dp ON fi.product_key = dp.product_key
GROUP BY dd.fiscal_year, dd.week_of_year, ds.region, dp.division
ORDER BY year, week_number, ds.region, dp.division;

SELECT * FROM insight360.vw_executive_summary ORDER BY year, month LIMIT 12;

SELECT * FROM insight360.vw_inventory_health
ORDER BY stockout_rate_pct DESC
LIMIT 20;