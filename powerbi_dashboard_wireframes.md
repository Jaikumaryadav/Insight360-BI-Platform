# Insight360 Executive BI Platform
## Phase 5 — Power BI Dashboard Wireframes & Interaction Design

**Project:** Meridian Retail Group — Insight360 Executive Intelligence Platform
**Phase:** 5 — Business Intelligence & Power BI Strategy (Dashboard Design)
**Depends on:** `powerbi_model_and_dax.md` (data model + DAX measure library)

---

## Table of Contents

1. [Canvas & Global Standards](#1-canvas--global-standards)
2. [Color Palette & Accessibility](#2-color-palette--accessibility)
3. [Global & Page-Level Slicers](#3-global--page-level-slicers)
4. [Page 1 — Executive Overview Dashboard](#4-page-1--executive-overview-dashboard)
5. [Page 2 — Retail & Online Sales Performance](#5-page-2--retail--online-sales-performance)
6. [Page 3 — Supply Chain & Inventory Health](#6-page-3--supply-chain--inventory-health)
7. [Page 4 — Workforce & Staffing Productivity](#7-page-4--workforce--staffing-productivity)
8. [Drillthrough Pages](#8-drillthrough-pages)
9. [Tooltip Page Strategy](#9-tooltip-page-strategy)
10. [Cross-Filtering & Interaction Rules](#10-cross-filtering--interaction-rules)

---

## 1. Canvas & Global Standards

| Setting | Value |
|---|---|
| Canvas size | **1920 × 1080** (16:9, "Custom" type in Power BI Desktop) |
| Grid unit | 16px base grid; all visuals snap to 16px increments |
| Page margins | 24px on all sides |
| Header band height | 88px (fixed, all pages) |
| Slicer band height | 56px (fixed, sits directly under header) |
| KPI card row height | 160px |
| Content area | Remaining ~752px, divided per page layout below |
| Font — Headers | Segoe UI Semibold, 20pt |
| Font — KPI values | Segoe UI Bold, 32pt |
| Font — KPI labels | Segoe UI, 11pt, uppercase, letter-spacing wide |
| Font — Body/axis | Segoe UI, 9–10pt |
| Visual header icons | Enabled, minimal (filter/more-options only) |
| Page navigation | Custom nav bar (image-based buttons), top-right of header band, all 4 pages + "Home" |

All four report pages share the same header band, slicer band, and navigation bar — only the content area changes — so the report feels like a single cohesive application rather than four disconnected pages.

---

## 2. Color Palette & Accessibility

**Theme name:** `Insight360_DarkSlate`

| Role | Color | Hex |
|---|---|---|
| Canvas background | Slate (near-black) | `#0F1B2D` |
| Card/panel background | Dark Blue | `#16273F` |
| Primary brand / positive | Deep Blue | `#2E5C8A` |
| Secondary data series | Steel Blue | `#5B8DB8` |
| Tertiary data series | Muted Teal | `#4B9C9C` |
| Alert / negative / risk | Accent Orange | `#E8873A` |
| Critical alert (stockout <3 days) | Red-Orange | `#D9502C` |
| Positive delta / on-target | Soft Green | `#5FAE73` |
| Neutral text (primary) | Off-White | `#EDEFF2` |
| Neutral text (secondary/labels) | Cool Gray | `#9AA7B8` |
| Gridlines / borders | Low-contrast Slate | `#22334E` |

**Accessibility guidelines:**
- All text-on-background pairs meet **WCAG AA contrast ratio ≥ 4.5:1** (off-white `#EDEFF2` on slate `#0F1B2D` and card `#16273F` both pass).
- Color is never the sole encoding for status — KPI cards and risk tables pair color with an icon (▲/▼/⚠) and a text label ("On Target", "At Risk").
- Orange/red-orange alert colors are reserved exclusively for negative/risk states (stockouts, overtime spikes, missed targets) — never used decoratively elsewhere, so their appearance is always meaningful.
- Categorical charts (channel, region, division) use the blue/teal spectrum, which remains distinguishable under the most common forms of color vision deficiency (deuteranopia/protanopia); orange is reserved for alerts so it never collides with categorical hues.
- Minimum interactive target size (slicers, buttons, bookmark icons): 32×32px.
- All visuals have descriptive Alt Text populated (Power BI Format pane → General → Alt Text) for screen reader compatibility.

---

## 3. Global & Page-Level Slicers

### 3.1 Global Slicers (Slicer Band — appear identically on all 4 pages, synced via Sync Slicers pane)

| Slicer | Field | Type | Default |
|---|---|---|---|
| Date Range | `dim_date[date_key]` | Between (date range slider) | Last 12 months |
| Region | `dim_store[region]` | Dropdown, multi-select | All selected |
| Store Format | `dim_store[store_format]` | Dropdown, multi-select | All selected |
| Product Division | `dim_product[division]` | Dropdown, multi-select | All selected |

Positioned left-to-right in the slicer band; each slicer is 280px wide with 16px gutter. A **"Reset Filters"** bookmark button sits at the far right of the slicer band (icon-only, 32×32px).

### 3.2 Page-Level Slicers (additional, local to a single page — placed in a collapsible left rail, 200px wide, or inline above the visual it governs)

| Page | Additional Slicer | Field |
|---|---|---|
| Page 2 | Channel | `fact_sales[channel]` |
| Page 2 | Customer Segment | `dim_customer[customer_segment]` |
| Page 3 | Category | `dim_product[category]` |
| Page 4 | Store (single-select search) | `dim_store[store_name]` |

---

## 4. Page 1 — Executive Overview Dashboard

**Audience:** C-Suite & VP of Operations. Glance-and-go: five KPIs, four supporting visuals, zero scrolling.

### 4.1 Layout Grid (content area: 1920×752, y-offset starts at 168px)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  HEADER: "Insight360 — Executive Overview"      [Nav: P1 P2 P3 P4]  [Refresh] │  88px
├──────────────────────────────────────────────────────────────────────────────┤
│  Date Range | Region | Store Format | Product Division      [Reset Filters]  │  56px
├──────────────────────────────────────────────────────────────────────────────┤
│ ┌────────────┬────────────┬────────────┬────────────┬────────────┐          │
│ │ NET SALES  │ NET SALES  │ RETURN     │ STOCKOUT   │ SPLH       │          │  160px
│ │ ₹42.8Cr    │ YoY +8.4%▲ │ RATE 6.2%  │ RATE 4.1%  │ ₹1,240/hr  │          │
│ └────────────┴────────────┴────────────┴────────────┴────────────┘          │
├───────────────────────────────────────┬──────────────────────────────────────┤
│  (1) Net Sales Trend vs. Target        │  (2) Revenue & Return Rate           │
│      Line + Clustered Column           │      by Channel — Bar/Donut combo    │  ~340px
│      (960 × 340)                       │      (928 × 340)                     │
├───────────────────────────────────────┼──────────────────────────────────────┤
│  (3) Top 5 / Bottom 5 Categories       │  (4) Regional Performance Map        │
│      by Net Sales — Bar Chart          │      (Filled Map / Shape Map)        │  ~380px
│      (960 × 380)                       │      (928 × 380)                     │
└───────────────────────────────────────┴──────────────────────────────────────┘
```

### 4.2 KPI Cards (5 cards, 352px wide × 160px each, 16px gutter)

| Card | Measure | Format | Conditional Formatting |
|---|---|---|---|
| Net Sales | `[Net Sales]` | ₹ Cr/L abbreviated, 1 decimal | — |
| Net Sales YoY % | `[Net Sales YoY Growth %]` | +0.0%▲ / -0.0%▼ | Green if ≥0, Orange if <0 |
| Return Rate % | `[Return Rate %]` | 0.0% | Orange if >7%, else neutral |
| Stockout Rate % | `[Stockout Rate %]` | 0.0% | Orange if >5%, Red if >10% |
| Sales per Labor Hour | `[Sales per Labor Hour (SPLH)]` | ₹#,##0/hr | — |

Card style: **Card visual (New)** with sparkline enabled (12-month trend) under each value, target/YoY comparison shown as a small delta chip top-right.

### 4.3 Visual Specifications

**(1) Net Sales Trend vs. Target — Line and Clustered Column Chart**
- X-axis: `dim_date[Year-Month]` (sorted by `YearMonthSort`)
- Column (bars): `[Net Sales]` (Deep Blue `#2E5C8A`)
- Line: `Net Sales Target` (flat or planned target measure, Accent Orange `#E8873A`, dashed)
- Secondary line (optional): `[Net Sales YTD]`
- Data labels: on line only, values abbreviated
- Interaction: clicking a month cross-filters visuals 2–4 on this page

**(2) Revenue & Return Rate by Sales Channel — Bar/Donut Combo**
- Left half: horizontal bar chart — `fact_sales[channel]` × `[Net Sales]`, bars colored by channel (Online = Steel Blue, Store = Muted Teal)
- Right half: donut chart — same channel field × `[Return Rate %]`, center label shows `[Return Rate %]` overall
- Legend: bottom, shared between both

**(3) Top 5 & Bottom 5 Product Categories by Net Sales — Bar Chart**
- Type: horizontal bar chart, diverging layout (Top 5 ascending in green-blue gradient, Bottom 5 in orange gradient), OR Decomposition Tree if root-cause drill is prioritized by stakeholders
- Axis: `dim_product[category]`, Values: `[Net Sales]`
- Sort: value descending for Top 5 panel, ascending for Bottom 5 panel (two side-by-side small multiples within the same visual container using a "Top N" and "Bottom N" filter pair)
- Data labels: on bar end, ₹ abbreviated

**(4) Regional Performance Heatmap / Map Visual**
- Type: **Filled Map** (or Shape Map with India state boundaries GeoJSON if available)
- Location: `dim_store[state]` or `dim_store[region]`
- Color saturation: `[Net Sales]` (darker blue = higher)
- Tooltip: custom tooltip page (see Section 9) showing region KPI snapshot
- Fallback: if geographic shape file unavailable, substitute a **Matrix heatmap** — rows = `region`, columns = `store_format`, values = `[Net Sales]` with color scale conditional formatting

---

## 5. Page 2 — Retail & Online Sales Performance

**Focus:** Channel breakdown, customer segments, discount effectiveness.

### 5.1 Layout Grid

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  HEADER + NAV                                                                 │  88px
├──────────────────────────────────────────────────────────────────────────────┤
│  Global Slicers          | Channel | Customer Segment      [Reset Filters]   │  56px
├───────────────────────────────────────┬──────────────────────────────────────┤
│  (1) Gross vs. Net Sales Analysis      │  (2) Sales & Return Rate:            │
│      Waterfall Chart                   │      Physical Stores vs. Digital     │  ~360px
│      (960 × 360)                       │      Clustered Bar + Line combo      │
│                                         │      (928 × 360)                    │
├───────────────────────────────────────┼──────────────────────────────────────┤
│  (3) Customer Segment Contribution     │  (4) Top 10 SKUs Matrix              │
│      Loyalty Tier Donut + Segment      │      (Drillthrough enabled)          │  ~360px
│      Treemap                           │      (928 × 360)                    │
│      (960 × 360)                       │                                      │
└───────────────────────────────────────┴──────────────────────────────────────┘
```

### 5.2 Visual Specifications

**(1) Gross vs. Net Sales Analysis — Waterfall Chart**
- Category breakdown: `Total Gross Sales` → `– Discount Amount` → `– Returns/Refunds` → `= Net Sales`
- Category axis: fixed 4-step breakdown category (calculated table or measure-based waterfall using a disconnected "Step" table)
- Increase color: Steel Blue; Decrease color: Accent Orange; Total color: Deep Blue
- Data labels: value + % of gross, on each step

**(2) Sales & Return Rate — Physical Stores vs. Digital**
- Type: Clustered Bar (Net Sales) + Line (Return Rate %) combo
- Category axis: `fact_sales[channel]` grouped into "Store" vs "Online" (or full channel list if >2 channels exist)
- Bars: `[Net Sales]`; Line (secondary axis): `[Return Rate %]`
- Reference line: overall average return rate (dashed gray) for context

**(3) Customer Segment Contribution**
- Left: Donut chart — `dim_customer[loyalty_tier]` × `[Net Sales]`
- Right: Treemap — `dim_customer[customer_segment]` × `[Net Sales]`, colored by segment
- Both visuals cross-filter each other and downstream page visuals when a segment/tier is clicked

**(4) Top 10 SKUs Matrix (Drillthrough enabled)**
- Type: Matrix visual
- Rows: `dim_product[product_name]` (Top 10 filter by `[Net Sales]`)
- Columns: `channel`
- Values: `[Net Sales]`, `[Sales Quantity]`, `[Return Rate %]` (conditional formatting: data bars on Net Sales, color scale on Return Rate)
- Right-click row → **Drillthrough → "SKU Deep Dive"** page (see Section 8.1)

---

## 6. Page 3 — Supply Chain & Inventory Health

**Focus:** Stockouts, East Region bottleneck, Electronics risk, replenishment dynamics.

### 6.1 Layout Grid

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  HEADER + NAV                                                                 │  88px
├──────────────────────────────────────────────────────────────────────────────┤
│  Global Slicers                       | Category               [Reset]      │  56px
├───────────────────────────────────────┬──────────────────────────────────────┤
│  (1) Weekly Stockout Rate Trend        │  (2) Category Out-of-Stock Risk      │
│      by Region — Line Chart            │      Matrix (Scatter: Rate x Days)   │  ~340px
│      (960 × 340)                       │      (928 × 340)                    │
├───────────────────────────────────────┼──────────────────────────────────────┤
│  (3) Inventory Depletion &             │  (4) High-Risk SKU Alert Table       │
│      Replenishment Efficiency          │      (<3 days safety stock)          │  ~380px
│      Stacked Column (960 × 380)        │      (928 × 380)                    │
└───────────────────────────────────────┴──────────────────────────────────────┘
```

### 6.2 Visual Specifications

**(1) Weekly Stockout Rate Trend by Region — Line Chart**
- X-axis: `dim_date[week_number]` (within selected date range)
- Lines: one per `dim_store[region]`, legend at right
- **East region line explicitly highlighted**: use conditional formatting / focus mode styling — East rendered in Accent Orange at 3px weight, all other regions in muted Steel Blue at 1.5px weight, so the East spike is immediately visible without needing a filter
- Reference line: overall average `[Stockout Rate %]` (dashed gray)
- Annotation: data label callout on East's peak point

**(2) Category Out-of-Stock Risk Matrix — Scatter Plot**
- X-axis: `[Stockout Rate %]`
- Y-axis: `[Average Stockout Duration Days]`
- Size: `[Sales Quantity]` (bubble size = sales volume at risk)
- Legend/color: `dim_product[division]` — **Electronics rendered in Red-Orange `#D9502C`** as a fixed color override to flag it as the known risk division per business context
- Quadrant lines: median split lines (X and Y) forming 4 quadrants; top-right quadrant ("High Rate + Long Duration") shaded with a subtle red overlay as the "Critical Risk" zone
- Tooltip: custom tooltip page showing category detail (Section 9)

**(3) Inventory Depletion & Replenishment Efficiency — Stacked Column Chart**
- X-axis: `dim_date[Year-Month]` or `week_number`
- Stacked columns: `opening_stock` (base, Steel Blue), `– sales_qty` (depletion, Accent Orange), `+ replenished_qty` (Muted Teal), net to `closing_stock`
- Alternative simpler build: clustered column of `[Average Closing Stock]` vs `replenished_qty` vs `sales_qty` per period
- Data labels: closing stock value only, to avoid clutter

**(4) High-Risk SKU Alert Table**
- Type: Table visual (not matrix — flat alert list)
- Filter: `safety_stock` remaining coverage `< 3 days` (calculated column/measure: `Days of Cover = closing_stock / (sales_qty / 7)` or similar rate-based formula)
- Columns: `product_name`, `store_name`, `region`, `closing_stock`, `safety_stock`, `Days of Cover`, `stockout_duration_days`
- Conditional formatting: `Days of Cover` column — icon set (⚠ red if <1 day, ⚠ orange if 1–3 days)
- Sort: `Days of Cover` ascending (most urgent first)
- Row limit: top 25 visible, scrollable

---

## 7. Page 4 — Workforce & Staffing Productivity

**Focus:** Store labor costs, overtime spikes during festive seasons, SPLH.

### 7.1 Layout Grid

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  HEADER + NAV                                                                 │  88px
├──────────────────────────────────────────────────────────────────────────────┤
│  Global Slicers                       | Store (search)         [Reset]      │  56px
├───────────────────────────────────────┬──────────────────────────────────────┤
│  (1) SPLH by Store Format              │  (2) Weekly Overtime Hours vs.       │
│      Column Chart                      │      Festive Season Trend            │  ~340px
│      (960 × 340)                       │      Line + Shaded Area              │
│                                         │      (928 × 340)                    │
├───────────────────────────────────────┼──────────────────────────────────────┤
│  (3) Labor Cost vs. Store Revenue      │  (4) Physical Store Staffing         │
│      Scatter Chart                     │      Efficiency Table                │  ~380px
│      (960 × 380)                       │      (928 × 380)                    │
└───────────────────────────────────────┴──────────────────────────────────────┘
```

### 7.2 Visual Specifications

**(1) Sales per Labor Hour (SPLH) by Store Format — Column Chart**
- X-axis: `dim_store[store_format]`
- Y-axis: `[Sales per Labor Hour (SPLH)]`
- Color: single Deep Blue series; bars below company-average SPLH auto-highlighted in Accent Orange via conditional formatting rule
- Reference line: company-wide average SPLH (dashed gray)
- Secondary metric as data label: `[Total Labor Cost]` shown as a subtitle/callout per bar

**(2) Weekly Overtime Hours vs. Festive Season Trend**
- Type: Line chart with shaded background area
- X-axis: `dim_date[week_number]` (full year view recommended, override global date slicer via "Edit Interactions" if needed, or keep synced)
- Line: `[Total Overtime Hours]` (Accent Orange)
- Background shading: weeks where `dim_date[is_festive_period] = TRUE` shaded in a translucent Muted Teal band (achieved via a second area-chart layer or a "Festive Period" reference band using analytics pane shading)
- Annotation: peak overtime week labeled with data callout

**(3) Labor Cost vs. Store Revenue Comparison — Scatter Chart**
- X-axis: `[Net Sales]` (per store)
- Y-axis: `[Total Labor Cost]` (per store)
- Size: `[Sales per Labor Hour (SPLH)]`
- Color: `dim_store[region]`
- Trend line: enabled (linear), to visually flag stores below the cost-efficiency trend line as outliers
- Tooltip: store name, format, region, SPLH, labor cost %, on hover

**(4) Physical Store Staffing Efficiency Table**
- Type: Table or Matrix visual
- Rows: `dim_store[store_name]`
- Columns: `allocated_headcount`, `actual_headcount`, `[Headcount Variance]`, `[Total Labor Hours]`, `[Total Overtime Hours]`, `[Sales per Labor Hour (SPLH)]`, `[Labor Cost as % of Net Sales]`
- Conditional formatting: data bars on SPLH, icon set (red/orange/green) on `Headcount Variance`
- Sort: SPLH descending (best performers first) with a toggle bookmark to re-sort ascending (worst-first) for management review mode

---

## 8. Drillthrough Pages

### 8.1 "SKU Deep Dive" Drillthrough Page
- **Entry points:** Page 2 Top 10 SKUs Matrix (row right-click), Page 3 Category Risk Matrix (bubble right-click)
- **Drillthrough filter field:** `dim_product[product_name]` (and `sku`)
- **Page contents:**
  - Header: SKU name, SKU code, division/category/subcategory breadcrumb, brand
  - KPI cards: `[Net Sales]`, `[Sales Quantity]`, `[Return Rate %]`, `[Average Closing Stock]`, `[Stockout Rate %]` — all scoped to this SKU
  - Trend chart: monthly Net Sales + Stockout Rate combo line, 12-month lookback
  - Store-level table: this SKU's performance across all stores (Net Sales, Stockout Rate, Closing Stock) sorted by Net Sales descending
  - **"Back" button** (standard Power BI back arrow) top-left

### 8.2 "Store Deep Dive" Drillthrough Page
- **Entry points:** Page 1 Regional Map, Page 4 Labor Cost vs. Revenue Scatter, Page 4 Staffing Efficiency Table
- **Drillthrough filter field:** `dim_store[store_name]`
- **Page contents:**
  - Header: store name, format, region, city/state, manager name, opening date
  - KPI cards: `[Net Sales]`, `[Return Rate %]`, `[Stockout Rate %]`, `[Sales per Labor Hour (SPLH)]`, `[Total Labor Cost]`
  - Category performance bar chart for this store
  - Staffing trend line (actual vs. allocated headcount, weekly)
  - **"Back" button** top-left

Both drillthrough pages are excluded from the page navigation bar (right-click page tab → "Hide page") and are reachable only via drillthrough or direct bookmark link.

---

## 9. Tooltip Page Strategy

Two custom **report page tooltips** (small canvas, 320×240px, "Allow use as tooltip" enabled in Page Information):

### 9.1 "Region Snapshot" Tooltip
- **Used by:** Page 1 Regional Map/Heatmap
- **Triggered on:** hover over a region
- **Contents:** region name, `[Net Sales]`, `[Net Sales YoY Growth %]`, `[Return Rate %]`, `[Stockout Rate %]`, mini sparkline of 6-month Net Sales trend
- Fields parameter: `dim_store[region]` set as the tooltip page's filter context field

### 9.2 "Category Risk Snapshot" Tooltip
- **Used by:** Page 3 Category Out-of-Stock Risk Matrix (scatter bubbles)
- **Triggered on:** hover over a bubble
- **Contents:** division/category name, `[Stockout Rate %]`, `[Average Stockout Duration Days]`, `[Average Closing Stock]`, count of active SKUs in category
- Fields parameter: `dim_product[division]` / `dim_product[category]` as filter context

Both tooltip pages inherit the report theme (dark slate background, off-white text) so they feel native rather than like a default white Power BI popup.

---

## 10. Cross-Filtering & Interaction Rules

| Rule | Detail |
|---|---|
| Default cross-filter behavior | All visuals within a page cross-filter each other (highlight mode) unless explicitly disabled below |
| Page 1 → KPI cards | KPI cards do **not** get cross-filtered by clicking visuals below them (Edit Interactions → None) — they always reflect the full slicer-defined context, not an ad hoc click |
| Map visual (Page 1) | Cross-filters visuals 1–3 on click; does not cross-filter itself |
| Waterfall (Page 2) | Waterfall steps are not click-filterable (structural breakdown, not a filter source) — Edit Interactions → None on downstream visuals |
| Scatter plots (Page 3, Page 4) | Clicking a bubble filters companion table/visual on the same page; does not affect global slicers |
| Drillthrough | Right-click only (not single-click) to avoid accidental navigation; drillthrough button also exposed via a visible "Deep Dive →" button on Top 10 SKUs Matrix and Staffing Efficiency Table for discoverability |
| Sync Slicers | All 4 global slicers synced across all 4 main pages (not synced to drillthrough/tooltip pages, which use their own filter context) |
| Bookmarks | "Reset Filters" bookmark (clears all slicers), "Best Performers" / "At Risk" toggle bookmark on Page 4 staffing table sort order |
| Mobile layout | Each page has a companion Mobile Layout (Power BI Desktop → View → Mobile Layout) prioritizing KPI cards and the single highest-value chart per page, stacked vertically |
