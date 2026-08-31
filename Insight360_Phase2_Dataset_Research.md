# Insight360 — Executive BI Platform for Retail
## Phase 2: Dataset Research & Selection
**Status:** Awaiting Approval | **Scope:** Research only — no Python, SQL, or Power BI performed in this phase

---

## Methodology

Ten publicly available, well-documented retail/e-commerce datasets were researched and evaluated against 17 criteria drawn directly from the Phase 1 Data Requirements (Section 4) and Data Dictionary (Section 5). Each dataset is scored out of 100, weighted toward the criteria that matter most for an **executive BI platform**: business realism, completeness across the sales→finance→customer→inventory chain, and suitability for star-schema modeling — not just raw row count or ML benchmark popularity (which is what most of these datasets were originally built for).

Every dataset below is real and independently verifiable at its source URL. No dataset was fabricated for this comparison.

---

## Dataset Profiles

### 1. UCI Online Retail II
- **Source:** UCI Machine Learning Repository (also mirrored on Kaggle) — https://archive.ics.uci.edu/dataset/502/online+retail+ii
- **License:** CC BY 4.0 — free to share and adapt with attribution.
- **Rows:** ~1.07M combined across two sheets <cite index="1-1">525,461 rows for 2009–2010 and 541,910 rows for 2010–2011</cite>, both at 8 columns per sheet.
- **Columns:** 8 (Invoice, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country).
- **Business realism:** High — <cite index="4-1">this is a real transactional dataset from a UK-based, non-store online retailer selling all-occasion gift-ware, with many wholesaler customers</cite>. Realistic messiness (cancellations, negative quantities) included.
- **Data completeness:** Moderate. Single business process only (sales); no cost/margin, no store dimension, no inventory, no marketing data.
- **Missing values:** Known issue — <cite index="5-1">Description has 1,454 missing values and CustomerID has 135,080 missing values out of 541,909 rows</cite>, requiring real cleaning decisions (a plus for demonstrating Python skills, a minus for out-of-the-box completeness).
- **Time span:** ~2 years (Dec 2009–Dec 2011).
- **Product information:** Thin — only a StockCode and free-text Description, no category hierarchy, no cost.
- **Customer information:** Thin — numeric CustomerID and Country only, no segment, no demographics.
- **Geographic information:** Country-level only (mostly UK, some EU).
- **Suitability for SQL:** High — flat, easy to load and query.
- **Suitability for Python:** High — the standard dataset for pandas cleaning tutorials.
- **Suitability for Power BI:** Moderate — good for a single sales-trend page, insufficient alone for a 6–7 page executive suite.
- **Suitability for executive dashboards:** Low-moderate — no margin, no regions, no store P&L.
- **Suitability for storytelling:** Moderate — RFM/customer segmentation stories work well; nothing at company/region/division level.
- **Suitability for ML:** High — this is the canonical dataset for RFM and customer segmentation modeling.
- **Suitability for forecasting:** Low — only 2 years, single business, no external demand drivers.
- **Score: 61/100**

### 2. Olist Brazilian E-Commerce Public Dataset
- **Source:** Kaggle — https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
- **License:** CC BY-NC-SA 4.0 (non-commercial, share-alike) as published by Olist.
- **Rows:** <cite index="10-1">~100,000 orders with product, customer, and review information</cite>, spread across <cite index="9-1">nine interconnected sub-datasets (customers, geolocation, order items, payments, reviews, orders, products, sellers, and category-name translation)</cite>.
- **Columns:** Varies per table; ~40+ columns in aggregate across the 9 tables.
- **Business realism:** High — <cite index="12-1">this is real, anonymized commercial data covering multiple marketplaces in Brazil, spanning order status, price, payment, freight performance, customer location, product attributes, and reviews</cite>.
- **Data completeness:** Strong relative to single-table datasets — genuinely multi-table/relational, closer to a real OLTP export than most Kaggle retail sets.
- **Missing values:** Low-moderate; well-documented and widely used in tutorials without major cleaning blockers.
- **Time span:** <cite index="9-1">2 years, October 2016 to September 2018</cite>.
- **Product information:** Category name + dimensions/weight; no cost/margin field (price and freight only).
- **Customer information:** <cite index="12-1">Customer ID and unique ID (to detect repurchase), plus location</cite> — decent for retention analysis, no demographics or loyalty tier.
- **Geographic information:** Strong — dedicated geolocation table mapping <cite index="12-1">Brazilian zip codes to lat/lng coordinates</cite>, excellent for map visuals.
- **Suitability for SQL:** High — genuinely relational, good for practicing joins across 9 tables.
- **Suitability for Python:** High — well-documented, popular for pandas/EDA projects.
- **Suitability for Power BI:** High — multi-table structure maps naturally to a star schema.
- **Suitability for executive dashboards:** Moderate — no cost/margin data limits financial-performance pages; marketplace model (multi-seller) doesn't map cleanly to a single-retailer P&L narrative.
- **Suitability for storytelling:** High — reviews + delivery performance + geography support a rich "customer experience" narrative.
- **Suitability for ML:** High — commonly used for delivery-delay prediction and review-score prediction.
- **Suitability for forecasting:** Moderate — 2 years is workable but order volume is modest for hierarchical forecasting.
- **Score: 68/100**

### 3. Instacart Market Basket Analysis
- **Source:** Kaggle competition — https://www.kaggle.com/c/instacart-market-basket-analysis
- **License:** Kaggle competition terms — <cite index="19-1">usable only for non-commercial purposes</cite>.
- **Rows:** <cite index="21-1">Orders file alone is ~3.4 million rows</cite>; <cite index="19-1">over 3 million grocery orders from more than 200,000 users</cite> in total across related files.
- **Columns:** Split across ~6 relational files (orders, products, aisles, departments, order_products).
- **Business realism:** High for behavioral/basket patterns, but **no price or revenue field exists anywhere in the dataset** — a critical gap for a BI/finance use case.
- **Data completeness:** Incomplete for BI purposes — excellent for basket composition, entirely absent on the financial side.
- **Missing values:** Low within what's provided.
- **Time span:** Order sequence per user, not true calendar-anchored multi-year history.
- **Product information:** Strong hierarchy (department → aisle → product), no price/cost.
- **Customer information:** Anonymized user IDs only, order sequences, no demographics, no loyalty tier, no location.
- **Geographic information:** None.
- **Suitability for SQL:** High — clean relational structure.
- **Suitability for Python:** High — a standard for association-rule mining (Apriori/FP-Growth).
- **Suitability for Power BI:** Low for exec dashboards — nothing to build a revenue or margin KPI from.
- **Suitability for executive dashboards:** Low — no financial layer at all.
- **Suitability for storytelling:** Moderate — strong for cross-sell/basket-affinity narrative only.
- **Suitability for ML:** Very high — this is a benchmark dataset for reorder-prediction and market-basket modeling.
- **Suitability for forecasting:** Low — not structured as a calendar time series with revenue.
- **Score: 47/100**

### 4. Rossmann Store Sales
- **Source:** Kaggle competition — https://www.kaggle.com/c/rossmann-store-sales
- **License:** Kaggle competition rules (research/educational use; redistribution restrictions apply).
- **Rows:** ~1.35M training rows (daily sales across 1,115 stores, ~2.5 years).
- **Columns:** ~9 core sales columns + ~10 store-attribute columns.
- **Business realism:** High — <cite index="29-1">Rossmann operates over 3,000 drug stores in 7 European countries</cite>, and <cite index="27-1">the dataset provides historical sales data for 1,115 Rossmann stores</cite> with promotions, competition distance, and holiday effects.
- **Data completeness:** Good for sales + store attributes; no customer-level data, no product SKU-level detail (store-day grain only), no explicit cost/margin field.
- **Missing values:** Some in competition-distance/open-since fields; manageable.
- **Time span:** ~2.5 years (2013–2015).
- **Product information:** None at SKU level — this dataset reports total store sales, not line-item detail.
- **Customer information:** Only a daily footfall-like "Customers" count per store, no individual customer records.
- **Geographic information:** <cite index="27-1">Store-state mapping is provided via a companion store_states file</cite>, German states only.
- **Suitability for SQL:** High — clean star-like structure (Sales fact + Store dimension).
- **Suitability for Python:** High — a canonical time-series/regression teaching dataset.
- **Suitability for Power BI:** Moderate — good for a Regional/Store Performance page, weak everywhere else.
- **Suitability for executive dashboards:** Moderate — store productivity and promotion-effect stories work well; no financial or customer depth.
- **Suitability for storytelling:** Moderate — strong "promotions drive sales" narrative, single category limits breadth.
- **Suitability for ML:** High — a standard regression/forecasting benchmark.
- **Suitability for forecasting:** High — <cite index="29-1">the original business problem is explicitly forecasting daily sales up to six weeks in advance</cite>.
- **Score: 64/100**

### 5. M5 Forecasting — Accuracy (Walmart)
- **Source:** Kaggle competition (hosted with Walmart & the Makridakis Forecasting Competition) — https://www.kaggle.com/competitions/m5-forecasting-accuracy
- **License:** Kaggle competition terms.
- **Rows:** <cite index="40-1">Sales data for 10 stores, each with 30,490 products, from 2011-01-29 to 2016-06-19</cite> — the wide-format sales table alone represents ~59M cell-level daily observations when unpivoted.
- **Columns:** 3 core files — <cite index="39-1">calendar (dates, events, SNAP flags), sell_prices (price by store/date), and sales_train (daily unit sales by item/store)</cite>.
- **Business realism:** High — <cite index="38-1">real hierarchical Walmart data across California, Texas, and Wisconsin, with products classified into categories and departments</cite>.
- **Data completeness:** Strong for demand/pricing, but unit-sales only — no explicit revenue, margin, or customer field.
- **Missing values:** Minimal in core sales; some nulls in event/holiday fields by design.
- **Time span:** <cite index="42-1">~5.4 years of daily history</cite> — the longest and most forecast-ready span in this comparison.
- **Product information:** <cite index="38-1">3,049 products across 3 categories and 7 departments</cite> — solid hierarchy depth.
- **Customer information:** None — no customer-level records at all.
- **Geographic information:** State-level only (CA/TX/WI), no true store address/region depth.
- **Suitability for SQL:** Moderate — very wide native format requires unpivoting before relational use.
- **Suitability for Python:** High — huge community of notebooks and tutorials.
- **Suitability for Power BI:** Moderate — large volume (Import Mode performance risk) with no financial or customer layer.
- **Suitability for executive dashboards:** Low-moderate — excellent for an Inventory/Forecast page, unusable for Finance or Customer pages.
- **Suitability for storytelling:** Moderate — strong seasonality/event narrative (SNAP benefits, holidays).
- **Suitability for ML:** Very high — the gold-standard hierarchical forecasting benchmark.
- **Suitability for forecasting:** Very high — purpose-built for this exact task.
- **Score: 70/100**

### 6. Superstore Sample Sales Dataset
- **Source:** Multiple Kaggle mirrors of the original Tableau sample dataset (e.g., https://www.kaggle.com/datasets/vivek468/superstore-dataset-final)
- **License:** Varies by mirror; the canonical Tableau-published version carries a Community Data License Agreement (Sharing).
- **Rows:** Varies by version — <cite index="46-1">one common version has 51,291 rows across 21 columns</cite>; the original Tableau sample is much smaller <cite index="49-1">(around 8,399 orders and 23 columns)</cite>.
- **Columns:** ~21–27 depending on version (Order, Ship, Customer, Segment, Region, Category, Sub-Category, Sales, Profit, Discount).
- **Business realism:** Moderate — designed for BI teaching, not a real company's raw export; numbers are plausible but the "business" behind it isn't a real retailer.
- **Data completeness:** Good breadth (has profit and discount, unusual among free datasets) but shallow depth per record.
- **Missing values:** Very low — this dataset is intentionally pre-cleaned for teaching.
- **Time span:** Typically ~4 years, varies by version.
- **Product information:** Category/Sub-Category only, no true SKU master or cost basis (profit is pre-computed, not derived from cost).
- **Customer information:** Segment (Consumer/Corporate/Home Office) and name only, no loyalty or demographic depth.
- **Geographic information:** Region/State/City present — good for map visuals.
- **Suitability for SQL:** High — simple, flat, ideal for beginner-to-intermediate SQL practice.
- **Suitability for Python:** High — heavily tutorialized.
- **Suitability for Power BI:** High — this is literally Tableau/Power BI's own default teaching dataset, extremely dashboard-ready.
- **Suitability for executive dashboards:** Moderate — good visuals, but is so widely recognized by reviewers as a "starter" dataset that it undercuts portfolio credibility if used as the primary source.
- **Suitability for storytelling:** Moderate — profit-by-discount-band is a well-worn but real insight; little room for an original narrative.
- **Suitability for ML:** Low-moderate — small feature set limits serious modeling.
- **Suitability for forecasting:** Low-moderate — short/inconsistent time span depending on version used.
- **Score: 58/100**

### 7. Dunnhumby — The Complete Journey
- **Source:** dunnhumby Source Files / mirrored on Kaggle — https://www.dunnhumby.com/source-files/
- **License:** dunnhumby's own terms — <cite index="57-1">the license requires dunnhumby's permission to publicly publish results obtained using the dataset</cite>, which is a material constraint for a public portfolio.
- **Rows:** <cite index="57-1">Transaction file alone is ~136MB</cite>; <cite index="60-1">2 years of purchase history across 2,500 households</cite>, spread over 8 tables.
- **Columns:** ~8 tables including transaction_data, hh_demographic, campaign_table, campaign_desc, coupon, coupon_redempt, product, causal_data.
- **Business realism:** Very high — <cite index="59-1">this is real household-level transaction data from a national grocery retailer, including loyalty-card and coupon-match discount details</cite>.
- **Data completeness:** Excellent for customer/marketing use cases — <cite index="59-1">it distinguishes loyalty-card vs non-loyalty pricing and tracks direct-marketing campaign history per household</cite>.
- **Missing values:** Low within core tables; demographics are only available for a subset of households (real-world realism, also a limitation).
- **Time span:** 2 years.
- **Product information:** Category/brand hierarchy present, no explicit unit cost (so true margin isn't derivable, only observed discount).
- **Customer information:** Best-in-class among free datasets — <cite index="59-1">household demographics, income band, homeownership, and age band are included for a subset of households</cite>.
- **Geographic information:** None (single unnamed retailer, no store addresses).
- **Suitability for SQL:** High — genuinely relational across 8 tables.
- **Suitability for Python:** High — <cite index="58-1">widely used for churn-prediction and retention modeling tutorials</cite>.
- **Suitability for Power BI:** Moderate — rich on customer/marketing pages, empty on regional/store pages.
- **Suitability for executive dashboards:** Moderate — outstanding Customer Analytics page potential, but the publication restriction is disqualifying for a public GitHub portfolio piece.
- **Suitability for storytelling:** High — <cite index="58-1">campaign and coupon redemption data supports a genuine marketing-effectiveness narrative</cite>.
- **Suitability for ML:** High — a standard churn/CLV modeling dataset.
- **Suitability for forecasting:** Low-moderate — grain and volume favor customer modeling over demand forecasting.
- **Score: 66/100** *(capped below its raw data quality because the license blocks the public-portfolio use case this project requires)*

### 8. Contoso Retail Data Warehouse (Microsoft / SQLBI Contoso Data Generator)
- **Source:** Originally Microsoft's official Contoso BI Demo Dataset; actively maintained today via the SQLBI Contoso Data Generator — https://www.sqlbi.com/tools/contoso-data-generator/
- **License:** Freely distributable sample/demo data; the modern SQLBI generator is open-source tooling.
- **Rows:** Fully configurable — <cite index="70-1">the classic Microsoft sample alone ships with over two million rows of sales data</cite>; the SQLBI generator can produce anywhere from tens of thousands to <cite index="68-1">many millions of order rows on demand, with a documented Sales, Orders, OrderRows, Customers, Stores, and Dates table set</cite>.
- **Columns:** Full star schema out of the box (Sales fact + Customer, Store, Product, Date, Currency dimensions).
- **Business realism:** Purpose-built for BI demonstration — <cite index="64-1">explicitly designed to cover C-level, sales/marketing, IT, and finance scenarios for the retail industry, with both OLTP-style transactions and OLAP-ready aggregations</cite>.
- **Data completeness:** Very high relative to the others — this is the only dataset in the comparison natively designed to support Finance, Sales, and Customer reporting simultaneously.
- **Missing values:** Minimal — a curated demo dataset, though <cite index="64-1">the underlying revenue/cost figures are explicitly symbolic rather than real audited financials</cite>.
- **Time span:** <cite index="64-1">The original sample runs 2007–2009</cite>; the modern SQLBI generator lets the builder choose any date range and row volume.
- **Product information:** Strong — full product hierarchy with brand, category, subcategory, and cost fields.
- **Customer information:** Present but generic/random — <cite index="69-1">customer and store attributes are generated using random data generation services layered onto the original Contoso schema</cite>, so there's no authentic behavioral signal (e.g., no real seasonality-driven loyalty patterns).
- **Geographic information:** Strong — multi-country structure (<cite index="69-1">Contoso is modeled as a multinational retailer based in Paris with a catalogue of 100K+ products</cite>), good for map visuals, but not India-specific.
- **Suitability for SQL:** Very high — literally ships as a SQL Server data warehouse.
- **Suitability for Python:** High — clean CSV/Parquet exports available via the generator.
- **Suitability for Power BI:** Very high — this is Microsoft's own reference dataset for teaching Power BI/DAX.
- **Suitability for executive dashboards:** Very high — the only dataset here with all of Sales, Finance (cost/margin), Customer, Product, and Store dimensions present simultaneously.
- **Suitability for storytelling:** Moderate — because the data is generated/random rather than behaviorally real, insights can feel synthetic ("discovered" patterns are generator artifacts, not real business truths) — a portfolio reviewer familiar with Contoso will recognize it immediately as demo data.
- **Suitability for ML:** Low-moderate — randomly generated relationships limit genuine predictive signal.
- **Suitability for forecasting:** Moderate — configurable trend/seasonality parameters exist but are synthetic by construction.
- **Score: 82/100**

### 9. Corporación Favorita Grocery Sales Forecasting
- **Source:** Kaggle competition — https://www.kaggle.com/c/favorita-grocery-sales-forecasting
- **License:** Kaggle competition terms.
- **Rows:** <cite index="76-1">125,497,040 training observations plus 3,370,464 test observations</cite> — by far the largest dataset in this comparison.
- **Columns:** Core sales table has 6 columns; supplementary files add store metadata, item metadata, oil price, holidays, and transaction counts.
- **Business realism:** High — <cite index="77-1">real data from Corporación Favorita, a large Ecuadorian grocery retailer operating hundreds of supermarkets with over 200,000 products</cite>.
- **Data completeness:** Good for demand-side signal, weak on financials — <cite index="79-1">the dataset is POS-derived and contains no inventory/stock information, so zero-sales periods can't be distinguished from true stockouts</cite>.
- **Missing values:** Documented gaps — <cite index="75-1">roughly 16% of the onpromotion values are missing</cite>.
- **Time span:** ~4.5 years.
- **Product information:** <cite index="74-1">Item metadata includes family, class, and a perishable flag</cite>; no unit cost, so margin isn't derivable.
- **Customer information:** None — this is store-item-date grain, no individual customers.
- **Geographic information:** <cite index="74-1">Store metadata includes city, state, store type, and a cluster grouping</cite> — Ecuador only.
- **Suitability for SQL:** Moderate — technically relational but the training table's 125M rows make routine querying heavy for a portfolio-scale Postgres instance.
- **Suitability for Python:** High but resource-intensive — a common benchmark for memory-optimization technique demonstrations.
- **Suitability for Power BI:** Low — this row volume is far beyond what Power BI Import Mode should carry for a responsive executive report without heavy pre-aggregation.
- **Suitability for executive dashboards:** Low — no financial layer, no customer layer, and volume works against fast page loads.
- **Suitability for storytelling:** Low-moderate — oil-price and holiday effects on an emerging-market grocery chain are interesting but tangential to Meridian's narrative.
- **Suitability for ML:** Very high — a premier large-scale forecasting benchmark.
- **Suitability for forecasting:** Very high — purpose-built, longest usable daily history among grocery-specific datasets here.
- **Score: 55/100** *(scored down specifically for BI/dashboard fit despite being excellent for pure forecasting/ML)*

### 10. Walmart Recruiting — Store Sales Forecasting (2014)
- **Source:** Kaggle competition — https://www.kaggle.com/c/walmart-recruiting-store-sales-forecasting
- **License:** Kaggle competition terms.
- **Rows:** <cite index="90-1">115,064 rows in the main training file, 45 rows of store metadata, and 8,190 rows of weekly external features</cite>.
- **Columns:** <cite index="90-1">Train: Store, Dept, Date, Weekly_Sales, IsHoliday; Store: Store, Type, Size; Features: Temperature, Fuel_Price, five MarkDown columns, CPI, Unemployment, IsHoliday</cite>.
- **Business realism:** High — <cite index="85-1">real historical sales for 45 Walmart stores across different regions, including holiday markdown events known to affect sales</cite>.
- **Data completeness:** Small and narrow — store-department-week grain only, no product SKU detail, no customer data, no cost/margin.
- **Missing values:** Notable — <cite index="90-1">the MarkDown columns have thousands of nulls (4,158 and 5,269 in two of the five markdown fields), and CPI/Unemployment have 585 nulls</cite>.
- **Time span:** <cite index="86-1">30 months of weekly data</cite>.
- **Product information:** None at SKU level — department-level aggregation only.
- **Customer information:** None.
- **Geographic information:** Store-region only, no city/state granularity in the public files.
- **Suitability for SQL:** High — small, simple, fast to load.
- **Suitability for Python:** High — good starter time-series dataset (smaller than M5, easier to iterate on).
- **Suitability for Power BI:** Low-moderate — dataset is too narrow to fill more than one dashboard page.
- **Suitability for executive dashboards:** Low — no financial, customer, or product layer.
- **Suitability for storytelling:** Moderate — the holiday-markdown effect is a genuinely useful, well-documented narrative.
- **Suitability for ML:** Moderate-high — small enough to iterate quickly, macro features (CPI, fuel price, unemployment) add real-world texture.
- **Suitability for forecasting:** High — purpose-built weekly forecasting task with holiday weighting built into the evaluation design.
- **Score: 50/100**

---

## Comparison Summary Table

| # | Dataset | Rows (approx.) | Time Span | Financial Data? | Customer Data? | Store/Region Data? | Score /100 |
|---|---|---|---|---|---|---|---|
| 1 | UCI Online Retail II | ~1.07M | 2 yrs | No (price only) | Thin | Country only | 61 |
| 2 | Olist Brazilian E-Commerce | ~100K orders / 9 tables | 2 yrs | Price/freight only | Moderate | Strong (geo) | 68 |
| 3 | Instacart Market Basket | ~3.4M orders | Sequential | None | Thin | None | 47 |
| 4 | Rossmann Store Sales | ~1.35M | 2.5 yrs | No margin | None | Moderate | 64 |
| 5 | M5 Forecasting (Walmart) | ~59M (unpivoted) | 5.4 yrs | No margin | None | State-level | 70 |
| 6 | Superstore Sample Sales | ~8K–51K (version-dependent) | ~4 yrs | Yes (profit/discount) | Thin | Strong | 58 |
| 7 | Dunnhumby Complete Journey | ~2.5M transactions / 8 tables | 2 yrs | Discount only | Very strong | None | 66 |
| 8 | Contoso Retail (Microsoft/SQLBI) | Configurable (2M+) | Configurable | Yes (cost/margin) | Moderate (synthetic) | Strong | **82** |
| 9 | Favorita Grocery Forecasting | ~125M+ | 4.5 yrs | No margin | None | Moderate | 55 |
| 10 | Walmart Recruiting 2014 | ~115K | 2.5 yrs | No margin | None | Weak | 50 |

---

## Recommendation

**No single dataset — real or otherwise — is sufficient on its own.** Every one of the 10 datasets researched has at least one structural gap that would block a core piece of the Phase 1 BRD:

- Datasets with strong **customer/loyalty depth** (Dunnhumby) have **no store/regional dimension** and carry a **publication-restrictive license** that conflicts with the portfolio's public-GitHub requirement.
- Datasets with strong **forecasting/time-series depth** (M5, Favorita, Rossmann, Walmart Recruiting) have **no customer dimension and no true cost/margin field**, which blocks the entire Financial Performance page and most of Section 6's Finance KPIs.
- Datasets with the best **out-of-the-box BI/star-schema shape** (Contoso) are **explicitly synthetic and randomly generated**, meaning any "insight" discovered in them is a generator artifact rather than a real, defensible business finding — which undermines the storytelling/case-study goal at the heart of this portfolio project.
- No dataset anywhere in this research — real or synthetic — models Meridian Retail Group's specific business narrative: an **omnichannel Indian retailer** with a **wholesale B2B channel**, **three named customer segments**, **four merchandise divisions**, a **214-store, 4-region footprint**, and a **scripted six-quarter East-region underperformance storyline**. That narrative is a project requirement from Phase 1, not something any public dataset was built to contain.

### Recommended Approach: Calibrated Synthetic Generation (confirms and formalizes the Phase 1 architecture)

Rather than forcing Meridian's schema onto a real dataset that wasn't built for it (which would mean silently overwriting real transactions with fictional business logic — a bad practice — or abandoning the Phase 1 business narrative entirely), the recommendation is to **generate Insight360's dataset synthetically using Python (Faker + NumPy/Pandas)**, exactly as scoped in Phase 1 Part 8, but **statistically calibrated against the four strongest datasets researched above** so the result behaves like real retail data rather than arbitrary random numbers:

| Benchmark dataset used for calibration | What Insight360 borrows from it |
|---|---|
| **Contoso Retail (Microsoft/SQLBI)** | Star-schema shape and table relationships (Sales fact + Customer/Store/Product/Date dimensions) — the closest structural template to Section 9's conceptual model. |
| **UCI Online Retail II** | Realistic transaction-level messiness patterns — invoice cancellations, missing CustomerIDs on a subset of rows, price/quantity distributions for a general-merchandise retailer. |
| **Rossmann Store Sales & M5 (Walmart)** | Seasonality curves, promotion-driven sales lift, and holiday/festive-period effects to calibrate Meridian's festive/EOSS demand spikes and forecast-accuracy simulation. |
| **Superstore Sample Sales** | Realistic discount-to-profit relationship shape, used to calibrate how Meridian's discount depth erodes margin by category. |
| **Dunnhumby Complete Journey** *(pattern reference only, no data reused)* | Realistic loyalty engagement and repeat-purchase distribution shapes, used only as a design reference for Meridian's segment-level retention curves — no Dunnhumby rows or files are copied, avoiding its publication-restrictive license entirely. |
| **Olist Brazilian E-Commerce** | Multi-table relational integrity pattern (customer/geolocation/order/payment/review separation) as a design reference for keeping Fact/Dim separation clean. |

This is a **combination approach in the sense the brief asked for** — it just combines these sources as *calibration references and structural templates* rather than literal row-level merges, which is the technically correct choice given that no two of these datasets share compatible keys, currencies, time periods, or business models (merging Ecuadorian grocery SKUs with UK gift-ware invoices and Wisconsin department codes would itself have to be substantially fabricated to reconcile — silently creating exactly the kind of unearned realism this research step exists to avoid).

---

## Data Acquisition Plan

### What data will be used
A fully synthetic dataset representing one full fiscal year (plus a simulated prior-year baseline for YoY comparisons) of Meridian Retail Group activity, generated in Phase 3 using Python (Faker, NumPy, Pandas), populating every table defined in the Phase 1 Data Dictionary (Section 5): Fact_Sales, Dim_Store, Dim_Product, Dim_Customer, Dim_Date, Fact_Inventory_Snapshot, Fact_Returns, Dim_Campaign, and Fact_Staffing. Generation parameters (seasonality curves, discount-margin relationships, missing-value rates, regional variance) will be calibrated against the benchmark datasets identified above rather than left fully random.

### Why it is needed
1. **No public dataset matches Meridian's business model** (omnichannel + wholesale, India-based, four merchandise divisions, three named customer segments) — using one directly would require fabricating so much on top of it that the "real dataset" label would be misleading.
2. **The Phase 1 business narrative is a required deliverable**, not incidental — the 25 business problems (East-region underperformance, discount-driven margin erosion, forecast inaccuracy, etc.) need to be genuinely present and discoverable in the data for Phase 8's insights to be honest rather than staged.
3. **Full schema coverage is required** — the BRD's Functional Requirements (Section 2) call for financial, customer, product, inventory, and staffing reporting simultaneously; no single public dataset covers all five domains, and calibrated synthetic generation is the only approach that does.
4. **Portfolio defensibility** — synthetic-but-calibrated data, openly disclosed as such (see Limitations below), is standard, accepted practice for portfolio projects and avoids licensing risk (e.g., Dunnhumby's publish-permission requirement, Kaggle competition redistribution terms) that would complicate public GitHub hosting.

### How it maps to the Business Requirements
- Fact_Sales/Dim_Store/Dim_Customer/Dim_Product/Dim_Date → directly implements the star schema in Phase 1 Section 9 and supports FR-1 through FR-6.
- Fact_Inventory_Snapshot → supports FR-7 (inventory health monitoring) and KPIs #23–26.
- Fact_Returns → supports KPI #21 (Return Rate %) and Problem #14.
- Dim_Campaign → supports FR-4/marketing KPIs #27–28 and Problem #18.
- Fact_Staffing → supports FR-9 and KPIs #30, #24 (productivity family).
- Calibrated seasonality/discount patterns → ensure Problems #1, #2, #3, #4, #8 are genuinely observable outcomes in the data, not scripted overlays.

### Limitations and Assumptions
- **Disclosure requirement:** The case study and README (Phase 11) will explicitly state the dataset is synthetic and calibrated against named public benchmarks — this will not be presented as real Meridian transaction data, protecting the integrity of the portfolio.
- **Calibration is directional, not statistical fitting:** Parameters are informed by the general shape/scale of the benchmark datasets' public documentation and summary statistics, not by direct statistical fitting to their raw distributions (no benchmark dataset's raw rows are ingested into Insight360's data).
- **Currency and locale:** Values will be generated in INR (₹) to match Meridian's stated revenue, which none of the benchmark datasets natively provide — currency scaling is a design choice, not a derived figure.
- **No real customer, store, or product data of any kind is used** — Dim_Customer, Dim_Store, and Dim_Product records are entirely fictional, avoiding any privacy or licensing concern.
- **Forecast data (Phase 7's stretch page) will itself be simulated** (a deliberately noisy version of actuals), not produced by a trained model, consistent with the Phase 1 scope boundary that excludes ML/forecasting models from v1.
- **Volumes will target the planning estimates in Phase 1 Section 4.2** (~3.5–5M Fact_Sales rows) but may be scaled down during initial development for iteration speed, with the calibration logic remaining constant regardless of final row count.

---

## Review Note

This phase deliberately stops short of finalizing exact row counts, column-level generation logic, or file formats — that belongs to Phase 3 (Python Data Cleaning) working from this plan. The core decision requiring your approval here is the **calibrated-synthetic approach** over forcing any single public dataset (including the strongest candidate, Contoso) into Meridian's schema.

**Status: Awaiting your review and approval before proceeding to Phase 3.**
