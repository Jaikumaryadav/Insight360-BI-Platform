# Insight360 Executive BI Platform
## Phase 5 — Power BI Data Model Architecture & DAX Measure Library

**Project:** Meridian Retail Group — Insight360 Executive Intelligence Platform
**Phase:** 5 — Business Intelligence & Power BI Strategy
**Source:** PostgreSQL `insight360` schema (Phase 4, verified)

---

## Table of Contents

1. [Data Model Architecture](#1-data-model-architecture)
2. [Table & Column Configuration](#2-table--column-configuration)
3. [Date Table Configuration](#3-date-table-configuration)
4. [DAX Measure Library](#4-dax-measure-library)
   - A. Sales & Revenue Metrics
   - B. Returns Analytics
   - C. Supply Chain & Inventory Metrics
   - D. Staffing & Productivity Metrics
5. [Display Folder Organization](#5-display-folder-organization)
6. [Implementation Notes](#6-implementation-notes)

---

## 1. Data Model Architecture

### 1.1 Star Schema Overview

Insight360 uses a classic **star schema** with four conformed dimensions shared across four fact tables. All relationships are **single-direction (filter flows from dimension → fact)**, **1-to-many**, and **active** unless otherwise noted.

```
                         ┌───────────────┐
                         │   dim_date    │
                         │  (Date Table) │
                         └───────┬───────┘
                                 │ 1
                 ┌───────────────┼───────────────┬───────────────┐
                 │ *             │ *              │ *             │ *
        ┌────────▼──────┐ ┌──────▼───────┐ ┌──────▼─────────────┐ ┌▼──────────────┐
        │  fact_sales    │ │ fact_returns │ │ fact_inventory_    │ │ fact_staffing │
        │                │ │              │ │ snapshot            │ │                │
        └───┬───┬───┬────┘ └───┬───┬──────┘ └───┬───┬─────────────┘ └───┬────────────┘
            │   │   │          │   │            │   │                   │
            │   │   │          │   │            │   │                   │
      ┌─────▼┐ ┌▼───┐ ┌▼───────▼┐ ┌▼──────┐ ┌───▼───┐                ┌──▼──────┐
      │store │ │prod│ │customer │ │store  │ │store  │                │ store   │
      │ key  │ │key │ │  key    │ │/prod  │ │/prod  │                │  key    │
      └──────┘ └────┘ └─────────┘ └───────┘ └───────┘                └─────────┘

  dim_store   ──1:*──▶ fact_sales, fact_returns, fact_inventory_snapshot, fact_staffing
  dim_product ──1:*──▶ fact_sales, fact_returns, fact_inventory_snapshot
  dim_customer──1:*──▶ fact_sales
  dim_date    ──1:*──▶ fact_sales, fact_returns, fact_inventory_snapshot, fact_staffing
```

### 1.2 Relationship Table

| From (One side)     | To (Many side)             | Cardinality | Cross-Filter Direction | Active |
|----------------------|------------------------------|-------------|--------------------------|--------|
| `dim_date[date_key]`     | `fact_sales[date_key]`             | 1:*         | Single (Date → Fact)     | Yes    |
| `dim_date[date_key]`     | `fact_returns[date_key]`           | 1:*         | Single (Date → Fact)     | Yes    |
| `dim_date[date_key]`     | `fact_inventory_snapshot[date_key]` | 1:*        | Single (Date → Fact)     | Yes    |
| `dim_date[date_key]`     | `fact_staffing[date_key]`          | 1:*         | Single (Date → Fact)     | Yes    |
| `dim_store[store_key]`    | `fact_sales[store_key]`            | 1:*         | Single (Store → Fact)    | Yes    |
| `dim_store[store_key]`    | `fact_returns[store_key]`          | 1:*         | Single (Store → Fact)    | Yes    |
| `dim_store[store_key]`    | `fact_inventory_snapshot[store_key]`| 1:*        | Single (Store → Fact)    | Yes    |
| `dim_store[store_key]`    | `fact_staffing[store_key]`         | 1:*         | Single (Store → Fact)    | Yes    |
| `dim_product[product_key]` | `fact_sales[product_key]`          | 1:*         | Single (Product → Fact)  | Yes    |
| `dim_product[product_key]` | `fact_returns[product_key]`        | 1:*         | Single (Product → Fact)  | Yes    |
| `dim_product[product_key]` | `fact_inventory_snapshot[product_key]`| 1:*      | Single (Product → Fact)  | Yes    |
| `dim_customer[customer_key]`| `fact_sales[customer_key]`         | 1:*         | Single (Customer → Fact) | Yes    |
| `fact_sales[sales_id]`   | `fact_returns[original_sales_id]`  | 1:*         | **Inactive** (see note)  | No     |

> **Note on `fact_sales` ↔ `fact_returns`:** A physical relationship on `sales_id` ↔ `original_sales_id` is created but left **inactive** to avoid a second filter path onto `fact_sales` (which already shares `dim_date`, `dim_store`, `dim_product` with `fact_returns`). Activate on demand using `USERELATIONSHIP()` inside specific "returns-linked-to-original-sale" measures if required (e.g., same-transaction return analysis). Standard return-rate measures rely on the shared dimension relationships instead, avoiding ambiguous multi-path filtering.

### 1.3 Design Principles

- **No fact-to-fact active relationships** — all cross-fact analysis (e.g., return rate = returns ÷ sales) is done via shared dimensions and `CALCULATE`/`DIVIDE`, not physical joins.
- **Single-direction filtering only** — bidirectional filters are avoided to prevent ambiguous filter propagation and to preserve query performance at fact-table scale (~4.2M rows in `fact_sales`).
- **Surrogate keys as text** — `store_key`, `product_key`, `customer_key` are `VARCHAR` surrogate keys; hidden from report canvas but retained for relationships and drill-through.
- **Hide foreign keys on fact tables** — all FK columns (`date_key`, `store_key`, `product_key`, `customer_key`) are hidden from the Report view; users browse via dimension tables/hierarchies only.

---

## 2. Table & Column Configuration

### 2.1 `dim_date`

| Column | Data Type | Format String | Notes |
|---|---|---|---|
| `date_key` | Date | `yyyy-mm-dd` | Sort key for table; marked as Date Table column |
| `year` | Whole Number | `0` | |
| `quarter` | Whole Number | `"Q"0` | |
| `month` | Whole Number | `0` | Hidden; used as sort-by for `month_name` |
| `month_name` | Text | — | **Sort by Column = `month`** |
| `week_number` | Whole Number | `0` | |
| `day_of_week` | Whole Number | `0` | Hidden; used as sort-by for `day_name` |
| `day_name` | Text | — | **Sort by Column = `day_of_week`** |
| `is_weekend` | Boolean (True/False) | — | |
| `is_holiday` | Boolean (True/False) | — | |
| `is_festive_period` | Boolean (True/False) | — | |

Additional calculated columns recommended:

```dax
dim_date[Year-Month] = FORMAT(dim_date[date_key], "MMM YYYY")
dim_date[YearMonthSort] = dim_date[year] * 100 + dim_date[month]   -- sort-by for Year-Month
dim_date[Fiscal Quarter] = "FY" & dim_date[year] & " Q" & dim_date[quarter]
```
- `Year-Month` → **Sort by Column = `YearMonthSort`**

### 2.2 `dim_store`

| Column | Data Type | Format String | Notes |
|---|---|---|---|
| `store_key` | Text | — | Hidden (relationship key) |
| `store_name` | Text | — | |
| `store_format` | Text | — | |
| `region` | Text | — | |
| `city` | Text | — | |
| `state` | Text | — | |
| `country` | Text | — | |
| `square_feet` | Whole Number | `#,##0` | |
| `opening_date` | Date | `yyyy-mm-dd` | |
| `manager_name` | Text | — | |
| `is_active` | Boolean (True/False) | — | Default slicer filter: `TRUE` |

Recommended hierarchy: **Geography** = `country` → `region` → `state` → `city` → `store_name`

### 2.3 `dim_product`

| Column | Data Type | Format String | Notes |
|---|---|---|---|
| `product_key` | Text | — | Hidden (relationship key) |
| `sku` | Text | — | |
| `product_name` | Text | — | |
| `division` | Text | — | |
| `category` | Text | — | |
| `subcategory` | Text | — | |
| `brand` | Text | — | |
| `base_price` | Decimal Number | `#,##0.00` (currency ₹) | |
| `unit_cost` | Decimal Number | `#,##0.00` (currency ₹) | |
| `is_active` | Boolean (True/False) | — | |

Recommended hierarchy: **Product** = `division` → `category` → `subcategory` → `product_name`

### 2.4 `dim_customer`

| Column | Data Type | Format String | Notes |
|---|---|---|---|
| `customer_key` | Text | — | Hidden (relationship key) |
| `first_name` / `last_name` | Text | — | Concatenate into `Full Name` calc column |
| `email` | Text | — | Hidden (PII — mask/exclude from report visuals) |
| `gender` | Text | — | |
| `age` | Whole Number | `0` | Bucket via calculated column `Age Band` |
| `city` / `state` / `country` | Text | — | |
| `customer_segment` | Text | — | |
| `signup_date` | Date | `yyyy-mm-dd` | |
| `loyalty_tier` | Text | — | Sort-by a calculated `Loyalty Tier Rank` column |

```dax
dim_customer[Full Name] = dim_customer[first_name] & " " & dim_customer[last_name]
dim_customer[Age Band] =
    SWITCH(
        TRUE(),
        dim_customer[age] < 25, "18-24",
        dim_customer[age] < 35, "25-34",
        dim_customer[age] < 45, "35-44",
        dim_customer[age] < 55, "45-54",
        dim_customer[age] >= 55, "55+",
        "Unknown"
    )
```

### 2.5 Fact Tables — Key Column Configuration

| Table | Column | Data Type | Format String |
|---|---|---|---|
| `fact_sales` | `quantity` | Whole Number | `#,##0` |
| `fact_sales` | `unit_price`, `discount_amount`, `net_sales` | Decimal Number | `#,##0.00` |
| `fact_sales` | `payment_method`, `channel` | Text | — |
| `fact_sales` | `return_flag` | Boolean | — |
| `fact_returns` | `quantity_returned` | Whole Number | `#,##0` |
| `fact_returns` | `refund_amount` | Decimal Number | `#,##0.00` |
| `fact_returns` | `is_restocked` | Boolean | — |
| `fact_inventory_snapshot` | `opening_stock`, `sales_qty`, `replenished_qty`, `closing_stock`, `safety_stock` | Whole Number | `#,##0` |
| `fact_inventory_snapshot` | `is_out_of_stock` | Boolean | — |
| `fact_inventory_snapshot` | `stockout_duration_days` | Whole Number | `0` |
| `fact_staffing` | `allocated_headcount`, `actual_headcount` | Whole Number | `#,##0` |
| `fact_staffing` | `scheduled_hours`, `actual_hours`, `overtime_hours` | Decimal Number | `#,##0.0` |
| `fact_staffing` | `labor_cost` | Decimal Number | `#,##0.00` (currency ₹) |
| `fact_staffing` | `sales_per_labor_hour` | Decimal Number | `#,##0.00` |

All fact-table FK columns (`date_key`, `store_key`, `product_key`, `customer_key`, `original_sales_id`) and technical ID columns (`sales_id`, `return_id`, `snapshot_id`, `staffing_id`) are set to **Hidden in Report View**.

---

## 3. Date Table Configuration

1. Select `dim_date` in Model view.
2. **Table Tools → Mark as Date Table → Mark as Date Table**, set the date column to `date_key`.
3. Confirm `date_key` is contiguous (no gaps) and fully covers the min/max dates across all fact tables — required for accurate Time Intelligence functions.
4. Set `dim_date[date_key]` sort order as the table's default sort (ascending).
5. Disable Power BI's built-in **Auto Date/Time** option (File → Options → Data Load → uncheck "Auto date/time for new files") so all time intelligence resolves through `dim_date` only.

---

## 4. DAX Measure Library

> All measures are written against the star schema defined above. `DIVIDE()` is used throughout instead of `/` to gracefully handle divide-by-zero as `BLANK()`. Time-intelligence measures assume `dim_date` is marked as the official Date Table (Section 3).

### A. Sales & Revenue Metrics
*(Display Folder: `Sales & Revenue`)*

```dax
[Total Gross Sales] =
SUMX(
    fact_sales,
    fact_sales[quantity] * fact_sales[unit_price]
)
```

```dax
[Total Discount Amount] =
SUM(fact_sales[discount_amount])
```

```dax
[Net Sales] =
SUM(fact_sales[net_sales])
```

```dax
[Sales Quantity] =
SUM(fact_sales[quantity])
```

```dax
[Average Order Value (AOV)] =
DIVIDE(
    [Net Sales],
    DISTINCTCOUNT(fact_sales[sales_id]),
    BLANK()
)
```

```dax
[Net Sales YTD] =
CALCULATE(
    [Net Sales],
    DATESYTD(dim_date[date_key])
)
```

```dax
[Net Sales PY] =
CALCULATE(
    [Net Sales],
    SAMEPERIODLASTYEAR(dim_date[date_key])
)
```

```dax
[Net Sales YoY Growth %] =
VAR CurrentNetSales = [Net Sales]
VAR PriorYearNetSales = [Net Sales PY]
RETURN
    DIVIDE(
        CurrentNetSales - PriorYearNetSales,
        PriorYearNetSales,
        BLANK()
    )
```

---

### B. Returns Analytics
*(Display Folder: `Returns Analytics`)*

```dax
[Total Returned Quantity] =
SUM(fact_returns[quantity_returned])
```

```dax
[Total Refund Amount] =
SUM(fact_returns[refund_amount])
```

```dax
[Return Rate %] =
DIVIDE(
    [Total Returned Quantity],
    [Sales Quantity],
    BLANK()
)
```

```dax
[Online Return Rate %] =
VAR OnlineReturnedQty =
    CALCULATE(
        [Total Returned Quantity],
        TREATAS( VALUES( fact_sales[channel] ), fact_returns[channel] ) -- see note below
    )
RETURN
    DIVIDE(
        CALCULATE( [Total Returned Quantity], fact_sales[channel] = "Online" ),
        CALCULATE( [Sales Quantity], fact_sales[channel] = "Online" ),
        BLANK()
    )
```

```dax
[Store Return Rate %] =
DIVIDE(
    CALCULATE( [Total Returned Quantity], fact_sales[channel] = "Store" ),
    CALCULATE( [Sales Quantity], fact_sales[channel] = "Store" ),
    BLANK()
)
```

> **Implementation note on Online/Store Return Rate:** `fact_returns` does not carry its own `channel` column — it inherits channel context from the originating sale. Two supported approaches:
> 1. **Preferred (model change):** add `channel` to `fact_returns` during ETL (denormalized from `fact_sales` at load time) so channel-filtered `CALCULATE` works directly against `fact_returns[channel]`.
> 2. **No model change:** activate the inactive `fact_sales`↔`fact_returns` relationship with `USERELATIONSHIP` inside the measure to pull returns through the matching sale's channel:
> ```dax
> [Online Return Rate %] =
> VAR OnlineReturnedQty =
>     CALCULATE(
>         [Total Returned Quantity],
>         USERELATIONSHIP( fact_sales[sales_id], fact_returns[original_sales_id] ),
>         fact_sales[channel] = "Online"
>     )
> VAR OnlineSoldQty =
>     CALCULATE( [Sales Quantity], fact_sales[channel] = "Online" )
> RETURN
>     DIVIDE( OnlineReturnedQty, OnlineSoldQty, BLANK() )
> ```
> Option 1 (denormalized `channel` on `fact_returns`) is the recommended production approach for performance at scale; the measures above assume it.

---

### C. Supply Chain & Inventory Metrics
*(Display Folder: `Supply Chain & Inventory`)*

```dax
[Average Closing Stock] =
AVERAGE(fact_inventory_snapshot[closing_stock])
```

```dax
[Total Snapshots] =
COUNTROWS(fact_inventory_snapshot)
```

```dax
[Stockout Snapshots] =
CALCULATE(
    COUNTROWS(fact_inventory_snapshot),
    fact_inventory_snapshot[is_out_of_stock] = TRUE
)
```

```dax
[Stockout Rate %] =
DIVIDE(
    [Stockout Snapshots],
    [Total Snapshots],
    BLANK()
)
```

```dax
[East Region Stockout Rate %] =
CALCULATE(
    [Stockout Rate %],
    dim_store[region] = "East"
)
```

```dax
[Stockout Duration Days] =
SUM(fact_inventory_snapshot[stockout_duration_days])
```

```dax
[Average Stockout Duration Days] =
AVERAGE(fact_inventory_snapshot[stockout_duration_days])
```

---

### D. Staffing & Productivity Metrics
*(Display Folder: `Staffing & Productivity`)*

```dax
[Total Labor Hours] =
SUM(fact_staffing[actual_hours])
```

```dax
[Total Scheduled Hours] =
SUM(fact_staffing[scheduled_hours])
```

```dax
[Total Overtime Hours] =
SUM(fact_staffing[overtime_hours])
```

```dax
[Total Labor Cost] =
SUM(fact_staffing[labor_cost])
```

```dax
[Sales per Labor Hour (SPLH)] =
DIVIDE(
    [Net Sales],
    [Total Labor Hours],
    BLANK()
)
```

```dax
[Labor Cost as % of Net Sales] =
DIVIDE(
    [Total Labor Cost],
    [Net Sales],
    BLANK()
)
```

```dax
[Headcount Variance] =
SUM(fact_staffing[actual_headcount]) - SUM(fact_staffing[allocated_headcount])
```

---

## 5. Display Folder Organization

Configure in Power BI Desktop's **Model view → Properties pane → Display folder** for each measure:

```
Insight360 Measures
├── Sales & Revenue
│   ├── Total Gross Sales
│   ├── Total Discount Amount
│   ├── Net Sales
│   ├── Sales Quantity
│   ├── Average Order Value (AOV)
│   ├── Net Sales YTD
│   ├── Net Sales PY
│   └── Net Sales YoY Growth %
├── Returns Analytics
│   ├── Total Returned Quantity
│   ├── Total Refund Amount
│   ├── Return Rate %
│   ├── Online Return Rate %
│   └── Store Return Rate %
├── Supply Chain & Inventory
│   ├── Average Closing Stock
│   ├── Total Snapshots
│   ├── Stockout Snapshots
│   ├── Stockout Rate %
│   ├── East Region Stockout Rate %
│   ├── Stockout Duration Days
│   └── Average Stockout Duration Days
└── Staffing & Productivity
    ├── Total Labor Hours
    ├── Total Scheduled Hours
    ├── Total Overtime Hours
    ├── Total Labor Cost
    ├── Sales per Labor Hour (SPLH)
    ├── Labor Cost as % of Net Sales
    └── Headcount Variance
```

Best practice: create a hidden, dedicated **`_Measures`** table (no columns, disconnected) to house all measures rather than scattering them across fact tables — keeps the Fields pane clean for business users.

---

## 6. Implementation Notes

- **Performance:** with `fact_sales` at ~4.2M rows, prefer `SUM`/`SUMX` over `SUMX` on iterated calculated columns; push heavy transformations (e.g., `net_sales`) upstream into PostgreSQL/ETL rather than Power Query where possible, since `net_sales` is already materialized in the fact table.
- **Storage mode:** Import mode recommended for Phase 5 given dataset size fits comfortably in Power BI Premium/Pro capacity; revisit DirectQuery or Composite mode only if near-real-time inventory refresh becomes a requirement.
- **Row-Level Security (future phase):** `dim_store[region]` and `dim_store[store_key]` are natural RLS anchor columns for regional manager access scoping.
- **Refresh cadence:** align scheduled refresh with the `load_data.py` batch load cadence from Phase 4 to avoid partial-day data during business hours.
- **Currency:** all monetary format strings assume INR (₹); adjust format string locale codes if multi-currency reporting is introduced later.
- **Validation crosswalk:** every measure here should reconcile against the corresponding aggregate in `validate_sql.sql` (Section 3 business metrics) during Power BI model QA — e.g., `[Net Sales]` total should match `total_net_sales` from the SQL audit, `[Stockout Rate %]` by region should match the SQL region-level stockout query.
