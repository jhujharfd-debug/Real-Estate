"""
Dubai Real Estate Intelligence Agent
=====================================
Professional AI-powered real estate analysis platform for Dubai's property market.
Designed for investors, brokers, developers, property managers, and buyers.

Tech Stack: Flask | SQLite | Pandas | NumPy | Optional OpenAI
Run:        python app.py
Visit:      http://127.0.0.1:5000
"""

import os
import json
import sqlite3
import pandas as pd
import numpy as np
import csv
import io
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file

# ── Optional OpenAI integration ───────────────────────────────────────────────
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# ── App Setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB upload cap

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.join(BASE_DIR, 'data')

# On Vercel only /tmp is writable; fall back to local paths for dev
_WRITABLE   = '/tmp' if os.environ.get('VERCEL') else BASE_DIR
DATABASE    = os.path.join(_WRITABLE, 'realestate.db')
UPLOAD_DIR  = os.path.join(_WRITABLE, 'uploads')

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── OpenAI (optional) ─────────────────────────────────────────────────────────
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
openai_client  = None
if OPENAI_AVAILABLE and OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ══════════════════════════════════════════════════════════════════════════════
# COMMUNITY MARKET DATA  (Dubai 2024 approximate figures)
# ══════════════════════════════════════════════════════════════════════════════
COMMUNITIES = {
    'Dubai Marina': {
        'avg_price_sqft': 1850, 'avg_annual_rent': 125000, 'growth_rate': 8.5,
        'rental_yield': 6.2, 'investment_score': 85, 'type': 'Waterfront',
        'risk': 'Medium', 'min_price': 800000, 'max_price': 15000000,
        'strengths': ['High rental demand', 'Waterfront lifestyle', 'Metro access', 'Expat favourite'],
        'risks':     ['High competition', 'Elevated service charges', 'Parking costs'],
        'best_for':  'Rental income investors, expat professionals',
        'popular_units': 'Studios, 1BR, 2BR apartments, penthouses',
        'emoji': '⚓'
    },
    'Downtown Dubai': {
        'avg_price_sqft': 2200, 'avg_annual_rent': 155000, 'growth_rate': 7.8,
        'rental_yield': 5.8, 'investment_score': 87, 'type': 'Urban Premium',
        'risk': 'Low', 'min_price': 1200000, 'max_price': 50000000,
        'strengths': ['Brand value', 'Capital appreciation', 'Tourism demand', 'World-class infrastructure'],
        'risks':     ['Premium pricing', 'High service charges', 'Traffic congestion'],
        'best_for':  'Capital appreciation investors, luxury buyers',
        'popular_units': 'Apartments, penthouses, hotel apartments',
        'emoji': '🏙️'
    },
    'Business Bay': {
        'avg_price_sqft': 1650, 'avg_annual_rent': 110000, 'growth_rate': 9.2,
        'rental_yield': 6.8, 'investment_score': 83, 'type': 'Business District',
        'risk': 'Medium', 'min_price': 600000, 'max_price': 12000000,
        'strengths': ['High rental yields', 'Business hub', 'Canal views', 'Strong growth momentum'],
        'risks':     ['Oversupply risk in studios', 'Traffic', 'Ongoing construction'],
        'best_for':  'Yield-focused investors, working professionals',
        'popular_units': 'Studios, 1BR, hotel apartments',
        'emoji': '🏢'
    },
    'Jumeirah Village Circle (JVC)': {
        'avg_price_sqft': 950, 'avg_annual_rent': 65000, 'growth_rate': 10.5,
        'rental_yield': 7.8, 'investment_score': 80, 'type': 'Affordable',
        'risk': 'Medium-Low', 'min_price': 350000, 'max_price': 3000000,
        'strengths': ['Affordable entry point', 'Highest rental yields', 'Community growth', 'Diverse supply'],
        'risks':     ['Traffic bottlenecks', 'No metro access', 'Still developing'],
        'best_for':  'First-time investors, budget buyers, yield maximizers',
        'popular_units': 'Studios, 1BR, 2BR, townhouses',
        'emoji': '🏘️'
    },
    'Palm Jumeirah': {
        'avg_price_sqft': 2800, 'avg_annual_rent': 200000, 'growth_rate': 6.5,
        'rental_yield': 5.2, 'investment_score': 82, 'type': 'Ultra-Luxury',
        'risk': 'Low-Medium', 'min_price': 2000000, 'max_price': 200000000,
        'strengths': ['World-famous address', 'Luxury lifestyle', 'HNW tenant pool', 'Holiday home premium'],
        'risks':     ['Very high entry cost', 'Niche market', 'Limited liquidity'],
        'best_for':  'Luxury investors, wealth preservation, holiday homes',
        'popular_units': 'Apartments, signature villas, penthouses',
        'emoji': '🌴'
    },
    'Dubai Hills Estate': {
        'avg_price_sqft': 1450, 'avg_annual_rent': 140000, 'growth_rate': 11.2,
        'rental_yield': 5.9, 'investment_score': 84, 'type': 'Premium Family',
        'risk': 'Low', 'min_price': 1500000, 'max_price': 25000000,
        'strengths': ['Family lifestyle', 'Golf course', 'Mall proximity', 'Strong appreciation'],
        'risks':     ['Car-dependent', 'High villa service charges'],
        'best_for':  'Family investors, long-term capital growth seekers',
        'popular_units': 'Villas, townhouses, apartments',
        'emoji': '⛳'
    },
    'Arabian Ranches': {
        'avg_price_sqft': 1200, 'avg_annual_rent': 180000, 'growth_rate': 7.2,
        'rental_yield': 5.5, 'investment_score': 78, 'type': 'Villa Community',
        'risk': 'Low', 'min_price': 2500000, 'max_price': 20000000,
        'strengths': ['Established community', 'Family lifestyle', 'Good schools nearby', 'Stable returns'],
        'risks':     ['Car-dependent', 'Distance from CBD', 'Limited apartments'],
        'best_for':  'Family buyers, long-term stable investors',
        'popular_units': 'Villas, townhouses',
        'emoji': '🐎'
    },
    'Meydan': {
        'avg_price_sqft': 1350, 'avg_annual_rent': 95000, 'growth_rate': 12.8,
        'rental_yield': 6.5, 'investment_score': 79, 'type': 'Emerging Premium',
        'risk': 'Medium', 'min_price': 800000, 'max_price': 15000000,
        'strengths': ['High growth potential', 'Racecourse lifestyle', 'New developments', 'Luxury amenities'],
        'risks':     ['Still maturing', 'Limited retail', 'Traffic on race days'],
        'best_for':  'Growth-oriented investors, lifestyle buyers',
        'popular_units': 'Villas, townhouses, apartments',
        'emoji': '🏇'
    },
    'Dubai Creek Harbour': {
        'avg_price_sqft': 1750, 'avg_annual_rent': 105000, 'growth_rate': 13.5,
        'rental_yield': 6.0, 'investment_score': 81, 'type': 'Waterfront Emerging',
        'risk': 'Medium', 'min_price': 900000, 'max_price': 20000000,
        'strengths': ['Future landmark district', 'Waterfront living', 'Strong appreciation path', 'Creek Tower'],
        'risks':     ['Under development', 'Limited current amenities', 'Longer ROI timeline'],
        'best_for':  'Off-plan investors, long-horizon buyers',
        'popular_units': 'Apartments, penthouses',
        'emoji': '🌊'
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# DATABASE LAYER
# ══════════════════════════════════════════════════════════════════════════════

def get_db():
    """Open a database connection with row-as-dict factory."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create schema and seed with sample Dubai property data."""
    conn = get_db()
    cur  = conn.cursor()

    cur.executescript('''
        CREATE TABLE IF NOT EXISTS properties (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            property_name   TEXT    NOT NULL,
            community       TEXT    NOT NULL,
            type            TEXT    NOT NULL,
            price           REAL    NOT NULL,
            area            REAL    NOT NULL,
            bedrooms        INTEGER NOT NULL DEFAULT 0,
            bathrooms       INTEGER NOT NULL DEFAULT 0,
            annual_rent     REAL    DEFAULT 0,
            service_charges REAL    DEFAULT 0,
            status          TEXT    DEFAULT "Ready",
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS communities (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            community_name  TEXT    UNIQUE NOT NULL,
            avg_price_sqft  REAL,
            avg_annual_rent REAL,
            growth_rate     REAL,
            rental_yield    REAL,
            investment_score REAL,
            last_updated    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS leads (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL,
            email           TEXT,
            phone           TEXT,
            lead_type       TEXT    DEFAULT "Buyer",
            budget          REAL    DEFAULT 0,
            preferred_area  TEXT,
            notes           TEXT,
            score           INTEGER DEFAULT 0,
            status          TEXT    DEFAULT "New",
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS reports (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            report_name     TEXT    NOT NULL,
            generated_date  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            report_type     TEXT    NOT NULL,
            report_data     TEXT
        );
    ''')

    # Seed community reference table
    for name, data in COMMUNITIES.items():
        cur.execute('''
            INSERT OR IGNORE INTO communities
              (community_name, avg_price_sqft, avg_annual_rent,
               growth_rate, rental_yield, investment_score)
            VALUES (?,?,?,?,?,?)
        ''', (name, data['avg_price_sqft'], data['avg_annual_rent'],
              data['growth_rate'], data['rental_yield'], data['investment_score']))

    # Seed sample properties if table is empty
    if cur.execute('SELECT COUNT(*) FROM properties').fetchone()[0] == 0:
        sample = [
            ('Marina Heights Tower',      'Dubai Marina',               'Apartment', 1850000, 950,  2, 2, 115000, 18000, 'Ready'),
            ('Burj Vista Residence',       'Downtown Dubai',             'Apartment', 3200000, 1450, 3, 3, 180000, 28000, 'Ready'),
            ('Canal Front Residence',      'Business Bay',               'Apartment', 1200000, 750,  1, 1,  82000, 14000, 'Ready'),
            ('JVC Circle Terrace',         'Jumeirah Village Circle (JVC)', 'Apartment', 680000, 800, 2, 2, 55000,  9000, 'Ready'),
            ('Signature Villa Palm',       'Palm Jumeirah',              'Villa',    12500000, 4500, 5, 6, 580000, 75000, 'Ready'),
            ('Hills Park Townhouse',       'Dubai Hills Estate',         'Townhouse', 2800000, 2200, 4, 4, 160000, 22000, 'Ready'),
            ('Ranches Garden Villas',      'Arabian Ranches',            'Villa',     4200000, 3200, 5, 5, 220000, 30000, 'Ready'),
            ('Polo Villas Meydan',         'Meydan',                     'Villa',     3500000, 2800, 4, 4, 210000, 25000, 'Ready'),
            ('Creek Horizon Tower',        'Dubai Creek Harbour',        'Apartment', 1600000, 900,  2, 2,  95000, 16000, 'Off-Plan'),
            ('Marina Gate Studio',         'Dubai Marina',               'Studio',     720000, 450,  0, 1,  60000,  9500, 'Ready'),
            ('Vida Residence Downtown',    'Downtown Dubai',             'Apartment', 2100000, 1100, 2, 2, 130000, 22000, 'Ready'),
            ('Bay Square Office',          'Business Bay',               'Office',    1800000, 1200, 0, 2, 140000, 18000, 'Ready'),
            ('JVC Community Tower',        'Jumeirah Village Circle (JVC)', 'Apartment', 480000, 600, 1, 1, 42000,  7000, 'Ready'),
            ('Shoreline Apartments Palm',  'Palm Jumeirah',              'Apartment', 2500000, 1350, 2, 2, 140000, 20000, 'Ready'),
            ('Hills View Apartment',       'Dubai Hills Estate',         'Apartment', 1650000, 1050, 2, 2,  98000, 16000, 'Ready'),
            ('Creek Vista Glory',          'Dubai Creek Harbour',        'Apartment', 1950000, 1100, 2, 2, 115000, 19000, 'Off-Plan'),
            ('Meydan Avenue Townhouse',    'Meydan',                     'Townhouse', 2200000, 1800, 3, 3, 140000, 20000, 'Ready'),
            ('Arabian Ranches 3 Villa',    'Arabian Ranches',            'Villa',     3800000, 2900, 4, 4, 200000, 27000, 'Off-Plan'),
        ]
        cur.executemany('''
            INSERT INTO properties
              (property_name, community, type, price, area, bedrooms, bathrooms,
               annual_rent, service_charges, status)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        ''', sample)

    # Seed sample leads if empty
    if cur.execute('SELECT COUNT(*) FROM leads').fetchone()[0] == 0:
        leads_seed = [
            ('Ahmed Al Mansoori',   'ahmed@example.com',   '+971501234567', 'Investor', 5000000, 'Downtown Dubai',            'Seeking rental income property for portfolio expansion', 88, 'Hot'),
            ('Sarah Johnson',       'sarah@example.com',   '+971509876543', 'Buyer',    2500000, 'Dubai Hills Estate',        'UK family relocating, needs 4BR villa by Q3 2025',     75, 'Warm'),
            ('Wei Zhang',           'wei@example.com',     '+971551234567', 'Investor', 1500000, 'Business Bay',             'Portfolio expansion, prefers high yield assets',        92, 'Hot'),
            ('Priya Sharma',        'priya@example.com',   '+971521234567', 'Buyer',     800000, 'Jumeirah Village Circle (JVC)', 'First-time buyer, needs 2BR apartment',           60, 'Warm'),
            ("Michael O'Brien",     'michael@example.com', '+971561234567', 'Seller',        0, 'Dubai Marina',             'Selling 3BR apartment, urgent timeline',               70, 'Active'),
            ('Fatima Al Rashidi',   'fatima@example.com',  '+971507654321', 'Investor', 8000000, 'Palm Jumeirah',            'UHNW client, looking for holiday home + rental',       95, 'Hot'),
            ('David Williams',      'david@example.com',   '+971531234567', 'Buyer',    1200000, 'Dubai Marina',             'Relocating from London, prefers waterfront',           65, 'Warm'),
        ]
        cur.executemany('''
            INSERT INTO leads
              (name, email, phone, lead_type, budget, preferred_area, notes, score, status)
            VALUES (?,?,?,?,?,?,?,?,?)
        ''', leads_seed)

    conn.commit()
    conn.close()

# ══════════════════════════════════════════════════════════════════════════════
# ANALYSIS ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def calc_gross_yield(annual_rent, price):
    if price <= 0: return 0.0
    return round((annual_rent / price) * 100, 2)

def calc_net_yield(annual_rent, price, svc_charges, vacancy=0.05):
    if price <= 0: return 0.0
    net_income = annual_rent * (1 - vacancy) - svc_charges
    return round((net_income / price) * 100, 2)

def calc_roi(annual_rent, price, svc_charges, growth_rate, vacancy=0.05):
    return round(calc_net_yield(annual_rent, price, svc_charges, vacancy) + growth_rate, 2)

def future_value(price, growth_rate, years):
    """Compound appreciation: FV = PV × (1 + r)^n"""
    return round(price * ((1 + growth_rate / 100) ** years), 0)

def monthly_cash_flow(annual_rent, svc_charges, vacancy=0.05):
    net_annual = annual_rent * (1 - vacancy) - svc_charges
    return round(net_annual / 12, 0)

def investment_score(yield_val, roi, growth_rate, risk='Medium'):
    # Weighted scoring: yield 40% | ROI 35% | growth 25%
    y_score = min(yield_val * 6, 40)
    r_score = min(roi * 3.5, 35)
    g_score = min(growth_rate * 1.9, 25)
    penalties = {'Low': 0, 'Low-Medium': -2, 'Medium': -5, 'Medium-High': -10, 'High': -15}
    total = y_score + r_score + g_score + penalties.get(risk, -5)
    return max(0, min(100, round(total, 1)))

def property_recs(data):
    """Build AI-style recommendation bullets for a property."""
    score = data.get('investment_score', 50)
    y     = data.get('gross_yield', 0)
    roi   = data.get('roi', 0)
    comm  = data.get('community', '')
    ptype = data.get('property_type', 'Property')
    info  = COMMUNITIES.get(comm, {})
    risk  = info.get('risk', 'Medium')
    recs  = []

    # Yield verdict
    if y >= 7:
        recs.append(f"STRONG BUY: {ptype} delivers {y}% gross yield — well above Dubai average of 5.5–6.5%. Excellent income-generating asset.")
    elif y >= 5.5:
        recs.append(f"BUY: Solid {y}% gross yield aligns with Dubai benchmarks. Good income-generating asset.")
    elif y >= 4:
        recs.append(f"HOLD/CONSIDER: Yield of {y}% is below average. Best suited for a capital-appreciation-led strategy.")
    else:
        recs.append(f"CAUTION: Low {y}% yield limits rental income potential. Renegotiate price or target appreciation play.")

    # ROI verdict
    if roi >= 12:
        recs.append(f"Outstanding total ROI of {roi}% (income + appreciation) — top-tier opportunity.")
    elif roi >= 8:
        recs.append(f"Strong total ROI of {roi}%. Well-positioned combining rental income and capital growth.")
    elif roi >= 5:
        recs.append(f"Moderate ROI of {roi}%. Verify that future appreciation meets your return target.")
    else:
        recs.append(f"ROI of {roi}% is below minimum benchmark. Negotiate price or explore alternative communities.")

    # Community insight
    if info:
        recs.append(f"{comm}: {info.get('growth_rate', 0)}% p.a. price growth | Risk: {risk} | Best for: {info.get('best_for', 'various investors')}.")

    # Score interpretation
    if score >= 80:
        recs.append(f"Investment Score {score}/100 — EXCELLENT. Top-tier Dubai investment opportunity.")
    elif score >= 65:
        recs.append(f"Investment Score {score}/100 — GOOD. Above-average fundamentals.")
    elif score >= 50:
        recs.append(f"Investment Score {score}/100 — AVERAGE. Acceptable with some risk factors.")
    else:
        recs.append(f"Investment Score {score}/100 — BELOW AVERAGE. Thorough due diligence required.")

    return recs

def community_insight(name):
    """Generate insight bullets for one community."""
    info = COMMUNITIES.get(name, {})
    if not info:
        return ["Community data not available."]
    g = info.get('growth_rate', 0)
    y = info.get('rental_yield', 0)
    bullets = []

    if g > 11:
        bullets.append(f"HIGH GROWTH ALERT: {g}% annual price growth — among Dubai's fastest-growing areas.")
    elif g > 8:
        bullets.append(f"STRONG GROWTH: {g}% annual appreciation well above market average.")
    else:
        bullets.append(f"STABLE GROWTH: Consistent {g}% annual appreciation — reliable long-term bet.")

    if y > 7:
        bullets.append(f"EXCEPTIONAL YIELD: {y}% places this community in Dubai's top-yield tier.")
    elif y > 5.5:
        bullets.append(f"MARKET-RATE YIELD: {y}% is in line with Dubai benchmarks.")
    else:
        bullets.append(f"APPRECIATION PLAY: {y}% yield — rewards capital growth over rental income.")

    for s in info.get('strengths', [])[:2]:
        bullets.append(f"Advantage: {s}")
    for r in info.get('risks', [])[:1]:
        bullets.append(f"Watch out: {r}")
    bullets.append(f"Best for: {info.get('best_for', 'Various investor profiles')}")
    return bullets

def market_insights():
    """Generate the full AI market intelligence report."""
    by_growth = sorted(COMMUNITIES.items(), key=lambda x: x[1]['growth_rate'], reverse=True)
    by_yield  = sorted(COMMUNITIES.items(), key=lambda x: x[1]['rental_yield'], reverse=True)
    by_score  = sorted(COMMUNITIES.items(), key=lambda x: x[1]['investment_score'], reverse=True)
    by_price  = sorted(COMMUNITIES.items(), key=lambda x: x[1]['avg_price_sqft'])
    undervalued = [c for c in by_price[:4] if COMMUNITIES[c[0]]['growth_rate'] > 9]

    avg_yield  = round(float(np.mean([v['rental_yield']  for v in COMMUNITIES.values()])), 1)
    avg_growth = round(float(np.mean([v['growth_rate']   for v in COMMUNITIES.values()])), 1)

    return {
        'market_overview': {
            'summary': (
                "Dubai's real estate market continues to outperform global peers, driven by strong population "
                "growth, tourism recovery, landmark regulatory reforms, and record foreign investment. "
                f"Average market appreciation stands at {avg_growth}% with rental yields averaging {avg_yield}%."
            ),
            'key_stats': {
                'avg_yield':        f"{avg_yield}%",
                'avg_growth':       f"{avg_growth}%",
                'communities':      len(COMMUNITIES),
                'top_yield_area':   by_yield[0][0],
                'fastest_growing':  by_growth[0][0],
                'safest_community': [c[0] for c in by_score if COMMUNITIES[c[0]]['risk'] == 'Low'][0],
            }
        },
        'top_growth': [
            {'name': n, 'growth': f"{d['growth_rate']}%", 'score': d['investment_score'],
             'note': f"{d['growth_rate']}% p.a. growth | Score {d['investment_score']}/100 | {d.get('best_for', '')}"}
            for n, d in by_growth[:3]
        ],
        'top_yield': [
            {'name': n, 'yield': f"{d['rental_yield']}%", 'price_sqft': f"AED {d['avg_price_sqft']:,}",
             'note': f"{d['rental_yield']}% gross yield at AED {d['avg_price_sqft']:,}/sqft"}
            for n, d in by_yield[:3]
        ],
        'top_investment': [
            {'name': n, 'score': d['investment_score'], 'type': d['type'], 'risk': d['risk']}
            for n, d in by_score[:3]
        ],
        'emerging': [
            {'name': n, 'price_sqft': f"AED {d['avg_price_sqft']:,}", 'growth': f"{d['growth_rate']}%",
             'note': f"Undervalued at AED {d['avg_price_sqft']:,}/sqft with {d['growth_rate']}% growth"}
            for n, d in undervalued
        ],
        'buyer_insights': [
            "Dubai's Golden Visa (AED 2M+ property) continues to drive premium property demand from global investors.",
            "Off-plan purchases offer 10–30% developer discounts with flexible post-handover payment plans.",
            "Freehold zones allow 100% foreign ownership — Marina, Downtown, JVC, Business Bay all eligible.",
            "Mortgage finance available for expats up to 75% LTV for first properties under AED 5M.",
            "Q1 and Q3 typically see more motivated sellers and fresh developer project launches.",
        ],
        'seller_insights': [
            "Dubai is in a seller's market phase — quality supply is below demand in prime locations.",
            "Properties priced within 5% of market value sell 60% faster in current conditions.",
            "Professional staging and photography can increase final sale price by 5–8%.",
            "International buyer pool is strongest in Q4 (Oct–Dec) when seasonal residents return.",
            "Ensure NOC from developer and clear title deed are ready before listing to avoid delays.",
        ],
        'investor_insights': [
            f"Highest total return: {by_growth[0][0]} — {by_growth[0][1]['growth_rate']}% growth + {by_growth[0][1]['rental_yield']}% yield.",
            f"Best pure yield play: {by_yield[0][0]} at {by_yield[0][1]['rental_yield']}% gross rental yield.",
            "Short-term rental (Airbnb) can generate 20–40% premium over long-term rent in Marina, Downtown, Palm.",
            "Off-plan in Dubai Creek Harbour and Meydan offers early-mover appreciation advantage.",
            "Portfolio diversification across 2–3 communities significantly reduces concentration risk.",
        ],
        'risk_alerts': [
            "Monitor US Fed interest rate movements — UAE dirham is pegged to USD; rates affect mortgage affordability.",
            "Oversupply risk in Business Bay studio segment — focus on 1BR+ for better occupancy rates.",
            "For off-plan purchases, verify developer RERA registration and escrow account compliance.",
            "Service charge hikes in aging buildings can erode net yields — review 5-year RERA records.",
            "Currency risk for non-AED investors is low — AED/USD peg at 3.67 stable since 1997.",
        ],
        'generated_at': datetime.now().strftime('%B %d, %Y at %H:%M')
    }

def build_recommendations(budget, prop_type, areas, goal, rent_goal):
    """Score and rank community recommendations against investor profile."""
    recs = []
    for area in areas:
        info = COMMUNITIES.get(area)
        if not info or budget < info.get('min_price', 0):
            continue
        # Skip villa-only areas for apartment searches
        if prop_type in ['Apartment', 'Studio'] and area in ['Arabian Ranches']:
            continue
        # Skip apartment-only areas for villa searches
        if prop_type in ['Villa'] and area in ['Dubai Marina', 'Business Bay']:
            continue

        est_price  = min(budget * 0.92, info['max_price'])
        est_area   = round(est_price / info['avg_price_sqft'])
        est_rent   = info['avg_annual_rent']
        est_svc    = est_area * 18  # ~AED18/sqft average service charge

        gy  = calc_gross_yield(est_rent, est_price)
        ny  = calc_net_yield(est_rent, est_price, est_svc)
        roi = calc_roi(est_rent, est_price, est_svc, info['growth_rate'])
        fv5 = int(future_value(est_price, info['growth_rate'], 5))
        scr = investment_score(gy, roi, info['growth_rate'], info['risk'])

        if goal == 'Rental Income':
            fit = min(95, gy * 12) if gy >= 6 else min(75, gy * 10)
        elif goal == 'Capital Growth':
            fit = min(95, info['growth_rate'] * 7) if info['growth_rate'] >= 10 else min(75, info['growth_rate'] * 5.5)
        else:
            fit = min(95, gy * 6 + info['growth_rate'] * 3)

        recs.append({
            'community':          area,
            'property_type':      prop_type,
            'estimated_price':    int(est_price),
            'estimated_area':     est_area,
            'est_annual_rent':    int(est_rent),
            'gross_yield':        gy,
            'net_yield':          ny,
            'total_roi':          roi,
            'growth_rate':        info['growth_rate'],
            'investment_score':   scr,
            'goal_fit':           round(fit),
            'risk_level':         info['risk'],
            'fv_5yr':             fv5,
            'capital_gain_5yr':   fv5 - int(est_price),
            'best_for':           info['best_for'],
            'strengths':          info['strengths'][:3],
            'type':               info['type'],
            'summary':            f"{area} offers {gy}% yield with {info['growth_rate']}% growth. {info['best_for']}."
        })

    recs.sort(key=lambda x: x['goal_fit'], reverse=True)
    return recs[:6]

def auto_score_lead(d):
    """Auto-score a lead 0–100 based on budget, type, and contact info."""
    score  = 0
    budget = float(d.get('budget', 0))
    ltype  = d.get('lead_type', 'Buyer')

    if   budget >= 5000000: score += 40
    elif budget >= 2000000: score += 30
    elif budget >= 1000000: score += 20
    elif budget >= 500000:  score += 10

    if   ltype == 'Investor': score += 30
    elif ltype == 'Buyer':    score += 20
    elif ltype == 'Seller':   score += 15
    else:                     score += 5

    if d.get('email'): score += 15
    if d.get('phone'): score += 15

    return min(score, 100)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    by_yield   = sorted(COMMUNITIES.items(), key=lambda x: x[1]['rental_yield'],   reverse=True)
    by_growth  = sorted(COMMUNITIES.items(), key=lambda x: x[1]['growth_rate'],    reverse=True)
    by_score   = sorted(COMMUNITIES.items(), key=lambda x: x[1]['investment_score'], reverse=True)
    conn = get_db()
    prop_count = conn.execute('SELECT COUNT(*) FROM properties').fetchone()[0]
    lead_count = conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
    conn.close()
    stats = {
        'properties':     prop_count,
        'leads':          lead_count,
        'communities':    len(COMMUNITIES),
        'top_yield_name': by_yield[0][0],
        'top_yield_val':  by_yield[0][1]['rental_yield'],
        'top_growth_name':by_growth[0][0],
        'top_growth_val': by_growth[0][1]['growth_rate'],
        'avg_yield':      round(float(np.mean([v['rental_yield']  for v in COMMUNITIES.values()])), 1),
        'avg_growth':     round(float(np.mean([v['growth_rate']   for v in COMMUNITIES.values()])), 1),
        'top3_score':     [{'name': n, 'score': d['investment_score'], 'type': d['type']} for n, d in by_score[:3]],
    }
    return render_template('index.html', stats=stats, communities=COMMUNITIES)

@app.route('/property-analyzer')
def property_analyzer():
    return render_template('property_analyzer.html', communities=list(COMMUNITIES.keys()))

@app.route('/community-comparison')
def community_comparison():
    return render_template('community_comparison.html', communities=COMMUNITIES)

@app.route('/recommendations')
def recommendations():
    return render_template('recommendations.html', communities=list(COMMUNITIES.keys()))

@app.route('/insights')
def insights():
    return render_template('insights.html')

@app.route('/leads')
def leads():
    return render_template('leads.html', communities=list(COMMUNITIES.keys()))

@app.route('/reports')
def reports():
    conn = get_db()
    saved = conn.execute('SELECT * FROM reports ORDER BY generated_date DESC LIMIT 30').fetchall()
    conn.close()
    return render_template('reports.html', reports=saved, communities=list(COMMUNITIES.keys()))

# ══════════════════════════════════════════════════════════════════════════════
# API — Property Analysis
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/analyze-property', methods=['POST'])
def api_analyze():
    try:
        d     = request.json
        name  = d.get('property_name', 'Property')
        comm  = d.get('community', '')
        ptype = d.get('property_type', 'Apartment')
        beds  = int(d.get('bedrooms', 0))
        baths = int(d.get('bathrooms', 1))
        area  = float(d.get('area_sqft', 0))
        price = float(d.get('purchase_price', 0))
        rent  = float(d.get('annual_rent', 0))
        svc   = float(d.get('service_charges', 0))

        if price <= 0:
            return jsonify({'error': 'Purchase price must be greater than 0'}), 400

        info       = COMMUNITIES.get(comm, {})
        growth     = info.get('growth_rate', 7.0)
        risk       = info.get('risk', 'Medium')
        price_sqft = round(price / area, 0) if area > 0 else 0
        gy         = calc_gross_yield(rent, price)
        ny         = calc_net_yield(rent, price, svc)
        roi        = calc_roi(rent, price, svc, growth)
        fv5        = int(future_value(price, growth, 5))
        fv10       = int(future_value(price, growth, 10))
        mcf        = int(monthly_cash_flow(rent, svc))
        score      = investment_score(gy, roi, growth, risk)

        rec_input = {
            'investment_score': score, 'gross_yield': gy, 'roi': roi,
            'community': comm, 'property_type': ptype
        }
        result = {
            'property_name': name, 'community': comm, 'property_type': ptype,
            'bedrooms': beds, 'bathrooms': baths, 'area_sqft': area,
            'purchase_price': price, 'annual_rent': rent, 'service_charges': svc,
            'price_per_sqft': price_sqft, 'gross_yield': gy, 'net_yield': ny,
            'roi': roi, 'growth_rate': growth, 'investment_score': score,
            'risk_level': risk, 'monthly_cash_flow': mcf,
            'fv_5yr': fv5, 'fv_10yr': fv10,
            'gain_5yr': fv5 - int(price), 'gain_10yr': fv10 - int(price),
            'recommendations': property_recs(rec_input),
            'community_insight': community_insight(comm),
            'community_info': info
        }

        conn = get_db()
        conn.execute('''
            INSERT INTO properties
              (property_name,community,type,price,area,bedrooms,bathrooms,annual_rent,service_charges)
            VALUES (?,?,?,?,?,?,?,?,?)
        ''', (name, comm, ptype, price, area, beds, baths, rent, svc))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'data': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compare-communities', methods=['POST'])
def api_compare():
    try:
        selected = request.json.get('communities', [])
        if len(selected) < 2:
            return jsonify({'error': 'Select at least 2 communities to compare'}), 400

        rows = []
        for n in selected:
            info = COMMUNITIES.get(n)
            if info:
                rows.append({'name': n, **info, 'insights': community_insight(n)})

        rows.sort(key=lambda x: x['investment_score'], reverse=True)
        for i, r in enumerate(rows): r['rank'] = i + 1
        return jsonify({'success': True, 'data': rows})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-recommendations', methods=['POST'])
def api_recommend():
    try:
        d      = request.json
        budget = float(d.get('budget', 0))
        if budget <= 0:
            return jsonify({'error': 'Budget must be greater than 0'}), 400

        areas  = d.get('preferred_areas', list(COMMUNITIES.keys())) or list(COMMUNITIES.keys())
        recs   = build_recommendations(
            budget, d.get('property_type', 'Apartment'), areas,
            d.get('investment_goal', 'Balanced'), float(d.get('rental_goal', 0))
        )
        return jsonify({'success': True, 'data': recs, 'count': len(recs)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-insights', methods=['POST'])
def api_insights():
    try:
        data = market_insights()
        if openai_client:
            try:
                mo  = data['market_overview']
                prompt = (
                    f"You are a Dubai real estate expert. Top yield area: {mo['key_stats']['top_yield_area']}, "
                    f"fastest growing: {mo['key_stats']['fastest_growing']}, "
                    f"avg yield: {mo['key_stats']['avg_yield']}, avg growth: {mo['key_stats']['avg_growth']}. "
                    "Give 3 concise executive investment insights for Dubai in 2024. Under 2 sentences each."
                )
                resp = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300
                )
                data['ai_executive_summary'] = resp.choices[0].message.content
            except Exception:
                data['ai_executive_summary'] = None
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ══════════════════════════════════════════════════════════════════════════════
# API — Leads CRUD
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/leads', methods=['GET'])
def api_leads_get():
    search = request.args.get('q', '')
    ltype  = request.args.get('type', '')
    conn   = get_db()
    sql    = 'SELECT * FROM leads WHERE 1=1'
    params = []
    if search:
        sql += ' AND (name LIKE ? OR email LIKE ? OR preferred_area LIKE ?)'
        params += [f'%{search}%'] * 3
    if ltype:
        sql += ' AND lead_type = ?'
        params.append(ltype)
    sql += ' ORDER BY score DESC, created_at DESC'
    rows  = conn.execute(sql, params).fetchall()
    conn.close()
    return jsonify({'success': True, 'data': [dict(r) for r in rows]})

@app.route('/api/leads', methods=['POST'])
def api_leads_add():
    try:
        d = request.json
        if not d.get('name', '').strip():
            return jsonify({'error': 'Name is required'}), 400
        score = auto_score_lead(d)
        conn  = get_db()
        cur   = conn.execute('''
            INSERT INTO leads
              (name,email,phone,lead_type,budget,preferred_area,notes,score,status)
            VALUES (?,?,?,?,?,?,?,?,?)
        ''', (d.get('name','').strip(), d.get('email',''), d.get('phone',''),
              d.get('lead_type','Buyer'), float(d.get('budget',0)),
              d.get('preferred_area',''), d.get('notes',''), score,
              d.get('status','New')))
        conn.commit(); lid = cur.lastrowid; conn.close()
        return jsonify({'success': True, 'id': lid, 'score': score})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leads/<int:lid>', methods=['GET'])
def api_lead_get(lid):
    conn = get_db()
    row  = conn.execute('SELECT * FROM leads WHERE id=?', (lid,)).fetchone()
    conn.close()
    if not row: return jsonify({'error': 'Not found'}), 404
    return jsonify({'success': True, 'data': dict(row)})

@app.route('/api/leads/<int:lid>', methods=['PUT'])
def api_lead_update(lid):
    try:
        d = request.json
        conn = get_db()
        conn.execute('''
            UPDATE leads SET name=?,email=?,phone=?,lead_type=?,budget=?,
              preferred_area=?,notes=?,status=? WHERE id=?
        ''', (d.get('name'), d.get('email'), d.get('phone'), d.get('lead_type'),
              float(d.get('budget',0)), d.get('preferred_area'), d.get('notes'),
              d.get('status'), lid))
        conn.commit(); conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leads/<int:lid>', methods=['DELETE'])
def api_lead_delete(lid):
    try:
        conn = get_db()
        conn.execute('DELETE FROM leads WHERE id=?', (lid,))
        conn.commit(); conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ══════════════════════════════════════════════════════════════════════════════
# API — CSV Upload
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/upload-csv', methods=['POST'])
def api_upload():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        f         = request.files['file']
        data_type = request.form.get('data_type', 'properties')
        if not f.filename.lower().endswith('.csv'):
            return jsonify({'error': 'Only CSV files are supported'}), 400

        content = f.stream.read().decode('utf-8')
        reader  = list(csv.DictReader(io.StringIO(content)))
        if not reader:
            return jsonify({'error': 'CSV is empty'}), 400

        imported, errors = 0, []
        conn = get_db()

        def get(row, *keys, default='', cast=str):
            for k in keys:
                if k in row and row[k]:
                    try: return cast(row[k])
                    except: pass
            return cast(default) if default != '' else default

        if data_type == 'properties':
            for i, row in enumerate(reader):
                try:
                    conn.execute('''
                        INSERT INTO properties
                          (property_name,community,type,price,area,bedrooms,bathrooms,annual_rent,status)
                        VALUES (?,?,?,?,?,?,?,?,?)
                    ''', (
                        get(row,'property_name','Property Name', default=f'Property {i+1}'),
                        get(row,'community','Community'),
                        get(row,'type','Type', default='Apartment'),
                        get(row,'price','Price', default='0', cast=float),
                        get(row,'area','Area', default='0', cast=float),
                        get(row,'bedrooms','Bedrooms', default='0', cast=int),
                        get(row,'bathrooms','Bathrooms', default='0', cast=int),
                        get(row,'annual_rent','Annual Rent', default='0', cast=float),
                        get(row,'status','Status', default='Ready'),
                    ))
                    imported += 1
                except Exception as ex:
                    errors.append(f"Row {i+2}: {ex}")

        elif data_type == 'leads':
            for i, row in enumerate(reader):
                try:
                    d = {
                        'name':          get(row,'name','Name'),
                        'email':         get(row,'email','Email'),
                        'phone':         get(row,'phone','Phone'),
                        'lead_type':     get(row,'lead_type','Lead Type','Type', default='Buyer'),
                        'budget':        get(row,'budget','Budget', default='0', cast=float),
                        'preferred_area':get(row,'preferred_area','Preferred Area'),
                        'notes':         get(row,'notes','Notes'),
                    }
                    score = auto_score_lead(d)
                    conn.execute('''
                        INSERT INTO leads
                          (name,email,phone,lead_type,budget,preferred_area,notes,score)
                        VALUES (?,?,?,?,?,?,?,?)
                    ''', (d['name'],d['email'],d['phone'],d['lead_type'],
                          d['budget'],d['preferred_area'],d['notes'],score))
                    imported += 1
                except Exception as ex:
                    errors.append(f"Row {i+2}: {ex}")

        conn.commit(); conn.close()
        return jsonify({'success': True, 'imported': imported, 'total': len(reader),
                        'errors': errors[:10], 'preview': reader[:5]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ══════════════════════════════════════════════════════════════════════════════
# API — Reports
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/generate-report', methods=['POST'])
def api_gen_report():
    try:
        d     = request.json
        rtype = d.get('report_type', 'market_overview')
        comm  = d.get('community', '')
        data  = {}
        name  = ''

        if rtype == 'market_overview':
            data = market_insights()
            name = f"Dubai Market Overview — {datetime.now().strftime('%B %Y')}"

        elif rtype == 'community':
            if not comm:
                return jsonify({'error': 'Community is required'}), 400
            info = COMMUNITIES.get(comm, {})
            data = {'community': comm, 'metrics': info,
                    'insights': community_insight(comm),
                    'generated_at': datetime.now().strftime('%B %d, %Y')}
            name = f"{comm} Investment Report — {datetime.now().strftime('%B %Y')}"

        elif rtype == 'executive_summary':
            top = sorted(COMMUNITIES.items(), key=lambda x: x[1]['investment_score'], reverse=True)
            data = {
                'title': 'Dubai Real Estate Executive Summary',
                'top_communities': [{'name': n, **v} for n, v in top[:5]],
                'market': market_insights(),
                'generated_at': datetime.now().strftime('%B %d, %Y')
            }
            name = f"Executive Summary Report — {datetime.now().strftime('%B %Y')}"

        conn = get_db()
        cur  = conn.execute('INSERT INTO reports (report_name,report_type,report_data) VALUES (?,?,?)',
                            (name, rtype, json.dumps(data)))
        rid  = cur.lastrowid
        conn.commit(); conn.close()
        return jsonify({'success': True, 'report_id': rid, 'report_name': name, 'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-report/<int:rid>')
def api_download_report(rid):
    try:
        conn   = get_db()
        report = conn.execute('SELECT * FROM reports WHERE id=?', (rid,)).fetchone()
        conn.close()
        if not report:
            return jsonify({'error': 'Report not found'}), 404

        d   = json.loads(report['report_data'])
        out = io.StringIO()

        def line(ch='─', width=60): out.write(ch * width + '\n')
        def h(title):
            out.write('\n'); line(); out.write(f"  {title}\n"); line()

        line('=')
        out.write('  DUBAI REAL ESTATE INTELLIGENCE AGENT\n')
        out.write(f"  {report['report_name']}\n")
        out.write(f"  Generated: {report['generated_date']}\n")
        line('=')

        def dump(obj, indent=2):
            if isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            out.write(f"{' '*indent}{k}: {v}\n")
                        out.write('\n')
                    else:
                        out.write(f"{' '*indent}• {item}\n")
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, (list, dict)):
                        out.write(f"{' '*indent}{k}:\n"); dump(v, indent+4)
                    else:
                        out.write(f"{' '*indent}{k}: {v}\n")
            else:
                out.write(f"{' '*indent}{obj}\n")

        if 'market_overview' in d:
            h('MARKET OVERVIEW'); dump(d['market_overview'])
        if 'top_growth'      in d:
            h('TOP GROWTH COMMUNITIES'); dump(d['top_growth'])
        if 'top_yield'       in d:
            h('TOP YIELD COMMUNITIES'); dump(d['top_yield'])
        if 'investor_insights' in d:
            h('INVESTOR INSIGHTS'); dump(d['investor_insights'])
        if 'risk_alerts'     in d:
            h('RISK ALERTS'); dump(d['risk_alerts'])
        if 'community'       in d:
            h(f"COMMUNITY: {d.get('community','')}"); dump(d.get('metrics',{}))
            h('INSIGHTS'); dump(d.get('insights',[]))
        if 'top_communities' in d:
            h('TOP INVESTMENT COMMUNITIES')
            for c in d['top_communities']:
                out.write(f"\n  {c.get('name','')}\n")
                for k in ['investment_score','rental_yield','growth_rate','risk','type']:
                    out.write(f"    {k}: {c.get(k,'')}\n")

        out.write('\n'); line('=')
        out.write('  Dubai Real Estate Intelligence Agent\n'); line('=')
        out.seek(0)

        fname = f"dubai_re_{rtype}_{rid}_{datetime.now().strftime('%Y%m%d')}.txt"
        return send_file(io.BytesIO(out.getvalue().encode('utf-8')),
                         mimetype='text/plain', as_attachment=True, download_name=fname)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/properties')
def api_properties():
    conn  = get_db()
    rows  = conn.execute('SELECT * FROM properties ORDER BY created_at DESC LIMIT 100').fetchall()
    conn.close()
    return jsonify({'success': True, 'data': [dict(r) for r in rows]})

@app.route('/api/communities')
def api_communities():
    return jsonify({'success': True, 'data': [{'name': n, **v} for n, v in COMMUNITIES.items()]})

# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

init_db()

if __name__ == '__main__':
    print("=" * 62)
    print("   Dubai Real Estate Intelligence Agent  v1.0")
    print("=" * 62)
    print("  OpenAI:", "Connected" if openai_client else "Not configured (rule-based mode)")
    print("  Server: http://127.0.0.1:5000")
    print("=" * 62)
    app.run(debug=True, host='0.0.0.0', port=5000)
