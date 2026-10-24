-- Analytical SQL Queries for BazaarLens-IR (PostgreSQL 15+)

-- Query 1: Category Revenue Concentration & Pareto Share (CTE + Window Functions)
WITH category_gmv AS (
    SELECT
        c.category_id,
        c.category_title,
        COUNT(p.product_id) AS total_skus,
        SUM(CASE WHEN p.is_available THEN 1 ELSE 0 END) AS available_skus,
        SUM(p.sales_count_week) AS weekly_units_sold,
        SUM(p.weekly_gmv_proxy_toman) AS category_weekly_gmv_toman,
        ROUND(AVG(p.discount_pct), 2) AS avg_discount_pct,
        ROUND(AVG(CASE WHEN p.is_free_shipping THEN 100.0 ELSE 0.0 END), 1) AS free_shipping_pct
    FROM fact_products p
    JOIN dim_categories c ON p.category_id = c.category_id
    GROUP BY c.category_id, c.category_title
)
SELECT
    category_id,
    category_title,
    total_skus,
    weekly_units_sold,
    category_weekly_gmv_toman,
    ROUND(100.0 * category_weekly_gmv_toman / NULLIF(SUM(category_weekly_gmv_toman) OVER (), 0), 2) AS gmv_share_pct,
    ROUND(100.0 * SUM(category_weekly_gmv_toman) OVER (ORDER BY category_weekly_gmv_toman DESC)
          / NULLIF(SUM(category_weekly_gmv_toman) OVER (), 0), 2) AS cumulative_gmv_share_pct,
    avg_discount_pct,
    free_shipping_pct
FROM category_gmv
ORDER BY category_weekly_gmv_toman DESC;

-- Query 2: Shipping Policy & Preparation Delay Matrix (CASE WHEN + GROUP BY)
SELECT
    CASE
        WHEN preparation_days <= 2 THEN '1. Fast Dispatch (1-2 Days)'
        WHEN preparation_days BETWEEN 3 AND 5 THEN '2. Standard Dispatch (3-5 Days)'
        ELSE '3. Slow Dispatch (6+ Days)'
    END AS dispatch_tier,
    is_free_shipping,
    COUNT(product_id) AS sku_count,
    ROUND(AVG(sales_count_week), 2) AS avg_weekly_units_per_sku,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_toman)::numeric, 0) AS median_price_toman,
    ROUND(AVG(bayesian_rating), 2) AS avg_bayesian_rating
FROM fact_products
WHERE is_available = TRUE
GROUP BY 1, 2
ORDER BY 1, is_free_shipping DESC;

-- Query 3: Top Performing Vendors Within Each Category Using DENSE_RANK()
WITH vendor_cat_perf AS (
    SELECT
        p.category_id,
        c.category_title,
        p.vendor_name,
        v.vendor_status_title,
        COUNT(p.product_id) AS active_skus,
        SUM(p.sales_count_week) AS total_weekly_units,
        SUM(p.weekly_gmv_proxy_toman) AS vendor_weekly_gmv_toman,
        ROUND(AVG(p.bayesian_rating), 3) AS vendor_bayesian_rating,
        DENSE_RANK() OVER (
            PARTITION BY p.category_id
            ORDER BY SUM(p.weekly_gmv_proxy_toman) DESC
        ) AS category_rank
    FROM fact_products p
    JOIN dim_categories c ON p.category_id = c.category_id
    JOIN dim_vendors v ON p.vendor_name = v.vendor_name
    WHERE p.is_available = TRUE
    GROUP BY p.category_id, c.category_title, p.vendor_name, v.vendor_status_title
)
SELECT *
FROM vendor_cat_perf
WHERE category_rank <= 3
ORDER BY category_id, category_rank;

-- Query 4: Post-Load Data Integrity Check
SELECT
    COUNT(*) FILTER (WHERE price_toman <= 0) AS invalid_price_count,
    COUNT(*) FILTER (WHERE price_toman > primary_price_toman) AS inverted_discount_count,
    COUNT(*) FILTER (WHERE stock < 0) AS negative_stock_count,
    COUNT(*) - COUNT(DISTINCT product_id) AS duplicate_pk_count
FROM fact_products;
