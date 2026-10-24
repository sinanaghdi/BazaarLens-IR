-- PostgreSQL 15+ Schema for BazaarLens-IR (BaSalam Marketplace Analytics)
-- All monetary columns ending in `_rial` store raw integers; `_toman` store converted numeric values.

DROP TABLE IF EXISTS fact_reviews CASCADE;
DROP TABLE IF EXISTS fact_products CASCADE;
DROP TABLE IF EXISTS dim_vendors CASCADE;
DROP TABLE IF EXISTS dim_categories CASCADE;

CREATE TABLE dim_categories (
    category_id INTEGER PRIMARY KEY,
    category_title VARCHAR(255) NOT NULL
);

CREATE TABLE dim_vendors (
    vendor_name VARCHAR(120) PRIMARY KEY,
    vendor_score NUMERIC(3, 2) CHECK (vendor_score BETWEEN 0.00 AND 5.00),
    vendor_status_title VARCHAR(100) NOT NULL
);

CREATE TABLE fact_products (
    product_id VARCHAR(64) PRIMARY KEY,
    product_name TEXT NOT NULL,
    category_id INTEGER NOT NULL REFERENCES dim_categories(category_id),
    vendor_name VARCHAR(120) NOT NULL REFERENCES dim_vendors(vendor_name),
    price_rial BIGINT NOT NULL CHECK (price_rial > 0),
    primary_price_rial BIGINT NOT NULL CHECK (primary_price_rial >= price_rial),
    price_toman NUMERIC(14, 0) NOT NULL CHECK (price_toman > 0),
    primary_price_toman NUMERIC(14, 0) NOT NULL CHECK (primary_price_toman >= price_toman),
    discount_pct NUMERIC(5, 2) NOT NULL DEFAULT 0.00 CHECK (discount_pct BETWEEN 0.00 AND 100.00),
    stock INTEGER NOT NULL CHECK (stock >= 0),
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    is_free_shipping BOOLEAN NOT NULL DEFAULT FALSE,
    preparation_days INTEGER NOT NULL CHECK (preparation_days >= 0),
    weight_grams INTEGER CHECK (weight_grams > 0),
    rating_average NUMERIC(3, 2) CHECK (rating_average BETWEEN 1.00 AND 5.00),
    rating_count INTEGER NOT NULL DEFAULT 0 CHECK (rating_count >= 0),
    bayesian_rating NUMERIC(4, 3),
    sales_count_week INTEGER NOT NULL DEFAULT 0 CHECK (sales_count_week >= 0),
    weekly_gmv_proxy_toman NUMERIC(16, 0) NOT NULL DEFAULT 0,
    data_origin VARCHAR(32) NOT NULL DEFAULT 'real'
);

CREATE INDEX idx_fact_products_category ON fact_products(category_id);
CREATE INDEX idx_fact_products_vendor ON fact_products(vendor_name);
CREATE INDEX idx_fact_products_shipping ON fact_products(is_free_shipping, is_available);

CREATE TABLE fact_reviews (
    review_id VARCHAR(64) PRIMARY KEY,
    product_id VARCHAR(64) NOT NULL REFERENCES fact_products(product_id),
    created_at DATE NOT NULL,
    user_id_anon VARCHAR(64) NOT NULL,
    rating SMALLINT CHECK (rating BETWEEN 1 AND 5),
    like_count INTEGER NOT NULL DEFAULT 0,
    dislike_count INTEGER NOT NULL DEFAULT 0,
    review_text TEXT
);
