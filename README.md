# Dubai Real Estate Intelligence Agent

Professional AI-powered property investment analysis platform for Dubai's property market.

## Features

- **Property Analyzer** — ROI, rental yield, cash flow, appreciation forecast, AI recommendations
- **Community Comparison** — 9 Dubai communities side-by-side with charts
- **Investment Recommendations** — AI-matched picks based on your budget and goals
- **AI Market Insights** — Comprehensive market intelligence report (optionally OpenAI-enhanced)
- **Lead Management** — Full CRUD with auto-scoring and CSV import
- **Reports & Downloads** — Downloadable market, community, and executive reports
- **CSV Upload** — Import property listings and lead data

## Installation

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. (Optional) Set OpenAI API key

```bash
# Windows PowerShell
$env:OPENAI_API_KEY = "sk-your-key-here"

# Windows Command Prompt
set OPENAI_API_KEY=sk-your-key-here
```

Without an API key the app runs in rule-based mode — all features work, AI insights are generated from built-in logic.

### 3. Run the application

```bash
python app.py
```

### 4. Open in browser

Visit: **http://127.0.0.1:5000**

## VS Code Setup

1. Open the project folder: `File → Open Folder → Dubai Real Estate`
2. Install the Python extension
3. Select the Python interpreter: `Ctrl+Shift+P → Python: Select Interpreter`
4. Open integrated terminal: `` Ctrl+` ``
5. Run: `pip install -r requirements.txt && python app.py`
6. Click the link in the terminal output

## Project Structure

```
Dubai Real Estate/
├── app.py                    # Flask backend — all API endpoints and analysis logic
├── requirements.txt          # Python dependencies
├── database/
│   └── realestate.db         # SQLite database (auto-created on first run)
├── templates/
│   ├── base.html             # Shared layout, sidebar, topbar
│   ├── index.html            # Home page
│   ├── property_analyzer.html
│   ├── community_comparison.html
│   ├── recommendations.html
│   ├── insights.html
│   ├── leads.html
│   └── reports.html
├── static/
│   ├── css/style.css         # Full corporate dark theme
│   └── js/app.js             # Shared utilities and chart config
├── data/
│   ├── dubai_properties.csv  # Sample property listings
│   ├── dubai_market_data.csv # Community market benchmarks
│   └── dubai_rentals.csv     # Rental data by bedroom count
└── uploads/                  # Uploaded CSV files (auto-created)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analyze-property` | Analyze a property (ROI, yield, score, recommendations) |
| POST | `/api/compare-communities` | Compare 2–9 communities |
| POST | `/api/get-recommendations` | AI property recommendations |
| POST | `/api/generate-insights` | Full AI market intelligence report |
| GET  | `/api/leads` | List leads (supports ?q=search&type=Investor) |
| POST | `/api/leads` | Add new lead (auto-scored) |
| GET  | `/api/leads/<id>` | Get single lead |
| PUT  | `/api/leads/<id>` | Update lead |
| DELETE | `/api/leads/<id>` | Delete lead |
| POST | `/api/upload-csv` | Upload CSV (data_type: properties or leads) |
| POST | `/api/generate-report` | Generate and save report |
| GET  | `/api/download-report/<id>` | Download report as text file |
| GET  | `/api/properties` | List stored properties |
| GET  | `/api/communities` | Get all community data |

## Community Data Coverage

| Community | Avg AED/sqft | Yield | Growth | Score |
|-----------|-------------|-------|--------|-------|
| Dubai Marina | 1,850 | 6.2% | 8.5% | 85 |
| Downtown Dubai | 2,200 | 5.8% | 7.8% | 87 |
| Business Bay | 1,650 | 6.8% | 9.2% | 83 |
| JVC | 950 | 7.8% | 10.5% | 80 |
| Palm Jumeirah | 2,800 | 5.2% | 6.5% | 82 |
| Dubai Hills Estate | 1,450 | 5.9% | 11.2% | 84 |
| Arabian Ranches | 1,200 | 5.5% | 7.2% | 78 |
| Meydan | 1,350 | 6.5% | 12.8% | 79 |
| Dubai Creek Harbour | 1,750 | 6.0% | 13.5% | 81 |

## Technologies

- **Backend**: Python 3.9+, Flask 2.3+, SQLite, Pandas, NumPy
- **Frontend**: HTML5, CSS3, Vanilla JavaScript, Chart.js 4, Bootstrap Icons
- **AI**: Rule-based engine + optional OpenAI GPT-3.5 Turbo
- **Reports**: Plain-text downloadable reports

## Disclaimer

All market data is approximate and for investment guidance purposes only. Always conduct professional due diligence before any real estate transaction.
