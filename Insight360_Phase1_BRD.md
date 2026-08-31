# Insight360 — Executive BI Platform for Retail
## Phase 1 (Expanded): Business Requirements & Foundation Document
**Client (Fictional):** Meridian Retail Group (MRG) | **Project:** Insight360 | **Version:** 1.0 | **Status:** Awaiting Approval

---

## 1. Business Requirements Document (BRD)

### 1.1 Scope

**In Scope**
- Design and delivery of a single, unified executive BI platform (Insight360) covering Sales, Finance, Customer, Product, Inventory, and Regional/Store performance for Meridian Retail Group.
- Coverage of all four merchandise divisions, three store formats, the digital channel, and the wholesale B2B channel.
- A synthetic but statistically realistic dataset representing one full fiscal year of transactional history, refreshed conceptually on a monthly cadence (simulated, not live).
- A star-schema data model, a curated DAX measure layer, and a 6–7 page Power BI dashboard suite.
- Supporting documentation: data dictionary, KPI catalog, business case, and a written insights narrative.
- Portfolio packaging: GitHub repository, case study, and walkthrough materials.

**Out of Scope**
- Live/production data integration with any real retail system (this is a simulated environment).
- Predictive/ML forecasting models (Phase 7's "Forecast & Planning" page will visualize forecast-vs-actual using simulated forecast data, not a trained model — that is a possible future extension, explicitly not v1).
- Mobile-native app development (dashboard will be Power BI, viewable on mobile via the Power BI app, but not custom-built for mobile).
- Real-time/streaming data (batch/simulated refresh only).
- Row-level security implementation beyond a conceptual design note.
- Multi-language localization.

### 1.2 Objectives

1. Demonstrate end-to-end BI capability: data generation → cleaning → modeling → visualization → narrative insight, mirroring a real analytics team's workflow.
2. Produce an executive dashboard that a CEO, CFO, or COO could plausibly use to run a monthly business review.
3. Translate the 25 identified business problems into a prioritized, MVP-scoped set of dashboard pages and KPIs.
4. Build a portfolio artifact strong enough to withstand hiring-manager scrutiny — meaning it must show reasoning (why this KPI, why this chart), not just visuals.
5. Establish a reusable architecture and documentation pattern that could extend to future portfolio projects.

### 1.3 Assumptions

- Meridian Retail Group, its stores, employees, and customers are entirely fictional; all data will be synthetically generated but designed to reflect statistically realistic retail patterns (seasonality, regional variance, category mix).
- One fiscal year of daily-grain transactional data is sufficient to demonstrate trend, seasonality, and YoY-style analysis (simulated prior-year baseline will be generated for comparison purposes).
- Power BI Desktop (and optionally Power BI Service for publishing) is the target BI tool; no alternate tool (Tableau, Looker) is in scope for v1.
- The developer (project owner) has or will acquire working familiarity with Python, SQL, and Power BI DAX during Phases 3–7.
- "Executive" in this context means CEO/CFO/COO/Director-level personas as defined in Phase 1 Part 2, not IT/engineering personas.

### 1.4 Constraints

- **Time/Scope discipline:** Of the 25 business problems and 100 business questions catalogued, only a prioritized subset will be operationalized into KPIs and visuals (see Section 1.6 and the MVP scoping note below). This is a deliberate constraint to avoid dashboard bloat.
- **Tooling:** Free/self-hostable tools only (PostgreSQL, Python, Power BI Desktop) — no paid enterprise licenses, consistent with a portfolio project budget of $0.
- **Data realism ceiling:** Synthetic data can approximate but not perfectly replicate real retail data anomalies (fraud patterns, POS system errors, true customer behavior). This is disclosed transparently in the case study rather than hidden.
- **Single developer:** No dedicated QA, data engineering, or design team — all roles (data engineer, analyst, BI developer, technical writer) are performed by one person, which affects timeline but not deliverable quality expectations.

### 1.5 Success Criteria

A phase/deliverable is considered successful when:
- Every KPI on a dashboard page traces back to a specific stakeholder need and business question defined in this document (no orphan visuals).
- A first-time viewer can understand the state of the business within 10 seconds of opening the Executive Overview page.
- The data model passes referential integrity checks (no orphaned fact rows, no broken relationships) — validated conceptually here, verified technically in Phase 4/6.
- The GitHub repository can be understood by a reader who has never spoken to the project owner, using only the README and /docs folder.
- The finished project can answer, live and interactively, at least 25–30 of the 100 catalogued business questions without opening a raw data file.

### 1.6 Deliverables (Master List)

| # | Deliverable | Phase Produced |
|---|---|---|
| 1 | Expanded Business Requirements Document (this document) | 1 |
| 2 | Data dictionary & synthetic data generation plan | 2 |
| 3 | Cleaned, validated datasets (CSV/DB-ready) | 3 |
| 4 | PostgreSQL database with star schema | 4 |
| 5 | EDA summary (charts + written observations) | 5 |
| 6 | Validated Power BI data model (relationships + DAX foundation) | 6 |
| 7 | 6–7 page Power BI executive dashboard | 7 |
| 8 | Written business insights & executive narrative | 8 |
| 9 | GitHub repository (structured, documented) | 9 |
| 10 | README, KPI dictionary, data dictionary (polished) | 10 |
| 11 | Case study, screenshots, walkthrough recording | 11 |
| 12 | Resume/LinkedIn bullet integration | 12 |

**MVP Scoping Note (carried forward from original Phase 1):** Of the 25 business problems, the following **15** are designated priority-one and will directly drive KPI/dashboard design: #1 Declining Net Margin, #2 East Region Underperformance, #3 Inventory Imbalance, #4 Discount Abuse, #5 Low Customer Retention, #7 Revenue Concentration Risk, #8 Poor Demand Forecasting, #10 Loyalty Under-Penetration, #13 Store Productivity Gaps, #14 Return Rate Volatility, #15 Weak Cross-Sell, #18 Marketing Attribution Ambiguity, #19 Shrinkage & Loss, #23 Customer Segmentation Gaps, #25 Slow Executive Reporting Cycle. The remaining 10 problems remain documented for portfolio depth (showing full diagnostic thinking) but are not directly wired to v1 visuals. This will be finalized collaboratively at Phase 2.

---

## 2. Functional Requirements

Functional requirements describe **what the system must do**, expressed as capabilities the dashboard and underlying data platform must support.

**FR-1 — Multi-level performance monitoring**
The system shall present revenue, margin, and growth metrics at Company → Region → Store level, with drill-down from summary to detail.

**FR-2 — Time intelligence**
The system shall support Month-to-Date, Quarter-to-Date, Year-to-Date, and Year-over-Year comparisons for all core KPIs.

**FR-3 — Cross-filtering**
All report pages shall respond to a shared set of global filters (Date, Region, Channel, Category) such that a filter change on one visual updates all related visuals on the page.

**FR-4 — Channel segmentation**
The system shall break down performance by Store, Online, and Wholesale channels independently and in combination.

**FR-5 — Customer segmentation**
The system shall classify and report on customers by segment (Value, Premium, Digital Native) and by loyalty status (member vs non-member).

**FR-6 — Product hierarchy navigation**
The system shall allow drill-down from Division → Category → SKU for sales, margin, and inventory metrics.

**FR-7 — Inventory health monitoring**
The system shall surface stockout rate, overstock indicators, and inventory turnover at category and warehouse level.

**FR-8 — Financial bridge reporting**
The system shall provide a margin waterfall showing the path from gross revenue to net margin, including discount impact.

**FR-9 — Store diagnostic view**
The system shall provide store-level productivity metrics (revenue/sq ft, sales/employee-hour) to support Regional Manager and Store Manager decisions.

**FR-10 — Pre-configured views**
The system shall provide bookmarked views for recurring executive questions (e.g., "Top 10 Underperforming Stores," "This Quarter vs Last Quarter").

**FR-11 — Exportability**
Underlying tables (e.g., store performance detail) shall be exportable to Excel/CSV directly from the report for offline analysis, consistent with standard Power BI capability.

**FR-12 — Narrative layer**
The system shall be accompanied by a written insights document that interprets dashboard findings in business language, not just raw numbers.

---

## 3. Non-Functional Requirements

Non-functional requirements describe **how well** the system must perform, independent of specific features.

| Category | Requirement |
|---|---|
| **Usability** | A non-technical executive must be able to interpret the Executive Overview page without training, within 10 seconds. |
| **Performance** | Report pages shall render/refresh in under 5 seconds on the modeled data volume (see Section 4.2), consistent with standard Power BI Import Mode performance. |
| **Consistency** | Visual design (color palette, fonts, KPI card style, navigation) shall be uniform across all pages via a shared Power BI theme file. |
| **Data Integrity** | The data model shall enforce referential integrity — every fact row must resolve to valid dimension keys with zero orphaned records. |
| **Maintainability** | DAX measures shall be organized into a dedicated measures table (not scattered across visuals) and named using a consistent convention for future extensibility. |
| **Documentation Quality** | Every KPI, table, and column shall be documented such that a new analyst could onboard onto the project using only the /docs folder. |
| **Portability** | The project shall run entirely on free/open tooling (PostgreSQL, Python, Power BI Desktop) with no proprietary or paid dependencies. |
| **Accessibility** | Color choices shall maintain sufficient contrast for readability and avoid red/green as the sole differentiator (colorblind-conscious palette), given red/green is the default "bad/good" convention in retail dashboards. |
| **Auditability** | Every number on the dashboard shall be traceable back to a specific DAX measure and source table — no hard-coded or manually overridden values. |
| **Version Control** | All code, schema, and documentation changes shall be tracked in Git with a feature-branch workflow and a tagged v1.0 release. |

---

## 4. Data Requirements

### 4.1 Data Domains Required

| Domain | Description | Grain |
|---|---|---|
| Sales Transactions | Every line-item sale across store, online, and wholesale channels | Transaction line |
| Store Master | The 214 physical stores plus a virtual "Online" and "Wholesale" pseudo-store | Store |
| Product Master | SKUs across 4 divisions and their sub-categories | SKU |
| Customer Master | Loyalty and non-loyalty customer profiles | Customer |
| Date Master | Calendar with fiscal periods, festive/EOSS flags, weekday/weekend flags | Day |
| Inventory Snapshot | Periodic stock-on-hand by SKU by location | SKU x Location x Period |
| Marketing Campaign | Campaign metadata, spend, channel, target segment | Campaign |
| Returns | Return transactions linked back to original sale | Return line |
| Employee/Staffing (light) | Store-level headcount and hours, for productivity KPIs | Store x Period |

### 4.2 Estimated Data Volumes (for realism and performance planning)

| Table | Approx. Row Count | Notes |
|---|---|---|
| Fact_Sales | ~3.5–5 million rows | 1 fiscal year, daily transactions across 214 stores + online + wholesale |
| Dim_Customer | ~4.2 million rows (subset actively transacting) | Matches stated loyalty base |
| Dim_Product | ~3,000–5,000 SKUs | Across 4 divisions |
| Dim_Store | 214 stores + 2 virtual channels | Fixed |
| Dim_Date | ~730 rows (2 fiscal years for YoY) | Fixed |
| Fact_Inventory_Snapshot | ~500,000–1M rows | Weekly snapshots x SKU x location (sampled, not full daily grain) |
| Fact_Returns | ~150,000–250,000 rows | ~5–7% of transactions, matching stated return-rate patterns |
| Dim_Campaign | ~50–80 rows | Campaigns across the fiscal year |
| Fact_Staffing | ~214 stores x 52 weeks | Store-week grain |

*(Exact volumes to be finalized in Phase 2 dataset design — figures above are planning targets, not final specifications.)*

### 4.3 Data Quality Requirements

- No duplicate transaction IDs.
- Every foreign key in Fact_Sales must resolve to a valid Dim_Customer, Dim_Product, Dim_Store, and Dim_Date record.
- Revenue, quantity, and discount fields must be non-negative except where a documented return/credit convention applies.
- Date fields must fall within the defined fiscal calendar with no future-dated transactions.
- Synthetic data must reflect stated business patterns (e.g., East region genuinely underperforming, Electronics genuinely lower-margin) so that the dashboard's "discoveries" are real discoveries within the simulation, not arbitrary noise.

---

## 5. Complete Data Dictionary

### 5.1 Fact_Sales

| Column | Type | Description |
|---|---|---|
| sales_id | String (PK) | Unique transaction line identifier |
| date_key | Date (FK) | Links to Dim_Date |
| store_key | Int (FK) | Links to Dim_Store (or virtual Online/Wholesale) |
| product_key | Int (FK) | Links to Dim_Product |
| customer_key | Int (FK, nullable) | Links to Dim_Customer; null for non-loyalty/anonymous transactions |
| channel | String | Store / Online / Wholesale |
| quantity | Integer | Units sold in the line |
| unit_price | Decimal | List price per unit |
| discount_amount | Decimal | Discount applied to the line |
| net_sales_amount | Decimal | (unit_price × quantity) − discount_amount |
| cost_amount | Decimal | COGS for the line, used to derive margin |
| loyalty_flag | Boolean | Whether the transaction is tied to a loyalty ID |
| promotion_id | String (FK, nullable) | Links to Dim_Campaign if promotion-driven |

### 5.2 Dim_Store

| Column | Type | Description |
|---|---|---|
| store_key | Int (PK) | Unique store identifier |
| store_name | String | Display name |
| store_format | String | Flagship / Express / Outlet / Online / Wholesale |
| region | String | North / South / East / West |
| city | String | Store city |
| sqft | Integer | Store square footage (physical stores only) |
| open_date | Date | Store opening date, used for new-vs-mature classification |
| store_status | String | Active / Closed |

### 5.3 Dim_Product

| Column | Type | Description |
|---|---|---|
| product_key | Int (PK) | Unique SKU identifier |
| sku_name | String | Product display name |
| division | String | Apparel & Footwear / Home & Living / Electronics & Accessories / Daily Essentials |
| category | String | Sub-category (e.g., Menswear, Kitchenware, Audio) |
| brand | String | Brand or private-label flag |
| list_price | Decimal | Standard retail price |
| unit_cost | Decimal | Standard cost, used for margin calculations |
| launch_date | Date | Used to identify new-vs-existing SKUs (cannibalization analysis) |

### 5.4 Dim_Customer

| Column | Type | Description |
|---|---|---|
| customer_key | Int (PK) | Unique customer identifier |
| loyalty_id | String (nullable) | Loyalty program ID, null if non-member |
| segment | String | Value Shopper / Premium Shopper / Digital Native |
| enrollment_date | Date | Loyalty enrollment date, null if non-member |
| region | String | Customer's primary shopping region |
| preferred_channel | String | Store / Online, based on transaction history |

### 5.5 Dim_Date

| Column | Type | Description |
|---|---|---|
| date_key | Date (PK) | Calendar date |
| fiscal_year | Int | Fiscal year label |
| fiscal_quarter | String | Q1–Q4 |
| month_name | String | Calendar month |
| week_of_year | Int | ISO week number |
| day_of_week | String | Weekday name |
| is_weekend | Boolean | Weekend flag |
| is_festive_period | Boolean | Festive/EOSS season flag |

### 5.6 Fact_Inventory_Snapshot

| Column | Type | Description |
|---|---|---|
| snapshot_id | String (PK) | Unique snapshot record ID |
| date_key | Date (FK) | Snapshot date |
| store_key | Int (FK) | Location (store or warehouse) |
| product_key | Int (FK) | SKU |
| units_on_hand | Integer | Stock quantity at snapshot time |
| units_on_order | Integer | Units in transit/on order |
| reorder_point | Integer | Threshold for stockout risk flagging |

### 5.7 Fact_Returns

| Column | Type | Description |
|---|---|---|
| return_id | String (PK) | Unique return record ID |
| original_sales_id | String (FK) | Links back to Fact_Sales |
| date_key | Date (FK) | Return date |
| product_key | Int (FK) | SKU returned |
| quantity_returned | Integer | Units returned |
| return_reason | String | Size/Fit, Defective, Changed Mind, Other |
| refund_amount | Decimal | Amount refunded |

### 5.8 Dim_Campaign

| Column | Type | Description |
|---|---|---|
| campaign_id | String (PK) | Unique campaign identifier |
| campaign_name | String | Display name |
| channel | String | Email / SMS / Digital Ads / In-Store |
| target_segment | String | Customer segment targeted |
| start_date / end_date | Date | Campaign window |
| spend_amount | Decimal | Total campaign spend |

### 5.9 Fact_Staffing

| Column | Type | Description |
|---|---|---|
| staffing_id | String (PK) | Unique record ID |
| store_key | Int (FK) | Store |
| week_start_date | Date (FK-linked to Dim_Date) | Week grain |
| headcount | Integer | Active staff count for the week |
| total_hours | Decimal | Total scheduled hours |

---

## 6. KPI Catalog

Each KPI below includes Definition, Formula, Business Purpose, Primary Stakeholder, and Dashboard Page.

### Revenue & Sales

**1. Total Revenue**
- Definition: Net sales value across all channels.
- Formula: `SUM(net_sales_amount)`
- Purpose: Primary top-line health indicator.
- Stakeholder: CEO, Sales Director
- Page: Executive Overview, Sales & Revenue Deep Dive

**2. YoY Revenue Growth %**
- Definition: Revenue growth vs the same period last year.
- Formula: `(Current Period Revenue − Prior Year Revenue) / Prior Year Revenue`
- Purpose: Tracks whether growth targets (e.g., digital share expansion) are on pace.
- Stakeholder: CEO, CFO
- Page: Executive Overview

**3. Revenue by Channel**
- Definition: Split of revenue across Store, Online, Wholesale.
- Formula: `SUM(net_sales_amount)` grouped by `channel`
- Purpose: Tracks progress toward 35%→50% digital revenue share goal.
- Stakeholder: CEO, Sales Director
- Page: Sales & Revenue Deep Dive

**4. Average Transaction Value (ATV)**
- Definition: Average value of a single transaction.
- Formula: `SUM(net_sales_amount) / COUNT(DISTINCT sales_id)`
- Purpose: Indicates basket strength; flat/declining ATV signals cross-sell weakness (Problem #15).
- Stakeholder: Sales Director, Marketing Manager
- Page: Sales & Revenue Deep Dive

**5. Conversion Rate**
- Definition: Share of store footfall converted into transactions.
- Formula: `COUNT(DISTINCT sales_id) / Footfall Count`
- Purpose: Diagnoses store-level effectiveness, not just traffic.
- Stakeholder: Store Manager, Regional Manager
- Page: Regional/Store Performance

**6. Same-Store Sales Growth (SSSG)**
- Definition: Revenue growth for stores open >12 months, isolating organic growth from new-store growth.
- Formula: `(Current Period Revenue − Prior Year Revenue) / Prior Year Revenue`, filtered to mature stores
- Purpose: Distinguishes true performance from expansion-driven growth (Problem #7, #21).
- Stakeholder: CEO, Regional Managers
- Page: Regional/Store Performance

**7. Basket Size (Items per Transaction)**
- Definition: Average number of line items per transaction.
- Formula: `SUM(quantity) / COUNT(DISTINCT sales_id)`
- Purpose: Directly measures cross-sell effectiveness (Problem #15).
- Stakeholder: Sales Director, Marketing Manager
- Page: Sales & Revenue Deep Dive

### Financial

**8. Gross Margin %**
- Definition: Profitability after cost of goods sold.
- Formula: `(net_sales_amount − cost_amount) / net_sales_amount`
- Purpose: Core profitability lever; central to the +300bps margin goal (Problem #1).
- Stakeholder: CFO
- Page: Executive Overview, Financial Performance

**9. Net Profit Margin %**
- Definition: Bottom-line profitability after operating expenses.
- Formula: `(Gross Margin $ − Operating Expenses) / Revenue`
- Purpose: Ultimate profitability health check.
- Stakeholder: CFO, CEO
- Page: Financial Performance

**10. Operating Expense Ratio**
- Definition: Operating costs as a share of revenue.
- Formula: `Operating Expenses / Revenue`
- Purpose: Cost discipline tracking by department/region.
- Stakeholder: CFO, Finance Team
- Page: Financial Performance

**11. Discount Rate / Discount Penetration**
- Definition: Share of revenue sold at a discount, and average discount depth.
- Formula: `SUM(discount_amount) / SUM(unit_price × quantity)`
- Purpose: Directly diagnoses margin erosion from discounting (Problem #1, #4).
- Stakeholder: CFO, Merchandising
- Page: Financial Performance

**12. EBITDA (simplified)**
- Definition: Earnings before interest, tax, depreciation, and amortization.
- Formula: `Net Profit + Depreciation & Amortization + Interest + Tax` (modeled at a simplified/estimated level given no full GL in scope)
- Purpose: Standard investor-facing profitability metric.
- Stakeholder: CEO, CFO
- Page: Financial Performance

**13. Budget vs Actual Variance**
- Definition: Deviation of actual spend/revenue from budgeted plan.
- Formula: `(Actual − Budget) / Budget`
- Purpose: Financial planning discipline.
- Stakeholder: CFO, Finance Team
- Page: Financial Performance

### Customer

**14. Customer Retention Rate**
- Definition: Share of customers who made a repeat purchase within a defined window.
- Formula: `Repeat Customers (90-day) / Total First-Time Customers`
- Purpose: Directly tracks Problem #5 (34% repeat rate).
- Stakeholder: Marketing Manager, Customer Experience Team
- Page: Customer Analytics

**15. Customer Lifetime Value (LTV)**
- Definition: Estimated total revenue from a customer over their relationship.
- Formula: `Average Order Value × Purchase Frequency × Estimated Customer Lifespan`
- Purpose: Sets a rational ceiling for acquisition spend (Problem #11).
- Stakeholder: Marketing Manager, CFO
- Page: Customer Analytics

**16. Loyalty Penetration Rate**
- Definition: Share of transactions tied to a loyalty ID.
- Formula: `COUNT(sales_id WHERE loyalty_flag = TRUE) / COUNT(sales_id)`
- Purpose: Tracks progress toward the 48%→70% loyalty goal (Problem #10).
- Stakeholder: Marketing Manager
- Page: Customer Analytics

**17. Customer Acquisition Cost (CAC)**
- Definition: Average marketing spend required to acquire one new customer.
- Formula: `Total Acquisition-Targeted Campaign Spend / New Customers Acquired`
- Purpose: Tracks Problem #11 (rising CAC without proportional LTV growth).
- Stakeholder: Marketing Manager, CFO
- Page: Customer Analytics

**18. Repeat Purchase Rate (30/60/90-day)**
- Definition: Share of customers returning within specific windows.
- Formula: `Customers with 2nd purchase within N days / Total First-Time Customers`
- Purpose: Granular retention diagnostic beyond a single 90-day figure.
- Stakeholder: Customer Experience Team
- Page: Customer Analytics

**19. Churn Rate (Loyalty)**
- Definition: Share of previously active loyalty members with no purchase in a trailing period.
- Formula: `Lapsed Members / Active Members (prior period)`
- Purpose: Early warning signal for retention health.
- Stakeholder: Marketing Manager
- Page: Customer Analytics

### Product & Inventory

**20. Sell-Through Rate**
- Definition: Share of received inventory that has sold.
- Formula: `Units Sold / Units Received`
- Purpose: Merchandising effectiveness; informs reorder/markdown timing.
- Stakeholder: Supply Chain Manager, Merchandising
- Page: Product & Inventory

**21. Return Rate %**
- Definition: Share of sold units that are returned.
- Formula: `Units Returned / Units Sold`
- Purpose: Quality/fit signal; tracks Problem #14 (online vs in-store gap).
- Stakeholder: Customer Experience Team, Merchandising
- Page: Product & Inventory

**22. Category Margin Contribution**
- Definition: Dollar margin contributed by each product category.
- Formula: `SUM(net_sales_amount − cost_amount)` grouped by `category`
- Purpose: Portfolio profitability view; flags margin-dilutive categories (Problem #12).
- Stakeholder: CFO, Merchandising
- Page: Product & Inventory

**23. Inventory Turnover**
- Definition: How efficiently inventory converts to sales.
- Formula: `COGS / Average Inventory Value`
- Purpose: Capital efficiency signal (Problem #3, growth goal on carrying cost).
- Stakeholder: Supply Chain Manager
- Page: Product & Inventory

**24. Stockout Rate**
- Definition: Share of SKU-location combinations with zero available stock.
- Formula: `COUNT(SKU-Location WHERE units_on_hand = 0) / Total SKU-Location Combinations`
- Purpose: Direct lost-sales driver (Problem #3).
- Stakeholder: Supply Chain Manager, COO
- Page: Product & Inventory

**25. Days of Inventory on Hand (DOH)**
- Definition: How many days current stock would last at current sales velocity.
- Formula: `(Average Inventory Value / COGS) × 365`
- Purpose: Balances overstock risk against stockout risk.
- Stakeholder: Supply Chain Manager
- Page: Product & Inventory

**26. Forecast Accuracy**
- Definition: How closely actual sales matched forecasted demand.
- Formula: `1 − (ABS(Actual − Forecast) / Actual)`
- Purpose: Tracks Problem #8 (forecast accuracy below 70%).
- Stakeholder: Supply Chain Manager, COO
- Page: Forecast & Planning

### Marketing

**27. Campaign ROI**
- Definition: Return generated per unit of campaign spend.
- Formula: `(Attributed Revenue − Campaign Spend) / Campaign Spend`
- Purpose: Tracks Problem #18 (attribution ambiguity) by giving a directional, if imperfect, ROI view.
- Stakeholder: Marketing Manager, CFO
- Page: Sales & Revenue Deep Dive (Marketing sub-view)

**28. Promotional Sales Share**
- Definition: Share of revenue sold at a discount/promotion vs full price.
- Formula: `SUM(net_sales_amount WHERE promotion_id IS NOT NULL) / SUM(net_sales_amount)`
- Purpose: Tracks discount dependency (Problem #4).
- Stakeholder: Marketing Manager, CFO
- Page: Financial Performance

### Operations & Store

**29. Revenue per Square Foot**
- Definition: Sales efficiency per unit of physical retail space.
- Formula: `Store Revenue / Store sqft`
- Purpose: Direct store productivity comparison (Problem #13).
- Stakeholder: Regional Manager, COO
- Page: Regional/Store Performance

**30. Sales per Employee-Hour**
- Definition: Labor productivity per store.
- Formula: `Store Revenue / Total Staffing Hours`
- Purpose: Diagnoses workforce productivity variance (Problem #24).
- Stakeholder: Store Manager, Regional Manager
- Page: Regional/Store Performance

**31. Shrinkage Rate**
- Definition: Inventory loss not explained by recorded sales/returns.
- Formula: `(Expected Inventory − Actual Counted Inventory) / Expected Inventory`
- Purpose: Tracks Problem #19, especially Outlet-format exposure.
- Stakeholder: COO, Store Operations
- Page: Regional/Store Performance

**32. Fulfillment Time**
- Definition: Average days from online order to delivery.
- Formula: `AVG(delivery_date − order_date)`
- Purpose: Tracks Problem #9 (digital fulfillment lag vs competitors).
- Stakeholder: COO, Supply Chain Manager
- Page: Product & Inventory / Regional Performance

**33. Order Accuracy Rate**
- Definition: Share of orders fulfilled without error.
- Formula: `Accurate Orders / Total Orders`
- Purpose: Operational quality signal tied to CX.
- Stakeholder: COO, Customer Experience Team
- Page: Regional/Store Performance

### Executive Composite

**34. Regional Margin %**
- Definition: Gross margin percentage isolated by region.
- Formula: `(Regional Revenue − Regional COGS) / Regional Revenue`
- Purpose: Root-cause layer beneath Problem #2 (East region underperformance) — reveals whether the issue is volume or margin.
- Stakeholder: Regional Managers, CFO
- Page: Regional/Store Performance

**35. Revenue Concentration Index**
- Definition: Share of total revenue generated by the top 15% of stores.
- Formula: `SUM(Revenue, Top 15% Stores by Revenue) / Total Revenue`
- Purpose: Direct measurement of Problem #7 (fragility risk).
- Stakeholder: CEO, COO
- Page: Regional/Store Performance

---

## 7. Dashboard Wireframes (Textual Layout)

### Page 1 — Executive Overview
```
[Left Nav Bar]  |  INSIGHT360 — EXECUTIVE OVERVIEW
----------------|--------------------------------------------------------
                | [Global Filters: Date Range | Region | Channel | Category]
                |
                | [KPI Card: Total     [KPI Card: Gross    [KPI Card: YoY   [KPI Card: Loyalty
                |  Revenue, w/ trend    Margin %, w/       Growth %, w/     Penetration %,
                |  arrow]               target band]        trend arrow]    w/ trend arrow]
                |
                | [Large Line Chart: Revenue Trend, 12 months, current vs prior year overlay]
                |
                | [Region Map: color-coded by performance]   [Small Bar: Revenue by Channel]
                |
                | [Callout Text Box: "Auto-generated" narrative summary of top 2-3 movements]
```

### Page 2 — Sales & Revenue Deep Dive
```
[Left Nav Bar]  |  SALES & REVENUE DEEP DIVE
----------------|--------------------------------------------------------
                | [Filters carried from global + local Category filter]
                |
                | [Line: Revenue Trend by Channel]      [Bar: ATV by Region]
                |
                | [Funnel: Footfall → Conversion → Transaction]
                |
                | [Bar: Basket Size Trend, 8 quarters]  [Table: Top/Bottom 10 Stores by SSSG]
```

### Page 3 — Financial Performance
```
[Left Nav Bar]  |  FINANCIAL PERFORMANCE
----------------|--------------------------------------------------------
                | [Waterfall: Gross Revenue → Discounts → COGS → OpEx → Net Margin]
                |
                | [Bar: Operating Expense Ratio by Department]
                |
                | [Line: Gross Margin % Trend, 8 quarters, with target band]
                |
                | [Table: Budget vs Actual by Department, conditional formatting on variance]
```

### Page 4 — Customer Analytics
```
[Left Nav Bar]  |  CUSTOMER ANALYTICS
----------------|--------------------------------------------------------
                | [KPI Cards: Retention Rate | Loyalty Penetration | CAC | LTV]
                |
                | [Cohort Heatmap: Retention by Signup Month]
                |
                | [Donut: Customers by Segment]         [Bar: LTV by Segment]
                |
                | [Line: Repeat Purchase Rate, 30/60/90-day, trended]
```

### Page 5 — Product & Inventory
```
[Left Nav Bar]  |  PRODUCT & INVENTORY
----------------|--------------------------------------------------------
                | [Treemap: Category Margin Contribution]
                |
                | [Bar: Sell-Through Rate by Category]   [Bar: Return Rate by Category]
                |
                | [Matrix: SKU-level drill — Stock on Hand | Turnover | Stockout Flag]
                |
                | [Small Multiples: Inventory Aging by Division]
```

### Page 6 — Regional/Store Performance
```
[Left Nav Bar]  |  REGIONAL / STORE PERFORMANCE
----------------|--------------------------------------------------------
                | [Map: Region → Store drill-through, color = Revenue/Margin toggle]
                |
                | [Bar: Revenue per Sq Ft, ranked, top/bottom highlighted]
                |
                | [Bar: Sales per Employee-Hour, ranked]
                |
                | [Table: Store-level detail — Revenue | Margin | SSSG | Shrinkage]
```

### Page 7 — Forecast & Planning (Stretch)
```
[Left Nav Bar]  |  FORECAST & PLANNING
----------------|--------------------------------------------------------
                | [Line: Forecast vs Actual, trailing 12 months]
                |
                | [KPI Card: Forecast Accuracy %]
                |
                | [Bar: Forecasted Demand by Category, next quarter]
```

**Common elements across all pages:** persistent left-nav (icon + label), consistent color theme, page title in top-left, global filter bar pinned at top, footer with "Data as of [date]" for transparency.

---

## 8. Executive Reporting Strategy

- **Cadence:** Designed to simulate a monthly business review (MBR) cadence, with the dashboard always reflecting "as of" the most recent simulated period — directly addressing Problem #25 (slow 10+ day reporting cycle) by contrast: this report is designed to be always-current rather than a static end-of-month deck.
- **Inverted Pyramid principle:** Executive Overview answers "how is the business doing" in one glance; each subsequent page answers "why," in increasing detail; drill-through and matrix/table visuals answer "which specific store/SKU/customer," for the rare cases an executive needs to go that deep.
- **One-click recurring answers:** Bookmarks pre-package the questions leadership asks every single review cycle (e.g., "show me underperforming stores," "show me this quarter vs last"), removing the need to rebuild the same filter combination repeatedly.
- **Narrative pairing:** Every dashboard is paired with a short written insights document (Phase 8) — the dashboard shows *what* happened, the narrative explains *why it matters and what to do about it*, mirroring how insights are actually delivered in a real corporate setting (a dashboard alone rarely drives a decision; a dashboard plus a point of view does).
- **Single source of truth principle:** All KPIs are defined once in the KPI Catalog (Section 6) and reused identically across every page and stakeholder view — no page is allowed to redefine "Revenue" differently, which directly addresses the fragmented/inconsistent reporting pain point named by the CEO persona.

---

## 9. Star Schema Design (Conceptual)

```
                              ┌───────────────┐
                              │   Dim_Date    │
                              └───────┬───────┘
                                      │
        ┌───────────────┐    ┌───────┴────────┐    ┌────────────────┐
        │  Dim_Customer  │────┤                │────│   Dim_Store    │
        └───────────────┘    │                │    └────────────────┘
                              │  Fact_Sales    │
        ┌───────────────┐    │  (grain: 1 row │    ┌────────────────┐
        │  Dim_Product   │────┤  per sale line)│────│  Dim_Campaign  │
        └───────────────┘    └───────┬────────┘    └────────────────┘
                                      │
                     ┌────────────────┼────────────────┐
                     │                │                │
             ┌───────┴──────┐ ┌──────┴───────┐ ┌───────┴────────┐
             │ Fact_Returns │ │Fact_Inventory │ │ Fact_Staffing  │
             │ (FK: sales_id,│ │  _Snapshot   │ │ (FK: store_key,│
             │ product_key,  │ │(FK: product_ │ │  date_key)     │
             │ date_key)     │ │key, store_key,│ │                │
             │               │ │ date_key)    │ │                │
             └──────────────┘ └──────────────┘ └────────────────┘
```

**Design rationale:**
- **Fact_Sales** is the central fact table at transaction-line grain — the finest grain needed to support both aggregate KPIs (Total Revenue) and granular drill-through (SKU-level, store-level).
- **Fact_Returns, Fact_Inventory_Snapshot, and Fact_Staffing** are modeled as secondary fact tables at their own natural grain (rather than forced into Fact_Sales), since returns, inventory, and staffing are conceptually distinct business processes — this is standard Kimball practice ("one fact table per business process").
- **Dim_Date** is shared across all fact tables to enable consistent time intelligence and cross-fact analysis (e.g., "was a stockout linked to a subsequent lost-sale period").
- **Dim_Store** doubles as the location dimension for Online and Wholesale via virtual store records, avoiding a separate channel dimension while keeping the model simple — channel-level reporting is instead handled via a `channel` attribute rather than a fully separate dimension, since channel doesn't have its own rich attribute set beyond a handful of fields.
- **No snowflaking:** Dimensions are kept flat (denormalized) rather than snowflaked, which is the standard Power BI/DAX performance best practice and keeps the model easy to explain in a portfolio review.

---

## 10. Project Architecture Diagram

```
┌───────────────────────────┐
│   Raw / Simulated Data     │   Faker-generated transactions, store/product/
│                            │   customer masters, inventory snapshots
└─────────────┬──────────────┘
              │
              ▼
┌───────────────────────────┐
│  Python (Pandas/NumPy)     │   Cleaning, deduplication, null handling,
│  Cleaning & Validation     │   type casting, referential integrity checks
└─────────────┬──────────────┘
              │
              ▼
┌───────────────────────────┐
│  PostgreSQL Database       │   Staged, cleaned, queryable relational store
└─────────────┬──────────────┘
              │
              ▼
┌───────────────────────────┐
│  Star Schema Design        │   Fact_Sales + Fact_Returns + Fact_Inventory +
│                            │   Fact_Staffing, surrounded by Dim tables
└─────────────┬──────────────┘
              │
              ▼
┌───────────────────────────┐
│  Power BI                  │   Data model import, relationships,
│                            │   DAX measure layer, theme application
└─────────────┬──────────────┘
              │
              ▼
┌───────────────────────────┐
│  Executive Dashboard       │   6–7 pages per Section 7 wireframes
└─────────────┬──────────────┘
              │
              ▼
┌───────────────────────────┐
│  Business Insights         │   Written narrative analysis (Phase 8)
└─────────────┬──────────────┘
              │
              ▼
┌───────────────────────────┐
│  Presentation / Case Study │   Executive walkthrough deck
└─────────────┬──────────────┘
              │
              ▼
┌───────────────────────────┐
│  GitHub Repository         │   Versioned, documented, portfolio-ready
└─────────────┬──────────────┘
              │
              ▼
┌───────────────────────────┐
│  Portfolio                 │   Case study, screenshots, live report link
└───────────────────────────┘
```

---

## 11. GitHub Repository Structure

```
insight360-retail-bi/
│
├── README.md                        # Elevator pitch, architecture diagram, screenshots
│
├── /data
│   ├── /raw                         # Original synthetic data outputs (Faker)
│   └── /cleaned                     # Post-cleaning, validated datasets
│
├── /sql
│   ├── /schema                      # DDL for star schema (fact + dim tables)
│   └── /queries                     # Validation queries, sample analytical queries
│
├── /python
│   ├── /scripts                     # Data generation & cleaning scripts
│   └── /notebooks                   # EDA notebooks (Phase 5)
│
├── /powerbi
│   ├── Insight360.pbix              # Main report file
│   └── /theme                       # Custom Power BI theme JSON
│
├── /docs
│   ├── business_case.md             # Business problems, stakeholders, goals
│   ├── kpi_dictionary.md            # Full KPI catalog (Section 6, formalized)
│   ├── data_dictionary.md           # Full data dictionary (Section 5, formalized)
│   └── architecture.md              # Architecture diagram + explanation
│
├── /screenshots
│   └── (one high-res PNG per dashboard page, captioned)
│
└── /case-study
    └── insight360_case_study.md     # Problem → Approach → Insights → Impact
```

**Rationale:** Folder-per-phase mirrors the actual project lifecycle (Section 10 diagram), so a reviewer browsing the repo experiences the same story arc as the build process — this is intentional; the repo structure is itself part of the portfolio narrative, not just file storage.

---

## 12. Final Deliverables (Consolidated)

1. Expanded Business Requirements Document *(this document)*
2. Data dictionary & dataset generation plan
3. Cleaned, validated synthetic datasets
4. PostgreSQL database implementing the star schema
5. EDA summary with written observations
6. Validated Power BI data model with DAX measure layer
7. 6–7 page executive Power BI dashboard
8. Written executive insights narrative
9. Structured, documented GitHub repository
10. Polished README, KPI dictionary, and data dictionary
11. Case study, dashboard screenshots, and walkthrough recording
12. Resume/LinkedIn integration bullets

---

## Review Note

This expanded Phase 1 document formalizes scope, requirements, data structure, KPI definitions, and architecture in enough detail that Phase 2 (Dataset Research & Design) can begin directly from it without re-deriving business logic. The 15 priority business problems (Section 1.6) and 35 catalogued KPIs (Section 6) are the operative scope for the MVP build — the remaining problems and questions stay documented for portfolio depth but are not wired to v1 visuals, consistent with the original scoping note.

**Status: Awaiting your review and approval before proceeding to Phase 2.**
