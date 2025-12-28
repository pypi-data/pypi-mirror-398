#!/usr/bin/env python3
"""Setup script for ECI Claims Vetting pipeline.

Creates SQLite database, initializes schema, and generates mock data:
- Claims tracking table
- Voyage database (mock shipping voyages)
- Buyer registry (buyer legitimacy database)
- Validation results table
- Decision results table
- Mock PDF documents (claim forms, invoices, bills of lading)

Usage:
    python scripts/setup_eci_database.py [--db-path <path>] [--output-dir <dir>] [--reset] [--approve-count <n>] [--request-docs-count <n>] [--escalate-count <n>]
    uv run -m scripts.setup_eci_database --db-path projects/ensemble/data/eci/eci_database.db --reset
"""

import sqlite3
import os
import sys
import argparse
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

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
    
    # Claims table - tracks all claims
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            claim_id TEXT PRIMARY KEY,
            claim_form_path TEXT,
            invoice_path TEXT,
            bol_path TEXT,
            policy_number TEXT,
            policy_path TEXT,
            claim_reason_category TEXT,
            claim_reason_description TEXT,
            claimant_name TEXT,
            claimant_email TEXT,
            buyer_name TEXT,
            seller_name TEXT,
            invoice_number TEXT,
            invoice_amount REAL,
            invoice_date TEXT,
            currency_code TEXT,
            currency_symbol TEXT,
            shipment_vessel TEXT,
            shipment_origin_port TEXT,
            shipment_destination_port TEXT,
            bol_date TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            run_id TEXT
        )
    """)
    
    # Voyages table - mock voyage database
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voyages (
            voyage_id TEXT PRIMARY KEY,
            vessel_name TEXT NOT NULL,
            origin_port TEXT NOT NULL,
            destination_port TEXT NOT NULL,
            departure_date TEXT NOT NULL,
            arrival_date TEXT NOT NULL,
            voyage_window_days INTEGER DEFAULT 3,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Buyer registry table - buyer legitimacy database
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS buyer_registry (
            buyer_id TEXT PRIMARY KEY,
            company_name TEXT NOT NULL,
            registration_date TEXT,
            domain TEXT,
            domain_age_years INTEGER,
            domain_country TEXT,
            email_domain TEXT,
            company_status TEXT,
            risk_flags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Validation results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS validation_results (
            result_id TEXT PRIMARY KEY,
            claim_id TEXT NOT NULL,
            validator_type TEXT NOT NULL,
            passed INTEGER NOT NULL,
            issues_found TEXT,
            details TEXT,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (claim_id) REFERENCES claims(claim_id)
        )
    """)
    
    # Decision results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decision_results (
            decision_id TEXT PRIMARY KEY,
            claim_id TEXT NOT NULL,
            decision TEXT NOT NULL,
            risk_score INTEGER,
            red_flags TEXT,
            requested_evidence TEXT,
            rationale TEXT,
            decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (claim_id) REFERENCES claims(claim_id)
        )
    """)
    
    # Policies table - tracks insurance policies
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS policies (
            policy_number TEXT PRIMARY KEY,
            policy_path TEXT NOT NULL,
            insured_party TEXT NOT NULL,
            coverage_start_date TEXT NOT NULL,
            coverage_end_date TEXT NOT NULL,
            coverage_limit REAL NOT NULL,
            deductible REAL,
            coverage_percentage REAL,
            commercial_risk_coverage INTEGER DEFAULT 1,
            political_risk_coverage INTEGER DEFAULT 0,
            covered_risks TEXT,
            exclusions TEXT,
            max_claims_per_term INTEGER,
            max_claims_per_year INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Claim history table - tracks past claims for a policy
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS claim_history (
            history_id TEXT PRIMARY KEY,
            policy_number TEXT NOT NULL,
            claim_id TEXT NOT NULL,
            claim_date TEXT NOT NULL,
            claim_amount REAL NOT NULL,
            claim_status TEXT NOT NULL,
            decision TEXT,
            risk_score INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (policy_number) REFERENCES policies(policy_number)
        )
    """)
    
    # Create indexes for faster lookups
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_claims_run_id ON claims(run_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_claims_policy_number ON claims(policy_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_policies_insured_party ON policies(insured_party)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_voyages_vessel_ports ON voyages(vessel_name, origin_port, destination_port)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_buyer_registry_company ON buyer_registry(company_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_validation_results_claim ON validation_results(claim_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_decision_results_claim ON decision_results(claim_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_claim_history_policy ON claim_history(policy_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_claim_history_date ON claim_history(claim_date)")
    
    conn.commit()
    conn.close()
    print("✓ Database schema created")


def generate_mock_voyages(cursor, count: int = 30) -> List[Dict[str, Any]]:
    """Generate mock voyage data."""
    # Realistic vessel names
    vessel_prefixes = ["MV", "MS", "SS"]
    vessel_names = [
        "Pacific Star", "Atlantic Dream", "Ocean Navigator", "Sea Horizon", 
        "Maritime Express", "Cargo Master", "Blue Wave", "Eastern Glory",
        "Western Pride", "Northern Light", "Southern Cross", "Global Trader",
        "Fortune Ship", "Liberty Vessel", "Victory Ship", "Enterprise",
        "Discovery", "Endeavour", "Explorer", "Pioneer"
    ]
    
    # Common major ports
    ports = [
        "Shanghai", "Singapore", "Rotterdam", "Los Angeles", "Hamburg",
        "Dubai", "Hong Kong", "Busan", "Ningbo", "Shenzhen",
        "Guangzhou", "Qingdao", "Tianjin", "Kaohsiung", "Port Klang",
        "Antwerp", "Xiamen", "New York", "Tanjung Pelepas", "Laem Chabang"
    ]
    
    voyages = []
    base_date = datetime.now() - timedelta(days=180)  # Start 6 months ago
    
    for i in range(count):
        voyage_id = f"VOY-{random.randint(10000, 99999)}"
        vessel_name = f"{random.choice(vessel_prefixes)} {random.choice(vessel_names)}"
        
        # Select origin and destination (must be different)
        origin = random.choice(ports)
        destination = random.choice([p for p in ports if p != origin])
        
        # Calculate voyage duration based on rough distance estimates
        # Shanghai-LA: 14 days, Rotterdam-Shanghai: 30 days, etc.
        voyage_duration = random.randint(7, 45)
        
        # Random departure date in past 6 months
        departure_date = base_date + timedelta(days=random.randint(0, 150))
        arrival_date = departure_date + timedelta(days=voyage_duration)
        
        voyage = {
            "voyage_id": voyage_id,
            "vessel_name": vessel_name,
            "origin_port": origin,
            "destination_port": destination,
            "departure_date": departure_date.strftime("%Y-%m-%d"),
            "arrival_date": arrival_date.strftime("%Y-%m-%d"),
            "voyage_window_days": 3  # ±3 days tolerance
        }
        
        cursor.execute("""
            INSERT OR REPLACE INTO voyages 
            (voyage_id, vessel_name, origin_port, destination_port, departure_date, arrival_date, voyage_window_days)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            voyage["voyage_id"],
            voyage["vessel_name"],
            voyage["origin_port"],
            voyage["destination_port"],
            voyage["departure_date"],
            voyage["arrival_date"],
            voyage["voyage_window_days"]
        ))
        
        voyages.append(voyage)
    
    print(f"✓ Generated {len(voyages)} mock voyages")
    return voyages


def generate_mock_buyers(cursor, count: int = 25) -> List[Dict[str, Any]]:
    """Generate mock buyer registry with risk profiles."""
    company_types = ["Corp", "Inc", "Ltd", "LLC", "GmbH", "SA", "AG", "Holdings"]
    industries = [
        "Electronics", "Textiles", "Machinery", "Automotive", "Chemicals",
        "Pharmaceuticals", "Food Products", "Steel", "Plastics", "Furniture"
    ]
    
    countries = [
        "USA", "China", "Germany", "UK", "Japan", "Singapore", "Netherlands", "South Korea",
        "Canada", "Australia", "India", "France", "Italy", "Spain", "Brazil", "Mexico",
        "Switzerland", "UAE", "Saudi Arabia", "Thailand", "Malaysia", "Indonesia", "Philippines",
        "Turkey", "Poland", "Sweden", "Norway", "Denmark", "Belgium", "Austria"
    ]
    country_tlds = {
        "USA": "com", "China": "cn", "Germany": "de", "UK": "co.uk",
        "Japan": "jp", "Singapore": "sg", "Netherlands": "nl", "South Korea": "kr",
        "Canada": "ca", "Australia": "au", "India": "in", "France": "fr", "Italy": "it",
        "Spain": "es", "Brazil": "br", "Mexico": "mx", "Switzerland": "ch", "UAE": "ae",
        "Saudi Arabia": "sa", "Thailand": "th", "Malaysia": "my", "Indonesia": "id",
        "Philippines": "ph", "Turkey": "tr", "Poland": "pl", "Sweden": "se", "Norway": "no",
        "Denmark": "dk", "Belgium": "be", "Austria": "at"
    }
    
    buyers = []
    
    for i in range(count):
        buyer_id = f"BUY-{random.randint(10000, 99999)}"
        industry = random.choice(industries)
        company_name = f"{random.choice(['Global', 'Pacific', 'United', 'International', 'Asia', 'Euro'])} {industry} {random.choice(company_types)}"
        
        # Determine risk profile (60% legitimate, 25% medium risk, 15% high risk)
        risk_category = random.choices(
            ['legitimate', 'medium_risk', 'high_risk'],
            weights=[60, 25, 15],
            k=1
        )[0]
        
        country = random.choice(countries)
        tld = country_tlds[country]
        
        if risk_category == 'legitimate':
            # Established company
            registration_date = (datetime.now() - timedelta(days=random.randint(1825, 7300))).strftime("%Y-%m-%d")  # 5-20 years
            domain_age_years = random.randint(5, 20)
            company_status = "Active"
            domain_country = country
            email_domain = f"{company_name.lower().replace(' ', '')}.{tld}"
            risk_flags = "None"
            
        elif risk_category == 'medium_risk':
            # Young company
            registration_date = (datetime.now() - timedelta(days=random.randint(365, 1095))).strftime("%Y-%m-%d")  # 1-3 years
            domain_age_years = random.randint(1, 3)
            company_status = "Active"
            # Sometimes domain country doesn't match
            domain_country = country if random.random() < 0.7 else random.choice([c for c in countries if c != country])
            email_domain = f"{company_name.lower().replace(' ', '')}.{tld}"
            risk_flags = random.choice(["Young company", "Domain age mismatch"])
            
        else:  # high_risk
            # Very young or suspicious company
            registration_date = (datetime.now() - timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d")  # < 1 year
            domain_age_years = random.randint(0, 1)
            company_status = random.choice(["Active", "Pending", "Suspended"])
            # Domain country often doesn't match
            domain_country = random.choice([c for c in countries if c != country])
            email_domain = f"{company_name.lower().replace(' ', '')}.{random.choice(['com', 'net', 'org'])}"
            risk_flags = random.choice([
                "Very young company, Domain-country mismatch",
                "Company status suspended, Domain age < 1 year",
                "Domain-country mismatch, Email domain mismatch"
            ])
        
        buyer = {
            "buyer_id": buyer_id,
            "company_name": company_name,
            "registration_date": registration_date,
            "domain": f"{company_name.lower().replace(' ', '')}.{tld}",
            "domain_age_years": domain_age_years,
            "domain_country": domain_country,
            "email_domain": email_domain,
            "company_status": company_status,
            "risk_flags": risk_flags
        }
        
        cursor.execute("""
            INSERT OR REPLACE INTO buyer_registry
            (buyer_id, company_name, registration_date, domain, domain_age_years, domain_country, email_domain, company_status, risk_flags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            buyer["buyer_id"],
            buyer["company_name"],
            buyer["registration_date"],
            buyer["domain"],
            buyer["domain_age_years"],
            buyer["domain_country"],
            buyer["email_domain"],
            buyer["company_status"],
            buyer["risk_flags"]
        ))
        
        buyers.append(buyer)
    
    print(f"✓ Generated {len(buyers)} mock buyers (risk distribution: 60% legitimate, 25% medium, 15% high)")
    return buyers


def calculate_expected_risk_score(scenario: Dict[str, Any], buyer: Dict[str, Any]) -> int:
    """Calculate expected risk score based on scenario type and buyer profile.
    
    Risk scoring rules (from edc_decision_recommender.jinja):
    - Validation failure: +30 points
    - Buyer not found: +25 points
    - Buyer high risk: +30 points, medium risk: +15 points
    - Unknown voyage: +25 points
    - Date outside window: +20 points
    - Low extraction confidence (< 0.7): +15 points (we assume normal confidence for generated claims)
    
    Note: Actual risk scores may differ if:
    - Buyer name doesn't match exactly in database (buyer not found: +25)
    - Vessel/port combination doesn't match exactly (unknown voyage: +25)
      * CRITICAL: SQLite = operator is case-sensitive. If OCR extracts "Ss Pioneer" 
        but database has "SS Pioneer", the query will fail (unknown voyage: +25)
    - Amounts don't match due to extraction/rounding (validation failure: +30)
    - Extraction confidence is low (< 0.7: +15)
    
    Args:
        scenario: Scenario dict with type and issues
        buyer: Buyer dict with risk profile
    
    Returns:
        Expected risk score (0-100) based on intended scenario configuration
    """
    risk_score = 0
    
    scenario_type = scenario.get("type", "")
    issues = scenario.get("issues", [])
    issues_str = ", ".join(issues) if issues else ""
    
    # Check for validation failures (amount mismatch, date discrepancy)
    if scenario_type in ["amount_mismatch", "date_discrepancy"]:
        risk_score += 30  # Validation failure
    
    # Check for unknown voyage (check both type and issues)
    # Also check if vessel_name contains "Unknown" which indicates unknown voyage
    vessel_name = scenario.get("vessel_name", "")
    if (scenario_type == "unknown_voyage" or 
        "Vessel/port combination not found" in issues_str or
        "unknown_voyage" in scenario_type.lower() or
        "Unknown" in vessel_name):
        risk_score += 25  # Unknown voyage
    
    # Check for date outside window
    if (scenario_type == "bol_outside_window" or 
        "Bill of lading date falls outside" in issues_str):
        risk_score += 20  # Date outside window
    
    # Check buyer risk
    # According to buyer checker prompt:
    # - Legitimate: company_status = 'Active' AND domain_age_years >= 5 AND risk_flags = 'None'
    # - Medium Risk: company_status = 'Active' AND domain_age_years >= 1 AND domain_age_years < 5, minor risk flags (young company, domain age mismatch)
    # - High Risk: company_status != 'Active' OR domain_age_years < 1 OR serious risk flags (domain-country mismatch, suspended status)
    if buyer:
        domain_age = buyer.get("domain_age_years", 0)
        company_status = buyer.get("company_status", "")
        risk_flags = buyer.get("risk_flags", "")
        
        # Check for serious risk flags first (domain-country mismatch, suspended status)
        has_serious_flags = (
            "domain-country mismatch" in risk_flags.lower() or
            "suspended" in company_status.lower() or
            company_status.lower() != "active"
        )
        
        # High risk: domain_age < 1 OR company_status != "Active" OR serious risk flags
        if domain_age < 1 or has_serious_flags:
            risk_score += 30  # High risk buyer
        # Medium risk: domain_age >= 1 and < 5, Active status, minor flags (including "Domain age mismatch")
        elif domain_age >= 1 and domain_age < 5 and company_status == "Active":
            risk_score += 15  # Medium risk buyer
        # Legitimate: domain_age >= 5, Active, no risk flags (or risk_flags = "None")
        # No points added (risk_score stays at base)
    
    # Cap at 100
    risk_score = min(risk_score, 100)
    
    return risk_score


# Claim reason definitions with detailed descriptions
CLAIM_REASONS = {
    "approve": [
        {
            "category": "Commercial Risk",
            "description": "The buyer, {buyer_name}, failed to make payment of ${claim_amount:,.2f} for invoice {invoice_number} dated {invoice_date}. Despite multiple payment reminders sent via email and registered mail, and a 30-day grace period following the original payment due date, no payment has been received as of the claim date. The buyer has not responded to any communications regarding this outstanding invoice, and our accounts receivable department has confirmed that all standard collection procedures have been exhausted without success."
        },
        {
            "category": "Commercial Risk",
            "description": "The buyer, {buyer_name}, has been declared insolvent by the court of {country} on {insolvency_date}. This declaration was made after the buyer failed to meet its financial obligations to multiple creditors. Our invoice {invoice_number} for ${claim_amount:,.2f} dated {invoice_date} remains unpaid. We have received official documentation from the bankruptcy court confirming the insolvency proceedings and the appointment of a liquidator to manage the buyer's assets."
        },
        {
            "category": "Commercial Risk",
            "description": "The buyer, {buyer_name}, has defaulted on payment for invoice {invoice_number} dated {invoice_date} in the amount of ${claim_amount:,.2f}. The payment was due {days_overdue} days ago. Despite repeated attempts to contact the buyer through multiple channels including email, phone, and registered mail, we have received no response. Our credit department has verified that the buyer's account is in default status and all standard collection efforts have been unsuccessful."
        },
    ],
    "request_docs": [
        {
            "category": "Commercial Risk",
            "description": "The buyer, {buyer_name}, has delayed payment for invoice {invoice_number} dated {invoice_date} in the amount of ${claim_amount:,.2f}. The payment is currently {days_overdue} days overdue. The buyer has communicated that they are experiencing temporary cash flow difficulties but have not provided sufficient documentation to support their claim or establish a clear payment timeline. We require additional financial documentation and a formal payment plan before proceeding with the claim."
        },
        {
            "category": "Political Risk",
            "description": "The buyer, {buyer_name}, located in {country}, has informed us that they are unable to transfer payment of ${claim_amount:,.2f} for invoice {invoice_number} due to currency transfer restrictions imposed by the local government. The central bank has implemented new regulations limiting foreign currency transfers, and the buyer has provided documentation showing their transfer application was denied. We require additional documentation from the buyer and confirmation from the central bank regarding the specific restrictions and their duration."
        },
        {
            "category": "Commercial Risk",
            "description": "The buyer, {buyer_name}, has disputed the invoice {invoice_number} dated {invoice_date} for ${claim_amount:,.2f}, claiming that the goods received did not match the specifications in the purchase order. However, the buyer has not provided detailed documentation of the alleged discrepancies, photographs of the goods, or a formal inspection report. We require comprehensive documentation including the original purchase order, delivery receipts, inspection reports, and photographic evidence to properly assess the validity of this claim."
        },
    ],
    "escalate": [
        {
            "category": "Political Risk",
            "description": "The buyer, {buyer_name}, located in {country}, has been unable to make payment of ${claim_amount:,.2f} for invoice {invoice_number} due to war and civil disturbance in the region. The buyer's facilities have been damaged, and the local government has declared a state of emergency. Transportation routes are blocked, and the buyer's operations have been severely disrupted. We have received reports from multiple sources confirming the conflict situation, but require additional verification from official sources and assessment of the extent of damage to the buyer's operations."
        },
        {
            "category": "Commercial Risk",
            "description": "The buyer, {buyer_name}, has been identified as potentially engaging in fraudulent activities. Our investigation has revealed discrepancies between the information provided by the buyer during the credit application process and the actual circumstances. The buyer's company registration documents appear to be inconsistent with their stated business operations, and there are indications of misrepresentation regarding their financial standing. This case requires immediate escalation to the Special Investigations Unit for a comprehensive fraud investigation."
        },
        {
            "category": "Political Risk",
            "description": "The buyer, {buyer_name}, located in {country}, has been unable to make payment of ${claim_amount:,.2f} for invoice {invoice_number} due to expropriation of their assets by the local government. The buyer's facilities and bank accounts have been seized by government authorities without compensation. We have received official notification from the buyer's legal counsel confirming the expropriation, but require additional documentation including government notices, legal filings, and confirmation from independent sources to verify the circumstances and assess the claim."
        },
    ],
    "reject": [
        {
            "category": "Excluded Risk",
            "description": "The claim relates to a pre-existing condition that was not disclosed at the time of policy issuance. The buyer, {buyer_name}, had outstanding payment issues that existed prior to the policy coverage period, and these issues were not reported during the application process. The policy explicitly excludes coverage for claims arising from pre-existing conditions or circumstances known to the insured party but not disclosed to the insurer."
        },
        {
            "category": "Excluded Risk",
            "description": "The claim involves willful misconduct on the part of the insured party. Our investigation has revealed that the insured party knowingly engaged in business practices that violated the terms of the policy, including extending credit to a buyer with known financial difficulties without proper authorization. The policy explicitly excludes coverage for losses resulting from willful misconduct, gross negligence, or violation of policy terms by the insured party."
        },
    ],
}


def generate_policy_pdf(
    policy_number: str,
    insured_party: str,
    target_decision: str,
    coverage_limit: float,
    output_path: Path,
    currency_code: str = "USD",
    currency_symbol: str = "$"
) -> Dict[str, Any]:
    """Generate export credit insurance policy PDF. Returns policy dict with path."""
    if not REPORTLAB_AVAILABLE:
        return {
            "policy_number": policy_number,
            "policy_path": None,
            "coverage_limit": coverage_limit,
            "deductible": 0,
            "coverage_percentage": 0.9,
        }
    
    filename = f"policy_{policy_number}.pdf"
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
    story.append(Paragraph("Export Credit Insurance Policy", title_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Policy details based on target decision
    if target_decision == "approve":
        # Broad coverage, high limits
        commercial_coverage = True
        political_coverage = True
        deductible = coverage_limit * 0.02  # 2% deductible
        coverage_pct = 0.90  # 90% coverage
        max_claims_per_term = 50  # High limit for approve scenarios
        max_claims_per_year = 20
        covered_risks = [
            "Buyer insolvency",
            "Buyer payment default (commercial)",
            "Buyer payment default (political)",
            "War and civil disturbance",
            "Expropriation",
            "Currency inconvertibility",
            "Currency transfer restrictions",
            "Pre-shipment risk",
            "Post-shipment risk"
        ]
        exclusions = [
            "Pre-existing conditions",
            "Willful misconduct",
            "Nuclear risks"
        ]
    elif target_decision == "request_docs":
        # Standard coverage, moderate limits
        commercial_coverage = True
        political_coverage = True
        deductible = coverage_limit * 0.05  # 5% deductible
        coverage_pct = 0.85  # 85% coverage
        max_claims_per_term = 30  # Moderate limit
        max_claims_per_year = 12
        covered_risks = [
            "Buyer insolvency",
            "Buyer payment default (commercial)",
            "Currency transfer restrictions",
            "Post-shipment risk"
        ]
        exclusions = [
            "Pre-existing conditions",
            "War and civil disturbance",
            "Expropriation",
            "Willful misconduct",
            "Nuclear risks",
            "Pre-shipment risk"
        ]
    elif target_decision == "escalate":
        # Limited coverage, lower limits
        commercial_coverage = True
        political_coverage = False
        deductible = coverage_limit * 0.10  # 10% deductible
        coverage_pct = 0.75  # 75% coverage
        max_claims_per_term = 20  # Lower limit
        max_claims_per_year = 8
        covered_risks = [
            "Buyer insolvency",
            "Buyer payment default (commercial)"
        ]
        exclusions = [
            "Pre-existing conditions",
            "All political risks",
            "War and civil disturbance",
            "Expropriation",
            "Currency inconvertibility",
            "Willful misconduct",
            "Nuclear risks",
            "Pre-shipment risk"
        ]
    else:  # reject
        # Very limited coverage
        commercial_coverage = True
        political_coverage = False
        deductible = coverage_limit * 0.15  # 15% deductible
        coverage_pct = 0.60  # 60% coverage
        max_claims_per_term = 10  # Very low limit
        max_claims_per_year = 4
        covered_risks = [
            "Buyer insolvency (verified cases only)"
        ]
        exclusions = [
            "Pre-existing conditions",
            "All political risks",
            "Buyer payment default",
            "War and civil disturbance",
            "Expropriation",
            "Currency inconvertibility",
            "Willful misconduct",
            "Gross negligence",
            "Nuclear risks",
            "Pre-shipment risk"
        ]
    
    # Coverage period
    coverage_start = datetime.now() - timedelta(days=365)
    coverage_end = datetime.now() + timedelta(days=365)
    
    # Policy information
    policy_data = [
        ["Policy Number:", policy_number],
        ["Insured Party:", insured_party],
        ["Policy Period:", f"{coverage_start.strftime('%Y-%m-%d')} to {coverage_end.strftime('%Y-%m-%d')}"],
        ["", ""],
        ["Coverage Details", ""],
        ["Coverage Limit:", f"{currency_symbol}{coverage_limit:,.2f}"],
        ["Deductible:", f"{currency_symbol}{deductible:,.2f}"],
        ["Coverage Percentage:", f"{coverage_pct*100:.0f}%"],
        ["Commercial Risk Coverage:", "Yes" if commercial_coverage else "No"],
        ["Political Risk Coverage:", "Yes" if political_coverage else "No"],
        ["", ""],
        ["Covered Risks", ""],
    ]
    
    for risk in covered_risks:
        policy_data.append(["", f"• {risk}"])
    
    policy_data.append(["", ""])
    policy_data.append(["Exclusions", ""])
    
    for exclusion in exclusions:
        policy_data.append(["", f"• {exclusion}"])
    
    policy_data.append(["", ""])
    policy_data.append(["Claim Limits", ""])
    policy_data.append(["", f"Maximum claims per policy term: {max_claims_per_term}"])
    policy_data.append(["", f"Maximum claims per calendar year: {max_claims_per_year}"])
    policy_data.append(["", ""])
    policy_data.append(["Policy Terms", ""])
    policy_data.append(["", "This policy provides coverage for export credit risks as specified above."])
    policy_data.append(["", "Claims must be submitted within 90 days of the loss event."])
    policy_data.append(["", "All claims are subject to verification and approval by the insurer."])
    policy_data.append(["", "The insured party must maintain accurate records of all transactions."])
    policy_data.append(["", f"Policy term limit: Maximum {max_claims_per_term} claims per policy term."])
    policy_data.append(["", f"Annual limit: Maximum {max_claims_per_year} claims per calendar year."])
    
    table = Table(policy_data, colWidths=[2.5 * inch, 4 * inch])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('FONTNAME', (0, 4), (0, 4), 'Helvetica-Bold'),
        ('FONTNAME', (0, 11), (0, 11), 'Helvetica-Bold'),
        ('FONTNAME', (0, 11 + len(covered_risks) + 1), (0, 11 + len(covered_risks) + 1), 'Helvetica-Bold'),
        ('FONTNAME', (0, 11 + len(covered_risks) + len(exclusions) + 2), (0, 11 + len(covered_risks) + len(exclusions) + 2), 'Helvetica-Bold'),
    ]))
    
    story.append(table)
    doc.build(story)
    
    return {
        "policy_number": policy_number,
        "policy_path": str(filepath.resolve()),
        "insured_party": insured_party,
        "coverage_start_date": coverage_start.strftime("%Y-%m-%d"),
        "coverage_end_date": coverage_end.strftime("%Y-%m-%d"),
        "coverage_limit": coverage_limit,
        "deductible": deductible,
        "coverage_percentage": coverage_pct,
        "commercial_risk_coverage": 1 if commercial_coverage else 0,
        "political_risk_coverage": 1 if political_coverage else 0,
        "covered_risks": ", ".join(covered_risks),
        "exclusions": ", ".join(exclusions),
        "max_claims_per_term": max_claims_per_term,
        "max_claims_per_year": max_claims_per_year,
    }


def generate_claim_scenario(
    claim_index: int,
    target_decision: str,
    voyages: List[Dict],
    buyers: List[Dict],
    policy_output_path: Path
) -> Dict[str, Any]:
    """Generate a claim scenario targeting a specific decision category.
    
    Args:
        claim_index: Index of the claim being generated
        target_decision: One of 'approve', 'request_docs', 'escalate', 'reject'
        voyages: List of available voyages
        buyers: List of available buyers
        policy_output_path: Path to save policy PDFs
    
    Returns:
        Dict with claim data and scenario information
    """
    
    # Select buyer and voyage based on target decision
    voyage = random.choice(voyages)
    
    # Generate claim data
    claim_id = f"CLM-{random.randint(100000, 999999)}"
    invoice_number = f"INV-{random.randint(10000, 99999)}"
    
    # Base amounts
    base_amount = round(random.uniform(10000, 500000), 2)
    
    # Currency mapping based on country (will be set after buyer selection)
    country_currency_map = {
        "USA": ("USD", "$"),
        "China": ("CNY", "¥"),
        "Germany": ("EUR", "€"),
        "UK": ("GBP", "£"),
        "Japan": ("JPY", "¥"),
        "Singapore": ("SGD", "S$"),
        "Netherlands": ("EUR", "€"),
        "South Korea": ("KRW", "KRW"),  # Using "KRW" instead of ₩ as reportlab may not render it correctly
        "Canada": ("CAD", "C$"),
        "Australia": ("AUD", "A$"),
        "India": ("INR", "INR"),  # Using "INR" instead of ₹ as reportlab may not render it correctly
        "France": ("EUR", "€"),
        "Italy": ("EUR", "€"),
        "Spain": ("EUR", "€"),
        "Brazil": ("BRL", "R$"),
        "Mexico": ("MXN", "$"),
        "Switzerland": ("CHF", "CHF"),
        "UAE": ("AED", "AED"),
        "Saudi Arabia": ("SAR", "SAR"),
        "Thailand": ("THB", "THB"),  # Using "THB" instead of ฿ as reportlab may not render it correctly
        "Malaysia": ("MYR", "RM"),
        "Indonesia": ("IDR", "IDR"),  # Using "IDR" instead of "Rp" for consistency
        "Philippines": ("PHP", "PHP"),  # Using "PHP" instead of ₱ as reportlab may not render it correctly
        "Turkey": ("TRY", "TRY"),  # Using "TRY" instead of ₺ as reportlab may not render it correctly
        "Poland": ("PLN", "PLN"),  # Using "PLN" instead of zł as reportlab may not render it correctly
        "Sweden": ("SEK", "SEK"),  # Using "SEK" instead of "kr" to avoid confusion with other kr currencies
        "Norway": ("NOK", "NOK"),  # Using "NOK" instead of "kr" to avoid confusion
        "Denmark": ("DKK", "DKK"),  # Using "DKK" instead of "kr" to avoid confusion
        "Belgium": ("EUR", "€"),
        "Austria": ("EUR", "€"),
    }
    
    # Currency will be determined after buyer selection based on buyer's country
    currency_code, currency_symbol = ("USD", "$")  # Default, will be updated after buyer selection
    
    # Claimant information
    claimant_first_names = ["John", "Sarah", "Michael", "Emily", "David", "Jessica", "Robert", "Amanda"]
    claimant_last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
    claimant_name = f"{random.choice(claimant_first_names)} {random.choice(claimant_last_names)}"
    claimant_email = f"{claimant_name.lower().replace(' ', '.')}@example.com"
    
    # Seller information
    seller_companies = [
        "Acme Exports Ltd", "Global Trade Corp", "Pacific Shipping Inc",
        "International Freight LLC", "Ocean Cargo Solutions", "Maritime Logistics Group"
    ]
    seller_name = random.choice(seller_companies)
    
    # Generate policy for this claim
    policy_number = f"POL-{random.randint(100000, 999999)}"
    # Coverage limit should be higher than claim amount, with variations by scenario
    if target_decision == "approve":
        coverage_limit = base_amount * random.uniform(1.5, 2.5)  # 150-250% of claim
    elif target_decision == "request_docs":
        coverage_limit = base_amount * random.uniform(1.2, 1.8)  # 120-180% of claim
    elif target_decision == "escalate":
        coverage_limit = base_amount * random.uniform(1.0, 1.5)  # 100-150% of claim
    else:  # reject
        coverage_limit = base_amount * random.uniform(0.8, 1.2)  # 80-120% of claim (may be insufficient)
    
    coverage_limit = round(coverage_limit, 2)
    
    # Policy PDF will be generated after currency is determined
    # (We need buyer selection first to determine currency)
    policy_data = None  # Will be generated after currency is set
    
    # Select claim reason based on target decision
    available_reasons = CLAIM_REASONS.get(target_decision, CLAIM_REASONS["approve"])
    reason_template = random.choice(available_reasons)
    
    # Calculate days overdue for claim reason description
    invoice_date_obj = None  # Will be set later in scenario
    days_overdue = random.randint(30, 120)
    insolvency_date = (datetime.now() - timedelta(days=random.randint(10, 30))).strftime("%Y-%m-%d")
    countries = [
        "USA", "China", "Germany", "UK", "Japan", "Singapore", "Netherlands", "South Korea",
        "Canada", "Australia", "India", "France", "Italy", "Spain", "Brazil", "Mexico",
        "Switzerland", "UAE", "Saudi Arabia", "Thailand", "Malaysia", "Indonesia", "Philippines",
        "Turkey", "Poland", "Sweden", "Norway", "Denmark", "Belgium", "Austria"
    ]
    country = random.choice(countries)
    
    # Scenario determination based on target decision
    scenario = {}
    
    if target_decision == "approve":
        # CRITICAL: For approve scenarios, ensure EVERYTHING matches perfectly
        # 1. Select ONLY legitimate buyers (domain_age_years >= 5, Active, risk_flags = "None")
        legitimate_buyers = [
            b for b in buyers 
            if b.get("domain_age_years", 0) >= 5 
            and b.get("company_status") == "Active"
            and b.get("risk_flags") == "None"
        ]
        if not legitimate_buyers:
            # If no legitimate buyers exist, create one by modifying an existing buyer
            # This should not happen with 60% legitimate distribution, but handle it
            fallback_buyer = random.choice(buyers).copy()
            fallback_buyer["domain_age_years"] = 10
            fallback_buyer["company_status"] = "Active"
            fallback_buyer["risk_flags"] = "None"
            legitimate_buyers = [fallback_buyer]
        buyer = random.choice(legitimate_buyers)
        
        # Determine currency based on buyer's country
        buyer_country = buyer.get("domain_country", "USA")
        currency_code, currency_symbol = country_currency_map.get(buyer_country, ("USD", "$"))
        
        # 2. Use the selected voyage EXACTLY (vessel_name, origin_port, destination_port must match)
        #    NOTE: OCR/extraction may change vessel name case (e.g., "SS Pioneer" → "Ss Pioneer")
        #    This causes SQLite case-sensitive queries to fail. Shipment validator should use
        #    case-insensitive matching (LOWER() or COLLATE NOCASE) for approve scenarios.
        # 3. Ensure BOL date is WITHIN voyage window (departure_date ± 3 days)
        #    Use 0 or ±1 days to be safely within the ±3 day window
        departure_date = datetime.strptime(voyage["departure_date"], "%Y-%m-%d")
        bol_date = departure_date + timedelta(days=random.choice([-1, 0, 1]))  # Safely within ±3 window
        
        # 4. Ensure invoice_date is BEFORE bol_date (invoice_date <= bol_date)
        #    Set invoice_date to be 7-10 days before departure, ensuring it's before bol_date
        invoice_date = departure_date - timedelta(days=random.randint(7, 10))
        
        # 5. Ensure amounts match EXACTLY (claim_amount == invoice_amount)
        #    Use same base_amount for both
        
        # Valid scenario - everything matches, legitimate buyer only
        scenario["type"] = "valid"
        scenario["claim_amount"] = base_amount
        scenario["invoice_amount"] = base_amount  # Exact match
        scenario["invoice_date"] = invoice_date
        scenario["bol_date"] = bol_date
        scenario["buyer"] = buyer
        scenario["vessel_name"] = voyage["vessel_name"]  # Exact match
        scenario["origin_port"] = voyage["origin_port"]  # Exact match
        scenario["destination_port"] = voyage["destination_port"]  # Exact match
        scenario["invoice_number"] = invoice_number
        scenario["issues"] = []
    
    elif target_decision == "request_docs":
        # Medium risk - minor issues that need clarification
        # Use scenarios that result in "request_docs" decision (risk score 26-50)
        # Need to combine minor issues to reach 26-50 range:
        # - Date outside window: +20 points
        # - Medium risk buyer: +15 points
        # Total: 35 points (in request_docs range)
        
        # CRITICAL: Select ONLY medium-risk buyers (1-4 years old, Active, minor flags only)
        # Must NOT have "Domain-country mismatch" (that's high risk)
        medium_risk_buyers = [
            b for b in buyers 
            if b.get("domain_age_years", 0) >= 1 
            and b.get("domain_age_years", 0) < 5 
            and b.get("company_status") == "Active"
            and "domain-country mismatch" not in b.get("risk_flags", "").lower()
        ]
        if not medium_risk_buyers:
            # If no medium risk buyers without serious flags, create one
            fallback_buyer = random.choice([b for b in buyers if b.get("domain_age_years", 0) >= 1 and b.get("domain_age_years", 0) < 5]).copy()
            fallback_buyer["company_status"] = "Active"
            fallback_buyer["risk_flags"] = "Young company"  # Minor flag only
            medium_risk_buyers = [fallback_buyer]
        
        scenario["buyer"] = random.choice(medium_risk_buyers)
        
        # Determine currency based on buyer's country
        buyer_country = scenario["buyer"].get("domain_country", "USA")
        currency_code, currency_symbol = country_currency_map.get(buyer_country, ("USD", "$"))
        
        # Ensure invoice_date is BEFORE bol_date to avoid validation failure
        departure_date = datetime.strptime(voyage["departure_date"], "%Y-%m-%d")
        invoice_date = departure_date - timedelta(days=random.randint(7, 10))
        
        # BOL date slightly outside voyage window (4-6 days, not way outside)
        # This ensures date outside window (+20) but voyage is still found
        bol_date = departure_date + timedelta(days=random.choice([-6, -5, -4, 4, 5, 6]))
        
        # Always combine medium-risk buyer (+15) with date outside window (+20) = 35 points (in 26-50 range)
        scenario["type"] = "bol_outside_window"
        scenario["claim_amount"] = base_amount
        scenario["invoice_amount"] = base_amount  # Exact match to avoid validation failure
        scenario["invoice_date"] = invoice_date
        scenario["bol_date"] = bol_date
        scenario["vessel_name"] = voyage["vessel_name"]  # Exact match to ensure voyage found
        scenario["origin_port"] = voyage["origin_port"]  # Exact match
        scenario["destination_port"] = voyage["destination_port"]  # Exact match
        scenario["invoice_number"] = invoice_number
        scenario["issues"] = [
            "Bill of lading date falls outside known voyage window",
            f"Buyer is young company ({scenario['buyer'].get('domain_age_years', 'unknown')} years old)"
        ]
    
    else:  # target_decision == "escalate"
        # For escalate scenarios, use any buyer (will be filtered later)
        buyer = random.choice(buyers)
        
        # Dates for escalate scenarios (will be adjusted per scenario type)
        invoice_date = datetime.strptime(voyage["departure_date"], "%Y-%m-%d") - timedelta(days=random.randint(5, 15))
        bol_date = datetime.strptime(voyage["departure_date"], "%Y-%m-%d") + timedelta(days=random.randint(-2, 2))
        
        # High risk - serious issues that require investigation
        # Use scenarios that result in "escalate" decision (risk score 51-75)
        # Risk scoring: high-risk buyer +30, unknown voyage +25, validation failure +30, date outside +20
        # Need 51+ points total, so combine issues appropriately
        issue_types = [
            "amount_mismatch_with_high_risk_buyer",  # Validation failure +30 + high-risk buyer +30 = 60
            "unknown_voyage_with_high_risk_buyer",   # Unknown voyage +25 + high-risk buyer +30 = 55
            "date_discrepancy_with_high_risk_buyer", # Validation failure +30 + high-risk buyer +30 = 60
            "suspicious_buyer_with_unknown_voyage"   # High-risk buyer +30 + unknown voyage +25 = 55
        ]
        selected_issue = random.choice(issue_types)
        
        # Find high-risk buyers according to buyer checker logic:
        # High Risk: company_status != 'Active' OR domain_age_years < 1 OR serious risk flags (domain-country mismatch, suspended status)
        # Must NOT include "Domain age mismatch" (that's medium risk)
        high_risk_buyers = [
            b for b in buyers 
            if b.get("domain_age_years", 0) < 1 
            or b.get("company_status", "").lower() != "active"
            or "domain-country mismatch" in b.get("risk_flags", "").lower()
            or "suspended" in b.get("company_status", "").lower()
        ]
        
        # If no high-risk buyers found, create one by modifying a buyer
        if not high_risk_buyers:
            # Take a random buyer and make it high-risk
            fallback_buyer = random.choice(buyers)
            fallback_buyer = fallback_buyer.copy()
            fallback_buyer["domain_age_years"] = 0
            fallback_buyer["company_status"] = "Suspended"
            fallback_buyer["risk_flags"] = "Very young company, Domain-country mismatch, Company status suspended"
            high_risk_buyers = [fallback_buyer]
        
        high_risk_buyer = random.choice(high_risk_buyers)
        
        # Determine currency based on buyer's country
        buyer_country = high_risk_buyer.get("domain_country", "USA")
        currency_code, currency_symbol = country_currency_map.get(buyer_country, ("USD", "$"))
        
        if selected_issue == "amount_mismatch_with_high_risk_buyer":
            # Validation failure (+30) + high-risk buyer (+30) = 60 points
            scenario["type"] = "amount_mismatch"
            scenario["claim_amount"] = base_amount
            scenario["invoice_amount"] = base_amount * random.uniform(0.7, 1.4)  # 30-40% difference to ensure validation failure
            scenario["invoice_date"] = invoice_date
            scenario["bol_date"] = bol_date
            scenario["buyer"] = high_risk_buyer
            scenario["vessel_name"] = voyage["vessel_name"]
            scenario["origin_port"] = voyage["origin_port"]
            scenario["destination_port"] = voyage["destination_port"]
            scenario["invoice_number"] = invoice_number
            scenario["issues"] = [
                "Amount mismatch between claim form and invoice",
                f"Buyer has risk flags: {high_risk_buyer['risk_flags']}"
            ]
            
        elif selected_issue == "unknown_voyage_with_high_risk_buyer":
            # Unknown voyage (+25) + high-risk buyer (+30) = 55 points
            scenario["type"] = "unknown_voyage"
            scenario["claim_amount"] = base_amount
            scenario["invoice_amount"] = base_amount
            scenario["invoice_date"] = invoice_date
            scenario["bol_date"] = bol_date
            scenario["buyer"] = high_risk_buyer
            scenario["vessel_name"] = f"MV Unknown-{random.randint(100, 999)}"  # Non-existent vessel
            scenario["origin_port"] = voyage["origin_port"]
            scenario["destination_port"] = voyage["destination_port"]
            scenario["invoice_number"] = invoice_number
            scenario["issues"] = [
                "Vessel/port combination not found in voyage database",
                f"Buyer has risk flags: {high_risk_buyer['risk_flags']}"
            ]
            
        elif selected_issue == "date_discrepancy_with_high_risk_buyer":
            # Validation failure (+30) + high-risk buyer (+30) = 60 points
            scenario["type"] = "date_discrepancy"
            scenario["claim_amount"] = base_amount
            scenario["invoice_amount"] = base_amount
            scenario["invoice_date"] = bol_date + timedelta(days=random.randint(5, 15))  # Invoice after BOL (clear discrepancy)
            scenario["bol_date"] = bol_date
            scenario["buyer"] = high_risk_buyer
            scenario["vessel_name"] = voyage["vessel_name"]
            scenario["origin_port"] = voyage["origin_port"]
            scenario["destination_port"] = voyage["destination_port"]
            scenario["invoice_number"] = invoice_number
            scenario["issues"] = [
                "Invoice date is after bill of lading date",
                f"Buyer has risk flags: {high_risk_buyer['risk_flags']}"
            ]
            
        else:  # suspicious_buyer_with_date_issue
            # High-risk buyer (+30) + date outside window (+20) = 50 points (not enough!)
            # Change to: high-risk buyer + unknown voyage = 55 points (escalate range)
            scenario["type"] = "suspicious_buyer"
            scenario["claim_amount"] = base_amount
            scenario["invoice_amount"] = base_amount
            scenario["invoice_date"] = invoice_date
            scenario["bol_date"] = bol_date
            scenario["buyer"] = high_risk_buyer
            # Use unknown vessel to add +25 points: 30 + 25 = 55 points (escalate)
            scenario["vessel_name"] = f"MV Unknown-{random.randint(100, 999)}"  # Non-existent vessel
            scenario["origin_port"] = voyage["origin_port"]
            scenario["destination_port"] = voyage["destination_port"]
            scenario["invoice_number"] = invoice_number
            scenario["issues"] = [
                f"Buyer has risk flags: {high_risk_buyer['risk_flags']}",
                "Vessel/port combination not found in voyage database"
            ]
    
    # Format claim reason description with actual values
    buyer_name_for_reason = scenario["buyer"]["company_name"]
    invoice_date_str = scenario["invoice_date"].strftime("%Y-%m-%d")
    
    # Format the claim reason description
    claim_reason_description = reason_template["description"].format(
        buyer_name=buyer_name_for_reason,
        claim_amount=base_amount,
        invoice_number=invoice_number,
        invoice_date=invoice_date_str,
        days_overdue=days_overdue,
        insolvency_date=insolvency_date,
        country=country
    )
    
    # Ensure currency is set based on final buyer (in case it wasn't set earlier)
    if "currency_code" not in locals() or currency_code is None:
        buyer_country = scenario["buyer"].get("domain_country", "USA")
        currency_code, currency_symbol = country_currency_map.get(buyer_country, ("USD", "$"))
    
    # Generate policy PDF now that we have currency
    if policy_data is None:
        policy_data = generate_policy_pdf(
            policy_number=policy_number,
            insured_party=seller_name,
            target_decision=target_decision,
            coverage_limit=coverage_limit,
            output_path=policy_output_path,
            currency_code=currency_code,
            currency_symbol=currency_symbol
        )
    
    # Calculate expected risk score
    expected_risk_score = calculate_expected_risk_score(scenario, scenario["buyer"])
    
    # Determine expected decision based on risk score
    if expected_risk_score <= 25:
        expected_decision = "approve"
    elif expected_risk_score <= 50:
        expected_decision = "request_docs"
    elif expected_risk_score <= 75:
        expected_decision = "escalate"
    else:
        expected_decision = "reject"
    
    claim = {
        "claim_id": claim_id,
        "policy_number": policy_number,
        "policy_path": policy_data["policy_path"],
        "claim_reason_category": reason_template["category"],
        "claim_reason_description": claim_reason_description,
        "claimant_name": claimant_name,
        "claimant_email": claimant_email,
        "buyer_name": scenario["buyer"]["company_name"],
        "seller_name": seller_name,
        "invoice_number": scenario["invoice_number"],
        "claim_amount": round(scenario["claim_amount"], 2),
        "invoice_amount": round(scenario["invoice_amount"], 2),
        "invoice_date": scenario["invoice_date"].strftime("%Y-%m-%d"),
        "currency_code": currency_code,
        "currency_symbol": currency_symbol,
        "shipment_vessel": scenario["vessel_name"],
        "shipment_origin_port": scenario["origin_port"],
        "shipment_destination_port": scenario["destination_port"],
        "bol_date": scenario["bol_date"].strftime("%Y-%m-%d"),
        "scenario_type": scenario["type"],
        "expected_issues": scenario["issues"],
        "expected_risk_score": expected_risk_score,
        "expected_decision": expected_decision,
        "policy_data": policy_data  # Include full policy data for database insertion
    }
    
    return claim


def generate_claim_form_pdf(claim: Dict, output_path: Path) -> str:
    """Generate claim form PDF. Returns absolute path."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is required for PDF generation")
    
    filename = f"claim_form_{claim['claim_id']}.pdf"
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
    story.append(Paragraph("Insurance Claim Form", title_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Claim information table
    data = [
        ["Claim ID:", claim["claim_id"]],
        ["Claim Date:", datetime.now().strftime("%Y-%m-%d")],
        ["Policy Number:", claim.get("policy_number", "N/A")],
        ["", ""],
        ["Claimant Information", ""],
        ["Name:", claim["claimant_name"]],
        ["Email:", claim["claimant_email"]],
        ["", ""],
        ["Claim Details", ""],
        ["Claim Amount:", f"{claim.get('currency_symbol', '$')}{claim['claim_amount']:,.2f}"],
        ["Claim Reason Category:", claim.get("claim_reason_category", "N/A")],
        ["", ""],
        ["Buyer Information", ""],
        ["Buyer Company:", claim["buyer_name"]],
        ["", ""],
        ["Seller Information", ""],
        ["Seller Company:", claim["seller_name"]],
        ["", ""],
        ["Invoice Information", ""],
        ["Invoice Number:", claim["invoice_number"]],
        ["", ""],
        ["Shipment Information", ""],
        ["Vessel Name:", claim["shipment_vessel"]],
        ["Origin Port:", claim["shipment_origin_port"]],
        ["Destination Port:", claim["shipment_destination_port"]],
    ]
    
    table = Table(data, colWidths=[2.5 * inch, 4 * inch])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        # Bold section headers
        ('FONTNAME', (0, 4), (0, 4), 'Helvetica-Bold'),
        ('FONTNAME', (0, 8), (0, 8), 'Helvetica-Bold'),
        ('FONTNAME', (0, 12), (0, 12), 'Helvetica-Bold'),
        ('FONTNAME', (0, 15), (0, 15), 'Helvetica-Bold'),
        ('FONTNAME', (0, 18), (0, 18), 'Helvetica-Bold'),
        ('FONTNAME', (0, 21), (0, 21), 'Helvetica-Bold'),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 0.2 * inch))
    
    # Add claim reason description as a separate paragraph
    reason_desc = claim.get("claim_reason_description", "")
    if reason_desc:
        reason_style = ParagraphStyle(
            'ReasonStyle',
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=0.2 * inch,
            rightIndent=0.2 * inch,
            spaceAfter=12,
            alignment=TA_JUSTIFY
        )
        story.append(Paragraph("<b>Detailed Claim Reason:</b>", reason_style))
        story.append(Paragraph(reason_desc, reason_style))
    doc.build(story)
    return str(filepath)


def generate_invoice_pdf(claim: Dict, output_path: Path) -> str:
    """Generate commercial invoice PDF. Returns absolute path."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is required for PDF generation")
    
    filename = f"invoice_{claim['claim_id']}.pdf"
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
    story.append(Paragraph("Commercial Invoice", title_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Invoice header
    header_data = [
        ["Invoice Number:", claim["invoice_number"]],
        ["Invoice Date:", claim["invoice_date"]],
        ["", ""],
        ["Seller:", claim["seller_name"]],
        ["Buyer:", claim["buyer_name"]],
    ]
    
    header_table = Table(header_data, colWidths=[2 * inch, 4.5 * inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Line items
    products = [
        "Electronic Components", "Textile Materials", "Machinery Parts",
        "Automotive Parts", "Chemical Products", "Steel Products"
    ]
    
    num_items = random.randint(2, 5)
    line_items = [["Description", "Quantity", "Unit Price", "Amount"]]
    
    subtotal = 0
    for i in range(num_items):
        product = random.choice(products)
        quantity = random.randint(10, 1000)
        unit_price = round(claim['invoice_amount'] / (num_items * quantity * random.uniform(0.8, 1.2)), 2)
        amount = round(quantity * unit_price, 2)
        subtotal += amount
        currency_symbol = claim.get('currency_symbol', '$')
        line_items.append([product, str(quantity), f"{currency_symbol}{unit_price:,.2f}", f"{currency_symbol}{amount:,.2f}"])
    
    # Adjust to match invoice amount
    adjustment = claim['invoice_amount'] - subtotal
    currency_symbol = claim.get('currency_symbol', '$')
    if abs(adjustment) > 0.01:
        line_items.append(["Adjustment", "", "", f"{currency_symbol}{adjustment:,.2f}"])
    
    line_items.append(["", "", "Total:", f"{currency_symbol}{claim['invoice_amount']:,.2f}"])
    
    items_table = Table(line_items, colWidths=[3 * inch, 1 * inch, 1.25 * inch, 1.25 * inch])
    items_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -2), 1, colors.grey),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(items_table)
    
    doc.build(story)
    return str(filepath.absolute())


def generate_bill_of_lading_pdf(claim: Dict, output_path: Path) -> str:
    """Generate bill of lading PDF. Returns absolute path."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is required for PDF generation")
    
    filename = f"bol_{claim['claim_id']}.pdf"
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
    story.append(Paragraph("Bill of Lading", title_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # BOL information
    bol_number = f"BOL-{random.randint(100000, 999999)}"
    
    data = [
        ["B/L Number:", bol_number],
        ["B/L Date:", claim["bol_date"]],
        ["", ""],
        ["Shipper:", claim["seller_name"]],
        ["Consignee:", claim["buyer_name"]],
        ["", ""],
        ["Vessel Information", ""],
        ["Vessel Name:", claim["shipment_vessel"]],
        ["Port of Loading:", claim["shipment_origin_port"]],
        ["Port of Discharge:", claim["shipment_destination_port"]],
        ["", ""],
        ["Cargo Description", ""],
        ["Description:", "Containerized Cargo - See Manifest"],
        ["Container No:", f"CONT-{random.randint(100000, 999999)}"],
        ["Gross Weight:", f"{random.randint(5000, 25000)} kg"],
    ]
    
    table = Table(data, colWidths=[2.5 * inch, 4 * inch])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        # Bold section headers
        ('FONTNAME', (0, 6), (0, 6), 'Helvetica-Bold'),
        ('FONTNAME', (0, 11), (0, 11), 'Helvetica-Bold'),
    ]))
    
    story.append(table)
    doc.build(story)
    return str(filepath.absolute())


def generate_past_claim_history(
    cursor,
    policy_number: str,
    policy_data: Dict[str, Any],
    target_decision: str
) -> List[Dict[str, Any]]:
    """Generate past claim history for a policy based on target decision scenario.
    
    Args:
        cursor: Database cursor
        policy_number: Policy number
        policy_data: Policy data dictionary with coverage dates and limits
        target_decision: Target decision scenario (approve, request_docs, escalate, reject)
    
    Returns:
        List of claim history records
    """
    max_claims_per_term = policy_data.get("max_claims_per_term", 30)
    max_claims_per_year = policy_data.get("max_claims_per_year", 12)
    coverage_start = datetime.strptime(policy_data["coverage_start_date"], "%Y-%m-%d")
    coverage_end = datetime.strptime(policy_data["coverage_end_date"], "%Y-%m-%d")
    
    # Determine number of past claims based on target decision
    if target_decision == "approve":
        # Low claim count - well within limits
        num_claims = random.randint(2, max_claims_per_term // 3)
    elif target_decision == "request_docs":
        # Moderate claim count - approaching limits
        num_claims = random.randint(max_claims_per_term // 2, max_claims_per_term - 5)
    elif target_decision == "escalate":
        # High claim count - near or at limits
        num_claims = random.randint(max_claims_per_term - 3, max_claims_per_term)
    else:  # reject
        # Exceeds limits - too many claims
        num_claims = random.randint(max_claims_per_term + 1, max_claims_per_term + 5)
    
    # Ensure we don't exceed reasonable bounds
    num_claims = min(num_claims, max_claims_per_term + 5)
    num_claims = max(num_claims, 0)
    
    claim_history = []
    decisions = ["approve", "request_docs", "escalate", "reject"]
    statuses = ["approved", "pending", "rejected", "under_review"]
    
    # Generate claims distributed over the policy period
    for i in range(num_claims):
        # Random date within policy period
        days_into_policy = random.randint(0, (coverage_end - coverage_start).days)
        claim_date = coverage_start + timedelta(days=days_into_policy)
        
        # Random claim amount (10% to 50% of coverage limit)
        claim_amount = policy_data["coverage_limit"] * random.uniform(0.10, 0.50)
        
        # Risk score based on target decision scenario (not random decision)
        # This ensures historical claims align with the scenario's risk profile
        if target_decision == "approve":
            # For approve scenarios: ensure ALL historical claims have risk_score < 70
            # Most should be low-risk (0-25), allow some medium-risk (26-50) but none high-risk
            if random.random() < 0.8:  # 80% low-risk
                risk_score = random.randint(0, 25)
            else:  # 20% medium-risk
                risk_score = random.randint(26, 50)
            # Ensure no high-risk claims (risk_score >= 70)
            assert risk_score < 70, "Approve scenario should not have high-risk historical claims"
        elif target_decision == "request_docs":
            # For request_docs: allow mix of low/medium, maybe 1-2 medium-high (51-69), but limit high-risk
            rand_val = random.random()
            if rand_val < 0.6:  # 60% low-risk
                risk_score = random.randint(0, 25)
            elif rand_val < 0.9:  # 30% medium-risk
                risk_score = random.randint(26, 50)
            else:  # 10% medium-high risk (but still < 70)
                risk_score = random.randint(51, 69)
        elif target_decision == "escalate":
            # For escalate: allow mix including some high-risk (>= 70)
            rand_val = random.random()
            if rand_val < 0.4:  # 40% low-risk
                risk_score = random.randint(0, 25)
            elif rand_val < 0.7:  # 30% medium-risk
                risk_score = random.randint(26, 50)
            elif rand_val < 0.9:  # 20% medium-high risk
                risk_score = random.randint(51, 69)
            else:  # 10% high-risk
                risk_score = random.randint(70, 100)
        else:  # reject
            # For reject: many high-risk claims
            rand_val = random.random()
            if rand_val < 0.3:  # 30% low-risk
                risk_score = random.randint(0, 25)
            elif rand_val < 0.5:  # 20% medium-risk
                risk_score = random.randint(26, 50)
            elif rand_val < 0.7:  # 20% medium-high risk
                risk_score = random.randint(51, 69)
            else:  # 30% high-risk
                risk_score = random.randint(70, 100)
        
        # Assign decision and status based on risk score (for consistency)
        if risk_score <= 25:
            decision = "approve"
            status = "approved"
        elif risk_score <= 50:
            decision = "request_docs"
            status = random.choice(["approved", "pending", "under_review"])
        elif risk_score <= 75:
            decision = "escalate"
            status = random.choice(["pending", "under_review", "rejected"])
        else:  # risk_score > 75
            decision = "reject"
            status = "rejected"
        
        history_id = f"HIST-{policy_number}-{i+1:03d}"
        claim_id = f"CLM-{random.randint(100000, 999999)}"
        
        history_record = {
            "history_id": history_id,
            "policy_number": policy_number,
            "claim_id": claim_id,
            "claim_date": claim_date.strftime("%Y-%m-%d"),
            "claim_amount": round(claim_amount, 2),
            "claim_status": status,
            "decision": decision,
            "risk_score": risk_score,
        }
        
        cursor.execute("""
            INSERT OR REPLACE INTO claim_history (
                history_id, policy_number, claim_id, claim_date,
                claim_amount, claim_status, decision, risk_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            history_record["history_id"],
            history_record["policy_number"],
            history_record["claim_id"],
            history_record["claim_date"],
            history_record["claim_amount"],
            history_record["claim_status"],
            history_record["decision"],
            history_record["risk_score"],
        ))
        
        claim_history.append(history_record)
    
    return claim_history


def main():
    parser = argparse.ArgumentParser(description="Setup ECI Claims database and mock data")
    parser.add_argument(
        "--db-path",
        type=str,
        default="projects/ensemble/data/eci/eci_database.db",
        help="Path to SQLite database file (default: projects/ensemble/data/eci/eci_database.db)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="projects/ensemble/data/eci/documents",
        help="PDF output directory (default: projects/ensemble/data/eci/documents)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop existing tables and recreate (WARNING: deletes all data). Default: False (off)"
    )
    parser.add_argument(
        "--approve-count",
        type=int,
        default=1,
        help="Number of claims to generate for 'approve' decision (default: 1)"
    )
    parser.add_argument(
        "--request-docs-count",
        type=int,
        default=1,
        help="Number of claims to generate for 'request_docs' decision (default: 1)"
    )
    parser.add_argument(
        "--escalate-count",
        type=int,
        default=1,
        help="Number of claims to generate for 'escalate' decision (default: 1)"
    )
    parser.add_argument(
        "--voyage-count",
        type=int,
        default=30,
        help="Number of voyages in database (default: 30)"
    )
    parser.add_argument(
        "--buyer-count",
        type=int,
        default=25,
        help="Number of buyers in registry (default: 25)"
    )
    
    args = parser.parse_args()
    
    # Detect project name for path resolution
    project_name = detect_project_name(Path.cwd())
    
    # Resolve paths intelligently (works from repo root or project_dir)
    db_path = resolve_script_path(args.db_path, project_name=project_name)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_path = resolve_script_path(args.output_dir, project_name=project_name)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create policies directory
    policy_output_path = output_path.parent / "policies"
    policy_output_path.mkdir(parents=True, exist_ok=True)
    
    total_claims = args.approve_count + args.request_docs_count + args.escalate_count
    
    print("=" * 70)
    print("ECI Claims Database Setup")
    print("=" * 70)
    print(f"\nDatabase: {db_path}")
    print(f"Output directory: {output_path}")
    print(f"Reset mode: {args.reset}")
    print(f"Claims to generate: {total_claims} total")
    print(f"  - Approve: {args.approve_count}")
    print(f"  - Request Docs: {args.request_docs_count}")
    print(f"  - Escalate: {args.escalate_count}")
    print(f"Voyages in database: {args.voyage_count}")
    print(f"Buyers in registry: {args.buyer_count}")
    print()
    
    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Reset if requested
    if args.reset:
        print("⚠ Resetting database (dropping all tables)...")
        cursor.execute("DROP TABLE IF EXISTS decision_results")
        cursor.execute("DROP TABLE IF EXISTS validation_results")
        cursor.execute("DROP TABLE IF EXISTS claim_history")
        cursor.execute("DROP TABLE IF EXISTS claims")
        cursor.execute("DROP TABLE IF EXISTS policies")
        cursor.execute("DROP TABLE IF EXISTS voyages")
        cursor.execute("DROP TABLE IF EXISTS buyer_registry")
        conn.commit()
        print("✓ Tables dropped")
        
        # Clean up old PDF files
        print("⚠ Cleaning up old PDF files...")
        pdf_count = 0
        for pdf_file in output_path.glob("*.pdf"):
            pdf_file.unlink()
            pdf_count += 1
        for pdf_file in policy_output_path.glob("*.pdf"):
            pdf_file.unlink()
            pdf_count += 1
        if pdf_count > 0:
            print(f"✓ Deleted {pdf_count} old PDF file(s)")
        else:
            print("✓ No old PDF files to clean up")
        
        # Clean up old report files
        reports_path = db_path.parent / "reports"
        if reports_path.exists():
            print("⚠ Cleaning up old report files...")
            report_count = 0
            for report_file in reports_path.glob("*.md"):
                report_file.unlink()
                report_count += 1
            if report_count > 0:
                print(f"✓ Deleted {report_count} old report file(s)")
            else:
                print("✓ No old report files to clean up")
        else:
            print("✓ Reports directory does not exist, skipping cleanup")
    
    # Create schema
    print("\n1. Creating database schema...")
    create_database_schema(str(db_path))
    
    # Generate voyage database
    print("\n2. Generating voyage database...")
    voyages = generate_mock_voyages(cursor, args.voyage_count)
    
    # Generate buyer registry
    print("\n3. Generating buyer registry...")
    buyers = generate_mock_buyers(cursor, args.buyer_count)
    
    conn.commit()
    
    # Generate claims by category
    print(f"\n4. Generating {total_claims} claims with documents...")
    claims_created = []
    claim_counter = 0
    
    # Generate approve claims
    for i in range(args.approve_count):
        claim_counter += 1
        try:
            claim = generate_claim_scenario(claim_counter, "approve", voyages, buyers, policy_output_path)
            
            if REPORTLAB_AVAILABLE:
                claim_form_path = generate_claim_form_pdf(claim, output_path)
                invoice_path = generate_invoice_pdf(claim, output_path)
                bol_path = generate_bill_of_lading_pdf(claim, output_path)
                
                print(f"  ✓ Claim {claim_counter}/{total_claims}: {claim['claim_id']} (approve - {claim['scenario_type']})")
                print(f"    Expected Risk Score: {claim['expected_risk_score']}/100 → {claim['expected_decision'].upper()}")
                if claim['expected_issues']:
                    print(f"    Issues: {', '.join(claim['expected_issues'])}")
            else:
                claim_form_path = None
                invoice_path = None
                bol_path = None
            
            # Store absolute paths
            claim["claim_form_path"] = str(Path(claim_form_path).resolve()) if claim_form_path else None
            claim["invoice_path"] = str(Path(invoice_path).resolve()) if invoice_path else None
            claim["bol_path"] = str(Path(bol_path).resolve()) if bol_path else None
            
            # Save policy to database
            policy_data = claim.get("policy_data", {})
            if policy_data and policy_data.get("policy_path"):
                cursor.execute("""
                    INSERT OR REPLACE INTO policies (
                        policy_number, policy_path, insured_party, coverage_start_date, coverage_end_date,
                        coverage_limit, deductible, coverage_percentage,
                        commercial_risk_coverage, political_risk_coverage,
                        covered_risks, exclusions, max_claims_per_term, max_claims_per_year
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    policy_data["policy_number"],
                    policy_data["policy_path"],
                    policy_data["insured_party"],
                    policy_data["coverage_start_date"],
                    policy_data["coverage_end_date"],
                    policy_data["coverage_limit"],
                    policy_data["deductible"],
                    policy_data["coverage_percentage"],
                    policy_data["commercial_risk_coverage"],
                    policy_data["political_risk_coverage"],
                    policy_data["covered_risks"],
                    policy_data["exclusions"],
                    policy_data.get("max_claims_per_term"),
                    policy_data.get("max_claims_per_year"),
                ))
                
                # Generate past claim history for this policy
                generate_past_claim_history(
                    cursor,
                    policy_data["policy_number"],
                    policy_data,
                    "approve"
                )
            
            # Insert into database
            cursor.execute("""
                INSERT INTO claims (
                    claim_id, claim_form_path, invoice_path, bol_path,
                    policy_number, policy_path, claim_reason_category, claim_reason_description,
                    claimant_name, claimant_email, buyer_name, seller_name,
                    invoice_number, invoice_amount, invoice_date,
                    currency_code, currency_symbol,
                    shipment_vessel, shipment_origin_port, shipment_destination_port, bol_date,
                    status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """, (
                claim["claim_id"],
                claim["claim_form_path"],
                claim["invoice_path"],
                claim["bol_path"],
                claim.get("policy_number"),
                claim.get("policy_path"),
                claim.get("claim_reason_category"),
                claim.get("claim_reason_description"),
                claim["claimant_name"],
                claim["claimant_email"],
                claim["buyer_name"],
                claim["seller_name"],
                claim["invoice_number"],
                claim["invoice_amount"],
                claim["invoice_date"],
                claim.get("currency_code"),
                claim.get("currency_symbol"),
                claim["shipment_vessel"],
                claim["shipment_origin_port"],
                claim["shipment_destination_port"],
                claim["bol_date"],
            ))
            
            claims_created.append(claim)
        except Exception as e:
            print(f"  ✗ Failed to generate claim {claim_counter}: {e}")
    
    # Generate request_docs claims
    for i in range(args.request_docs_count):
        claim_counter += 1
        try:
            claim = generate_claim_scenario(claim_counter, "request_docs", voyages, buyers, policy_output_path)
            
            if REPORTLAB_AVAILABLE:
                claim_form_path = generate_claim_form_pdf(claim, output_path)
                invoice_path = generate_invoice_pdf(claim, output_path)
                bol_path = generate_bill_of_lading_pdf(claim, output_path)
                
                print(f"  ✓ Claim {claim_counter}/{total_claims}: {claim['claim_id']} (request_docs - {claim['scenario_type']})")
                print(f"    Expected Risk Score: {claim['expected_risk_score']}/100 → {claim['expected_decision'].upper()}")
                if claim['expected_issues']:
                    print(f"    Issues: {', '.join(claim['expected_issues'])}")
            else:
                claim_form_path = None
                invoice_path = None
                bol_path = None
            
            # Store absolute paths
            claim["claim_form_path"] = str(Path(claim_form_path).resolve()) if claim_form_path else None
            claim["invoice_path"] = str(Path(invoice_path).resolve()) if invoice_path else None
            claim["bol_path"] = str(Path(bol_path).resolve()) if bol_path else None
            
            # Save policy to database
            policy_data = claim.get("policy_data", {})
            if policy_data and policy_data.get("policy_path"):
                cursor.execute("""
                    INSERT OR REPLACE INTO policies (
                        policy_number, policy_path, insured_party, coverage_start_date, coverage_end_date,
                        coverage_limit, deductible, coverage_percentage,
                        commercial_risk_coverage, political_risk_coverage,
                        covered_risks, exclusions, max_claims_per_term, max_claims_per_year
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    policy_data["policy_number"],
                    policy_data["policy_path"],
                    policy_data["insured_party"],
                    policy_data["coverage_start_date"],
                    policy_data["coverage_end_date"],
                    policy_data["coverage_limit"],
                    policy_data["deductible"],
                    policy_data["coverage_percentage"],
                    policy_data["commercial_risk_coverage"],
                    policy_data["political_risk_coverage"],
                    policy_data["covered_risks"],
                    policy_data["exclusions"],
                    policy_data.get("max_claims_per_term"),
                    policy_data.get("max_claims_per_year"),
                ))
                
                # Generate past claim history for this policy
                generate_past_claim_history(
                    cursor,
                    policy_data["policy_number"],
                    policy_data,
                    "escalate"
                )
            
            # Insert into database
            cursor.execute("""
                INSERT INTO claims (
                    claim_id, claim_form_path, invoice_path, bol_path,
                    policy_number, policy_path, claim_reason_category, claim_reason_description,
                    claimant_name, claimant_email, buyer_name, seller_name,
                    invoice_number, invoice_amount, invoice_date,
                    currency_code, currency_symbol,
                    shipment_vessel, shipment_origin_port, shipment_destination_port, bol_date,
                    status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """, (
                claim["claim_id"],
                claim["claim_form_path"],
                claim["invoice_path"],
                claim["bol_path"],
                claim.get("policy_number"),
                claim.get("policy_path"),
                claim.get("claim_reason_category"),
                claim.get("claim_reason_description"),
                claim["claimant_name"],
                claim["claimant_email"],
                claim["buyer_name"],
                claim["seller_name"],
                claim["invoice_number"],
                claim["invoice_amount"],
                claim["invoice_date"],
                claim.get("currency_code"),
                claim.get("currency_symbol"),
                claim["shipment_vessel"],
                claim["shipment_origin_port"],
                claim["shipment_destination_port"],
                claim["bol_date"],
            ))
            
            claims_created.append(claim)
        except Exception as e:
            print(f"  ✗ Failed to generate claim {claim_counter}: {e}")
    
    # Generate escalate claims
    for i in range(args.escalate_count):
        claim_counter += 1
        try:
            claim = generate_claim_scenario(claim_counter, "escalate", voyages, buyers, policy_output_path)
            
            if REPORTLAB_AVAILABLE:
                claim_form_path = generate_claim_form_pdf(claim, output_path)
                invoice_path = generate_invoice_pdf(claim, output_path)
                bol_path = generate_bill_of_lading_pdf(claim, output_path)
                
                print(f"  ✓ Claim {claim_counter}/{total_claims}: {claim['claim_id']} (escalate - {claim['scenario_type']})")
                print(f"    Expected Risk Score: {claim['expected_risk_score']}/100 → {claim['expected_decision'].upper()}")
                if claim['expected_issues']:
                    print(f"    Issues: {', '.join(claim['expected_issues'])}")
            else:
                claim_form_path = None
                invoice_path = None
                bol_path = None
            
            # Store absolute paths
            claim["claim_form_path"] = str(Path(claim_form_path).resolve()) if claim_form_path else None
            claim["invoice_path"] = str(Path(invoice_path).resolve()) if invoice_path else None
            claim["bol_path"] = str(Path(bol_path).resolve()) if bol_path else None
            
            # Save policy to database
            policy_data = claim.get("policy_data", {})
            if policy_data and policy_data.get("policy_path"):
                cursor.execute("""
                    INSERT OR REPLACE INTO policies (
                        policy_number, policy_path, insured_party, coverage_start_date, coverage_end_date,
                        coverage_limit, deductible, coverage_percentage,
                        commercial_risk_coverage, political_risk_coverage,
                        covered_risks, exclusions, max_claims_per_term, max_claims_per_year
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    policy_data["policy_number"],
                    policy_data["policy_path"],
                    policy_data["insured_party"],
                    policy_data["coverage_start_date"],
                    policy_data["coverage_end_date"],
                    policy_data["coverage_limit"],
                    policy_data["deductible"],
                    policy_data["coverage_percentage"],
                    policy_data["commercial_risk_coverage"],
                    policy_data["political_risk_coverage"],
                    policy_data["covered_risks"],
                    policy_data["exclusions"],
                    policy_data.get("max_claims_per_term"),
                    policy_data.get("max_claims_per_year"),
                ))
                
                # Generate past claim history for this policy
                generate_past_claim_history(
                    cursor,
                    policy_data["policy_number"],
                    policy_data,
                    "escalate"
                )
            
            # Insert into database
            cursor.execute("""
                INSERT INTO claims (
                    claim_id, claim_form_path, invoice_path, bol_path,
                    policy_number, policy_path, claim_reason_category, claim_reason_description,
                    claimant_name, claimant_email, buyer_name, seller_name,
                    invoice_number, invoice_amount, invoice_date,
                    currency_code, currency_symbol,
                    shipment_vessel, shipment_origin_port, shipment_destination_port, bol_date,
                    status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """, (
                claim["claim_id"],
                claim["claim_form_path"],
                claim["invoice_path"],
                claim["bol_path"],
                claim.get("policy_number"),
                claim.get("policy_path"),
                claim.get("claim_reason_category"),
                claim.get("claim_reason_description"),
                claim["claimant_name"],
                claim["claimant_email"],
                claim["buyer_name"],
                claim["seller_name"],
                claim["invoice_number"],
                claim["invoice_amount"],
                claim["invoice_date"],
                claim.get("currency_code"),
                claim.get("currency_symbol"),
                claim["shipment_vessel"],
                claim["shipment_origin_port"],
                claim["shipment_destination_port"],
                claim["bol_date"],
            ))
            
            claims_created.append(claim)
        except Exception as e:
            print(f"  ✗ Failed to generate claim {claim_counter}: {e}")
    
    conn.commit()
    conn.close()
    
    # Summary
    print("\n" + "=" * 70)
    print("Setup Complete!")
    print("=" * 70)
    print(f"\nDatabase: {db_path}")
    print(f"Output directory: {output_path}")
    
    # Count records
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM voyages")
    voyage_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM buyer_registry")
    buyer_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM claims")
    claim_count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"\nDatabase Records:")
    print(f"  Voyages: {voyage_count}")
    print(f"  Buyers: {buyer_count}")
    print(f"  Claims: {claim_count}")
    
    if REPORTLAB_AVAILABLE:
        print(f"\nGenerated Files:")
        print(f"  PDF documents: {output_path}")
        for claim in claims_created:
            print(f"    - claim_form_{claim['claim_id']}.pdf")
            print(f"    - invoice_{claim['claim_id']}.pdf")
            print(f"    - bol_{claim['claim_id']}.pdf")
    
    # Validation mix summary
    valid_count = len([c for c in claims_created if c['scenario_type'] == 'valid'])
    invalid_count = len(claims_created) - valid_count
    print(f"\nValidation Mix:")
    print(f"  Valid claims: {valid_count} ({valid_count/len(claims_created)*100:.0f}%)")
    print(f"  Claims with issues: {invalid_count} ({invalid_count/len(claims_created)*100:.0f}%)")
    
    print("\n✓ Setup complete! You can now run the ECI Claims Vetter pipeline.")


if __name__ == "__main__":
    main()

