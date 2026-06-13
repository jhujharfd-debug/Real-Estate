# Dubai Real Estate Intelligence Agent — Workflow Documentation

## System Architecture

```
Browser (HTML/CSS/JS)
    │
    ├── Chart.js (visualisations)
    ├── Bootstrap Icons (UI icons)
    └── Fetch API (AJAX calls)
         │
         ▼
Flask Application (app.py)
    │
    ├── Analysis Engine
    │   ├── calc_gross_yield()       — (Rent / Price) × 100
    │   ├── calc_net_yield()         — After service charges + vacancy
    │   ├── calc_roi()               — Net yield + appreciation rate
    │   ├── future_value()           — Compound growth FV = PV × (1+r)^n
    │   ├── monthly_cash_flow()      — Annual net income ÷ 12
    │   └── investment_score()       — Weighted 0–100 score
    │
    ├── Intelligence Engine
    │   ├── property_recs()          — AI recommendation bullets
    │   ├── community_insight()      — Community analysis bullets
    │   ├── market_insights()        — Full market intelligence report
    │   └── build_recommendations()  — Profile-matched community picks
    │
    ├── Lead Engine
    │   └── auto_score_lead()        — Budget + type + contact scoring
    │
    └── SQLite Database (database/realestate.db)
        ├── properties
        ├── communities
        ├── leads
        └── reports
```

## User Workflows

### 1. Property Analysis

1. Navigate to **Property Analyzer**
2. Enter property details (name, community, type, beds/baths, area, price, rent, service charges)
3. Click **Run AI Analysis**
4. System calculates:
   - Gross Yield = Annual Rent / Purchase Price × 100
   - Net Yield = (Rent × (1 - vacancy) - Service Charges) / Price × 100
   - ROI = Net Yield + Community Growth Rate
   - Future Values at 5 and 10 years
   - Investment Score (0–100)
5. AI recommendations and community insights are generated
6. 10-year projection chart is rendered
7. Property is saved to the database

### 2. Community Comparison

1. Navigate to **Community Comparison**
2. Select 2 or more communities (all 9 selected by default)
3. Click **Compare Selected**
4. System returns:
   - Ranked cards by investment score
   - Detailed comparison table (all metrics)
   - Rental yield bar chart
   - Growth rate bar chart
   - Investment score horizontal bar chart
   - Individual community insights

### 3. Investment Recommendations

1. Navigate to **Recommendations**
2. Set your profile:
   - Budget (AED)
   - Property type preference
   - Investment goal (Rental Income / Capital Growth / Balanced)
   - Minimum annual rental goal
   - Preferred communities
3. Click **Find My Best Investments**
4. System filters communities by budget compatibility, then scores each by goal fit
5. Top 6 matches returned with full metrics and 5-year projections

### 4. AI Market Insights

1. Navigate to **AI Market Insights**
2. Insights generate automatically on page load (or click Refresh)
3. Report includes:
   - Market overview with key statistics
   - Top 3 growth communities
   - Top 3 yield communities
   - Top 3 investment score communities
   - Emerging opportunities (undervalued + high growth)
   - Buyer / Seller / Investor intelligence
   - Risk alerts
   - Community yield vs growth chart
   - Investment score ranking chart
4. If OpenAI key is set, an AI-enhanced executive summary is prepended

### 5. Lead Management

1. Navigate to **Lead Management**
2. **Add lead**: Click Add Lead → fill form → Save
3. Lead is auto-scored (0–100) based on:
   - Budget (0–40 pts)
   - Lead type (Investor=30, Buyer=20, Seller=15)
   - Contact info completeness (email=15, phone=15)
4. **Edit lead**: Click pencil icon on any row
5. **Delete lead**: Click trash icon (confirmation required)
6. **Search**: Type in search box to filter by name/email/area
7. **Filter by type**: Use filter buttons (All / Investor / Buyer / Seller)
8. **Import**: Upload CSV file (supports drag-and-drop)

### 6. Reports

1. Navigate to **Reports**
2. Select report type:
   - **Market Overview** — Full 9-community analysis
   - **Community Report** — Select a specific community
   - **Executive Summary** — Top 5 communities + strategic overview
3. Click **Generate Report**
4. Report saved to database; download link appears
5. All saved reports listed in the table below with individual download buttons

### 7. CSV Upload

Supported CSV schemas:

**Properties**:
```
property_name, community, type, price, area, bedrooms, bathrooms, annual_rent, service_charges, status
```

**Leads**:
```
name, email, phone, lead_type, budget, preferred_area, notes
```

## Investment Score Formula

```
score = (gross_yield × 6)   [max 40 pts]
      + (total_roi × 3.5)   [max 35 pts]
      + (growth_rate × 1.9) [max 25 pts]
      - risk_penalty         [Low=0, Medium=-5, High=-15]

Clamped to 0–100.
```

## Lead Scoring Formula

```
score = budget_pts (0–40)       # 5M+ → 40, 2M+ → 30, 1M+ → 20, 500K+ → 10
      + type_pts (5–30)          # Investor=30, Buyer=20, Seller=15, other=5
      + contact_pts (0–30)       # email=15, phone=15

Clamped to 0–100.
```

## Database Schema

```sql
properties (id, property_name, community, type, price, area, bedrooms, bathrooms,
            annual_rent, service_charges, status, created_at)

communities (id, community_name, avg_price_sqft, avg_annual_rent, growth_rate,
             rental_yield, investment_score, last_updated)

leads (id, name, email, phone, lead_type, budget, preferred_area, notes,
       score, status, created_at)

reports (id, report_name, generated_date, report_type, report_data)
```

## Environment Variables

| Variable | Purpose | Required |
|----------|---------|---------|
| `OPENAI_API_KEY` | OpenAI API key for enhanced insights | No |

## Running in Production

For production deployment, replace the dev server with Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```
