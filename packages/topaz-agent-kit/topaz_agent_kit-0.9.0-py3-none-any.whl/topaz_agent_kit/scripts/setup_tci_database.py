#!/usr/bin/env python3
"""Setup script for TCI Policy Risk Assessor pipeline.

Creates SQLite database, initializes schema, and generates mock data:
- Policy applications table
- Buyer news database (mock news articles)
- Risk factors database (industry/region risk data)
- Risk assessments table
- Recommendations table
- Mock PDF documents (application forms, financial statements, contracts, etc.)

Usage:
    python scripts/setup_tci_database.py [--db-path <path>] [--output-dir <dir>] [--reset] [--low-risk-count <n>] [--moderate-risk-count <n>] [--high-risk-count <n>]
    uv run -m scripts.setup_tci_database --db-path projects/ensemble/data/tci/tci_database.db --reset
"""

import sqlite3
import os
import sys
import argparse
import random
import uuid
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from topaz_agent_kit.utils.path_resolver import resolve_script_path, detect_project_name

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not available. PDF generation will be skipped.")
    print("Install with: pip install reportlab")


def create_database_schema(db_path: str) -> None:
    """Create all database tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Policy applications table - tracks all policy applications
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS policy_applications (
            application_id TEXT PRIMARY KEY,
            seller_name TEXT NOT NULL,
            seller_email TEXT NOT NULL,
            buyer_name TEXT NOT NULL,
            buyer_id TEXT,
            requested_amount REAL NOT NULL,
            requested_term_days INTEGER,
            currency_code TEXT,
            currency_symbol TEXT,
            application_form_path TEXT,
            financial_statements_path TEXT,
            supply_contract_path TEXT,
            bank_reference_path TEXT,
            sanctions_report_path TEXT,
            aged_debtors_path TEXT,
            internal_assessment_path TEXT,
            credit_bureau_path TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            run_id TEXT
        )
    """)
    
    # Buyer news table - mock news articles database
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS buyer_news (
            news_id TEXT PRIMARY KEY,
            buyer_id TEXT NOT NULL,
            headline TEXT NOT NULL,
            article_text TEXT,
            publication_date TEXT NOT NULL,
            sentiment_score REAL,
            risk_indicators TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Risk factors table - industry/region risk data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_factors (
            factor_id TEXT PRIMARY KEY,
            region TEXT NOT NULL,
            industry TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            factors_json TEXT,
            effective_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Risk assessments table - individual risk factor scores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_assessments (
            application_id TEXT NOT NULL,
            risk_factor_name TEXT NOT NULL,
            score REAL NOT NULL,
            weight REAL NOT NULL,
            weighted_score REAL NOT NULL,
            assessment_text TEXT,
            data_source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (application_id, risk_factor_name),
            FOREIGN KEY (application_id) REFERENCES policy_applications(application_id)
        )
    """)
    
    # Recommendations table - AI-generated underwriting recommendations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            application_id TEXT PRIMARY KEY,
            total_risk_score REAL NOT NULL,
            creditworthiness_level TEXT NOT NULL,
            recommended_credit_limit REAL,
            underwriting_recommendation TEXT NOT NULL,
            terms_and_conditions TEXT,
            confidence_score REAL,
            rationale TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES policy_applications(application_id)
        )
    """)
    
    # Final decisions table - human decisions from HITL gates
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS final_decisions (
            application_id TEXT PRIMARY KEY,
            decision TEXT NOT NULL,
            final_credit_limit REAL,
            final_terms TEXT,
            decision_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES policy_applications(application_id)
        )
    """)
    
    # Create indexes for faster lookups
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_applications_status ON policy_applications(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_applications_run_id ON policy_applications(run_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_applications_buyer ON policy_applications(buyer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_buyer_news_buyer ON buyer_news(buyer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_buyer_news_date ON buyer_news(publication_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_risk_factors_region_industry ON risk_factors(region, industry)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_risk_assessments_application ON risk_assessments(application_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recommendations_application ON recommendations(application_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_final_decisions_application ON final_decisions(application_id)")
    
    conn.commit()
    conn.close()
    print("✓ Database schema created")


def generate_mock_buyer_news(cursor, buyer_ids: List[str], articles_per_buyer: int = 3) -> List[Dict[str, Any]]:
    """Generate mock news articles for buyers."""
    news_articles = []
    
    # News templates with different sentiment and risk indicators
    positive_news = [
        {
            "headline": "{buyer_name} Announces Major Expansion in {region}",
            "article": "{buyer_name}, a leading manufacturer in the {industry} sector, has announced plans to expand operations in {region}. The company plans to invest £{amount} million in new facilities, creating approximately {jobs} new jobs. CEO {ceo_name} stated, 'This expansion reflects our strong financial position and commitment to growth in key markets.'",
            "sentiment": 0.7,
            "risk_indicators": {"type": "positive_growth", "impact": "positive"}
        },
        {
            "headline": "{buyer_name} Reports Strong Q{quarter} Financial Results",
            "article": "{buyer_name} has reported robust financial performance for Q{quarter}, with revenue growth of {growth}% year-over-year. The company's strong balance sheet and improved cash flow position have been well-received by investors. Analysts have upgraded the company's credit rating outlook.",
            "sentiment": 0.6,
            "risk_indicators": {"type": "financial_strength", "impact": "positive"}
        },
        {
            "headline": "{buyer_name} Secures Major Contract Worth £{amount} Million",
            "article": "{buyer_name} has secured a significant multi-year contract valued at £{amount} million with a major international client. This contract is expected to provide stable revenue streams over the next {years} years and strengthen the company's market position.",
            "sentiment": 0.8,
            "risk_indicators": {"type": "contract_win", "impact": "positive"}
        }
    ]
    
    neutral_news = [
        {
            "headline": "{buyer_name} Appoints New Chief Financial Officer",
            "article": "{buyer_name} has announced the appointment of {cfo_name} as its new Chief Financial Officer, effective {date}. {cfo_name} brings {years} years of experience in financial management and strategic planning to the role.",
            "sentiment": 0.0,
            "risk_indicators": {"type": "management_change", "impact": "neutral"}
        },
        {
            "headline": "{buyer_name} Completes Factory Modernization Project",
            "article": "{buyer_name} has completed a £{amount} million modernization project at its {location} facility. The upgrades are expected to improve operational efficiency and reduce production costs by approximately {savings}%.",
            "sentiment": 0.2,
            "risk_indicators": {"type": "operational_improvement", "impact": "neutral"}
        }
    ]
    
    negative_news = [
        {
            "headline": "{buyer_name} Reports Payment Delays Following Market Downturn",
            "article": "{buyer_name} has experienced temporary cash flow challenges following a downturn in the {industry} market. The company has reported delays in payment to some suppliers, though management expects the situation to improve within {months} months as market conditions stabilize.",
            "sentiment": -0.4,
            "risk_indicators": {"type": "payment_delays", "impact": "negative", "severity": "moderate", "remediation": "expected_improvement"}
        },
        {
            "headline": "{buyer_name} Addresses Past Compliance Issues",
            "article": "{buyer_name} has resolved previous compliance issues identified in {year}. The company has implemented new internal controls and compliance procedures, with external auditors confirming the effectiveness of these measures. Management has committed to maintaining high standards going forward.",
            "sentiment": -0.2,
            "risk_indicators": {"type": "past_fraud_remediation", "impact": "negative", "severity": "low", "remediation": "documented"}
        }
    ]
    
    all_news = positive_news + neutral_news + negative_news
    
    regions = ["UK", "Germany", "France", "Netherlands", "Belgium", "Poland"]
    industries = ["Manufacturing", "Engineering", "Electronics", "Automotive", "Chemicals", "Textiles"]
    ceo_names = ["John Smith", "Maria Garcia", "David Chen", "Sarah Johnson", "Michael Brown"]
    cfo_names = ["Robert Williams", "Emma Davis", "James Wilson", "Lisa Anderson", "Thomas Taylor"]
    
    for buyer_id in buyer_ids:
        buyer_name = f"Buyer-{buyer_id.split('-')[-1]}"
        region = random.choice(regions)
        industry = random.choice(industries)
        
        # Generate articles for this buyer
        selected_news = random.sample(all_news, min(articles_per_buyer, len(all_news)))
        
        for news_template in selected_news:
            news_id = f"NEWS-{random.randint(100000, 999999)}"
            publication_date = (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d")
            
            # Fill in template variables
            headline = news_template["headline"].format(
                buyer_name=buyer_name,
                region=region,
                industry=industry,
                quarter=random.randint(1, 4),
                amount=random.randint(5, 50),
                jobs=random.randint(50, 500),
                years=random.randint(2, 5),
                growth=random.randint(5, 25),
                location=random.choice(["Manchester", "Birmingham", "Leeds", "Glasgow", "Bristol"]),
                savings=random.randint(5, 15),
                months=random.randint(3, 6),
                year=random.randint(2020, 2023),
                ceo_name=random.choice(ceo_names),
                cfo_name=random.choice(cfo_names),
                date=(datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
            )
            
            article_text = news_template["article"].format(
                buyer_name=buyer_name,
                region=region,
                industry=industry,
                quarter=random.randint(1, 4),
                amount=random.randint(5, 50),
                jobs=random.randint(50, 500),
                years=random.randint(2, 5),
                growth=random.randint(5, 25),
                location=random.choice(["Manchester", "Birmingham", "Leeds", "Glasgow", "Bristol"]),
                savings=random.randint(5, 15),
                months=random.randint(3, 6),
                year=random.randint(2020, 2023),
                ceo_name=random.choice(ceo_names),
                cfo_name=random.choice(cfo_names),
                date=(datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
            )
            
            news_article = {
                "news_id": news_id,
                "buyer_id": buyer_id,
                "headline": headline,
                "article_text": article_text,
                "publication_date": publication_date,
                "sentiment_score": news_template["sentiment"],
                "risk_indicators": json.dumps(news_template["risk_indicators"])
            }
            
            cursor.execute("""
                INSERT OR REPLACE INTO buyer_news
                (news_id, buyer_id, headline, article_text, publication_date, sentiment_score, risk_indicators)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                news_article["news_id"],
                news_article["buyer_id"],
                news_article["headline"],
                news_article["article_text"],
                news_article["publication_date"],
                news_article["sentiment_score"],
                news_article["risk_indicators"]
            ))
            
            news_articles.append(news_article)
    
    print(f"✓ Generated {len(news_articles)} news articles for {len(buyer_ids)} buyers")
    return news_articles


def generate_mock_risk_factors(cursor) -> List[Dict[str, Any]]:
    """Generate mock risk factors for different regions and industries."""
    regions = ["UK", "Germany", "France", "Netherlands", "Belgium", "Poland", "Spain", "Italy"]
    industries = [
        "Manufacturing", "Engineering", "Electronics", "Automotive", 
        "Chemicals", "Textiles", "Food & Beverage", "Pharmaceuticals"
    ]
    
    risk_factors_list = []
    
    # Risk level distribution: 40% low, 40% medium, 20% high
    risk_levels = ["low", "medium", "high"]
    risk_weights = [0.4, 0.4, 0.2]
    
    for region in regions:
        for industry in industries:
            factor_id = f"RF-{region[:3].upper()}-{industry[:3].upper()}-{random.randint(1000, 9999)}"
            risk_level = random.choices(risk_levels, weights=risk_weights, k=1)[0]
            effective_date = (datetime.now() - timedelta(days=random.randint(1, 90))).strftime("%Y-%m-%d")
            
            # Generate risk factors JSON based on risk level
            if risk_level == "low":
                factors = {
                    "economic_stability": "stable",
                    "market_growth": "positive",
                    "regulatory_environment": "favorable",
                    "competition_level": "moderate",
                    "supply_chain_risk": "low"
                }
            elif risk_level == "medium":
                factors = {
                    "economic_stability": "moderate",
                    "market_growth": "stable",
                    "regulatory_environment": "neutral",
                    "competition_level": "high",
                    "supply_chain_risk": "moderate"
                }
            else:  # high
                factors = {
                    "economic_stability": "volatile",
                    "market_growth": "declining",
                    "regulatory_environment": "challenging",
                    "competition_level": "very_high",
                    "supply_chain_risk": "high"
                }
            
            risk_factor = {
                "factor_id": factor_id,
                "region": region,
                "industry": industry,
                "risk_level": risk_level,
                "factors_json": json.dumps(factors),
                "effective_date": effective_date
            }
            
            cursor.execute("""
                INSERT OR REPLACE INTO risk_factors
                (factor_id, region, industry, risk_level, factors_json, effective_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                risk_factor["factor_id"],
                risk_factor["region"],
                risk_factor["industry"],
                risk_factor["risk_level"],
                risk_factor["factors_json"],
                risk_factor["effective_date"]
            ))
            
            risk_factors_list.append(risk_factor)
    
    print(f"✓ Generated {len(risk_factors_list)} risk factor records ({len(regions)} regions × {len(industries)} industries)")
    return risk_factors_list


# ============================================================================
# PDF Generation Functions
# ============================================================================

def generate_application_form_pdf(application: Dict[str, Any], output_path: Path) -> str:
    """Generate Application Form PDF. Returns absolute path."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is required for PDF generation")
    
    filename = f"application_form_{application['application_id']}.pdf"
    filepath = output_path / filename
    
    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=20,
        textColor=colors.HexColor('#003366'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Application Form", title_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Applicant's Details
    app_data = [
        ["Applicant's Details", ""],
        ["Company name", application.get("seller_name", "N/A")],
        ["Registered number", application.get("seller_registered_number", "12345678")],
        ["Contact name", application.get("seller_contact_name", "John Smith")],
        ["Position", application.get("seller_position", "Credit Manager")],
        ["Address", application.get("seller_address", "50 Industrial Park, London")],
        ["Postcode", application.get("seller_postcode", "EC1A 1AA")],
        ["Website", application.get("seller_website", "www.example.com")],
        ["Email", application.get("seller_email", "contact@example.com")],
        ["Is cover required for any other Group company?", application.get("group_company_cover", "No")],
        ["", ""],
        ["Business Activities", ""],
        ["Do you act as an agent or principal?", application.get("agent_or_principal", "Principal")],
        ["What goods / services do you sell?", application.get("goods_services", "Industrial machinery components")],
        ["To which trade sector do you sell?", application.get("trade_sector", "Manufacturing and Engineering")],
        ["Do you manufacture the goods that you sell?", application.get("manufacture_goods", "Yes")],
        ["Is your business seasonal?", application.get("seasonal_business", "No")],
        ["", ""],
        ["Buyer to be Insured", ""],
        ["Buyer name", application.get("buyer_name", "N/A")],
        ["Buyer address", application.get("buyer_address", "N/A")],
        ["Registered number", application.get("buyer_registered_number", "87654321")],
        ["Is cover required on any other company associated with this Buyer?", application.get("associated_company_cover", "No")],
        ["", ""],
        ["Contract to be Insured", ""],
        ["Please describe the contract to be insured", application.get("contract_description", "Supply of machinery components over a 12-month period")],
        ["Why are you looking to insure this Buyer / contract?", application.get("insurance_reason", "To mitigate risk of non-payment")],
        ["Is the contract in respect of revolving business or a specific project?", application.get("business_type", "Revolving business")],
        ["Do you have a written supply contract with the Buyer?", "Yes (attached)"],
        ["What is the period from date of contract to date of shipment?", f"{application.get('shipment_period_days', 30)} days"],
        ["What are the terms of payment?", application.get("payment_terms", "60 days net")],
        ["Do these differ from your standard terms of payment?", application.get("differ_from_standard", "No")],
        ["What is the expected maximum exposure under the contract?", f"{application.get('currency_symbol', '£')}{application.get('requested_amount', 0):,.0f}"],
        ["", ""],
        ["Trading History and Terms", ""],
        ["How long have you traded with this Buyer?", f"{application.get('trading_years', 3)} years"],
        ["Have you ever experienced payment delays or other problems?", application.get("payment_delays", "Yes, occasional delays up to 15 days")],
        ["What is the expected turnover with this Buyer in the forthcoming 12 months?", f"{application.get('currency_symbol', '£')}{application.get('expected_turnover', 1200000):,.0f}"],
        [f"Current aged debt analysis for the Buyer ({application.get('currency', 'GBP')}):", ""],
        ["Current (not yet due)", f"{application.get('currency_symbol', '£')}{application.get('aged_debt_current', 200000):,.0f}"],
        ["1-30 days overdue", f"{application.get('currency_symbol', '£')}{application.get('aged_debt_1_30', 50000):,.0f}"],
        ["31-60 days overdue", f"{application.get('currency_symbol', '£')}{application.get('aged_debt_31_60', 10000):,.0f}"],
        ["61-90 days overdue", f"{application.get('currency_symbol', '£')}{application.get('aged_debt_61_90', 0):,.0f}"],
        ["Over 90 days overdue", f"{application.get('currency_symbol', '£')}{application.get('aged_debt_90_plus', 0):,.0f}"],
        ["Total", f"{application.get('currency_symbol', '£')}{application.get('aged_debt_total', 260000):,.0f}"],
        ["", ""],
        ["Sanctions", ""],
        ["Do you currently trade with any Buyers subject to US, EU or UK Sanctions?", application.get("sanctions_trading", "No")],
        ["Do you carry out checks on your Buyers?", application.get("sanctions_checks", "Yes")],
        ["", ""],
        ["Declaration", ""],
        ["I declare that I have made a fair presentation of the risk", ""],
        ["Name of Signatory", application.get("seller_contact_name", "John Smith")],
        ["Position in company", application.get("seller_position", "Credit Manager")],
        ["Date", datetime.now().strftime("%d %B %Y")],
    ]
    
    # Convert data to Paragraphs for proper text wrapping
    app_data_paragraphs = []
    question_style = ParagraphStyle(
        'Question',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        leftIndent=0,
        rightIndent=0,
        fontName='Helvetica-Bold'
    )
    answer_style = ParagraphStyle(
        'Answer',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        leftIndent=0,
        rightIndent=0,
        wordWrap='LTR'
    )
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        leftIndent=0,
        rightIndent=0,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#003366')
    )
    
    for row in app_data:
        if row[0] == "" and row[1] == "":
            app_data_paragraphs.append(["", ""])
        elif row[0] in ["Applicant's Details", "Business Activities", "Buyer to be Insured", 
                        "Contract to be Insured", "Trading History and Terms", "Sanctions", "Declaration"]:
            app_data_paragraphs.append([Paragraph(row[0], header_style), ""])
        else:
            question = Paragraph(row[0], question_style)
            answer = Paragraph(str(row[1]) if row[1] else "", answer_style)
            app_data_paragraphs.append([question, answer])
    
    table = Table(app_data_paragraphs, colWidths=[2.8 * inch, 3.7 * inch])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    story.append(table)
    doc.build(story)
    return str(filepath.resolve())


def generate_financial_statements_pdf(application: Dict[str, Any], output_path: Path) -> str:
    """Generate Buyer Financial Statements PDF."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is required for PDF generation")
    
    filename = f"financial_statements_{application['application_id']}.pdf"
    filepath = output_path / filename
    
    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor('#003366'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Buyer Financial Statements", title_style))
    story.append(Paragraph(application.get("buyer_name", "N/A"), title_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Get currency information
    currency_symbol = application.get("currency_symbol", "€")
    currency = application.get("currency", "EUR")
    
    # Income Statement
    income_data = [
        [f"Income Statement ({currency_symbol} Millions)", "", "", ""],
        ["Item", "2024", "2023", "2022"],
        ["Revenue", f"{application.get('revenue_2024', 15)}", f"{application.get('revenue_2023', 12.5)}", f"{application.get('revenue_2022', 10)}"],
        ["Cost of Goods Sold", f"{application.get('cogs_2024', 6.2)}", f"{application.get('cogs_2023', 6)}", f"{application.get('cogs_2022', 5.5)}"],
        ["Gross Profit", f"{application.get('gross_profit_2024', 8.8)}", f"{application.get('gross_profit_2023', 6.5)}", f"{application.get('gross_profit_2022', 4.5)}"],
        ["Operating Expenses", f"{application.get('opex_2024', 2.2)}", f"{application.get('opex_2023', 2)}", f"{application.get('opex_2022', 1.8)}"],
        ["Net Income", f"{application.get('net_income_2024', 6.6)}", f"{application.get('net_income_2023', 4.5)}", f"{application.get('net_income_2022', 2.7)}"],
    ]
    
    income_table = Table(income_data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
    income_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E0E0E0')),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#F0F0F0')),
    ]))
    
    story.append(income_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Balance Sheet
    balance_data = [
        [f"Balance Sheet ({currency_symbol} Millions)", "", "", ""],
        ["Item", "2024", "2023", "2022"],
        ["Total Assets", f"{application.get('total_assets_2024', 21.5)}", f"{application.get('total_assets_2023', 19.2)}", f"{application.get('total_assets_2022', 18.3)}"],
        ["Current Assets", f"{application.get('current_assets_2024', 10)}", f"{application.get('current_assets_2023', 9)}", f"{application.get('current_assets_2022', 8)}"],
        ["Fixed Assets", f"{application.get('fixed_assets_2024', 10.5)}", f"{application.get('fixed_assets_2023', 10.2)}", f"{application.get('fixed_assets_2022', 10.3)}"],
        ["Current Liabilities", f"{application.get('current_liabilities_2024', 6)}", f"{application.get('current_liabilities_2023', 7)}", f"{application.get('current_liabilities_2022', 6)}"],
        ["Total Liabilities", f"{application.get('total_liabilities_2024', 10)}", f"{application.get('total_liabilities_2023', 8)}", f"{application.get('total_liabilities_2022', 7.5)}"],
        ["Shareholders' Equity", f"{application.get('equity_2024', 11.5)}", f"{application.get('equity_2023', 11.2)}", f"{application.get('equity_2022', 10.8)}"],
    ]
    
    balance_table = Table(balance_data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
    balance_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E0E0E0')),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#F0F0F0')),
    ]))
    
    story.append(balance_table)
    doc.build(story)
    return str(filepath.resolve())


def generate_supply_contract_pdf(application: Dict[str, Any], output_path: Path) -> str:
    """Generate Signed Supply Contract PDF with proper text wrapping."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is required for PDF generation")
    
    filename = f"supply_contract_{application['application_id']}.pdf"
    filepath = output_path / filename
    
    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor('#003366'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Signed Supply Contract", title_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Create styles for proper text wrapping
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        leftIndent=0,
        rightIndent=0,
        fontName='Helvetica-Bold'
    )
    
    value_style = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        leftIndent=0,
        rightIndent=0,
        wordWrap='LTR'
    )
    
    seller_name = application.get('seller_name', 'ABC Manufacturing Ltd')
    buyer_name = application.get('buyer_name', 'N/A')
    contract_date = application.get("contract_date", "1 Jan 2025")
    contract_description = application.get("contract_description", "Supply of industrial machinery components over 12 months")
    payment_terms = application.get("payment_terms", "60 days net from invoice date")
    currency_symbol = application.get('currency_symbol', '£')
    currency = application.get('currency', 'GBP')
    requested_amount = application.get('requested_amount', 500000)
    
    # Convert to Paragraphs for proper wrapping
    contract_data = [
        [Paragraph("Parties", label_style), 
         Paragraph(f"{seller_name} (Supplier) and {buyer_name} (Buyer)", value_style)],
        [Paragraph("Contract Date", label_style), 
         Paragraph(contract_date, value_style)],
        [Paragraph("Scope", label_style), 
         Paragraph(contract_description, value_style)],
        [Paragraph("Payment Terms", label_style), 
         Paragraph(payment_terms, value_style)],
        [Paragraph("Credit Limit", label_style), 
         Paragraph(f"{currency_symbol} {requested_amount:,.0f} ({currency})", value_style)],
        [Paragraph("Termination Clause", label_style), 
         Paragraph("Either party may terminate with 30 days' notice", value_style)],
    ]
    
    table = Table(contract_data, colWidths=[2.2 * inch, 4.3 * inch])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    story.append(table)
    doc.build(story)
    return str(filepath.resolve())


def generate_bank_reference_pdf(application: Dict[str, Any], output_path: Path) -> str:
    """Generate Bank Reference Letter PDF with proper formatting."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is required for PDF generation")
    
    filename = f"bank_reference_{application['application_id']}.pdf"
    filepath = output_path / filename
    
    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    ref_date = datetime.now().strftime("%d %B %Y")
    bank_name = application.get("bank_name", "Global Commerce Bank")
    buyer_name = application.get("buyer_name", "N/A")
    avg_balance = application.get("bank_avg_balance", 150000)
    credit_facility = application.get("bank_credit_facility", 300000)
    utilized = application.get("bank_utilized", 210000)
    delayed_repayment = application.get("bank_delayed_repayment", None)
    currency_symbol = application.get("currency_symbol", "£")
    account_since = application.get("bank_account_since", "January 2018")
    
    # Bank officer details
    bank_officer = application.get("bank_officer_name", "Sarah Mitchell")
    bank_position = application.get("bank_officer_position", "Senior Relationship Manager")
    bank_contact = application.get("bank_contact", "Tel: +44 20 1234 5678 | Email: s.mitchell@globalcommercebank.com")
    bank_address = application.get("bank_address", "123 Financial District, London EC2N 1AA, United Kingdom")
    
    # Styles
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        leftIndent=0,
        rightIndent=0,
        spaceAfter=12
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=12,
        leading=16,
        leftIndent=0,
        rightIndent=0,
        fontName='Helvetica-Bold',
        spaceAfter=8
    )
    
    signature_style = ParagraphStyle(
        'Signature',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        leftIndent=0,
        rightIndent=0,
        spaceBefore=24,
        spaceAfter=8
    )
    
    # Bank letterhead
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(f"<b>{bank_name}</b>", header_style))
    story.append(Paragraph(bank_address, normal_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Date
    story.append(Paragraph(f"Date: {ref_date}", normal_style))
    story.append(Spacer(1, 0.1 * inch))
    
    # Recipient
    insurance_company = application.get("insurance_company_name", "Export Credit Guarantee Corporation of India")
    story.append(Paragraph(f"To: {insurance_company}", normal_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Subject
    story.append(Paragraph(f"<b>Re: Bank Reference for {buyer_name}</b>", header_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Body paragraphs
    story.append(Paragraph(
        f"We confirm that <b>{buyer_name}</b> has maintained a business checking account with {bank_name} since {account_since}. "
        f"The average monthly balance over the past 12 months has been approximately {currency_symbol}{avg_balance:,.0f}.",
        normal_style
    ))
    story.append(Spacer(1, 0.15 * inch))
    
    story.append(Paragraph(
        f"The company has a revolving credit facility of {currency_symbol}{credit_facility:,.0f} with us, currently utilized at {currency_symbol}{utilized:,.0f}.",
        normal_style
    ))
    
    if delayed_repayment:
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph(
            f"We note that there was a delayed repayment: {delayed_repayment}. Since then, repayments have been timely.",
            normal_style
        ))
    
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        f"Based on our records, <b>{buyer_name}</b> is considered a customer in good standing.",
        normal_style
    ))
    
    story.append(Spacer(1, 0.3 * inch))
    
    # Signature
    story.append(Paragraph("Yours sincerely,", signature_style))
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph(f"<b>{bank_officer}</b>", signature_style))
    story.append(Paragraph(bank_position, normal_style))
    story.append(Paragraph(bank_contact, normal_style))
    
    doc.build(story)
    return str(filepath.resolve())


def generate_sanctions_report_pdf(application: Dict[str, Any], output_path: Path) -> str:
    """Generate Sanctions and Compliance Screening Report PDF."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is required for PDF generation")
    
    filename = f"sanctions_report_{application['application_id']}.pdf"
    filepath = output_path / filename
    
    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor('#003366'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Sanctions and Compliance Screening Report", title_style))
    story.append(Spacer(1, 0.3 * inch))
    
    screening_date = datetime.now().strftime("%d %B %Y")
    buyer_name = application.get("buyer_name", "N/A")
    
    report_data = [
        ["Buyer Name", buyer_name],
        ["Screening Date", screening_date],
        ["Result", "No matches found on US, EU, or UK sanctions lists"],
        ["Compliance Status", "Cleared"],
    ]
    
    table = Table(report_data, colWidths=[2.5 * inch, 4 * inch])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(table)
    doc.build(story)
    return str(filepath.resolve())


def generate_aged_debtors_pdf(application: Dict[str, Any], output_path: Path) -> str:
    """Generate Aged Debtors Report PDF."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is required for PDF generation")
    
    filename = f"aged_debtors_{application['application_id']}.pdf"
    filepath = output_path / filename
    
    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor('#003366'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Aged Debtors Report", title_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Generate sample invoices
    invoices = []
    base_date = datetime.now()
    
    # Current invoice
    invoices.append([
        (base_date - timedelta(days=30)).strftime("%Y-%m-%d"),
        f"INV-{random.randint(1000, 9999)}",
        f"{application.get('currency_symbol', '£')}{application.get('aged_debt_current', 200000):,.0f}",
        (base_date + timedelta(days=30)).strftime("%Y-%m-%d"),
        "0",
        "Current"
    ])
    
    # Overdue invoices
    currency_symbol = application.get('currency_symbol', '£')
    if application.get('aged_debt_1_30', 0) > 0:
        invoices.append([
            (base_date - timedelta(days=45)).strftime("%Y-%m-%d"),
            f"INV-{random.randint(1000, 9999)}",
            f"{currency_symbol}{application.get('aged_debt_1_30', 50000):,.0f}",
            (base_date - timedelta(days=15)).strftime("%Y-%m-%d"),
            "15",
            "Overdue"
        ])
    
    if application.get('aged_debt_31_60', 0) > 0:
        invoices.append([
            (base_date - timedelta(days=60)).strftime("%Y-%m-%d"),
            f"INV-{random.randint(1000, 9999)}",
            f"{currency_symbol}{application.get('aged_debt_31_60', 10000):,.0f}",
            (base_date - timedelta(days=32)).strftime("%Y-%m-%d"),
            "32",
            "Overdue"
        ])
    
    currency = application.get('currency', 'GBP')
    table_data = [["Invoice Date", "Invoice Number", f"Amount ({currency})", "Due Date", "Days Overdue", "Status"]]
    table_data.extend(invoices)
    
    table = Table(table_data, colWidths=[1.2 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch, 1 * inch, 1 * inch])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E0E0E0')),
    ]))
    
    story.append(table)
    doc.build(story)
    return str(filepath.resolve())


def generate_internal_assessment_pdf(application: Dict[str, Any], output_path: Path) -> str:
    """Generate Internal Credit Assessment Report PDF."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is required for PDF generation")
    
    filename = f"internal_assessment_{application['application_id']}.pdf"
    filepath = output_path / filename
    
    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor('#003366'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Internal Credit Assessment Report", title_style))
    story.append(Spacer(1, 0.3 * inch))
    
    assessment_date = datetime.now().strftime("%B %Y")
    buyer_name = application.get("buyer_name", "N/A")
    credit_rating = application.get("internal_credit_rating", "BBB (Medium Risk)")
    recommended_limit = application.get("internal_recommended_limit", 500000)
    currency_symbol = application.get("currency_symbol", "£")
    currency = application.get("currency", "GBP")
    
    assessment_data = [
        ["Buyer", buyer_name],
        ["Assessment Date", assessment_date],
        ["Credit Rating", credit_rating],
        ["", ""],
        ["Key Findings:", ""],
        ["", "• Payment history mostly on time, occasional delays up to 15 days."],
        ["", "• Moderate debt levels, manageable liquidity."],
        ["", "• Industry outlook stable but competitive."],
        ["", f"• Recommended credit limit: {currency_symbol} {recommended_limit:,.0f} ({currency})"],
    ]
    
    table = Table(assessment_data, colWidths=[2.5 * inch, 4 * inch])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(table)
    doc.build(story)
    return str(filepath.resolve())


def generate_credit_bureau_pdf(application: Dict[str, Any], output_path: Path) -> str:
    """Generate Credit Bureau Report PDF matching the example format."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is required for PDF generation")
    
    filename = f"credit_bureau_{application['application_id']}.pdf"
    filepath = output_path / filename
    
    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor('#003366'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Credit Bureau Report", title_style))
    story.append(Spacer(1, 0.2 * inch))
    
    buyer_name = application.get("buyer_name", "N/A")
    credit_score = application.get("credit_bureau_score", 65)
    late_payments = application.get("credit_bureau_late_payments", 2)
    currency_symbol = application.get("currency_symbol", "£")
    
    # Determine risk category
    if credit_score >= 80:
        risk_category = "Low Risk"
    elif credit_score >= 65:
        risk_category = "Moderate Risk"
    else:
        risk_category = "High Risk"
    
    # Generate payment history details
    report_date = datetime.now().strftime("%d %B %Y")
    
    # Create payment history details based on late payments
    payment_history_items = []
    if late_payments > 0:
        # Generate specific payment delay instances
        delay_amounts = [75000, 50000, 100000, 60000]
        delay_days = [45, 31, 38, 42]
        for i in range(min(late_payments, len(delay_amounts))):
            amount = delay_amounts[i] if i < len(delay_amounts) else random.randint(40000, 100000)
            days = delay_days[i] if i < len(delay_days) else random.randint(30, 50)
            payment_history_items.append(f"One instance of a {days}-day delay on a {currency_symbol}{amount:,} invoice, resolved without default")
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        leftIndent=0,
        rightIndent=0
    )
    
    bold_style = ParagraphStyle(
        'Bold',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        fontName='Helvetica-Bold'
    )
    
    # Header information
    story.append(Paragraph(f"<b>Buyer:</b> {buyer_name}", normal_style))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(f"<b>Report Date:</b> {report_date}", normal_style))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(f"<b>Credit Score:</b> {credit_score} / 100 ({risk_category})", normal_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Payment History section
    story.append(Paragraph("<b>Payment History:</b>", bold_style))
    story.append(Spacer(1, 0.1 * inch))
    
    if late_payments > 0:
        story.append(Paragraph(f"- 12 months payment record shows {late_payments} late payment{'s' if late_payments > 1 else ''} (30+ days overdue) in last 6 months", normal_style))
        for item in payment_history_items:
            story.append(Paragraph(f"- {item}", normal_style))
    else:
        story.append(Paragraph("- 12 months payment record shows no late payments", normal_style))
    
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("<b>Public Records:</b> No bankruptcies or liens", normal_style))
    story.append(Spacer(1, 0.15 * inch))
    
    # Credit Utilization
    utilization = application.get("credit_utilization", 70)
    story.append(Paragraph(f"<b>Credit Utilization:</b> {utilization}% of available credit lines used", normal_style))
    story.append(Spacer(1, 0.15 * inch))
    
    # Comments
    if credit_score >= 80:
        comment = "Buyer shows low credit risk with excellent payment history."
    elif credit_score >= 65:
        comment = "Buyer shows moderate credit risk with some recent payment delays, but no defaults."
    else:
        comment = "Buyer shows elevated credit risk with multiple payment delays and concerns."
    
    story.append(Paragraph(f"<b>Comments:</b> {comment}", normal_style))
    
    doc.build(story)
    return str(filepath.resolve())


def generate_underwriting_manual_pdf(output_path: Path) -> str:
    """Generate Underwriting Manual PDF with detailed risk scoring guidelines."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is required for PDF generation")
    
    filename = "underwriting_manual.pdf"
    filepath = output_path / filename
    
    # Check if already exists
    if filepath.exists():
        return str(filepath.resolve())
    
    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=20,
        textColor=colors.HexColor('#003366'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Underwriting Manual Document", title_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Subtitle
    subtitle_style = ParagraphStyle(
        'Heading1',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#003366'),
        spaceAfter=12,
        spaceBefore=12
    )
    story.append(Paragraph("Risk Scoring Guidelines for Trade Credit Insurance", subtitle_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Risk factor guidelines
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        leftIndent=0,
        rightIndent=0
    )
    
    bold_style = ParagraphStyle(
        'Bold',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        fontName='Helvetica-Bold'
    )
    
    risk_factors = [
        {
            "name": "1. Financial Health (Weight 23%)",
            "guidelines": [
                "Score 90-100: Strong profitability, low leverage, current ratio >2.0",
                "Score 70-89: Moderate profitability, manageable debt, current ratio 1.0-2.0",
                "Score <70: Weak profitability, high debt, current ratio <1.0"
            ]
        },
        {
            "name": "2. Payment Behavior (Weight 19%)",
            "guidelines": [
                "Score 90-100: No overdue payments, consistent on-time payments",
                "Score 70-89: Occasional delays <30 days, no >60 days overdue",
                "Score <70: Frequent or prolonged overdue payments >60 days"
            ]
        },
        {
            "name": "3. Credit Rating (Weight 14%)",
            "guidelines": [
                "Score 90-100: AAA to A ratings",
                "Score 70-89: BBB to BB ratings",
                "Score <70: B or below, or no rating"
            ]
        },
        {
            "name": "4. Contract Terms (Weight 9%)",
            "guidelines": [
                "Score 90-100: Standard terms, clear payment schedule, no unusual clauses",
                "Score 70-89: Minor deviations in terms or payment schedules",
                "Score <70: Complex or high-risk contract terms"
            ]
        },
        {
            "name": "5. Sanctions & Compliance (Weight 4%)",
            "guidelines": [
                "Score 100: No sanctions, full compliance",
                "Score 0: Sanctions present or compliance failure"
            ]
        },
        {
            "name": "6. Industry & External Factors (Weight 8%)",
            "guidelines": [
                "Score 90-100: Stable or growing industry, positive outlook",
                "Score 70-89: Moderate risk industry",
                "Score <70: Declining or volatile industry"
            ]
        },
        {
            "name": "7. Credit Bureau Report (Weight 8%)",
            "guidelines": [
                "Score 90-100: Excellent credit score (>80), no late payments or defaults in last 12 months",
                "Score 70-89: Good credit score (65-80), minor late payments (<30 days)",
                "Score <70: Moderate to high risk, multiple late payments or defaults"
            ]
        },
        {
            "name": "8. Bank Reference Letter (Weight 4%)",
            "guidelines": [
                "Score 90-100: Customer in good standing, no repayment delays, positive endorsement",
                "Score 70-89: Customer generally good standing, minor delays resolved promptly",
                "Score <70: Significant repayment delays or negative remarks"
            ]
        },
        {
            "name": "9. External News & Media (Weight 11%)",
            "guidelines": [
                "Score 90-100: Positive news, growth events, strong market position, no adverse events",
                "Score 70-89: Neutral news, minor concerns with remediation documented, mixed sentiment",
                "Score <70: Negative news, fraud incidents, financial difficulties, adverse events"
            ]
        }
    ]
    
    for factor in risk_factors:
        story.append(Paragraph(factor["name"], bold_style))
        for guideline in factor["guidelines"]:
            story.append(Paragraph(f"• {guideline}", normal_style))
        story.append(Spacer(1, 0.15 * inch))
    
    story.append(Spacer(1, 0.2 * inch))
    
    # Final Score table
    story.append(Paragraph("Final Score, Risk Category & Credit Limit Recommendation", bold_style))
    story.append(Spacer(1, 0.15 * inch))
    
    # Create table with proper text wrapping
    table_style = ParagraphStyle(
        'TableText',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        leftIndent=0,
        rightIndent=0
    )
    
    table_data = [
        [
            Paragraph("Final Risk<br/>Score Range", table_style),
            Paragraph("Underwriting<br/>Risk Category", table_style),
            Paragraph("Credit Limit Recommendation<br/>(as % of Requested Limit)", table_style),
            Paragraph("Notes", table_style)
        ],
        [
            Paragraph("85-100", table_style),
            Paragraph("Low Risk", table_style),
            Paragraph("90%-100%", table_style),
            Paragraph("Approve with<br/>standard terms", table_style)
        ],
        [
            Paragraph("70-84", table_style),
            Paragraph("Moderate Risk", table_style),
            Paragraph("70%-90%", table_style),
            Paragraph("Approve with<br/>monitoring", table_style)
        ],
        [
            Paragraph("50-69", table_style),
            Paragraph("High Risk", table_style),
            Paragraph("40%-70%", table_style),
            Paragraph("Approve with caution<br/>or reduced limit", table_style)
        ],
        [
            Paragraph("<50", table_style),
            Paragraph("Decline", table_style),
            Paragraph("0%", table_style),
            Paragraph("Decline coverage", table_style)
        ]
    ]
    
    # Adjust column widths to fit page (letter size is 8.5 inches, minus margins)
    table = Table(table_data, colWidths=[1.3 * inch, 1.5 * inch, 2.5 * inch, 2.0 * inch])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E0E0E0')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
    ]))
    
    story.append(table)
    doc.build(story)
    return str(filepath.resolve())


# ============================================================================
# Application Scenario Generation
# ============================================================================

def generate_application_scenario(
    app_index: int,
    target_risk_level: str,  # "low", "moderate", "high"
    buyer_ids: List[str],
    applications_path: Path,
    credit_bureau_path: Path,
    insurance_company_name: str = "Export Credit Guarantee Corporation of India"
) -> Dict[str, Any]:
    """Generate a policy application scenario targeting a specific risk level."""
    
    application_id = f"APP-{random.randint(100000, 999999)}"
    buyer_id = random.choice(buyer_ids)
    
    # Country and currency mapping
    country_currency_map = {
        "United Kingdom": ("GBP", "£"),
        "United States": ("USD", "$"),
        "Germany": ("EUR", "€"),
        "France": ("EUR", "€"),
        "Italy": ("EUR", "€"),
        "Spain": ("EUR", "€"),
        "Netherlands": ("EUR", "€"),
        "Belgium": ("EUR", "€"),
        "Sweden": ("SEK", "SEK"),
        "Norway": ("NOK", "NOK"),
        "Denmark": ("DKK", "DKK"),
        "Switzerland": ("CHF", "CHF"),
        "Poland": ("PLN", "PLN"),
        "Czech Republic": ("CZK", "CZK"),
        "India": ("INR", "INR"),
        "China": ("CNY", "CNY"),
        "Japan": ("JPY", "JPY"),
        "Australia": ("AUD", "A$"),
        "Canada": ("CAD", "C$"),
        "Singapore": ("SGD", "S$"),
        "United Arab Emirates": ("AED", "AED"),
        "Saudi Arabia": ("SAR", "SAR"),
        "South Africa": ("ZAR", "R"),
        "Brazil": ("BRL", "R$"),
        "Mexico": ("MXN", "$"),
    }
    
    # Buyer countries (typically international buyers)
    buyer_countries = [
        "United Kingdom", "United States", "Germany", "France", "Italy", "Spain",
        "Netherlands", "Belgium", "Sweden", "Norway", "Denmark", "Switzerland",
        "Poland", "Czech Republic", "Australia", "Canada", "Singapore",
        "United Arab Emirates", "Saudi Arabia", "South Africa", "Brazil", "Mexico"
    ]
    
    # Seller countries (typically India-based for this use case)
    seller_countries = [
        "India", "United States", "United Kingdom", "Germany", "China", "Japan",
        "Singapore", "United Arab Emirates", "Australia", "Canada"
    ]
    
    # Assign random countries
    buyer_country = random.choice(buyer_countries)
    seller_country = random.choice(seller_countries)
    
    # Determine currency - prefer buyer's country currency, fallback to seller's
    buyer_currency, buyer_symbol = country_currency_map.get(buyer_country, ("USD", "$"))
    seller_currency, seller_symbol = country_currency_map.get(seller_country, ("USD", "$"))
    
    # Use buyer's currency as primary (since insurance is for buyer's payment)
    currency = buyer_currency
    currency_symbol = buyer_symbol
    
    # Realistic buyer company names based on country
    buyer_companies_by_country = {
        "United Kingdom": ["Britannia Engineering Ltd", "Thames Manufacturing Group", "London Industrial Solutions"],
        "United States": ["American Precision Corp", "Continental Manufacturing Inc", "Atlantic Engineering Solutions"],
        "Germany": ["Rhein Valley Engineering GmbH", "Bavarian Industrial Systems", "Hamburg Manufacturing Co"],
        "France": ["Paris Industrial Solutions", "Lyon Manufacturing Group", "Marseille Engineering Corp"],
        "Italy": ["Mediterranean Manufacturing", "Milan Industrial Systems", "Rome Engineering Solutions"],
        "Spain": ["Iberian Manufacturing Co", "Madrid Industrial Group", "Barcelona Engineering Solutions"],
        "Netherlands": ["Amsterdam Industrial Systems", "Rotterdam Manufacturing", "Dutch Engineering Solutions"],
        "Belgium": ["Brussels Manufacturing Group", "Antwerp Industrial Systems", "Belgian Engineering Co"],
        "Sweden": ["Stockholm Engineering AB", "Scandinavian Manufacturing", "Nordic Industrial Solutions"],
        "Norway": ["Oslo Manufacturing AS", "Norwegian Engineering", "Nordic Industrial Systems"],
        "Denmark": ["Copenhagen Engineering", "Danish Manufacturing", "Scandinavian Industrial Solutions"],
        "Switzerland": ["Zurich Manufacturing AG", "Swiss Engineering Solutions", "Alpine Industrial Systems"],
        "Poland": ["Warsaw Manufacturing", "Polish Engineering Solutions", "Krakow Industrial Systems"],
        "Czech Republic": ["Prague Engineering", "Czech Manufacturing", "Central European Industrial"],
        "Australia": ["Sydney Manufacturing", "Melbourne Engineering", "Australian Industrial Solutions"],
        "Canada": ["Toronto Manufacturing", "Vancouver Engineering", "Canadian Industrial Solutions"],
        "Singapore": ["Singapore Manufacturing Pte", "ASEAN Engineering Solutions", "Southeast Asian Industrial"],
        "United Arab Emirates": ["Dubai Manufacturing", "Abu Dhabi Engineering", "Gulf Industrial Solutions"],
        "Saudi Arabia": ["Riyadh Manufacturing", "Jeddah Engineering", "Saudi Industrial Solutions"],
        "South Africa": ["Johannesburg Manufacturing", "Cape Town Engineering", "South African Industrial"],
        "Brazil": ["São Paulo Manufacturing", "Rio Engineering", "Brazilian Industrial Solutions"],
        "Mexico": ["Mexico City Manufacturing", "Monterrey Engineering", "Mexican Industrial Solutions"],
    }
    
    buyer_company_pool = buyer_companies_by_country.get(buyer_country, ["International Manufacturing", "Global Engineering Solutions"])
    buyer_name = random.choice(buyer_company_pool)
    
    # Realistic seller company names (India-focused but can be international)
    seller_companies_by_country = {
        "India": ["Mahindra Industrial Components", "Tata Manufacturing Solutions", "Reliance Engineering Supplies",
                  "Adani Industrial Products", "Bharat Heavy Components", "Larsen & Toubro Manufacturing",
                  "Godrej Industrial Systems", "Jindal Steel Components", "Vedanta Manufacturing Group"],
        "United States": ["American Manufacturing Corp", "US Industrial Solutions", "Continental Components Inc"],
        "United Kingdom": ["British Manufacturing Ltd", "UK Industrial Solutions", "London Components Group"],
        "Germany": ["German Engineering Solutions", "Deutsche Manufacturing", "Berlin Industrial Systems"],
        "China": ["China Manufacturing Corp", "Shanghai Industrial", "Beijing Engineering Solutions"],
        "Japan": ["Tokyo Manufacturing", "Osaka Engineering", "Japanese Industrial Solutions"],
        "Singapore": ["Singapore Manufacturing Pte", "ASEAN Components", "Southeast Asian Industrial"],
        "United Arab Emirates": ["Dubai Manufacturing", "UAE Industrial Solutions", "Gulf Components"],
        "Australia": ["Sydney Manufacturing", "Australian Industrial", "Melbourne Engineering"],
        "Canada": ["Toronto Manufacturing", "Canadian Industrial", "Vancouver Components"],
    }
    
    seller_company_pool = seller_companies_by_country.get(seller_country, ["International Manufacturing", "Global Components"])
    seller_name = random.choice(seller_company_pool)
    seller_email = f"credit@{seller_name.lower().replace(' ', '').replace('ltd', '').replace('inc', '').replace('llc', '')}.com"
    
    base_amount = round(random.uniform(200000, 800000), 0)
    
    # Adjust financial metrics based on target risk level
    if target_risk_level == "low":
        current_ratio = random.uniform(1.5, 2.5)
        revenue_growth = random.uniform(0.15, 0.30)
        net_income_margin = random.uniform(0.35, 0.50)
        credit_score = random.randint(75, 90)
        late_payments = 0
        internal_rating = "A (Low Risk)"
        recommended_limit = base_amount * random.uniform(1.1, 1.3)
        aged_debt_1_30 = 0
        aged_debt_31_60 = 0
        bank_delayed = None
    elif target_risk_level == "moderate":
        current_ratio = random.uniform(1.0, 1.5)
        revenue_growth = random.uniform(0.05, 0.15)
        net_income_margin = random.uniform(0.25, 0.35)
        credit_score = random.randint(60, 75)
        late_payments = random.randint(1, 2)
        internal_rating = "BBB (Medium Risk)"
        recommended_limit = base_amount * random.uniform(0.9, 1.1)
        aged_debt_1_30 = base_amount * random.uniform(0.05, 0.15)
        aged_debt_31_60 = base_amount * random.uniform(0.01, 0.05)
        delayed_amount = random.randint(40000, 60000)
        bank_delayed = f"{currency_symbol}{delayed_amount:,} in March 2025, settled after 31-day delay"
    else:  # high
        current_ratio = random.uniform(0.7, 1.0)
        revenue_growth = random.uniform(-0.10, 0.05)
        net_income_margin = random.uniform(0.10, 0.25)
        credit_score = random.randint(40, 60)
        late_payments = random.randint(3, 5)
        internal_rating = "CCC (High Risk)"
        recommended_limit = base_amount * random.uniform(0.7, 0.9)
        aged_debt_1_30 = base_amount * random.uniform(0.15, 0.25)
        aged_debt_31_60 = base_amount * random.uniform(0.05, 0.15)
        aged_debt_61_90 = base_amount * random.uniform(0.01, 0.05)
        bank_delayed = "Multiple delayed repayments, account under review"
    
    # Calculate financial statement values
    revenue_2024 = 15.0
    revenue_2023 = revenue_2024 / (1 + revenue_growth)
    revenue_2022 = revenue_2023 / (1 + revenue_growth * 0.8)
    
    cogs_2024 = revenue_2024 * 0.4
    cogs_2023 = revenue_2023 * 0.48
    cogs_2022 = revenue_2022 * 0.55
    
    gross_profit_2024 = revenue_2024 - cogs_2024
    gross_profit_2023 = revenue_2023 - cogs_2023
    gross_profit_2022 = revenue_2022 - cogs_2022
    
    opex_2024 = revenue_2024 * 0.15
    opex_2023 = revenue_2023 * 0.16
    opex_2022 = revenue_2022 * 0.18
    
    net_income_2024 = revenue_2024 * net_income_margin
    net_income_2023 = revenue_2023 * (net_income_margin * 0.9)
    net_income_2022 = revenue_2022 * (net_income_margin * 0.8)
    
    total_assets_2024 = revenue_2024 * 1.4
    total_assets_2023 = revenue_2023 * 1.5
    total_assets_2022 = revenue_2022 * 1.8
    
    current_assets_2024 = total_assets_2024 * 0.47
    current_assets_2023 = total_assets_2023 * 0.47
    current_assets_2022 = total_assets_2022 * 0.44
    
    current_liabilities_2024 = current_assets_2024 / current_ratio
    current_liabilities_2023 = current_assets_2023 / (current_ratio * 1.1)
    current_liabilities_2022 = current_assets_2022 / (current_ratio * 1.2)
    
    total_liabilities_2024 = total_assets_2024 * 0.47
    total_liabilities_2023 = total_assets_2023 * 0.42
    total_liabilities_2022 = total_assets_2022 * 0.41
    
    equity_2024 = total_assets_2024 - total_liabilities_2024
    equity_2023 = total_assets_2023 - total_liabilities_2023
    equity_2022 = total_assets_2022 - total_liabilities_2022
    
    fixed_assets_2024 = total_assets_2024 - current_assets_2024
    fixed_assets_2023 = total_assets_2023 - current_assets_2023
    fixed_assets_2022 = total_assets_2022 - current_assets_2022
    
    application = {
        "application_id": application_id,
        "currency": currency,
        "currency_symbol": currency_symbol,
        "seller_name": seller_name,
        "seller_email": seller_email,
        "seller_registered_number": f"{random.randint(10000000, 99999999)}",
        "seller_contact_name": random.choice(["John Smith", "Sarah Johnson", "Michael Brown", "Emily Davis"]),
        "seller_position": "Credit Manager",
        "seller_address": f"{random.randint(1, 100)} Industrial Park, {random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad', 'Pune'])}" if seller_country == "India" else f"{random.randint(1, 100)} Industrial Park, {seller_country}",
        "seller_postcode": random.choice(["400001", "110001", "560001", "600001", "700001", "500001", "411001"]) if seller_country == "India" else random.choice(["EC1A 1AA", "M1 1AA", "B1 1AA", "LS1 1AA"]),
        "seller_website": f"www.{seller_name.lower().replace(' ', '').replace('ltd', '').replace('inc', '').replace('llc', '')}.com",
        "buyer_id": buyer_id,
        "buyer_name": buyer_name,
        "buyer_address": f"{random.randint(100, 999)} Tech Road, {buyer_country}",
        "buyer_registered_number": f"{random.randint(10000000, 99999999)}",
        "requested_amount": base_amount,
        "requested_term_days": random.choice([180, 365, 540, 730]),
        "contract_date": (datetime.now() - timedelta(days=random.randint(30, 90))).strftime("%d %b %Y"),
        "contract_description": "Supply of industrial machinery components over 12 months",
        "insurance_reason": "To mitigate risk of non-payment due to buyer's financial instability",
        "business_type": "Revolving business",
        "shipment_period_days": random.randint(20, 40),
        "payment_terms": "60 days net",
        "differ_from_standard": "No",
        "trading_years": random.randint(2, 5),
        "payment_delays": random.choice([
            "Yes, occasional delays up to 15 days",
            "No",
            "Yes, delays up to 30 days"
        ]),
        "expected_turnover": base_amount * random.uniform(2.0, 3.0),
        "aged_debt_current": base_amount * random.uniform(0.6, 0.8),
        "aged_debt_1_30": aged_debt_1_30,
        "aged_debt_31_60": aged_debt_31_60,
        "aged_debt_61_90": aged_debt_61_90 if target_risk_level == "high" else 0,
        "aged_debt_90_plus": 0,
        "aged_debt_total": base_amount * random.uniform(0.8, 1.2),
        "sanctions_trading": "No",
        "sanctions_checks": "Yes",
        "group_company_cover": "No",
        "agent_or_principal": "Principal",
        "goods_services": "Industrial machinery components",
        "trade_sector": "Manufacturing and Engineering",
        "manufacture_goods": "Yes",
        "seasonal_business": "No",
        "associated_company_cover": "No",
        "revenue_2024": round(revenue_2024, 1),
        "revenue_2023": round(revenue_2023, 1),
        "revenue_2022": round(revenue_2022, 1),
        "cogs_2024": round(cogs_2024, 1),
        "cogs_2023": round(cogs_2023, 1),
        "cogs_2022": round(cogs_2022, 1),
        "gross_profit_2024": round(gross_profit_2024, 1),
        "gross_profit_2023": round(gross_profit_2023, 1),
        "gross_profit_2022": round(gross_profit_2022, 1),
        "opex_2024": round(opex_2024, 1),
        "opex_2023": round(opex_2023, 1),
        "opex_2022": round(opex_2022, 1),
        "net_income_2024": round(net_income_2024, 1),
        "net_income_2023": round(net_income_2023, 1),
        "net_income_2022": round(net_income_2022, 1),
        "total_assets_2024": round(total_assets_2024, 1),
        "total_assets_2023": round(total_assets_2023, 1),
        "total_assets_2022": round(total_assets_2022, 1),
        "current_assets_2024": round(current_assets_2024, 1),
        "current_assets_2023": round(current_assets_2023, 1),
        "current_assets_2022": round(current_assets_2022, 1),
        "fixed_assets_2024": round(fixed_assets_2024, 1),
        "fixed_assets_2023": round(fixed_assets_2023, 1),
        "fixed_assets_2022": round(fixed_assets_2022, 1),
        "current_liabilities_2024": round(current_liabilities_2024, 1),
        "current_liabilities_2023": round(current_liabilities_2023, 1),
        "current_liabilities_2022": round(current_liabilities_2022, 1),
        "total_liabilities_2024": round(total_liabilities_2024, 1),
        "total_liabilities_2023": round(total_liabilities_2023, 1),
        "total_liabilities_2022": round(total_liabilities_2022, 1),
        "equity_2024": round(equity_2024, 1),
        "equity_2023": round(equity_2023, 1),
        "equity_2022": round(equity_2022, 1),
        "internal_credit_rating": internal_rating,
        "internal_recommended_limit": round(recommended_limit, 0),
        "credit_bureau_score": credit_score,
        "credit_bureau_late_payments": late_payments,
        "credit_bureau_defaults": 0,
        "bank_name": random.choice(["HSBC", "Barclays", "Lloyds", "NatWest", "Santander"]),
        "bank_avg_balance": base_amount * random.uniform(0.2, 0.4),
        "bank_credit_facility": base_amount * random.uniform(0.5, 0.8),
        "bank_utilized": base_amount * random.uniform(0.3, 0.6),
        "bank_delayed_repayment": bank_delayed,
        "insurance_company_name": insurance_company_name,
        "target_risk_level": target_risk_level
    }
    
    # Generate all PDFs
    if REPORTLAB_AVAILABLE:
        application["application_form_path"] = generate_application_form_pdf(application, applications_path)
        application["financial_statements_path"] = generate_financial_statements_pdf(application, applications_path)
        application["supply_contract_path"] = generate_supply_contract_pdf(application, applications_path)
        application["bank_reference_path"] = generate_bank_reference_pdf(application, applications_path)
        application["sanctions_report_path"] = generate_sanctions_report_pdf(application, applications_path)
        application["aged_debtors_path"] = generate_aged_debtors_pdf(application, applications_path)
        application["internal_assessment_path"] = generate_internal_assessment_pdf(application, applications_path)
        application["credit_bureau_path"] = generate_credit_bureau_pdf(application, credit_bureau_path)
    else:
        application["application_form_path"] = None
        application["financial_statements_path"] = None
        application["supply_contract_path"] = None
        application["bank_reference_path"] = None
        application["sanctions_report_path"] = None
        application["aged_debtors_path"] = None
        application["internal_assessment_path"] = None
        application["credit_bureau_path"] = None
    
    return application


def main():
    parser = argparse.ArgumentParser(description="Setup TCI Policy Risk Assessor database and mock data")
    parser.add_argument("--db-path", type=str, default="projects/ensemble/data/tci/tci_database.db",
        help="Path to SQLite database file")
    parser.add_argument("--output-dir", type=str, default="projects/ensemble/data/tci/documents",
        help="PDF output directory")
    parser.add_argument("--reset", action="store_true", help="Drop existing tables and recreate")
    parser.add_argument("--low-risk-count", type=int, default=1, help="Number of low-risk applications")
    parser.add_argument("--moderate-risk-count", type=int, default=1, help="Number of moderate-risk applications")
    parser.add_argument("--high-risk-count", type=int, default=1, help="Number of high-risk applications")
    parser.add_argument("--buyer-count", type=int, default=3, help="Number of buyers to generate news for")
    parser.add_argument("--insurance-company-name", type=str, 
                       default="Export Credit Guarantee Corporation of India",
                       help="Name of the insurance company")
    
    args = parser.parse_args()
    
    # Use insurance company name from args (no interactive prompt)
    insurance_company_name = args.insurance_company_name
    
    project_name = detect_project_name(Path.cwd())
    db_path = resolve_script_path(args.db_path, project_name=project_name)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    output_path = resolve_script_path(args.output_dir, project_name=project_name)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories for organized PDF storage
    applications_path = output_path / "applications"
    applications_path.mkdir(parents=True, exist_ok=True)
    internal_path = output_path / "internal"
    internal_path.mkdir(parents=True, exist_ok=True)
    credit_bureau_path = output_path / "credit_bureau"
    credit_bureau_path.mkdir(parents=True, exist_ok=True)
    
    total_applications = args.low_risk_count + args.moderate_risk_count + args.high_risk_count
    
    print("=" * 70)
    print("TCI Policy Risk Assessor Database Setup")
    print("=" * 70)
    print(f"\nDatabase: {db_path}")
    print(f"Output directory: {output_path}")
    print(f"Reset mode: {args.reset}")
    print(f"Applications to generate: {total_applications} total")
    print(f"  - Low Risk: {args.low_risk_count}")
    print(f"  - Moderate Risk: {args.moderate_risk_count}")
    print(f"  - High Risk: {args.high_risk_count}")
    print(f"Buyers for news: {args.buyer_count}")
    print()
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    if args.reset:
        print("⚠ Resetting database (dropping all tables)...")
        cursor.execute("DROP TABLE IF EXISTS final_decisions")
        cursor.execute("DROP TABLE IF EXISTS recommendations")
        cursor.execute("DROP TABLE IF EXISTS risk_assessments")
        cursor.execute("DROP TABLE IF EXISTS policy_applications")
        cursor.execute("DROP TABLE IF EXISTS buyer_news")
        cursor.execute("DROP TABLE IF EXISTS risk_factors")
        conn.commit()
        print("✓ Tables dropped")
        
        pdf_count = 0
        # Clean up PDFs from all subdirectories (recursive)
        for pdf_file in output_path.rglob("*.pdf"):
            pdf_file.unlink()
            pdf_count += 1
        if pdf_count > 0:
            print(f"✓ Deleted {pdf_count} old PDF file(s)")
        
        # Delete reports folder
        reports_path = db_path.parent / "reports"
        if reports_path.exists() and reports_path.is_dir():
            shutil.rmtree(reports_path)
            print(f"✓ Deleted reports folder: {reports_path}")
    
    print("\n1. Creating database schema...")
    create_database_schema(str(db_path))
    
    buyer_ids = [f"BUY-{random.randint(10000, 99999)}" for _ in range(args.buyer_count)]
    
    print("\n2. Generating buyer news database...")
    generate_mock_buyer_news(cursor, buyer_ids, articles_per_buyer=3)
    
    print("\n3. Generating risk factors database...")
    generate_mock_risk_factors(cursor)
    
    conn.commit()
    
    print("\n4. Generating underwriting manual...")
    if REPORTLAB_AVAILABLE:
        manual_path = generate_underwriting_manual_pdf(internal_path)
        print(f"✓ Underwriting manual: {manual_path}")
    
    print(f"\n5. Generating {total_applications} policy applications with documents...")
    applications_created = []
    app_counter = 0
    
    for risk_level, count in [("low", args.low_risk_count), ("moderate", args.moderate_risk_count), ("high", args.high_risk_count)]:
        for i in range(count):
            app_counter += 1
            try:
                application = generate_application_scenario(
                    app_counter, risk_level, buyer_ids, applications_path, credit_bureau_path, insurance_company_name
                )
                
                if REPORTLAB_AVAILABLE:
                    print(f"  ✓ Application {app_counter}/{total_applications}: {application['application_id']} ({risk_level} risk)")
                    currency_symbol = application.get('currency_symbol', '£')
                    print(f"    Requested Amount: {currency_symbol}{application['requested_amount']:,.0f}")
                    print(f"    Buyer: {application['buyer_name']}")
                
                cursor.execute("""
                    INSERT OR REPLACE INTO policy_applications (
                        application_id, seller_name, seller_email, buyer_name, buyer_id,
                        requested_amount, requested_term_days,
                        currency_code, currency_symbol,
                        application_form_path, financial_statements_path, supply_contract_path,
                        bank_reference_path, sanctions_report_path, aged_debtors_path,
                        internal_assessment_path, credit_bureau_path, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    application["application_id"],
                    application["seller_name"],
                    application["seller_email"],
                    application["buyer_name"],
                    application["buyer_id"],
                    application["requested_amount"],
                    application["requested_term_days"],
                    application.get("currency"),
                    application.get("currency_symbol"),
                    application.get("application_form_path"),
                    application.get("financial_statements_path"),
                    application.get("supply_contract_path"),
                    application.get("bank_reference_path"),
                    application.get("sanctions_report_path"),
                    application.get("aged_debtors_path"),
                    application.get("internal_assessment_path"),
                    application.get("credit_bureau_path"),
                    "pending"
                ))
                
                applications_created.append(application)
                
            except Exception as e:
                print(f"  ✗ Failed to generate application {app_counter}: {e}")
                import traceback
                traceback.print_exc()
    
    conn.commit()
    conn.close()
    
    print(f"\n✓ Setup complete!")
    print(f"  - {len(applications_created)} applications created")
    print(f"  - {args.buyer_count} buyers with news articles")
    print(f"  - Risk factors database populated")
    print(f"\nDatabase: {db_path}")
    print(f"Documents: {output_path}")


if __name__ == "__main__":
    main()
