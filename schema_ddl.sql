-- =====================================================================
-- Insight360 Executive BI Platform
-- Phase 4 — Data Engineering: PostgreSQL Schema DDL
-- Meridian Retail Group | Star Schema (4 Dimensions + 4 Facts)
-- =====================================================================

-- ---------------------------------------------------------------------
-- SCHEMA
-- ---------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS insight360;
SET search_path TO insight360, public;

-- ---------------------------------------------------------------------
-- DROP TABLES (reverse FK dependency order)
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS insight360.fact_staffing CASCADE;
DROP TABLE IF EXISTS insight360.fact_inventory_snapshot CASCADE;
DROP TABLE IF EXISTS insight360.fact_returns CASCADE;
DROP TABLE IF EXISTS insight360.fact_sales CASCADE;
DROP TABLE IF EXISTS insight360.dim_customer CASCADE;
DROP TABLE IF EXISTS insight360.dim_product CASCADE;
DROP TABLE IF EXISTS insight360.dim_store CASCADE;
DROP TABLE IF EXISTS insight360.dim_date CASCADE;

-- =====================================================================
-- DIMENSION TABLES
-- =====================================================================

-- ---------------------------------------------------------------------
-- dim_date
-- ---------------------------------------------------------------------
CREATE TABLE insight360.dim_date (
    date_key            DATE            NOT NULL,
    year                SMALLINT        NOT NULL,
    quarter             SMALLINT        NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    month               SMALLINT        NOT NULL CHECK (month BETWEEN 1 AND 12),
    month_name          VARCHAR(20)     NOT NULL,
    week_number         SMALLINT        NOT NULL CHECK (week_number BETWEEN 1 AND 53),
    day_of_week         SMALLINT        NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
    day_name            VARCHAR(20)     NOT NULL,
    is_weekend          BOOLEAN         NOT NULL DEFAULT FALSE,
    is_holiday          BOOLEAN         NOT NULL DEFAULT FALSE,
    is_festive_period    BOOLEAN         NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_dim_date PRIMARY KEY (date_key)
);

-- ---------------------------------------------------------------------
-- dim_store
-- ---------------------------------------------------------------------
CREATE TABLE insight360.dim_store (
    store_key           VARCHAR(20)     NOT NULL,
    store_name          VARCHAR(150)    NOT NULL,
    store_format        VARCHAR(50),
    region              VARCHAR(50),
    city                VARCHAR(100),
    state               VARCHAR(100),
    country             VARCHAR(100),
    square_feet         INTEGER         CHECK (square_feet >= 0),
    opening_date         DATE,
    manager_name         VARCHAR(150),
    is_active            BOOLEAN         NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_dim_store PRIMARY KEY (store_key)
);

-- ---------------------------------------------------------------------
-- dim_product
-- ---------------------------------------------------------------------
CREATE TABLE insight360.dim_product (
    product_key          VARCHAR(20)     NOT NULL,
    sku                  VARCHAR(50)     NOT NULL,
    product_name          VARCHAR(200)    NOT NULL,
    division             VARCHAR(50),
    category             VARCHAR(100),
    subcategory           VARCHAR(100),
    brand                VARCHAR(100),
    base_price            NUMERIC(12,2)   NOT NULL CHECK (base_price >= 0),
    unit_cost             NUMERIC(12,2)   NOT NULL CHECK (unit_cost >= 0),
    is_active             BOOLEAN         NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_dim_product PRIMARY KEY (product_key),
    CONSTRAINT uq_dim_product_sku UNIQUE (sku)
);

-- ---------------------------------------------------------------------
-- dim_customer
-- ---------------------------------------------------------------------
CREATE TABLE insight360.dim_customer (
    customer_key          VARCHAR(20)     NOT NULL,
    first_name            VARCHAR(100),
    last_name             VARCHAR(100),
    email                 VARCHAR(150),
    gender                VARCHAR(20),
    age                   SMALLINT        CHECK (age BETWEEN 0 AND 120),
    city                  VARCHAR(100),
    state                 VARCHAR(100),
    country               VARCHAR(100),
    customer_segment       VARCHAR(50),
    signup_date            DATE,
    loyalty_tier           VARCHAR(30),
    CONSTRAINT pk_dim_customer PRIMARY KEY (customer_key)
);

-- =====================================================================
-- FACT TABLES
-- =====================================================================

-- ---------------------------------------------------------------------
-- fact_sales
-- ---------------------------------------------------------------------
CREATE TABLE insight360.fact_sales (
    sales_id              VARCHAR(30)     NOT NULL,
    date_key              DATE            NOT NULL,
    store_key              VARCHAR(20)     NOT NULL,
    product_key            VARCHAR(20)     NOT NULL,
    customer_key            VARCHAR(20)     NOT NULL,
    quantity               INTEGER         NOT NULL CHECK (quantity >= 0),
    unit_price              NUMERIC(12,2)   NOT NULL CHECK (unit_price >= 0),
    discount_amount          NUMERIC(12,2)   NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
    net_sales               NUMERIC(14,2)   NOT NULL CHECK (net_sales >= 0),
    payment_method            VARCHAR(50),
    channel                 VARCHAR(30),
    return_flag              BOOLEAN         NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_fact_sales PRIMARY KEY (sales_id),
    CONSTRAINT fk_fact_sales_date
        FOREIGN KEY (date_key) REFERENCES insight360.dim_date (date_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_fact_sales_store
        FOREIGN KEY (store_key) REFERENCES insight360.dim_store (store_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_fact_sales_product
        FOREIGN KEY (product_key) REFERENCES insight360.dim_product (product_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_fact_sales_customer
        FOREIGN KEY (customer_key) REFERENCES insight360.dim_customer (customer_key)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ---------------------------------------------------------------------
-- fact_returns
-- ---------------------------------------------------------------------
CREATE TABLE insight360.fact_returns (
    return_id                VARCHAR(30)     NOT NULL,
    original_sales_id          VARCHAR(30)     NOT NULL,
    date_key                 DATE            NOT NULL,
    store_key                  VARCHAR(20)     NOT NULL,
    product_key                VARCHAR(20)     NOT NULL,
    quantity_returned            INTEGER         NOT NULL CHECK (quantity_returned >= 0),
    return_reason               VARCHAR(150),
    refund_amount               NUMERIC(12,2)   NOT NULL CHECK (refund_amount >= 0),
    is_restocked                BOOLEAN         NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_fact_returns PRIMARY KEY (return_id),
    CONSTRAINT fk_fact_returns_sales
        FOREIGN KEY (original_sales_id) REFERENCES insight360.fact_sales (sales_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_fact_returns_date
        FOREIGN KEY (date_key) REFERENCES insight360.dim_date (date_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_fact_returns_store
        FOREIGN KEY (store_key) REFERENCES insight360.dim_store (store_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_fact_returns_product
        FOREIGN KEY (product_key) REFERENCES insight360.dim_product (product_key)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ---------------------------------------------------------------------
-- fact_inventory_snapshot
-- ---------------------------------------------------------------------
CREATE TABLE insight360.fact_inventory_snapshot (
    snapshot_id                VARCHAR(30)     NOT NULL,
    date_key                   DATE            NOT NULL,
    store_key                    VARCHAR(20)     NOT NULL,
    product_key                  VARCHAR(20)     NOT NULL,
    opening_stock                 INTEGER         NOT NULL CHECK (opening_stock >= 0),
    sales_qty                    INTEGER         NOT NULL DEFAULT 0 CHECK (sales_qty >= 0),
    replenished_qty                INTEGER         NOT NULL DEFAULT 0 CHECK (replenished_qty >= 0),
    closing_stock                 INTEGER         NOT NULL CHECK (closing_stock >= 0),
    safety_stock                  INTEGER         NOT NULL DEFAULT 0 CHECK (safety_stock >= 0),
    is_out_of_stock                 BOOLEAN         NOT NULL DEFAULT FALSE,
    stockout_duration_days             SMALLINT        NOT NULL DEFAULT 0 CHECK (stockout_duration_days >= 0),
    CONSTRAINT pk_fact_inventory_snapshot PRIMARY KEY (snapshot_id),
    CONSTRAINT fk_fact_inventory_date
        FOREIGN KEY (date_key) REFERENCES insight360.dim_date (date_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_fact_inventory_store
        FOREIGN KEY (store_key) REFERENCES insight360.dim_store (store_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_fact_inventory_product
        FOREIGN KEY (product_key) REFERENCES insight360.dim_product (product_key)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ---------------------------------------------------------------------
-- fact_staffing
-- ---------------------------------------------------------------------
CREATE TABLE insight360.fact_staffing (
    staffing_id                VARCHAR(30)     NOT NULL,
    date_key                   DATE            NOT NULL,
    store_key                    VARCHAR(20)     NOT NULL,
    allocated_headcount             SMALLINT        NOT NULL CHECK (allocated_headcount >= 0),
    actual_headcount                SMALLINT        NOT NULL CHECK (actual_headcount >= 0),
    scheduled_hours                NUMERIC(8,2)    NOT NULL CHECK (scheduled_hours >= 0),
    actual_hours                  NUMERIC(8,2)    NOT NULL CHECK (actual_hours >= 0),
    overtime_hours                 NUMERIC(8,2)    NOT NULL DEFAULT 0 CHECK (overtime_hours >= 0),
    labor_cost                    NUMERIC(14,2)   NOT NULL CHECK (labor_cost >= 0),
    sales_per_labor_hour              NUMERIC(12,2),
    CONSTRAINT pk_fact_staffing PRIMARY KEY (staffing_id),
    CONSTRAINT fk_fact_staffing_date
        FOREIGN KEY (date_key) REFERENCES insight360.dim_date (date_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_fact_staffing_store
        FOREIGN KEY (store_key) REFERENCES insight360.dim_store (store_key)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- =====================================================================
-- INDEXES
-- =====================================================================

-- dim_store
CREATE INDEX idx_dim_store_region ON insight360.dim_store (region);
CREATE INDEX idx_dim_store_is_active ON insight360.dim_store (is_active);

-- dim_product
CREATE INDEX idx_dim_product_category ON insight360.dim_product (category);
CREATE INDEX idx_dim_product_division ON insight360.dim_product (division);
CREATE INDEX idx_dim_product_is_active ON insight360.dim_product (is_active);

-- dim_customer
CREATE INDEX idx_dim_customer_segment ON insight360.dim_customer (customer_segment);
CREATE INDEX idx_dim_customer_loyalty_tier ON insight360.dim_customer (loyalty_tier);

-- fact_sales
CREATE INDEX idx_fact_sales_date_key ON insight360.fact_sales (date_key);
CREATE INDEX idx_fact_sales_store_key ON insight360.fact_sales (store_key);
CREATE INDEX idx_fact_sales_product_key ON insight360.fact_sales (product_key);
CREATE INDEX idx_fact_sales_customer_key ON insight360.fact_sales (customer_key);
CREATE INDEX idx_fact_sales_channel ON insight360.fact_sales (channel);
CREATE INDEX idx_fact_sales_store_date ON insight360.fact_sales (store_key, date_key);
CREATE INDEX idx_fact_sales_product_date ON insight360.fact_sales (product_key, date_key);

-- fact_returns
CREATE INDEX idx_fact_returns_date_key ON insight360.fact_returns (date_key);
CREATE INDEX idx_fact_returns_store_key ON insight360.fact_returns (store_key);
CREATE INDEX idx_fact_returns_product_key ON insight360.fact_returns (product_key);
CREATE INDEX idx_fact_returns_original_sales_id ON insight360.fact_returns (original_sales_id);

-- fact_inventory_snapshot
CREATE INDEX idx_fact_inventory_date_key ON insight360.fact_inventory_snapshot (date_key);
CREATE INDEX idx_fact_inventory_store_key ON insight360.fact_inventory_snapshot (store_key);
CREATE INDEX idx_fact_inventory_product_key ON insight360.fact_inventory_snapshot (product_key);
CREATE INDEX idx_fact_inventory_out_of_stock ON insight360.fact_inventory_snapshot (is_out_of_stock);
CREATE INDEX idx_fact_inventory_store_product ON insight360.fact_inventory_snapshot (store_key, product_key);

-- fact_staffing
CREATE INDEX idx_fact_staffing_date_key ON insight360.fact_staffing (date_key);
CREATE INDEX idx_fact_staffing_store_key ON insight360.fact_staffing (store_key);

-- =====================================================================
-- END OF SCRIPT
-- =====================================================================
