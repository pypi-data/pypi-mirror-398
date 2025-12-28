#!/usr/bin/env python3
"""Setup script for Rate Case Filing pipeline.

Creates SQLite database, initializes schema, and generates mock data:
- Customer master data (5,000-10,000 customers)
- Interval usage data (hourly, 3-5 years)
- Demographics and equity attributes
- EV and DER indicators
- Customer segments (5-10 segments per state, pre-computed for rate design)
- Existing rate structures
- Voice of customer text (LLM-generated)

Usage:
    python scripts/setup_rate_case_database.py [options]
    
    # Full reset (input + output tables)
    uv run -m scripts.setup_rate_case_database --reset
    
    # Reset only output tables + existing_rates (keeps input data + voice_of_customer; re-populates existing_rates)
    uv run -m scripts.setup_rate_case_database --reset-outputs
    
    # Regenerate voice_of_customer with custom distribution (keeps all other data)
    uv run -m scripts.setup_rate_case_database --regenerate-voice \
        --voice-snippet-pct 15.0 \
        --voice-text-type-dist "complaint:0.50,survey:0.30,testimony:0.20" \
        --voice-sentiment-dist "positive:0.20,neutral:0.30,negative:0.50"
    
    # Regenerate existing_rates with high scenario (keeps all other data)
    uv run -m scripts.setup_rate_case_database --regenerate-rates --rate-scenario high
    
    # Regenerate existing_rates with low scenario (competitive market)
    uv run -m scripts.setup_rate_case_database --regenerate-rates --rate-scenario low
    
    # Regenerate customer segments (keeps all other data)
    uv run -m scripts.setup_rate_case_database --reset-segmentation
    
    # Generate with more negative sentiment (crisis scenario)
    uv run -m scripts.setup_rate_case_database --regenerate-voice \
        --voice-sentiment-dist "positive:0.10,neutral:0.20,negative:0.70" \
        --voice-topic-dist "rate_fairness:0.40,billing:0.30,outages:0.30"
"""

import sqlite3
import os
import sys
import argparse
import random
import json
import time
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    # Note: numpy is optional, we use standard random instead

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from topaz_agent_kit.utils.path_resolver import resolve_script_path, detect_project_name
from topaz_agent_kit.utils.logger import Logger

logger = Logger("RateCaseMockData")

# Try to import ModelFactory for LLM text generation
try:
    from topaz_agent_kit.models.model_factory import ModelFactory
    MODEL_FACTORY_AVAILABLE = True
except ImportError:
    MODEL_FACTORY_AVAILABLE = False
    logger.warning("ModelFactory not available. LLM text generation will be skipped.")
    logger.info("Use --no-llm flag to skip LLM generation.")


def create_database_schema(db_path: str) -> None:
    """Create all database tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Customer Master table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_master (
            customer_id TEXT PRIMARY KEY,
            rate_class TEXT NOT NULL,
            current_rate_type TEXT NOT NULL DEFAULT 'flat',
            income_qualified_flag BOOLEAN DEFAULT 0,
            zip_code TEXT NOT NULL,
            state TEXT NOT NULL,
            city TEXT NOT NULL,
            household_size INTEGER,
            dwelling_type TEXT,
            baseline_annual_kwh REAL NOT NULL,
            service_start_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Add current_rate_type column to existing tables (migration)
    try:
        cursor.execute("ALTER TABLE customer_master ADD COLUMN current_rate_type TEXT DEFAULT 'flat'")
    except sqlite3.OperationalError:
        # Column already exists, ignore
        pass
    
    # Interval Usage table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interval_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            kwh REAL NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customer_master(customer_id) ON DELETE CASCADE
        )
    """)
    
    # Demographics and Equity table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS demographics_equity (
            customer_id TEXT PRIMARY KEY,
            income_band TEXT NOT NULL,
            senior_flag BOOLEAN DEFAULT 0,
            medical_baseline_flag BOOLEAN DEFAULT 0,
            housing_burden_index REAL NOT NULL,
            disability_flag BOOLEAN DEFAULT 0,
            language_preference TEXT,
            FOREIGN KEY (customer_id) REFERENCES customer_master(customer_id) ON DELETE CASCADE
        )
    """)
    
    # EV and DER Indicators table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ev_der_indicators (
            customer_id TEXT PRIMARY KEY,
            ev_owner_flag BOOLEAN DEFAULT 0,
            ev_charger_type TEXT,
            estimated_ev_kwh_per_month REAL,
            ev_adoption_date TEXT,
            solar_flag BOOLEAN DEFAULT 0,
            solar_capacity_kw REAL,
            solar_installation_date TEXT,
            battery_flag BOOLEAN DEFAULT 0,
            battery_capacity_kwh REAL,
            net_metering_flag BOOLEAN DEFAULT 0,
            FOREIGN KEY (customer_id) REFERENCES customer_master(customer_id) ON DELETE CASCADE
        )
    """)
    
    # Existing Rates table (state-specific for rate case filing)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS existing_rates (
            rate_name TEXT NOT NULL,
            state TEXT NOT NULL,
            rate_class TEXT NOT NULL,
            rate_type TEXT NOT NULL,
            fixed_charge REAL NOT NULL,
            energy_charge REAL,
            tier_1_price REAL,
            tier_1_limit_kwh INTEGER,
            tier_2_price REAL,
            tier_2_limit_kwh INTEGER,
            tier_3_price REAL,
            tou_peak_price REAL,
            tou_offpeak_price REAL,
            tou_peak_hours TEXT,
            demand_charge_per_kw REAL,
            effective_date TEXT,
            description TEXT,
            PRIMARY KEY (rate_name, state)
        )
    """)
    
    # Voice of Customer table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voice_of_customer (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT,
            text_type TEXT NOT NULL,
            content TEXT NOT NULL,
            survey_type TEXT,
            question TEXT,
            answer TEXT,
            snippet TEXT,
            topic TEXT,
            sentiment TEXT,
            timestamp TEXT,
            source TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customer_master(customer_id) ON DELETE SET NULL
        )
    """)
    
    # Customer Segments table - pre-computed segments for rate design analysis
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_segments (
            segment_id TEXT PRIMARY KEY,
            segment_name TEXT NOT NULL,
            state TEXT NOT NULL,
            rate_class TEXT NOT NULL,
            rate_type TEXT,
            price_elasticity REAL NOT NULL,
            avg_annual_kwh REAL,
            characteristics_json TEXT,
            demographics_summary_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Customer Segment Membership table - maps customers to segments (many-to-many)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_segment_membership (
            customer_id TEXT NOT NULL,
            segment_id TEXT NOT NULL,
            PRIMARY KEY (customer_id, segment_id),
            FOREIGN KEY (customer_id) REFERENCES customer_master(customer_id) ON DELETE CASCADE,
            FOREIGN KEY (segment_id) REFERENCES customer_segments(segment_id) ON DELETE CASCADE
        )
    """)
    
    # =============================================================================
    # PIPELINE OUTPUT TABLES (for storing agent results)
    # =============================================================================
    # Note: rate_design_options are no longer stored in database.
    # Data flows through context variables only.
    # customer_segments are now pre-computed in the database for better segmentation.
    
    # Pipeline Runs table - tracks each pipeline execution and final artifacts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            run_id TEXT PRIMARY KEY,
            target_state TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            error_message TEXT,
            summary TEXT NOT NULL,
            file_path TEXT,
            recommended_option_id TEXT,
            recommended_option_name TEXT,
            final_option_id TEXT,
            final_option_name TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("✓ Database schema created (including pipeline output tables)")


def _create_output_tables_only(cursor) -> None:
    """Create only pipeline output tables (for --reset-outputs).
    
    Note: customer_segments and rate_design_options are created by agents during pipeline execution,
    so they should NOT be recreated here. They will be created by rate_designer agent.
    """
    # Pipeline Runs table - tracks each pipeline execution and final artifacts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            run_id TEXT PRIMARY KEY,
            target_state TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            error_message TEXT,
            summary TEXT NOT NULL,
            file_path TEXT,
            recommended_option_id TEXT,
            recommended_option_name TEXT,
            final_option_id TEXT,
            final_option_name TEXT
        )
    """)
    
    logger.info("✓ Pipeline output tables created")


def generate_customer_master(cursor, customer_count: int) -> List[Dict[str, Any]]:
    """Generate customer master data."""
    logger.info("Generating {} customers...", customer_count)
    
    # Geographic distribution
    states_cities = {
        "California": {
            "San Francisco": ["94102", "94103", "94104", "94105", "94107", "94108", "94109", "94110", "94111", "94112"],
            "Los Angeles": ["90001", "90002", "90003", "90004", "90005", "90006", "90007", "90008", "90009", "90010"]
        },
        "Texas": {
            "Houston": ["77001", "77002", "77003", "77004", "77005", "77006", "77007", "77008", "77009", "77010"],
            "Austin": ["78701", "78702", "78703", "78704", "78705", "78721", "78722", "78723", "78724", "78725"]
        },
        "Arizona": {
            "Phoenix": ["85001", "85002", "85003", "85004", "85005", "85006", "85007", "85008", "85009", "85010"],
            "Tucson": ["85701", "85702", "85703", "85704", "85705", "85706", "85707", "85708", "85709", "85710"]
        }
    }
    
    # Rate class distribution
    rate_classes = {
        "residential": 0.85,
        "commercial": 0.12,
        "industrial": 0.03
    }
    
    # Dwelling types (residential only)
    dwelling_types = {
        "single_family": 0.60,
        "apartment": 0.25,
        "condo": 0.10,
        "townhouse": 0.04,
        "mobile_home": 0.01
    }
    
    customers = []
    customer_id_counter = 1
    
    # Generate customers
    for i in range(customer_count):
        # Determine rate class
        rand = random.random()
        if rand < rate_classes["residential"]:
            rate_class = "residential"
        elif rand < rate_classes["residential"] + rate_classes["commercial"]:
            rate_class = "commercial"
        else:
            rate_class = "industrial"
        
        # Select state and city
        state = random.choice(list(states_cities.keys()))
        city = random.choice(list(states_cities[state].keys()))
        zip_code = random.choice(states_cities[state][city])
        
        # Generate customer ID
        customer_id = f"CUST-{customer_id_counter:06d}"
        customer_id_counter += 1
        
        # Household size (residential only)
        household_size = None
        dwelling_type = None
        if rate_class == "residential":
            household_size = random.choices(
                [1, 2, 3, 4, 5],
                weights=[0.25, 0.35, 0.25, 0.10, 0.05]
            )[0]
            
            # Dwelling type
            rand_dwelling = random.random()
            cumulative = 0
            for dtype, weight in dwelling_types.items():
                cumulative += weight
                if rand_dwelling <= cumulative:
                    dwelling_type = dtype
                    break
        
        # Baseline annual kWh
        if rate_class == "residential":
            baseline_annual_kwh = round(random.gauss(11000, 2000), 2)
            baseline_annual_kwh = max(8000, min(15000, baseline_annual_kwh))
        elif rate_class == "commercial":
            baseline_annual_kwh = round(random.gauss(100000, 30000), 2)
            baseline_annual_kwh = max(50000, min(200000, baseline_annual_kwh))
        else:  # industrial
            baseline_annual_kwh = round(random.gauss(1000000, 300000), 2)
            baseline_annual_kwh = max(500000, min(2000000, baseline_annual_kwh))
        
        # Service start date (past 3-10 years)
        years_ago = random.randint(3, 10)
        service_start_date = (datetime.now() - timedelta(days=years_ago * 365)).strftime("%Y-%m-%d")
        
        # Income qualified flag (will be correlated in demographics)
        income_qualified_flag = random.random() < 0.15  # 15% base rate, will adjust in demographics
        
        # Assign current rate type based on rate class
        # Residential: 50% flat, 30% tiered, 20% TOU
        # Commercial: 100% TOU (typical for commercial)
        # Industrial: 100% demand (typical for industrial)
        if rate_class == "residential":
            rate_type_rand = random.random()
            if rate_type_rand < 0.50:
                current_rate_type = "flat"
            elif rate_type_rand < 0.80:
                current_rate_type = "tiered"
            else:
                current_rate_type = "tou"
        elif rate_class == "commercial":
            current_rate_type = "tou"
        else:  # industrial
            current_rate_type = "demand"
        
        customer = {
            "customer_id": customer_id,
            "rate_class": rate_class,
            "current_rate_type": current_rate_type,
            "income_qualified_flag": income_qualified_flag,
            "zip_code": zip_code,
            "state": state,
            "city": city,
            "household_size": household_size,
            "dwelling_type": dwelling_type,
            "baseline_annual_kwh": baseline_annual_kwh,
            "service_start_date": service_start_date
        }
        customers.append(customer)
    
    # Insert into database
    cursor.executemany("""
        INSERT INTO customer_master 
        (customer_id, rate_class, current_rate_type, income_qualified_flag, zip_code, state, city, 
         household_size, dwelling_type, baseline_annual_kwh, service_start_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        (c["customer_id"], c["rate_class"], c["current_rate_type"], c["income_qualified_flag"], c["zip_code"],
         c["state"], c["city"], c["household_size"], c["dwelling_type"],
         c["baseline_annual_kwh"], c["service_start_date"])
        for c in customers
    ])
    
    logger.success("✓ Generated {} customers", len(customers))
    return customers


def generate_demographics_equity(cursor, customers: List[Dict[str, Any]]) -> None:
    """Generate demographics and equity data, correlated with customers."""
    logger.info("Generating demographics and equity data...")
    
    demographics = []
    
    for customer in customers:
        customer_id = customer["customer_id"]
        rate_class = customer["rate_class"]
        
        # Income band distribution (correlated with income_qualified_flag)
        if customer["income_qualified_flag"]:
            # If income qualified, 80% low, 20% medium
            income_band = random.choices(["low", "medium"], weights=[0.80, 0.20])[0]
        else:
            # If not income qualified, weighted distribution
            income_band = random.choices(
                ["low", "medium", "high"],
                weights=[0.20, 0.50, 0.30]
            )[0]
        
        # Housing burden index (correlated with income)
        if income_band == "low":
            housing_burden_index = round(random.uniform(0.4, 0.8), 3)
        elif income_band == "medium":
            housing_burden_index = round(random.uniform(0.2, 0.5), 3)
        else:  # high
            housing_burden_index = round(random.uniform(0.1, 0.3), 3)
        
        # Senior flag (15% of residential)
        senior_flag = False
        if rate_class == "residential":
            senior_flag = random.random() < 0.15
        
        # Medical baseline (correlated with seniors and low-income)
        medical_baseline_flag = False
        if rate_class == "residential":
            if senior_flag or income_band == "low":
                medical_baseline_flag = random.random() < 0.10
        
        # Disability flag (8% of residential)
        disability_flag = False
        if rate_class == "residential":
            disability_flag = random.random() < 0.08
        
        # Language preference
        language_preference = random.choices(
            ["english", "spanish", "other"],
            weights=[0.75, 0.20, 0.05]
        )[0]
        
        demographics.append((
            customer_id, income_band, senior_flag, medical_baseline_flag,
            housing_burden_index, disability_flag, language_preference
        ))
    
    cursor.executemany("""
        INSERT INTO demographics_equity
        (customer_id, income_band, senior_flag, medical_baseline_flag,
         housing_burden_index, disability_flag, language_preference)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, demographics)
    
    logger.success("✓ Generated demographics for {} customers", len(demographics))


def generate_ev_der_indicators(cursor, customers: List[Dict[str, Any]]) -> None:
    """Generate EV and DER indicators, correlated with income and geography."""
    logger.info("Generating EV and DER indicators...")
    
    ev_der_data = []
    
    for customer in customers:
        customer_id = customer["customer_id"]
        rate_class = customer["rate_class"]
        dwelling_type = customer.get("dwelling_type")
        
        # Only residential customers can have EV/solar/battery
        if rate_class != "residential":
            ev_der_data.append((
                customer_id, False, None, None, None,
                False, None, None, False, None, False
            ))
            continue
        
        # Get income band from demographics (we'll need to query or pass it)
        # For now, use income_qualified_flag as proxy
        is_high_income = not customer["income_qualified_flag"] and random.random() < 0.5
        is_suburban = dwelling_type == "single_family"
        
        # EV ownership (12% of residential, correlated with high income, suburban)
        ev_owner_flag = False
        ev_charger_type = None
        estimated_ev_kwh_per_month = None
        ev_adoption_date = None
        
        if is_high_income and is_suburban:
            ev_owner_flag = random.random() < 0.20  # 20% of high-income suburban
        elif is_high_income:
            ev_owner_flag = random.random() < 0.10  # 10% of high-income urban
        elif is_suburban:
            ev_owner_flag = random.random() < 0.08  # 8% of medium-income suburban
        else:
            ev_owner_flag = random.random() < 0.05  # 5% of others
        
        if ev_owner_flag:
            # Charger type
            if is_suburban:
                ev_charger_type = random.choices(
                    ["level_2", "level_1"],
                    weights=[0.80, 0.20]
                )[0]
            else:  # apartment/condo
                ev_charger_type = random.choices(
                    ["level_1", "level_2", "dc_fast"],
                    weights=[0.60, 0.35, 0.05]
                )[0]
            
            estimated_ev_kwh_per_month = round(random.gauss(450, 75), 2)
            estimated_ev_kwh_per_month = max(300, min(600, estimated_ev_kwh_per_month))
            
            # Adoption date (past 2-5 years)
            years_ago = random.randint(2, 5)
            ev_adoption_date = (datetime.now() - timedelta(days=years_ago * 365)).strftime("%Y-%m-%d")
        
        # Solar ownership (10% of residential, correlated with high income, suburban)
        solar_flag = False
        solar_capacity_kw = None
        solar_installation_date = None
        net_metering_flag = False
        
        if is_high_income and is_suburban:
            solar_flag = random.random() < 0.15  # 15% of high-income suburban
        elif is_high_income:
            solar_flag = random.random() < 0.05  # 5% of high-income urban
        elif is_suburban:
            solar_flag = random.random() < 0.08  # 8% of medium-income suburban
        else:
            solar_flag = random.random() < 0.02  # 2% of others
        
        if solar_flag:
            solar_capacity_kw = round(random.gauss(6.0, 1.5), 2)
            solar_capacity_kw = max(3.0, min(10.0, solar_capacity_kw))
            
            # Installation date (past 3-8 years)
            years_ago = random.randint(3, 8)
            solar_installation_date = (datetime.now() - timedelta(days=years_ago * 365)).strftime("%Y-%m-%d")
            
            net_metering_flag = random.random() < 0.95  # 95% have net metering
        
        # Battery ownership (2% of residential, mostly with solar)
        battery_flag = False
        battery_capacity_kwh = None
        
        if solar_flag and is_high_income and is_suburban:
            battery_flag = random.random() < 0.15  # 15% of solar+high-income+suburban
        elif solar_flag:
            battery_flag = random.random() < 0.05  # 5% of other solar owners
        
        if battery_flag:
            battery_capacity_kwh = round(random.gauss(10.0, 3.0), 2)
            battery_capacity_kwh = max(5.0, min(20.0, battery_capacity_kwh))
        
        ev_der_data.append((
            customer_id, ev_owner_flag, ev_charger_type, estimated_ev_kwh_per_month, ev_adoption_date,
            solar_flag, solar_capacity_kw, solar_installation_date,
            battery_flag, battery_capacity_kwh, net_metering_flag
        ))
    
    cursor.executemany("""
        INSERT INTO ev_der_indicators
        (customer_id, ev_owner_flag, ev_charger_type, estimated_ev_kwh_per_month, ev_adoption_date,
         solar_flag, solar_capacity_kw, solar_installation_date,
         battery_flag, battery_capacity_kwh, net_metering_flag)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ev_der_data)
    
    logger.success("✓ Generated EV/DER indicators for {} customers", len(ev_der_data))


def _safe_float(value: Any) -> float:
    """Safely convert value to float."""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def generate_customer_segments(cursor) -> None:
    """Generate sophisticated customer segments based on multiple dimensions (usage, demographics, DER, etc.).
    
    Creates 5-10 segments per state/rate_class combination:
    - High-load residential (above 75th percentile)
    - Medium-load residential (25th-75th percentile)
    - Low-load residential (below 25th percentile)
    - Income-qualified residential
    - Senior residential
    - EV owners
    - Solar owners
    - High housing burden
    - DER adopters (solar + battery)
    - Peak users (high load + high peak potential)
    """
    logger.info("Generating customer segments...")
    
    # Get all customers with their attributes (including current_rate_type)
    cursor.execute("""
        SELECT cm.customer_id,
               cm.rate_class,
               cm.current_rate_type,
               cm.income_qualified_flag,
               cm.baseline_annual_kwh,
               cm.state,
               de.senior_flag,
               de.housing_burden_index,
               edi.ev_owner_flag,
               edi.solar_flag,
               edi.battery_flag
        FROM customer_master cm
        LEFT JOIN demographics_equity de ON de.customer_id = cm.customer_id
        LEFT JOIN ev_der_indicators edi ON edi.customer_id = cm.customer_id
        ORDER BY cm.state, cm.rate_class, cm.baseline_annual_kwh
    """)
    customer_rows = cursor.fetchall()
    all_customers = [
        {
            "customer_id": row[0],
            "rate_class": row[1],
            "current_rate_type": row[2] or "flat",  # Default to flat if NULL
            "income_qualified_flag": row[3],
            "baseline_annual_kwh": row[4],
            "state": row[5],
            "senior_flag": row[6],
            "housing_burden_index": row[7],
            "ev_owner_flag": row[8],
            "solar_flag": row[9],
            "battery_flag": row[10]
        }
        for row in customer_rows
    ]
    
    if not all_customers:
        logger.warning("No customers found for segmentation")
        return
    
    # Group by state and rate_class
    by_state_class = {}
    for customer in all_customers:
        key = (customer["state"], customer["rate_class"])
        if key not in by_state_class:
            by_state_class[key] = []
        by_state_class[key].append(customer)
    
    segments_to_insert = []
    memberships_to_insert = []
    
    for (state, rate_class), customers in by_state_class.items():
        # Create segments for all rate classes (residential, commercial, industrial)
        # Previously only residential segments were created, now we support all classes
        
        state_abbr = state[:2].upper() if len(state) >= 2 else state.upper()
        rate_class_abbr = rate_class[:3].upper() if len(rate_class) >= 3 else rate_class.upper()
        
        # Calculate percentiles for usage-based segmentation
        baseline_vals = sorted([_safe_float(c["baseline_annual_kwh"]) for c in customers])
        if not baseline_vals:
            continue
        
        p25_idx = len(baseline_vals) // 4
        p75_idx = (len(baseline_vals) * 3) // 4
        p25 = baseline_vals[p25_idx] if p25_idx < len(baseline_vals) else baseline_vals[0]
        p75 = baseline_vals[p75_idx] if p75_idx < len(baseline_vals) else baseline_vals[-1]
        median = baseline_vals[len(baseline_vals) // 2]
        
        # Segment definitions
        segment_defs = []
        
        # For residential: create detailed segments
        # For commercial/industrial: create simpler segments based on usage and rate type
        if rate_class.lower() == "residential":
            # 1. High-load residential (above 75th percentile)
            high_load = [c for c in customers if _safe_float(c["baseline_annual_kwh"]) >= p75]
            if high_load:
                segment_defs.append({
                    "id": f"SEG-RES-HIGHLOAD-{state_abbr}",
                    "name": f"Residential High Load {state}",
                    "customers": high_load,
                    "elasticity": -0.19
                })
            
            # 2. Medium-load residential (25th-75th percentile)
            medium_load = [c for c in customers if p25 <= _safe_float(c["baseline_annual_kwh"]) < p75]
            if medium_load:
                segment_defs.append({
                    "id": f"SEG-RES-MEDLOAD-{state_abbr}",
                    "name": f"Residential Medium Load {state}",
                    "customers": medium_load,
                    "elasticity": -0.16
                })
            
            # 3. Low-load residential (below 25th percentile)
            low_load = [c for c in customers if _safe_float(c["baseline_annual_kwh"]) < p25]
            if low_load:
                segment_defs.append({
                    "id": f"SEG-RES-LOWLOAD-{state_abbr}",
                    "name": f"Residential Low Load {state}",
                    "customers": low_load,
                    "elasticity": -0.15
                })
            
            # 4. Income-qualified residential
            income_qualified = [c for c in customers if int(c.get("income_qualified_flag") or 0) == 1]
            if income_qualified:
                segment_defs.append({
                    "id": f"SEG-RES-INCOMEQ-{state_abbr}",
                    "name": f"Income-Qualified Residential {state}",
                    "customers": income_qualified,
                    "elasticity": -0.12
                })
            
            # 5. Senior residential
            seniors = [c for c in customers if int(c.get("senior_flag") or 0) == 1]
            if seniors:
                segment_defs.append({
                    "id": f"SEG-RES-SENIOR-{state_abbr}",
                    "name": f"Senior Residential {state}",
                    "customers": seniors,
                    "elasticity": -0.10
                })
            
            # 6. EV owners
            ev_owners = [c for c in customers if int(c.get("ev_owner_flag") or 0) == 1]
            if ev_owners:
                segment_defs.append({
                    "id": f"SEG-RES-EV-{state_abbr}",
                    "name": f"EV Owner Residential {state}",
                    "customers": ev_owners,
                    "elasticity": -0.22
                })
            
            # 7. Solar owners
            solar_owners = [c for c in customers if int(c.get("solar_flag") or 0) == 1]
            if solar_owners:
                segment_defs.append({
                    "id": f"SEG-RES-SOLAR-{state_abbr}",
                    "name": f"Solar Owner Residential {state}",
                    "customers": solar_owners,
                    "elasticity": -0.18
                })
            
            # 8. High housing burden (>= 0.30)
            high_burden = [c for c in customers if _safe_float(c.get("housing_burden_index") or 0) >= 0.30]
            if high_burden:
                segment_defs.append({
                    "id": f"SEG-RES-HIGHBURDEN-{state_abbr}",
                    "name": f"High Housing Burden Residential {state}",
                    "customers": high_burden,
                    "elasticity": -0.11
                })
            
            # 9. DER adopters (solar + battery)
            der_adopters = [c for c in customers if int(c.get("solar_flag") or 0) == 1 and int(c.get("battery_flag") or 0) == 1]
            if der_adopters:
                segment_defs.append({
                    "id": f"SEG-RES-DER-{state_abbr}",
                    "name": f"DER Adopter Residential {state}",
                    "customers": der_adopters,
                    "elasticity": -0.20
                })
            
            # 10. Peak users (high load + high peak potential) - use high load as proxy
            # This overlaps with high-load but provides a different perspective
            peak_users = [c for c in high_load if _safe_float(c["baseline_annual_kwh"]) >= p75 * 1.1]
            if peak_users and len(peak_users) >= 10:  # Only create if meaningful size
                segment_defs.append({
                    "id": f"SEG-RES-PEAK-{state_abbr}",
                    "name": f"Peak User Residential {state}",
                    "customers": peak_users,
                    "elasticity": -0.25
                })
            
            # 11-13. Rate type-based segments (important for rate type filtering)
            # These segments help rate designers understand which customers are on which rate types
            flat_rate_customers = [c for c in customers if (c.get("current_rate_type") or "flat").lower() == "flat"]
            if flat_rate_customers:
                segment_defs.append({
                    "id": f"SEG-RES-FLAT-{state_abbr}",
                    "name": f"Flat Rate Residential {state}",
                    "customers": flat_rate_customers,
                    "elasticity": -0.16  # Average elasticity for flat rate customers
                })
            
            tiered_rate_customers = [c for c in customers if (c.get("current_rate_type") or "flat").lower() == "tiered"]
            if tiered_rate_customers:
                segment_defs.append({
                    "id": f"SEG-RES-TIERED-{state_abbr}",
                    "name": f"Tiered Rate Residential {state}",
                    "customers": tiered_rate_customers,
                    "elasticity": -0.17  # Slightly more elastic due to tier awareness
                })
            
            tou_rate_customers = [c for c in customers if (c.get("current_rate_type") or "flat").lower() in ("tou", "time_of_use")]
            if tou_rate_customers:
                segment_defs.append({
                    "id": f"SEG-RES-TOU-{state_abbr}",
                    "name": f"TOU Rate Residential {state}",
                    "customers": tou_rate_customers,
                    "elasticity": -0.20  # More elastic due to ability to shift usage
                })
        else:
            # For commercial/industrial: create simpler segments based on usage and rate type
            # High-load commercial/industrial
            high_load = [c for c in customers if _safe_float(c["baseline_annual_kwh"]) >= p75]
            if high_load:
                segment_defs.append({
                    "id": f"SEG-{rate_class_abbr}-HIGHLOAD-{state_abbr}",
                    "name": f"{rate_class.title()} High Load {state}",
                    "customers": high_load,
                    "elasticity": -0.20 if rate_class.lower() == "commercial" else -0.15
                })
            
            # Medium-load commercial/industrial
            medium_load = [c for c in customers if p25 <= _safe_float(c["baseline_annual_kwh"]) < p75]
            if medium_load:
                segment_defs.append({
                    "id": f"SEG-{rate_class_abbr}-MEDLOAD-{state_abbr}",
                    "name": f"{rate_class.title()} Medium Load {state}",
                    "customers": medium_load,
                    "elasticity": -0.18 if rate_class.lower() == "commercial" else -0.14
                })
            
            # Low-load commercial/industrial
            low_load = [c for c in customers if _safe_float(c["baseline_annual_kwh"]) < p25]
            if low_load:
                segment_defs.append({
                    "id": f"SEG-{rate_class_abbr}-LOWLOAD-{state_abbr}",
                    "name": f"{rate_class.title()} Low Load {state}",
                    "customers": low_load,
                    "elasticity": -0.16 if rate_class.lower() == "commercial" else -0.13
                })
            
            # Rate type-based segments for commercial/industrial
            flat_rate_customers = [c for c in customers if (c.get("current_rate_type") or "flat").lower() == "flat"]
            if flat_rate_customers:
                segment_defs.append({
                    "id": f"SEG-{rate_class_abbr}-FLAT-{state_abbr}",
                    "name": f"Flat Rate {rate_class.title()} {state}",
                    "customers": flat_rate_customers,
                    "elasticity": -0.17
                })
            
            tiered_rate_customers = [c for c in customers if (c.get("current_rate_type") or "flat").lower() == "tiered"]
            if tiered_rate_customers:
                segment_defs.append({
                    "id": f"SEG-{rate_class_abbr}-TIERED-{state_abbr}",
                    "name": f"Tiered Rate {rate_class.title()} {state}",
                    "customers": tiered_rate_customers,
                    "elasticity": -0.18
                })
            
            tou_rate_customers = [c for c in customers if (c.get("current_rate_type") or "flat").lower() in ("tou", "time_of_use")]
            if tou_rate_customers:
                segment_defs.append({
                    "id": f"SEG-{rate_class_abbr}-TOU-{state_abbr}",
                    "name": f"TOU Rate {rate_class.title()} {state}",
                    "customers": tou_rate_customers,
                    "elasticity": -0.21
                })
            
            demand_rate_customers = [c for c in customers if (c.get("current_rate_type") or "flat").lower() == "demand"]
            if demand_rate_customers:
                segment_defs.append({
                    "id": f"SEG-{rate_class_abbr}-DEMAND-{state_abbr}",
                    "name": f"Demand Rate {rate_class.title()} {state}",
                    "customers": demand_rate_customers,
                    "elasticity": -0.19
                })
        
        # Create segments and memberships
        for seg_def in segment_defs:
            seg_customers = seg_def["customers"]
            if not seg_customers:
                continue
            
            customer_count = len(seg_customers)
            income_q = sum(1 for c in seg_customers if int(c.get("income_qualified_flag") or 0) == 1)
            seniors = sum(1 for c in seg_customers if int(c.get("senior_flag") or 0) == 1)
            ev = sum(1 for c in seg_customers if int(c.get("ev_owner_flag") or 0) == 1)
            solar = sum(1 for c in seg_customers if int(c.get("solar_flag") or 0) == 1)
            batt = sum(1 for c in seg_customers if int(c.get("battery_flag") or 0) == 1)
            avg_annual_kwh = sum(_safe_float(c["baseline_annual_kwh"]) for c in seg_customers) / max(1, customer_count)
            
            # Calculate rate type distribution
            flat_count = sum(1 for c in seg_customers if (c.get("current_rate_type") or "flat").lower() == "flat")
            tiered_count = sum(1 for c in seg_customers if (c.get("current_rate_type") or "flat").lower() == "tiered")
            tou_count = sum(1 for c in seg_customers if (c.get("current_rate_type") or "flat").lower() in ("tou", "time_of_use"))
            demand_count = sum(1 for c in seg_customers if (c.get("current_rate_type") or "flat").lower() == "demand")
            
            rate_type_distribution = f"Flat: {(flat_count/customer_count*100.0):.1f}%, Tiered: {(tiered_count/customer_count*100.0):.1f}%, TOU: {(tou_count/customer_count*100.0):.1f}%" if customer_count > 0 else "Flat: 0%, Tiered: 0%, TOU: 0%"
            if demand_count > 0:
                rate_type_distribution += f", Demand: {(demand_count/customer_count*100.0):.1f}%"
            
            characteristics = {
                "usage_pattern": seg_def["name"],
                "demographics": f"{(income_q/customer_count*100.0):.1f}% income-qualified; {(seniors/customer_count*100.0):.1f}% seniors" if customer_count > 0 else "0% income-qualified; 0% seniors",
                "ev_der_status": f"EV: {(ev/customer_count*100.0):.1f}%, Solar: {(solar/customer_count*100.0):.1f}%, Battery: {(batt/customer_count*100.0):.1f}%" if customer_count > 0 else "EV: 0%, Solar: 0%, Battery: 0%",
                "rate_type_distribution": rate_type_distribution,
                "avg_annual_kwh": round(avg_annual_kwh, 2),
            }
            demographics_summary = {
                "income_qualified": income_q,
                "seniors": seniors,
                "ev_owners": ev,
                "solar_owners": solar,
                "battery_owners": batt,
                "rate_type_distribution": {
                    "flat": flat_count,
                    "tiered": tiered_count,
                    "tou": tou_count,
                    "demand": demand_count
                }
            }
            
            # Determine rate_type for this segment
            # For rate-type-specific segments (FLAT, TIERED, TOU), extract from segment ID
            segment_rate_type = None
            seg_id_lower = seg_def["id"].lower()
            if "flat" in seg_id_lower:
                segment_rate_type = "flat"
            elif "tiered" in seg_id_lower:
                segment_rate_type = "tiered"
            elif "tou" in seg_id_lower:
                segment_rate_type = "tou"
            elif "demand" in seg_id_lower:
                segment_rate_type = "demand"
            # For other segments, use the dominant rate type in the segment
            if segment_rate_type is None and customer_count > 0:
                # Find dominant rate type
                if flat_count >= tiered_count and flat_count >= tou_count and flat_count >= demand_count:
                    segment_rate_type = "flat"
                elif tiered_count >= tou_count and tiered_count >= demand_count:
                    segment_rate_type = "tiered"
                elif tou_count >= demand_count:
                    segment_rate_type = "tou"
                else:
                    segment_rate_type = "demand"
            
            segments_to_insert.append((
                seg_def["id"],
                seg_def["name"],
                state,
                rate_class,
                segment_rate_type,  # Add rate_type to segments
                seg_def["elasticity"],
                round(avg_annual_kwh, 2),
                json.dumps(characteristics),
                json.dumps(demographics_summary)
            ))
            
            # Create memberships (customers can be in multiple segments)
            for customer in seg_customers:
                memberships_to_insert.append((
                    customer["customer_id"],
                    seg_def["id"]
                ))
    
    # Insert segments
    if segments_to_insert:
        cursor.executemany("""
            INSERT INTO customer_segments
            (segment_id, segment_name, state, rate_class, rate_type, price_elasticity, avg_annual_kwh,
             characteristics_json, demographics_summary_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, segments_to_insert)
        logger.success("✓ Generated {} customer segments", len(segments_to_insert))
    
    # Insert memberships
    if memberships_to_insert:
        cursor.executemany("""
            INSERT INTO customer_segment_membership
            (customer_id, segment_id)
            VALUES (?, ?)
        """, memberships_to_insert)
        logger.success("✓ Created {} segment memberships", len(memberships_to_insert))
    
    if not segments_to_insert:
        logger.warning("No segments generated")


def generate_existing_rates(
    cursor,
    states: List[str],
    rate_scenario: str = "baseline"
) -> None:
    """Generate existing rate structures by state with configurable scenarios.
    
    Args:
        cursor: Database cursor
        states: List of states to generate rates for
        rate_scenario: "baseline", "high", or "low" - adjusts all rates by multiplier
    """
    logger.info("Generating existing rate structures for states: {} (scenario: {})...", ", ".join(states), rate_scenario)
    
    # Scenario multipliers
    scenario_multipliers = {
        "baseline": 1.0,
        "high": 1.25,  # 25% higher rates
        "low": 0.85    # 15% lower rates
    }
    multiplier = scenario_multipliers.get(rate_scenario, 1.0)
    
    # Base rates (will be multiplied by scenario)
    base_rates = {
        "residential": {
            "flat": {
                "fixed_charge": 10.0,
                "energy_charge": 0.12,
                "tier_1_price": None,
                "tier_1_limit_kwh": None,
                "tier_2_price": None,
                "tier_2_limit_kwh": None,
                "tier_3_price": None,
                "tou_peak_price": None,
                "tou_offpeak_price": None,
                "tou_peak_hours": None,
                "demand_charge_per_kw": None
            },
            "tiered": {
                "fixed_charge": 10.0,
                "energy_charge": None,
                "tier_1_price": 0.10,
                "tier_1_limit_kwh": 500,
                "tier_2_price": 0.14,
                "tier_2_limit_kwh": 1000,
                "tier_3_price": 0.18,
                "tou_peak_price": None,
                "tou_offpeak_price": None,
                "tou_peak_hours": None,
                "demand_charge_per_kw": None
            },
            "tou": {
                "fixed_charge": 10.0,
                "energy_charge": None,
                "tier_1_price": None,
                "tier_1_limit_kwh": None,
                "tier_2_price": None,
                "tier_2_limit_kwh": None,
                "tier_3_price": None,
                "tou_peak_price": 0.20,
                "tou_offpeak_price": 0.10,
                "tou_peak_hours": "16:00-21:00",
                "demand_charge_per_kw": None
            }
        },
        "commercial": {
            "tou": {
                "fixed_charge": 50.0,
                "energy_charge": None,
                "tier_1_price": None,
                "tier_1_limit_kwh": None,
                "tier_2_price": None,
                "tier_2_limit_kwh": None,
                "tier_3_price": None,
                "tou_peak_price": 0.15,
                "tou_offpeak_price": 0.08,
                "tou_peak_hours": "08:00-22:00",
                "demand_charge_per_kw": 15.0
            }
        },
        "industrial": {
            "demand": {
                "fixed_charge": 200.0,
                "energy_charge": 0.06,
                "tier_1_price": None,
                "tier_1_limit_kwh": None,
                "tier_2_price": None,
                "tier_2_limit_kwh": None,
                "tier_3_price": None,
                "tou_peak_price": None,
                "tou_offpeak_price": None,
                "tou_peak_hours": None,
                "demand_charge_per_kw": 25.0
            }
        }
    }
    
    # State-specific rate variations (some states have higher/lower base rates)
    state_multipliers = {
        "California": 1.15,  # Higher due to renewable energy costs
        "Texas": 0.95,        # Lower due to deregulated market
        "Arizona": 1.10      # Slightly higher
    }
    
    rates = []
    for state in states:
        state_mult = state_multipliers.get(state, 1.0)
        total_mult = multiplier * state_mult
        
        # Generate rates for each rate class and type
        for rate_class, rate_types in base_rates.items():
            for rate_type, rate_params in rate_types.items():
                rate_name = f"{rate_class.upper()}_{rate_type.upper()}"
                
                # Apply multipliers to numeric values
                fixed_charge = rate_params["fixed_charge"] * total_mult if rate_params["fixed_charge"] else None
                energy_charge = rate_params["energy_charge"] * total_mult if rate_params["energy_charge"] else None
                tier_1_price = rate_params["tier_1_price"] * total_mult if rate_params["tier_1_price"] else None
                tier_2_price = rate_params["tier_2_price"] * total_mult if rate_params["tier_2_price"] else None
                tier_3_price = rate_params["tier_3_price"] * total_mult if rate_params["tier_3_price"] else None
                tou_peak_price = rate_params["tou_peak_price"] * total_mult if rate_params["tou_peak_price"] else None
                tou_offpeak_price = rate_params["tou_offpeak_price"] * total_mult if rate_params["tou_offpeak_price"] else None
                demand_charge = rate_params["demand_charge_per_kw"] * total_mult if rate_params["demand_charge_per_kw"] else None
                
                description = f"{state} {rate_class} {rate_type} rate"
                if rate_scenario != "baseline":
                    description += f" ({rate_scenario} scenario)"
                
                rates.append((
                    rate_name,
                    state,
                    rate_class,
                    rate_type,
                    round(fixed_charge, 2) if fixed_charge else None,
                    round(energy_charge, 4) if energy_charge else None,
                    round(tier_1_price, 4) if tier_1_price else None,
                    rate_params["tier_1_limit_kwh"],
                    round(tier_2_price, 4) if tier_2_price else None,
                    rate_params["tier_2_limit_kwh"],
                    round(tier_3_price, 4) if tier_3_price else None,
                    round(tou_peak_price, 4) if tou_peak_price else None,
                    round(tou_offpeak_price, 4) if tou_offpeak_price else None,
                    rate_params["tou_peak_hours"],
                    round(demand_charge, 2) if demand_charge else None,
                    "2020-01-01",
                    description
                ))
    
    cursor.executemany("""
        INSERT INTO existing_rates
        (rate_name, state, rate_class, rate_type, fixed_charge, energy_charge,
         tier_1_price, tier_1_limit_kwh, tier_2_price, tier_2_limit_kwh, tier_3_price,
         tou_peak_price, tou_offpeak_price, tou_peak_hours, demand_charge_per_kw,
         effective_date, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rates)
    
    logger.success("✓ Generated {} rate structures across {} states", len(rates), len(states))


def generate_interval_usage(
    cursor,
    customers: List[Dict[str, Any]],
    years: int,
    progress_file: Optional[str] = None,
    interval_type: str = "daily"
) -> None:
    """Generate interval usage data for all customers (hourly or daily)."""
    logger.info("Generating {} interval usage data for {} customers over {} years...", interval_type, len(customers), years)
    
    # Load progress if resuming
    completed_customers = set()
    if progress_file and os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                progress_data = json.load(f)
                completed_customers = set(progress_data.get("completed_customers", []))
                logger.info("Resuming from checkpoint: {} customers already completed", len(completed_customers))
        except Exception as e:
            logger.warning("Failed to load progress file: {}", e)
    
    # Get EV/DER data for load shape generation
    cursor.execute("SELECT customer_id, ev_owner_flag, solar_flag, battery_flag FROM ev_der_indicators")
    ev_der_map = {row[0]: {"ev": row[1], "solar": row[2], "battery": row[3]} for row in cursor.fetchall()}
    
    # Get demographics for usage patterns
    cursor.execute("SELECT customer_id, income_band, senior_flag FROM demographics_equity")
    demo_map = {row[0]: {"income": row[1], "senior": row[2]} for row in cursor.fetchall()}
    
    total_customers = len(customers)
    # Filter out already completed customers
    remaining_customers = [c for c in customers if c["customer_id"] not in completed_customers]
    total_remaining = len(remaining_customers)
    
    if total_remaining == 0:
        logger.info("All customers already processed, skipping interval generation")
        return
    
    start_time = time.time()
    batch_size = 100
    batch_count = 0
    
    # Generate data for each customer
    for idx, customer in enumerate(remaining_customers):
        customer_id = customer["customer_id"]
        rate_class = customer["rate_class"]
        baseline_annual_kwh = customer["baseline_annual_kwh"]
        ev_der = ev_der_map.get(customer_id, {})
        demo = demo_map.get(customer_id, {})
        
        # Generate interval data for this customer
        interval_data = _generate_customer_interval_usage(
            customer_id, rate_class, baseline_annual_kwh, years,
            ev_der.get("ev", False), ev_der.get("solar", False), ev_der.get("battery", False),
            demo.get("income", "medium"), demo.get("senior", False),
            interval_type=interval_type
        )
        
        # Insert in batches
        cursor.executemany("""
            INSERT INTO interval_usage (customer_id, timestamp, kwh)
            VALUES (?, ?, ?)
        """, interval_data)
        
        # Track completed
        completed_customers.add(customer_id)
        
        # Save progress every batch
        if (idx + 1) % batch_size == 0:
            batch_count += 1
            elapsed = time.time() - start_time
            rate = (idx + 1) / elapsed if elapsed > 0 else 0
            remaining = (total_remaining - idx - 1) / rate if rate > 0 else 0
            
            logger.info(
                "Progress: {}/{} customers ({:.1f}%), Batch {}, "
                "Elapsed: {:.1f}m, Est. remaining: {:.1f}m",
                idx + 1, total_remaining, (idx + 1) / total_remaining * 100,
                batch_count, elapsed / 60, remaining / 60
            )
            
            # Save checkpoint
            if progress_file:
                try:
                    with open(progress_file, 'w') as f:
                        json.dump({"completed_customers": list(completed_customers)}, f)
                except Exception as e:
                    logger.warning("Failed to save progress: {}", e)
            
            cursor.connection.commit()
    
    # Final commit
    cursor.connection.commit()
    
    logger.success("✓ Generated interval usage data for {} customers", total_remaining)


def _generate_customer_interval_usage(
    customer_id: str,
    rate_class: str,
    baseline_annual_kwh: float,
    years: int,
    ev_owner: bool,
    solar_owner: bool,
    battery_owner: bool,
    income_band: str,
    senior: bool,
    interval_type: str = "daily"
) -> List[tuple]:
    """Generate interval usage for a single customer (hourly or daily)."""
    interval_data = []
    
    # Start date (years ago)
    start_date = datetime.now() - timedelta(days=years * 365)
    
    if interval_type == "hourly":
        # Generate hourly data
        avg_hourly_kw = baseline_annual_kwh / 8760
        current_date = start_date
        end_date = datetime.now()
        
        while current_date < end_date:
            hour = current_date.hour
            day_of_week = current_date.weekday()  # 0=Monday, 6=Sunday
            month = current_date.month
            
            # Base load pattern
            if rate_class == "residential":
                base_kw = _get_residential_base_load(hour, day_of_week, month, avg_hourly_kw, senior)
            elif rate_class == "commercial":
                base_kw = _get_commercial_base_load(hour, day_of_week, avg_hourly_kw)
            else:  # industrial
                base_kw = _get_industrial_base_load(avg_hourly_kw)
            
            # Apply EV charging (overnight)
            if ev_owner and rate_class == "residential":
                if 23 <= hour or hour < 6:  # 11pm-6am
                    ev_kw = random.uniform(3.0, 7.0)
                    base_kw += ev_kw
            
            # Apply solar generation (daytime negative)
            if solar_owner and rate_class == "residential":
                if 10 <= hour < 16:  # 10am-4pm
                    solar_kw = random.uniform(2.0, 5.0)
                    base_kw -= solar_kw  # Negative = generation
            
            # Apply battery (evening discharge)
            if battery_owner and solar_owner and rate_class == "residential":
                if 16 <= hour < 21:  # 4pm-9pm
                    battery_kw = random.uniform(1.0, 3.0)
                    base_kw -= battery_kw
            
            # Ensure non-negative (for grid draw)
            kwh = max(0.1, base_kw)  # Minimum 0.1 kW
            
            interval_data.append((
                customer_id,
                current_date.strftime("%Y-%m-%dT%H:00:00Z"),
                round(kwh, 3)
            ))
            
            current_date += timedelta(hours=1)
    
    else:  # daily
        # Generate daily aggregated data
        avg_daily_kwh = baseline_annual_kwh / 365
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        while current_date < end_date:
            day_of_week = current_date.weekday()  # 0=Monday, 6=Sunday
            month = current_date.month
            is_weekend = day_of_week >= 5
            
            # Base daily consumption with seasonal and weekday patterns
            if rate_class == "residential":
                # Seasonal multiplier (summer AC, winter heating)
                if month in [6, 7, 8]:  # Summer
                    seasonal_mult = random.uniform(1.2, 1.5)
                elif month in [12, 1, 2]:  # Winter
                    seasonal_mult = random.uniform(1.1, 1.4)
                else:  # Spring/Fall
                    seasonal_mult = random.uniform(0.8, 1.1)
                
                # Weekend vs weekday
                if is_weekend:
                    daily_mult = random.uniform(0.9, 1.1)
                else:
                    daily_mult = random.uniform(1.0, 1.2)
                
                base_daily_kwh = avg_daily_kwh * seasonal_mult * daily_mult
                
            elif rate_class == "commercial":
                # Commercial: lower on weekends
                if is_weekend:
                    daily_mult = random.uniform(0.3, 0.5)
                else:
                    daily_mult = random.uniform(1.0, 1.2)
                base_daily_kwh = avg_daily_kwh * daily_mult
                
            else:  # industrial
                # Industrial: relatively constant
                base_daily_kwh = avg_daily_kwh * random.uniform(0.95, 1.05)
            
            # Apply EV impact (adds ~10-20 kWh/day for overnight charging)
            if ev_owner and rate_class == "residential":
                ev_daily_kwh = random.uniform(10.0, 20.0)
                base_daily_kwh += ev_daily_kwh
            
            # Apply solar impact (reduces net consumption by ~15-30 kWh/day)
            if solar_owner and rate_class == "residential":
                solar_daily_kwh = random.uniform(15.0, 30.0)
                base_daily_kwh -= solar_daily_kwh
            
            # Apply battery impact (further reduces evening consumption)
            if battery_owner and solar_owner and rate_class == "residential":
                battery_daily_kwh = random.uniform(5.0, 10.0)
                base_daily_kwh -= battery_daily_kwh
            
            # Ensure non-negative (for grid draw)
            daily_kwh = max(1.0, base_daily_kwh)
            
            interval_data.append((
                customer_id,
                current_date.strftime("%Y-%m-%dT00:00:00Z"),
                round(daily_kwh, 3)
            ))
            
            current_date += timedelta(days=1)
    
    return interval_data


def _get_residential_base_load(hour: int, day_of_week: int, month: int, avg_kw: float, senior: bool) -> float:
    """Get residential base load for a specific hour."""
    # Base load
    base = avg_kw * random.uniform(0.8, 1.2)
    
    # Evening peak (4pm-9pm)
    if 16 <= hour < 21:
        if day_of_week < 5:  # Weekday
            base *= random.uniform(1.3, 1.8)
        else:  # Weekend
            base *= random.uniform(1.2, 1.6)
    
    # Overnight (11pm-6am)
    if 23 <= hour or hour < 6:
        base *= random.uniform(0.6, 0.9)
    
    # AC load in summer (June-August)
    if month in [6, 7, 8]:
        if 12 <= hour < 20:  # Afternoon/evening
            base *= random.uniform(1.1, 1.3)
    
    # Heating load in winter (December-February)
    if month in [12, 1, 2]:
        base *= random.uniform(1.05, 1.15)
    
    # Senior patterns (home more during day)
    if senior:
        if 9 <= hour < 17:  # Daytime
            base *= random.uniform(1.1, 1.3)
    
    return base


def _get_commercial_base_load(hour: int, day_of_week: int, avg_kw: float) -> float:
    """Get commercial base load for a specific hour."""
    base = avg_kw
    
    # Business hours (8am-6pm, weekdays)
    if day_of_week < 5 and 8 <= hour < 18:
        base *= random.uniform(1.5, 2.5)
    else:
        base *= random.uniform(0.3, 0.6)  # Lower outside business hours
    
    return base


def _get_industrial_base_load(avg_kw: float) -> float:
    """Get industrial base load (steady 24/7)."""
    # Steady load with small variations
    return avg_kw * random.uniform(0.95, 1.05)


def _parse_distribution(dist_str: str) -> Dict[str, float]:
    """Parse distribution string like 'type1:0.4,type2:0.6' into dict."""
    dist = {}
    if not dist_str:
        return dist
    for item in dist_str.split(','):
        if ':' in item:
            key, value = item.split(':', 1)
            try:
                dist[key.strip()] = float(value.strip())
            except ValueError:
                logger.warning("Invalid distribution value '{}', skipping", item)
    return dist


def _extract_survey_qa(content: str) -> tuple[Optional[str], Optional[str]]:
    """
    Extract survey question/answer from a Q/A formatted text stored in voice_of_customer.content.

    Expected format (loose):
    Q: ...
    A: ...
    """
    if not content:
        return None, None
    text = content.strip()
    if "Q:" not in text or "A:" not in text:
        return None, None
    try:
        q_part = text.split("Q:", 1)[1]
        q_text, a_part = q_part.split("A:", 1)
        question = q_text.strip()
        answer = a_part.strip()
        if not question or not answer:
            return None, None
        return question, answer
    except Exception:
        return None, None


def generate_voice_of_customer(
    cursor,
    customers: List[Dict[str, Any]],
    use_llm: bool = True,
    model_type: str = "azure_openai",
    snippet_pct: float = 10.0,
    text_type_dist: Optional[str] = None,
    topic_dist: Optional[str] = None,
    sentiment_dist: Optional[str] = None
) -> None:
    """Generate voice of customer text snippets with configurable distribution."""
    snippet_count = int(len(customers) * snippet_pct / 100.0)
    policy_count = int(snippet_count * 0.15)  # 15% of customer snippets
    total_snippets = snippet_count + policy_count
    
    logger.info("Generating voice of customer text ({} customer snippets + {} policy/news = {} total)...", 
                snippet_count, policy_count, total_snippets)
    
    # Parse distributions or use defaults
    if text_type_dist:
        text_types = _parse_distribution(text_type_dist)
        # Normalize weights to sum to 1.0
        total_weight = sum(text_types.values())
        if total_weight > 0:
            text_types = {k: v / total_weight for k, v in text_types.items()}
    else:
        # Default distribution
        text_types = {
            "complaint": 0.40,
            "survey": 0.30,
            "policy_order": 0.15,
            "testimony": 0.10,
            "news": 0.05
        }
    
    # Parse topic distribution (for weighted selection)
    if topic_dist:
        topic_weights = _parse_distribution(topic_dist)
        topics = list(topic_weights.keys())
        topic_weights_list = list(topic_weights.values())
        # Normalize
        total_weight = sum(topic_weights_list)
        if total_weight > 0:
            topic_weights_list = [w / total_weight for w in topic_weights_list]
    else:
        # Default: equal weight for all topics
        topics = [
            "billing", "outages", "rate_fairness", "ev_programs",
            "income_assistance", "solar_programs", "service_quality", "peak_pricing"
        ]
        topic_weights_list = None  # Equal weights
    
    # Parse overall sentiment distribution
    if sentiment_dist:
        sentiment_weights = _parse_distribution(sentiment_dist)
        # Normalize
        total_weight = sum(sentiment_weights.values())
        if total_weight > 0:
            sentiment_weights = {k: v / total_weight for k, v in sentiment_weights.items()}
    else:
        sentiment_weights = {"positive": 0.30, "neutral": 0.40, "negative": 0.30}
    
    snippets = []
    
    # Customer-related snippets
    for i in range(snippet_count):
        customer = random.choice(customers)
        customer_id = customer["customer_id"]
        
        # Determine text type
        rand = random.random()
        cumulative = 0
        text_type = "complaint"
        for ttype, weight in text_types.items():
            cumulative += weight
            if rand <= cumulative:
                text_type = ttype
                break
        
        # Select topic (weighted if distribution provided)
        if topic_weights_list:
            topic = random.choices(topics, weights=topic_weights_list)[0]
        else:
            topic = random.choice(topics)
        
        # Sentiment (text-type specific, but influenced by overall distribution)
        if text_type == "complaint":
            # Complaints are mostly negative, but allow some neutral
            sentiment = random.choices(["negative", "neutral"], weights=[0.80, 0.20])[0]
        elif text_type == "survey":
            # Surveys follow overall sentiment distribution more closely
            sentiment = random.choices(
                list(sentiment_weights.keys()),
                weights=list(sentiment_weights.values())
            )[0]
        else:
            sentiment = "neutral"
        
        # Length
        if text_type in ["complaint", "testimony"]:
            length = random.randint(50, 200)
        elif text_type == "survey":
            length = random.randint(20, 100)
        elif text_type == "policy_order":
            length = random.randint(200, 500)
        else:  # news
            length = random.randint(150, 400)
        
        # Timestamp
        if text_type in ["complaint", "survey", "testimony"]:
            days_ago = random.randint(1, 365)
            timestamp = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            timestamp = None
        
        # Source
        if text_type == "complaint":
            source = "customer_service"
        elif text_type == "survey":
            source = "survey"
        elif text_type == "policy_order":
            source = "commission"
        elif text_type == "testimony":
            source = "public_hearing"
        else:
            source = "news"
        
        snippets.append({
            "customer_id": customer_id,
            "text_type": text_type,
            "topic": topic,
            "sentiment": sentiment,
            "length": length,
            "timestamp": timestamp,
            "source": source
        })
    
    # Policy order and news snippets (no customer_id)
    for i in range(policy_count):
        text_type = random.choice(["policy_order", "news"])
        topic = random.choice(["rate_fairness", "ev_programs", "income_assistance", "solar_programs"])
        
        snippets.append({
            "customer_id": None,
            "text_type": text_type,
            "topic": topic,
            "sentiment": "neutral",
            "length": random.randint(200, 500) if text_type == "policy_order" else random.randint(150, 400),
            "timestamp": None,
            "source": "commission" if text_type == "policy_order" else "news"
        })
    
    # Generate text content
    logger.info("Generating text content (using LLM: {})...", use_llm)
    
    if use_llm and MODEL_FACTORY_AVAILABLE:
        llm = None
        deployment_name = None
        try:
            llm = ModelFactory.get_model(model_type)
            deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")
            if not deployment_name:
                logger.warning("AZURE_OPENAI_DEPLOYMENT not set, using default")
                deployment_name = "gpt-4o-mini"
        except Exception as e:
            logger.error("Failed to initialize LLM: {}", e)
            logger.info("Falling back to template-based generation")
            use_llm = False
    
    voice_data = []
    for idx, snippet in enumerate(snippets):
        if use_llm and llm:
            try:
                # Special handling for survey type - generate Q&A format
                if snippet['text_type'] == "survey":
                    prompt = f"""Generate a realistic customer survey response about {snippet['topic']} from a utility customer.

Format: Question and Answer
Topic: {snippet['topic']}
Sentiment: {snippet['sentiment']}
Length: {snippet['length']} words total

Generate in this format:
Q: [Survey question about {snippet['topic']}]
A: [Customer's answer reflecting {snippet['sentiment']} sentiment]

Generate ONLY the Q&A text, no JSON, no metadata, no quotes."""
                else:
                    prompt = f"""Generate a realistic {snippet['text_type']} about {snippet['topic']} from a utility customer or regulatory context.

Type: {snippet['text_type']}
Topic: {snippet['topic']}
Sentiment: {snippet['sentiment']}
Length: {snippet['length']} words

Generate ONLY the text content, no JSON, no metadata, no quotes."""

                response = llm.chat.completions.create(
                    model=deployment_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8,
                    max_tokens=min(snippet['length'] * 2, 500)
                )
                content = response.choices[0].message.content.strip()
                
                # Remove quotes if present
                if content.startswith('"') and content.endswith('"'):
                    content = content[1:-1]
                
            except Exception as e:
                logger.warning("LLM generation failed for snippet {}: {}, using template", idx, e)
                content = _generate_template_text(snippet)
        else:
            content = _generate_template_text(snippet)
        
        survey_type = None
        question = None
        answer = None
        text_snippet = None

        if snippet["text_type"] == "survey":
            survey_type = snippet["topic"]
            question, answer = _extract_survey_qa(content)
            if answer:
                text_snippet = (answer[:240] + "…") if len(answer) > 240 else answer
            else:
                text_snippet = (content[:240] + "…") if len(content) > 240 else content
        else:
            text_snippet = (content[:240] + "…") if len(content) > 240 else content

        voice_data.append((
            snippet["customer_id"],
            snippet["text_type"],
            content,
            survey_type,
            question,
            answer,
            text_snippet,
            snippet["topic"],
            snippet["sentiment"],
            snippet["timestamp"],
            snippet["source"]
        ))
        
        # Progress and rate limiting
        if (idx + 1) % 50 == 0:
            logger.info("Generated {}/{} text snippets", idx + 1, len(snippets))
        
        if use_llm:
            time.sleep(0.1)  # Rate limiting
    
    # Insert into database
    cursor.executemany("""
        INSERT INTO voice_of_customer
        (customer_id, text_type, content, survey_type, question, answer, snippet, topic, sentiment, timestamp, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, voice_data)
    
    logger.success("✓ Generated {} voice of customer snippets", len(voice_data))


def _generate_template_text(snippet: Dict[str, Any]) -> str:
    """Generate template-based text as fallback."""
    text_type = snippet["text_type"]
    topic = snippet["topic"]
    sentiment = snippet["sentiment"]
    
    templates = {
        "complaint": {
            "billing": "I am very frustrated with my recent bill. The charges seem much higher than usual and I don't understand why. I've been a customer for years and this is unacceptable.",
            "rate_fairness": "The new rates are unfair to low-income customers like me. We can't afford these increases and it's putting a strain on our household budget.",
            "outages": "We've experienced multiple power outages this month and it's affecting my work from home. The utility needs to improve reliability.",
        },
        "survey": {
            "rate_fairness": "Q: How do you feel about the current rate structure?\nA: I think the current rates are reasonable, though I'd like to see more options for time-of-use pricing.",
            "ev_programs": "Q: Are you interested in EV charging programs?\nA: Yes, I'm interested in EV charging programs but need more information about how they work and what the costs would be.",
            "billing": "Q: How satisfied are you with your billing experience?\nA: The billing is generally clear, but I'd appreciate more detailed breakdowns of charges.",
            "outages": "Q: How would you rate the reliability of service?\nA: Service is mostly reliable, but we've had a few outages that were inconvenient.",
            "income_assistance": "Q: Are you aware of income-qualified assistance programs?\nA: I've heard about them but haven't applied. I'd like to know if I qualify.",
            "solar_programs": "Q: Would you consider installing solar panels?\nA: I'm interested but concerned about upfront costs and payback period.",
            "service_quality": "Q: How would you rate overall service quality?\nA: Service quality is good overall, but customer service response times could be better.",
            "peak_pricing": "Q: Would you be willing to shift usage to off-peak hours for lower rates?\nA: Yes, I'd be willing to shift some usage if the savings are meaningful.",
        },
        "policy_order": {
            "rate_fairness": "The Commission finds that the proposed rate structure adequately balances revenue requirements with customer affordability concerns. However, additional protections for low-income customers are warranted.",
        }
    }
    
    # Return template or generic text
    if text_type in templates and topic in templates[text_type]:
        return templates[text_type][topic]
    else:
        return f"This is a {sentiment} {text_type} about {topic} from a utility customer perspective."


def create_indexes(cursor) -> None:
    """Create indexes for faster queries."""
    logger.info("Creating indexes...")
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_customer_rate_class ON customer_master(rate_class)",
        "CREATE INDEX IF NOT EXISTS idx_customer_zip ON customer_master(zip_code)",
        "CREATE INDEX IF NOT EXISTS idx_customer_state ON customer_master(state)",
        "CREATE INDEX IF NOT EXISTS idx_interval_customer ON interval_usage(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_interval_timestamp ON interval_usage(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_interval_customer_timestamp ON interval_usage(customer_id, timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_demographics_income ON demographics_equity(income_band)",
        "CREATE INDEX IF NOT EXISTS idx_demographics_senior ON demographics_equity(senior_flag)",
        "CREATE INDEX IF NOT EXISTS idx_ev_owner ON ev_der_indicators(ev_owner_flag)",
        "CREATE INDEX IF NOT EXISTS idx_solar ON ev_der_indicators(solar_flag)",
        "CREATE INDEX IF NOT EXISTS idx_battery ON ev_der_indicators(battery_flag)",
        "CREATE INDEX IF NOT EXISTS idx_voc_type ON voice_of_customer(text_type)",
        "CREATE INDEX IF NOT EXISTS idx_voc_survey_type ON voice_of_customer(survey_type)",
        "CREATE INDEX IF NOT EXISTS idx_voc_topic ON voice_of_customer(topic)",
        "CREATE INDEX IF NOT EXISTS idx_voc_sentiment ON voice_of_customer(sentiment)",
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    logger.success("✓ Created indexes")


def main() -> int:
    """Main function to generate mock data."""
    try:
        parser = argparse.ArgumentParser(description="Setup Rate Case Filing database and mock data")
        parser.add_argument(
            "--db-path",
            type=str,
            default=None,
            help="Database file path (default: projects/ensemble/data/rate_case_filing/rate_case_database.db)"
        )
        parser.add_argument(
            "--customer-count",
            type=int,
            default=7500,
            help="Number of customers to generate (default: 7500)"
        )
        parser.add_argument(
            "--years",
            type=int,
            default=5,
            help="Years of interval usage data (default: 5)"
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Drop and recreate all tables (input + output)"
        )
        parser.add_argument(
            "--reset-outputs",
            action="store_true",
            help="Drop and recreate only pipeline output tables and voice_of_customer (keeps input data)"
        )
        parser.add_argument(
            "--reset-segmentation",
            action="store_true",
            help="Drop and recreate customer_segments and customer_segment_membership tables (keeps all other data)"
        )
        parser.add_argument(
            "--voice-snippet-pct",
            type=float,
            default=10.0,
            help="Percentage of customers to generate voice snippets for (default: 10.0)"
        )
        parser.add_argument(
            "--voice-text-type-dist",
            type=str,
            default="complaint:0.40,survey:0.30,policy_order:0.15,testimony:0.10,news:0.05",
            help="Text type distribution as 'type1:weight1,type2:weight2,...' (default: complaint:0.40,survey:0.30,policy_order:0.15,testimony:0.10,news:0.05)"
        )
        parser.add_argument(
            "--voice-topic-dist",
            type=str,
            default="billing:0.20,outages:0.15,rate_fairness:0.20,ev_programs:0.15,income_assistance:0.10,solar_programs:0.10,service_quality:0.05,peak_pricing:0.05",
            help="Topic distribution as 'topic1:weight1,topic2:weight2,...' (default: balanced distribution)"
        )
        parser.add_argument(
            "--voice-sentiment-dist",
            type=str,
            default="positive:0.30,neutral:0.40,negative:0.30",
            help="Overall sentiment distribution as 'sentiment1:weight1,sentiment2:weight2,...' (default: positive:0.30,neutral:0.40,negative:0.30)"
        )
        parser.add_argument(
            "--skip-interval",
            action="store_true",
            help="Skip interval_usage generation (for testing)"
        )
        parser.add_argument(
            "--interval",
            type=str,
            choices=["hourly", "daily"],
            default="daily",
            help="Interval granularity: 'hourly' (24x more rows) or 'daily' (default: daily)"
        )
        parser.add_argument(
            "--skip-voice",
            action="store_true",
            help="Skip voice_of_customer generation (for testing)"
        )
        parser.add_argument(
            "--regenerate-voice",
            action="store_true",
            help="Regenerate voice_of_customer only (drops and recreates voice table, skips other data generation)"
        )
        parser.add_argument(
            "--rate-scenario",
            type=str,
            choices=["baseline", "high", "low"],
            default="baseline",
            help="Rate scenario: 'baseline' (default), 'high' (+25%), or 'low' (-15%)"
        )
        parser.add_argument(
            "--regenerate-rates",
            action="store_true",
            help="Regenerate existing_rates only (drops and recreates rates table, skips other data generation)"
        )
        parser.add_argument(
            "--no-llm",
            action="store_true",
            help="Skip LLM, use template-based text generation"
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Batch size for interval generation (default: 100)"
        )
        parser.add_argument(
            "--progress-file",
            type=str,
            default=None,
            help="Progress checkpoint file path (default: <db-path>.progress.json)"
        )
        parser.add_argument(
            "--llm-model-type",
            type=str,
            default="azure_openai",
            help="Model type for ModelFactory (default: azure_openai)"
        )
        
        args = parser.parse_args()
        
        # Detect project name for path resolution
        project_name = detect_project_name(Path.cwd())
        
        # Resolve database path
        if args.db_path:
            db_path = resolve_script_path(args.db_path, project_name=project_name)
        else:
            db_path = resolve_script_path(
                "projects/ensemble/data/rate_case_filing/rate_case_database.db",
                project_name=project_name
            )
        
        # Progress file
        progress_file = args.progress_file
        if not progress_file:
            progress_file = str(db_path) + ".progress.json"
        
        # Ensure directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Calculate estimated row count and time (mode-aware)
        total_rows = 0
        time_str = "N/A"
        show_interval_stats = False

        # Modes that do NOT generate interval data (so interval estimate should be suppressed/zeroed)
        if args.reset_outputs:
            # Drops/recreates output tables + existing_rates and returns early
            time_str = "~<1 minute (reset outputs only)"
            total_rows = 0
            show_interval_stats = True
        elif args.regenerate_rates:
            time_str = "~<1 minute (regenerate rates only)"
            total_rows = 0
            show_interval_stats = True
        elif args.regenerate_voice:
            # Voice regeneration depends on LLM/template generation and snippet_pct
            time_str = "~minutes (regenerate voice only; depends on LLM/template)"
            total_rows = 0
            show_interval_stats = True
        elif args.skip_interval:
            total_rows = 0
            time_str = "N/A (skipping interval)"
            show_interval_stats = True
        else:
            show_interval_stats = True
            if args.interval == "hourly":
                total_rows = args.customer_count * args.years * 365 * 24
                rows_per_second = 1000  # Conservative estimate
            else:  # daily
                total_rows = args.customer_count * args.years * 365
                rows_per_second = 5000  # Daily is faster (fewer rows, simpler aggregation)

            estimated_seconds = total_rows / rows_per_second
            estimated_hours = estimated_seconds / 3600
            estimated_minutes = estimated_seconds / 60

            if estimated_hours >= 1:
                time_str = f"~{estimated_hours:.1f} hours"
            else:
                time_str = f"~{estimated_minutes:.0f} minutes"
        
        print("\n" + "=" * 70)
        print("Rate Case Filing - Mock Data Generator")
        print("=" * 70)
        print(f"\nDatabase: {db_path}")
        print(f"Customers: {args.customer_count:,}")
        print(f"Years: {args.years}")
        print(f"Reset outputs: {args.reset_outputs}")
        print(f"Regenerate voice: {args.regenerate_voice}")
        print(f"Regenerate rates: {args.regenerate_rates}")
        print(f"Reset segmentation: {args.reset_segmentation}")
        if show_interval_stats and not args.skip_interval and not args.reset_outputs and not args.regenerate_rates and not args.regenerate_voice and not args.reset_segmentation:
            print(f"Interval type: {args.interval}")
            print(f"Interval rows: {total_rows:,} ({total_rows/1_000_000:.1f}M)")
            print(f"Estimated time: {time_str}")
        elif show_interval_stats:
            # For modes that skip interval generation, still show consistent interval stats
            print(f"Interval type: {args.interval}")
            print(f"Interval rows: {total_rows:,} ({total_rows/1_000_000:.1f}M)")
            print(f"Estimated time: {time_str}")
        print(f"Reset mode: {args.reset}")
        print(f"Skip interval: {args.skip_interval}")
        print(f"Skip voice: {args.skip_voice}")
        print(f"Use LLM: {not args.no_llm}")
        print()
        
        if not args.skip_interval and total_rows > 50_000_000:
            logger.warning(f"Large dataset detected ({total_rows:,} rows). This may take several hours.")
            logger.info("Consider using --skip-interval for testing, or reduce --customer-count/--years")
            response = input("\nContinue? (y/N): ").strip().lower()
            if response != 'y':
                logger.info("Aborted by user")
                return 0
            print()
        
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Handle regenerate-voice mode (must be before other resets)
        if args.regenerate_voice:
            # Load existing customers (required for voice generation)
            cursor.execute("SELECT customer_id, rate_class, income_qualified_flag, zip_code, state, city, household_size, dwelling_type, baseline_annual_kwh, service_start_date FROM customer_master")
            customer_rows = cursor.fetchall()
            if not customer_rows:
                logger.error("No customers found in database. Please run full setup first.")
                conn.close()
                return 1
            
            customers = [
                {
                    "customer_id": row[0],
                    "rate_class": row[1],
                    "income_qualified_flag": row[2],
                    "zip_code": row[3],
                    "state": row[4],
                    "city": row[5],
                    "household_size": row[6],
                    "dwelling_type": row[7],
                    "baseline_annual_kwh": row[8],
                    "service_start_date": row[9]
                }
                for row in customer_rows
            ]
            
            logger.warning("Resetting voice_of_customer table...")
            cursor.execute("DROP TABLE IF EXISTS voice_of_customer")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS voice_of_customer (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id TEXT,
                    text_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    survey_type TEXT,
                    question TEXT,
                    answer TEXT,
                    snippet TEXT,
                    topic TEXT,
                    sentiment TEXT,
                    timestamp TEXT,
                    source TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customer_master(customer_id) ON DELETE SET NULL
                )
            """)
            conn.commit()
            logger.info("✓ Voice of customer table reset")
            
            # Generate voice data
            logger.info("Regenerating voice of customer with {} customers...", len(customers))
            generate_voice_of_customer(
                cursor, 
                customers, 
                use_llm=not args.no_llm, 
                model_type=args.llm_model_type,
                snippet_pct=args.voice_snippet_pct,
                text_type_dist=args.voice_text_type_dist,
                topic_dist=args.voice_topic_dist,
                sentiment_dist=args.voice_sentiment_dist
            )
            conn.commit()
            logger.success("✓ Voice of customer regeneration complete!")
            conn.close()
            return 0
        
        # Handle reset-segmentation mode
        if args.reset_segmentation:
            # Check if customers exist
            cursor.execute("SELECT COUNT(*) FROM customer_master")
            row = cursor.fetchone()
            customer_count = row[0] if row else 0
            if customer_count == 0:
                logger.error("No customers found in database. Please run full setup first.")
                conn.close()
                return 1
            
            logger.warning("Resetting customer_segments and customer_segment_membership tables...")
            cursor.execute("DROP TABLE IF EXISTS customer_segment_membership")
            cursor.execute("DROP TABLE IF EXISTS customer_segments")
            conn.commit()
            logger.info("✓ Segmentation tables dropped")
            
            # Recreate tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customer_segments (
                    segment_id TEXT PRIMARY KEY,
                    segment_name TEXT NOT NULL,
                    state TEXT NOT NULL,
                    rate_class TEXT NOT NULL,
                    rate_type TEXT,
                    price_elasticity REAL NOT NULL,
                    avg_annual_kwh REAL,
                    characteristics_json TEXT,
                    demographics_summary_json TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customer_segment_membership (
                    customer_id TEXT NOT NULL,
                    segment_id TEXT NOT NULL,
                    PRIMARY KEY (customer_id, segment_id),
                    FOREIGN KEY (customer_id) REFERENCES customer_master(customer_id) ON DELETE CASCADE,
                    FOREIGN KEY (segment_id) REFERENCES customer_segments(segment_id) ON DELETE CASCADE
                )
            """)
            conn.commit()
            logger.info("✓ Segmentation tables recreated")
            
            # Regenerate segments
            logger.info("Regenerating customer segments...")
            generate_customer_segments(cursor)
            conn.commit()
            logger.success("✓ Customer segments regeneration complete!")
            conn.close()
            return 0
        
        # Reset if requested
        if args.reset:
            logger.warning("Resetting database (dropping all tables)...")
            # Drop output tables first (due to foreign keys)
            cursor.execute("DROP TABLE IF EXISTS filing_artifacts")
            cursor.execute("DROP TABLE IF EXISTS regulatory_narratives")
            cursor.execute("DROP TABLE IF EXISTS recommendations")
            cursor.execute("DROP TABLE IF EXISTS state_comparisons")
            cursor.execute("DROP TABLE IF EXISTS equity_assessments")
            cursor.execute("DROP TABLE IF EXISTS simulation_results")
            # Note: rate_design_options are no longer in database (context-only)
            # customer_segments are now pre-computed in the database
            cursor.execute("DROP TABLE IF EXISTS pipeline_runs")
            # Drop input tables
            cursor.execute("DROP TABLE IF EXISTS voice_of_customer")
            cursor.execute("DROP TABLE IF EXISTS customer_segment_membership")
            cursor.execute("DROP TABLE IF EXISTS customer_segments")
            cursor.execute("DROP TABLE IF EXISTS interval_usage")
            cursor.execute("DROP TABLE IF EXISTS ev_der_indicators")
            cursor.execute("DROP TABLE IF EXISTS demographics_equity")
            cursor.execute("DROP TABLE IF EXISTS existing_rates")
            cursor.execute("DROP TABLE IF EXISTS customer_master")
            conn.commit()
            logger.info("✓ All tables dropped")
        elif args.reset_outputs:
            logger.warning("Resetting pipeline output tables and existing_rates (keeping input data + voice_of_customer)...")
            # Drop only output tables and existing_rates (keep voice_of_customer; use --regenerate-voice if needed)
            cursor.execute("DROP TABLE IF EXISTS regulatory_narratives")
            cursor.execute("DROP TABLE IF EXISTS recommendations")
            cursor.execute("DROP TABLE IF EXISTS state_comparisons")
            cursor.execute("DROP TABLE IF EXISTS equity_assessments")
            cursor.execute("DROP TABLE IF EXISTS simulation_results")
            # Note: customer_segments and rate_design_options are no longer in database (context-only)
            cursor.execute("DROP TABLE IF EXISTS pipeline_runs")
            cursor.execute("DROP TABLE IF EXISTS existing_rates")
            conn.commit()
            logger.info("✓ Output tables and existing_rates dropped")
            
            # Clear reports folder
            reports_dir = db_path.parent / "reports"
            if reports_dir.exists():
                try:
                    shutil.rmtree(reports_dir)
                    logger.info(f"✓ Cleared reports folder: {reports_dir}")
                except Exception as e:
                    logger.warning(f"Failed to clear reports folder {reports_dir}: {e}")
            else:
                logger.debug(f"Reports folder does not exist: {reports_dir} (skipping)")
        
        # Handle regenerate-rates mode (must be before reset_outputs)
        if args.regenerate_rates:
            # Get unique states from customers
            cursor.execute("SELECT DISTINCT state FROM customer_master")
            state_rows = cursor.fetchall()
            if not state_rows:
                logger.error("No customers found in database. Please run full setup first.")
                conn.close()
                return 1
            
            states = [row[0] for row in state_rows]
            
            logger.warning("Resetting existing_rates table...")
            cursor.execute("DROP TABLE IF EXISTS existing_rates")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS existing_rates (
                    rate_name TEXT NOT NULL,
                    state TEXT NOT NULL,
                    rate_class TEXT NOT NULL,
                    rate_type TEXT NOT NULL,
                    fixed_charge REAL NOT NULL,
                    energy_charge REAL,
                    tier_1_price REAL,
                    tier_1_limit_kwh INTEGER,
                    tier_2_price REAL,
                    tier_2_limit_kwh INTEGER,
                    tier_3_price REAL,
                    tou_peak_price REAL,
                    tou_offpeak_price REAL,
                    tou_peak_hours TEXT,
                    demand_charge_per_kw REAL,
                    effective_date TEXT,
                    description TEXT,
                    PRIMARY KEY (rate_name, state)
                )
            """)
            conn.commit()
            logger.info("✓ Existing rates table reset")
            
            # Generate rates
            logger.info("Regenerating existing rates for states: {} (scenario: {})...", ", ".join(states), args.rate_scenario)
            generate_existing_rates(cursor, states, rate_scenario=args.rate_scenario)
            conn.commit()
            logger.success("✓ Existing rates regeneration complete!")
            conn.close()
            return 0
        
        # Create schema
        if args.reset_outputs:
            # Only create output tables and existing_rates, skip input data generation
            logger.info("Creating pipeline output tables and existing_rates tables...")
            _create_output_tables_only(cursor)
            # Also create existing_rates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS existing_rates (
                    rate_name TEXT NOT NULL,
                    state TEXT NOT NULL,
                    rate_class TEXT NOT NULL,
                    rate_type TEXT NOT NULL,
                    fixed_charge REAL NOT NULL,
                    energy_charge REAL,
                    tier_1_price REAL,
                    tier_1_limit_kwh INTEGER,
                    tier_2_price REAL,
                    tier_2_limit_kwh INTEGER,
                    tier_3_price REAL,
                    tou_peak_price REAL,
                    tou_offpeak_price REAL,
                    tou_peak_hours TEXT,
                    demand_charge_per_kw REAL,
                    effective_date TEXT,
                    description TEXT,
                    PRIMARY KEY (rate_name, state)
                )
            """)

            # Repopulate existing_rates immediately so the pipeline can run after --reset-outputs.
            cursor.execute("SELECT DISTINCT state FROM customer_master")
            state_rows = cursor.fetchall()
            if not state_rows:
                logger.error("No customers found in database. Cannot repopulate existing_rates after --reset-outputs.")
                conn.close()
                return 1
            states = [row[0] for row in state_rows]
            logger.info(
                "Populating existing_rates for states: {} (scenario: {})...",
                ", ".join(states),
                args.rate_scenario,
            )
            generate_existing_rates(cursor, states, rate_scenario=args.rate_scenario)
            conn.commit()
            conn.commit()
            logger.success("✓ Pipeline output tables, voice_of_customer, and existing_rates reset complete!")
            logger.info("Input data preserved. You can now run the pipeline or regenerate voice_of_customer/rates.")
            conn.close()
            return 0
        else:
            logger.info("Creating database schema...")
            create_database_schema(str(db_path))
        
        # Generate data (only if not resetting outputs only)
        logger.info("Generating customer master data...")
        customers = generate_customer_master(cursor, args.customer_count)
        conn.commit()
        
        logger.info("Generating demographics and equity data...")
        generate_demographics_equity(cursor, customers)
        conn.commit()
        
        logger.info("Generating EV and DER indicators...")
        generate_ev_der_indicators(cursor, customers)
        conn.commit()
        
        logger.info("Generating customer segments...")
        generate_customer_segments(cursor)
        conn.commit()
        
        logger.info("Generating existing rate structures...")
        # Get unique states from customers
        states = list(set(c["state"] for c in customers))
        generate_existing_rates(cursor, states, rate_scenario=args.rate_scenario)
        conn.commit()
        
        if not args.skip_interval:
            logger.info("Generating interval usage data ({})...", args.interval)
            generate_interval_usage(cursor, customers, args.years, progress_file, interval_type=args.interval)
            conn.commit()
        else:
            logger.info("⏭ Skipping interval usage generation")
        
        if not args.skip_voice:
            logger.info("Generating voice of customer text...")
            generate_voice_of_customer(
                cursor, 
                customers, 
                use_llm=not args.no_llm, 
                model_type=args.llm_model_type,
                snippet_pct=args.voice_snippet_pct,
                text_type_dist=args.voice_text_type_dist,
                topic_dist=args.voice_topic_dist,
                sentiment_dist=args.voice_sentiment_dist
            )
            conn.commit()
        else:
            logger.info("⏭ Skipping voice of customer generation")
        
        # Create indexes
        logger.info("Creating indexes...")
        create_indexes(cursor)
        conn.commit()
        
        # VACUUM and ANALYZE
        logger.info("Optimizing database...")
        cursor.execute("VACUUM")
        cursor.execute("ANALYZE")
        conn.commit()
        
        conn.close()
        
        logger.success("✓ Database generation complete!")
        logger.info("Database location: {}", db_path)
        
        # Print summary
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM customer_master")
        customer_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM interval_usage")
        interval_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM voice_of_customer")
        voice_count = cursor.fetchone()[0]
        
        conn.close()
        
        print("\n" + "=" * 70)
        print("Generation Summary")
        print("=" * 70)
        print(f"Customers: {customer_count:,}")
        print(f"Interval usage records: {interval_count:,}")
        print(f"Voice of customer snippets: {voice_count:,}")
        try:
            db_size = db_path.stat().st_size / (1024*1024)
            print(f"Database size: {db_size:.1f} MB")
        except Exception:
            print("Database size: N/A")
        print()
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("\n⚠ Generation interrupted by user")
        logger.info("Progress has been saved. You can resume by running the script again.")
        return 1
    except Exception as e:
        logger.error("Generation failed: {}", e)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

