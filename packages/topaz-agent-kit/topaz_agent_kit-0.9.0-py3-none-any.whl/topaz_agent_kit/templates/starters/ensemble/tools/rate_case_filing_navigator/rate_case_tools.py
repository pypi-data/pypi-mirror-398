"""
Rate Case Filing Navigator - Pipeline-specific local tools.

Goal:
- Agents should NOT directly use sqlite_query/sqlite_execute or python_execute.
- LLM can generate ideas/text, but all DB reads/writes and deterministic computation must go through these tools.

This toolkit is intentionally opinionated and schema-aware for the rate case demo database created by:
  src/topaz_agent_kit/scripts/setup_rate_case_database.py
"""

from __future__ import annotations

import json
import os
import random
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from topaz_agent_kit.local_tools.registry import pipeline_tool
from topaz_agent_kit.utils.logger import Logger

_logger = Logger("RateCaseTools")


@dataclass
class _RateOption:
    option_id: str
    option_name: str
    rate_class: str
    rate_type: str
    fixed_charge: float
    energy_charge: float
    tier_structure: Dict[str, Any]
    tou_structure: Dict[str, Any]
    demand_charge: float
    assumptions: List[str]
    description: str


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------

def _validate_db_file(db_file: str) -> None:
    if not db_file:
        raise ValueError("db_file is required")
    if not os.path.exists(db_file):
        raise FileNotFoundError(f"Database file not found: {db_file}")
    if not os.path.isfile(db_file):
        raise ValueError(f"db_file is not a file: {db_file}")


def _connect(db_file: str) -> sqlite3.Connection:
    _validate_db_file(db_file)
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn


def _table_columns(conn: sqlite3.Connection, table_name: str) -> List[str]:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    cols = [row["name"] for row in cur.fetchall()]
    return cols


def _require_columns(conn: sqlite3.Connection, table_name: str, required: List[str]) -> None:
    cols = set(_table_columns(conn, table_name))
    missing = [c for c in required if c not in cols]
    if missing:
        _logger.error(
            "Schema mismatch for table {}. Missing columns: {}. Available: {}",
            table_name,
            missing,
            sorted(cols),
        )
        raise RuntimeError(f"Schema mismatch for table {table_name}. Missing columns: {missing}")


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ---------------------------------------------------------------------
# Deterministic computations (billing models)
# ---------------------------------------------------------------------

def _get_customer_current_rate(conn: sqlite3.Connection, state: str, rate_class: str, current_rate_type: str) -> Optional[Dict[str, Any]]:
    """
    Get customer's current rate from existing_rates table.
    Returns None if rate not found (will fall back to hardcoded baseline).
    """
    try:
        cur = conn.cursor()
        # Map rate_type values: "tou" -> "tou", "time_of_use" -> "tou", "flat" -> "flat", "tiered" -> "tiered"
        rate_type_map = {
            "flat": "flat",
            "tiered": "tiered",
            "tou": "tou",
            "time_of_use": "tou",
            "demand": "demand"
        }
        mapped_rate_type = rate_type_map.get(current_rate_type.lower(), current_rate_type.lower())
        
        cur.execute("""
            SELECT rate_name, rate_class, rate_type, fixed_charge, energy_charge,
                   tier_1_price, tier_1_limit_kwh, tier_2_price, tier_2_limit_kwh,
                   tier_3_price, tou_peak_price, tou_offpeak_price, tou_peak_hours,
                   demand_charge_per_kw, description
            FROM existing_rates
            WHERE state = ? AND rate_class = ? AND rate_type = ?
            LIMIT 1
        """, [state, rate_class, mapped_rate_type])
        
        row = cur.fetchone()
        if row:
            return dict(row)
        return None
    except Exception as e:
        _logger.warning("Failed to get customer current rate: state={}, rate_class={}, rate_type={}, error={}", 
                       state, rate_class, current_rate_type, str(e))
        return None


def _bill_baseline(total_kwh: float, customer_rate: Optional[Dict[str, Any]] = None, max_interval_kwh: float = 0.0, interval_count: int = 0) -> float:
    """
    Calculate baseline bill based on customer's current rate.
    If customer_rate is provided, use it; otherwise fall back to hardcoded baseline.
    """
    if customer_rate:
        rate_type = customer_rate.get("rate_type", "flat")
        fixed_charge = _safe_float(customer_rate.get("fixed_charge"), 11.0)
        
        if rate_type == "flat":
            energy_charge = _safe_float(customer_rate.get("energy_charge"), 0.12)
            return fixed_charge + (energy_charge * total_kwh)
        elif rate_type == "tiered":
            tier_1_price = _safe_float(customer_rate.get("tier_1_price"), 0.10)
            tier_1_limit = _safe_float(customer_rate.get("tier_1_limit_kwh"), 500.0)
            tier_2_price = _safe_float(customer_rate.get("tier_2_price"), 0.14)
            tier_2_limit = _safe_float(customer_rate.get("tier_2_limit_kwh"), 1000.0)
            
            tier1_kwh = min(total_kwh, tier_1_limit)
            tier2_kwh = min(max(0.0, total_kwh - tier_1_limit), tier_2_limit - tier_1_limit) if tier_2_limit > tier_1_limit else max(0.0, total_kwh - tier_1_limit)
            tier3_kwh = max(0.0, total_kwh - tier_2_limit) if tier_2_limit > tier_1_limit else 0.0
            tier_3_price = _safe_float(customer_rate.get("tier_3_price"), tier_2_price)
            
            return fixed_charge + (tier_1_price * tier1_kwh) + (tier_2_price * tier2_kwh) + (tier_3_price * tier3_kwh)
        elif rate_type in ("tou", "time_of_use"):
            tou_peak_price = _safe_float(customer_rate.get("tou_peak_price"), 0.20)
            tou_offpeak_price = _safe_float(customer_rate.get("tou_offpeak_price"), 0.10)
            
            # Use same peakiness calculation as _bill_tou
            avg = (total_kwh / interval_count) if interval_count else 0.0
            peakiness = 0.0
            if avg > 0:
                peakiness = max(0.0, min(1.0, (max_interval_kwh - avg) / avg))
            peak_share = min(0.6, 0.2 + 0.4 * peakiness)
            peak_kwh = total_kwh * peak_share
            off_kwh = total_kwh - peak_kwh
            
            return fixed_charge + (tou_peak_price * peak_kwh) + (tou_offpeak_price * off_kwh)
        else:
            # Fallback to flat rate calculation
            energy_charge = _safe_float(customer_rate.get("energy_charge"), 0.12)
            return fixed_charge + (energy_charge * total_kwh)
    
    # Fallback: hardcoded baseline for backward compatibility
    return 11.0 + (0.12 * total_kwh)


def _bill_flat(opt: _RateOption, total_kwh: float, income_qualified_flag: int) -> float:
    bill = opt.fixed_charge + (opt.energy_charge * total_kwh)
    # Handle income-qualified credits if encoded in description or assumptions (deterministic)
    # Check for common credit amounts: $15, $20, $25
    credit = 0.0
    desc = (opt.description or "").lower()
    assumptions_text = " ".join(opt.assumptions or []).lower() if opt.assumptions else ""
    combined_text = f"{desc} {assumptions_text}"
    
    if income_qualified_flag == 1 and "income" in combined_text:
        # Check for credit amounts in description or assumptions
        if "$15" in combined_text or "15/month" in combined_text or "15 per month" in combined_text:
            credit = 15.0
        elif "$20" in combined_text or "20/month" in combined_text or "20 per month" in combined_text:
            credit = 20.0
        elif "$25" in combined_text or "25/month" in combined_text or "25 per month" in combined_text:
            credit = 25.0
    
    bill = bill - credit
    # Note: demand_charge is added in the simulation loop (after this function) because it requires max_interval_kwh
    return max(0.0, bill)


def _bill_tiered(opt: _RateOption, total_kwh: float, income_qualified_flag: int) -> float:
    t1 = (opt.tier_structure or {}).get("tier_1", {}) or {}
    t2 = (opt.tier_structure or {}).get("tier_2", {}) or {}

    r1 = _safe_float(t1.get("rate"), opt.energy_charge)
    r2 = _safe_float(t2.get("rate"), opt.energy_charge)

    upper1 = 0.0
    rng = (t1.get("kwh_range", "") or "").replace(" ", "")
    if "-" in rng:
        try:
            upper1 = float(rng.split("-", 1)[1])
        except Exception:
            upper1 = 500.0
    if upper1 <= 0:
        upper1 = 500.0

    tier1_kwh = min(total_kwh, upper1)
    tier2_kwh = max(0.0, total_kwh - tier1_kwh)

    # Demo: tiered option may include an income-qualified credit encoded by design conventions:
    # - If description contains "$20" and "income" and customer is qualified => apply 20.
    # This is still deterministic, but avoids requiring another schema field.
    credit = 0.0
    desc = (opt.description or "").lower()
    if income_qualified_flag == 1 and "income" in desc and "$20" in desc:
        credit = 20.0

    bill = opt.fixed_charge + (r1 * tier1_kwh) + (r2 * tier2_kwh) - credit
    # Note: demand_charge is added in the simulation loop (after this function) because it requires max_interval_kwh
    return max(0.0, bill)


def _bill_tou(opt: _RateOption, total_kwh: float, max_interval_kwh: float, interval_count: int, income_qualified_flag: int) -> float:
    tou = opt.tou_structure or {}
    r_peak = _safe_float((tou.get("peak", {}) or {}).get("rate"), 0.20)
    r_off = _safe_float((tou.get("off_peak", {}) or {}).get("rate"), 0.10)

    avg = (total_kwh / interval_count) if interval_count else 0.0
    peakiness = 0.0
    if avg > 0:
        peakiness = max(0.0, min(1.0, (max_interval_kwh - avg) / avg))
    peak_share = min(0.6, 0.2 + 0.4 * peakiness)  # 20%-60%
    peak_kwh = total_kwh * peak_share
    off_kwh = total_kwh - peak_kwh

    bill = opt.fixed_charge + (r_peak * peak_kwh) + (r_off * off_kwh)

    # Demo: TOU option includes $25 income-qualified credit if encoded in description
    desc = (opt.description or "").lower()
    if income_qualified_flag == 1 and "income" in desc and "$25" in desc:
        bill -= 25.0
    # Note: demand_charge is added in the simulation loop (after this function) because it requires max_interval_kwh
    return max(0.0, bill)


# ---------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------

@pipeline_tool(toolkit="rate_case", name="rate_case_validate_and_summarize")
def rate_case_validate_and_summarize(
    db_file: str, 
    target_state: str, 
    target_rate_class: Optional[str] = None,
    target_rate_type: Optional[str] = None
) -> Dict[str, Any]:
    """Validate schema + return compact dataset summary for the given target_state.
    
    Optionally filters segments by target_rate_class and target_rate_type.
    If target_rate_class or target_rate_type is "all" or None, that filter is not applied.
    """
    _logger.input("rate_case_validate_and_summarize INPUT: db_file={}, target_state={}, target_rate_class={}, target_rate_type={}", 
                  db_file, target_state, target_rate_class, target_rate_type)

    conn = _connect(db_file)
    try:
        # Validate minimal schema used by the pipeline
        _require_columns(conn, "customer_master", ["customer_id", "rate_class", "current_rate_type", "income_qualified_flag", "state", "service_start_date"])
        _require_columns(conn, "interval_usage", ["customer_id", "timestamp", "kwh"])
        _require_columns(conn, "demographics_equity", ["customer_id", "income_band", "senior_flag", "housing_burden_index"])
        _require_columns(conn, "existing_rates", ["rate_name", "state", "rate_class", "rate_type", "fixed_charge"])
        _require_columns(conn, "voice_of_customer", ["id", "text_type", "content"])

        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) AS n FROM customer_master WHERE state = ?", [target_state])
        target_customers_row = cur.fetchone()
        target_customers = int(target_customers_row["n"]) if target_customers_row else 0

        cur.execute("SELECT MIN(service_start_date) AS start, MAX(service_start_date) AS end FROM customer_master WHERE state = ?", [target_state])
        cm_range = dict(cur.fetchone() or {})

        cur.execute(
            """
            SELECT COUNT(*) AS n,
                   MIN(iu.timestamp) AS start,
                   MAX(iu.timestamp) AS end,
                   COUNT(DISTINCT iu.customer_id) AS unique_customers
            FROM interval_usage iu
            INNER JOIN customer_master cm ON cm.customer_id = iu.customer_id
            WHERE cm.state = ?
            """,
            [target_state],
        )
        iu = dict(cur.fetchone() or {})

        cur.execute("SELECT COUNT(*) AS n FROM demographics_equity de INNER JOIN customer_master cm ON cm.customer_id = de.customer_id WHERE cm.state = ?", [target_state])
        de_row = cur.fetchone()
        de_n = int(de_row["n"]) if de_row else 0

        cur.execute("SELECT COUNT(*) AS n, GROUP_CONCAT(DISTINCT state) AS states FROM existing_rates")
        er = dict(cur.fetchone() or {})
        states = [s for s in (er.get("states") or "").split(",") if s]

        cur.execute("SELECT text_type, COUNT(*) AS n FROM voice_of_customer GROUP BY text_type")
        voc_dist = {row["text_type"]: int(row["n"]) for row in cur.fetchall()}

        # Read customer segments from database (if table exists)
        # Filter by target_rate_class and target_rate_type if provided (and not "all")
        customer_segments = []
        price_elasticity_estimates = {}
        try:
            # Build WHERE clause with optional filters
            where_clauses = ["state = ?"]
            params = [target_state]
            
            if target_rate_class and target_rate_class.lower() != "all":
                where_clauses.append("rate_class = ?")
                params.append(target_rate_class.lower())
            
            if target_rate_type and target_rate_type.lower() != "all":
                where_clauses.append("rate_type = ?")
                params.append(target_rate_type.lower())
            
            where_sql = " AND ".join(where_clauses)
            
            _logger.debug("Querying customer_segments with WHERE: {} and params: {}", where_sql, params)
            
            cur.execute(f"""
                SELECT segment_id, segment_name, rate_class, rate_type, price_elasticity, avg_annual_kwh,
                       characteristics_json, demographics_summary_json,
                       (SELECT COUNT(*) FROM customer_segment_membership csm WHERE csm.segment_id = cs.segment_id) as customer_count
                FROM customer_segments cs
                WHERE {where_sql}
                ORDER BY segment_id
            """, params)
            segment_rows = cur.fetchall()
            
            _logger.debug("Found {} segment rows from database", len(segment_rows))
            
            for row in segment_rows:
                try:
                    characteristics = json.loads(row["characteristics_json"]) if row["characteristics_json"] else {}
                    demographics_summary = json.loads(row["demographics_summary_json"]) if row["demographics_summary_json"] else {}
                except (json.JSONDecodeError, TypeError):
                    characteristics = {}
                    demographics_summary = {}
                
                segment_data = {
                    "segment_id": row["segment_id"],
                    "segment_name": row["segment_name"],
                    "rate_class": row["rate_class"],
                    "rate_type": row["rate_type"],
                    "customer_count": int(row["customer_count"]) if row["customer_count"] else 0,
                    "characteristics": characteristics,
                    "price_elasticity": _safe_float(row["price_elasticity"]),
                    "avg_annual_kwh": _safe_float(row["avg_annual_kwh"]),
                    "demographics_summary": demographics_summary,
                }
                customer_segments.append(segment_data)
                price_elasticity_estimates[row["segment_id"]] = _safe_float(row["price_elasticity"])
            
            _logger.info("Found {} customer segments for state={}, rate_class={}, rate_type={}", 
                        len(customer_segments), target_state, target_rate_class, target_rate_type)
        except sqlite3.OperationalError as e:
            # Table might not exist
            _logger.warning("Table customer_segments might not exist: {}", e)
            customer_segments = []
            price_elasticity_estimates = {}
        except Exception as e:
            # Other errors - log with full traceback
            _logger.error("Error reading customer segments: {}", e)
            import traceback
            _logger.error("Traceback: {}", traceback.format_exc())
            customer_segments = []
            price_elasticity_estimates = {}

        out = {
            "ok": True,
            "db_file": db_file,
            "target_state": target_state,
            "counts": {
                "customer_master_target_state": target_customers,
                "interval_usage_target_state": int(iu.get("n") or 0),
                "interval_usage_unique_customers_target_state": int(iu.get("unique_customers") or 0),
                "demographics_equity_target_state": de_n,
                "existing_rates_total": int(er.get("n") or 0),
                "voice_of_customer_by_type": voc_dist,
            },
            "date_ranges": {
                "customer_master_service_start_date": cm_range,
                "interval_usage_timestamp": {"start": iu.get("start"), "end": iu.get("end")},
            },
            "existing_rates_states_covered": states,
            "customer_segments": customer_segments,
            "price_elasticity_estimates": price_elasticity_estimates,
        }
        _logger.output("rate_case_validate_and_summarize OUTPUT: ok=true")
        return out
    finally:
        conn.close()


@pipeline_tool(toolkit="rate_case", name="rate_case_record_pipeline_run")
def rate_case_record_pipeline_run(
    db_file: str,
    target_state: str,
    status: str = "running",
    run_id: Optional[str] = None,
    summary: Optional[str] = None,
    file_path: Optional[str] = None,
    recommended_option_id: Optional[str] = None,
    recommended_option_name: Optional[str] = None,
    final_option_id: Optional[str] = None,
    final_option_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Create or update a pipeline_runs entry to track pipeline execution.
    
    For creating a new entry:
    - target_state: Required. The state for which rate case analysis is being performed.
    - status: Optional. Defaults to "running".
    - run_id: Optional. If not provided, will be auto-generated.
    - summary: Optional. Summary of the pipeline run.
    
    For updating an existing entry (e.g., when completing the pipeline or marking as unsupported):
    - run_id: Required. The run_id of the entry to update.
    - target_state: Required. Must match the existing entry's target_state (validated).
    - status: Required. New status (e.g., "completed", "unsupported", "failed").
    - summary: Required when status is "completed" or "unsupported". Summary of the pipeline execution or reason for unsupported status.
    - file_path: Optional. Path to the consolidated report file.
    - recommended_option_id: Optional. The option_id that was recommended by the recommender.
    - recommended_option_name: Optional. The option_name that was recommended.
    - final_option_id: Optional. The option_id that was finally selected by the user.
    - final_option_name: Optional. The option_name that was finally selected.
    """
    _logger.input(
        "rate_case_record_pipeline_run INPUT: db_file={}, target_state={}, status={}, run_id={}",
        db_file,
        target_state,
        status,
        run_id,
    )

    conn = _connect(db_file)
    try:
        cur = conn.cursor()
        
        # If run_id is provided, check if it exists for update
        if run_id:
            cur.execute("SELECT run_id, target_state FROM pipeline_runs WHERE run_id = ?", [run_id])
            existing = cur.fetchone()
            
            if existing:
                # Validate target_state matches (for updates)
                existing_target_state = existing["target_state"]
                if existing_target_state != target_state:
                    _logger.warning(
                        "target_state mismatch for run_id {}: existing={}, provided={}. Using existing value.",
                        run_id,
                        existing_target_state,
                        target_state,
                    )
                    target_state = existing_target_state
                
                # Update existing entry
                if status in ("completed", "unsupported") and not summary:
                    raise ValueError(f"summary is required when status is '{status}'")
                cur.execute(
                    """
                    UPDATE pipeline_runs
                    SET status = ?, summary = ?, file_path = ?, 
                        recommended_option_id = ?, recommended_option_name = ?,
                        final_option_id = ?, final_option_name = ?,
                        completed_at = CASE 
                            WHEN status NOT IN ('completed', 'unsupported') AND ? IN ('completed', 'unsupported') 
                            THEN CURRENT_TIMESTAMP 
                            ELSE completed_at 
                        END
                    WHERE run_id = ?
                    """,
                    [
                        status,
                        summary,
                        file_path,
                        recommended_option_id,
                        recommended_option_name,
                        final_option_id,
                        final_option_name,
                        status,
                        run_id,
                    ],
                )
                operation = "update"
                conn.commit()
                out = {"ok": True, "run_id": run_id, "status": status, "operation": operation}
                _logger.output("rate_case_record_pipeline_run OUTPUT: ok=true, operation=update, run_id={}", run_id)
                return out
            # If run_id provided but doesn't exist, treat as new entry with provided run_id
        
        # Generate run_id if not provided
        if not run_id:
            # Sanitize target_state for run_id (replace spaces with underscores)
            sanitized_state = target_state.replace(" ", "_")
            run_id = f"run_{sanitized_state}_{_utc_iso()}"
        
        # Insert new entry (summary is required but can be empty string for initial creation)
        # Set completed_at if status is "completed" or "unsupported" at insert time
        cur.execute(
            """
            INSERT INTO pipeline_runs (run_id, target_state, status, summary, file_path, 
                                       recommended_option_id, recommended_option_name,
                                       final_option_id, final_option_name, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 
                    CASE WHEN ? IN ('completed', 'unsupported') THEN CURRENT_TIMESTAMP ELSE NULL END)
            """,
            [
                run_id,
                target_state,
                status,
                summary if summary is not None else "",
                file_path,
                recommended_option_id,
                recommended_option_name,
                final_option_id,
                final_option_name,
                status,  # Used in CASE statement
            ],
        )
        operation = "insert"
        conn.commit()
        out = {"ok": True, "run_id": run_id, "target_state": target_state, "status": status, "operation": operation}
        _logger.output("rate_case_record_pipeline_run OUTPUT: ok=true, operation=insert, run_id={}", run_id)
        return out
    finally:
        conn.close()


@pipeline_tool(toolkit="rate_case", name="rate_case_build_customer_segments")
def rate_case_build_customer_segments(
    db_file: str, 
    target_state: str,
    target_rate_class: Optional[str] = None,
    target_rate_type: Optional[str] = None
) -> Dict[str, Any]:
    """Read pre-computed customer segments from database. Segments are generated during mock data setup.
    
    Returns segments for the target state from the customer_segments table.
    Optionally filters by target_rate_class and target_rate_type.
    If target_rate_class or target_rate_type is "all" or None, that filter is not applied.
    """
    _logger.input("rate_case_build_customer_segments INPUT: db_file={}, target_state={}, target_rate_class={}, target_rate_type={}", 
                  db_file, target_state, target_rate_class, target_rate_type)

    conn = _connect(db_file)
    try:
        cur = conn.cursor()
        
        # Check if customer_segments table exists
        cur.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='customer_segments'
        """)
        table_exists = cur.fetchone() is not None
        
        if not table_exists:
            _logger.warning("customer_segments table does not exist. Please run setup script to generate segments.")
            return {
                "ok": False,
                "segments": [],
                "rows_written": 0,
                "error": "customer_segments table not found. Run setup script to generate segments."
            }
        
        # Read segments from database for target state
        # Filter by target_rate_class and target_rate_type if provided (and not "all")
        where_clauses = ["state = ?"]
        params = [target_state]
        
        if target_rate_class and target_rate_class.lower() != "all":
            where_clauses.append("rate_class = ?")
            params.append(target_rate_class.lower())
        
        if target_rate_type and target_rate_type.lower() != "all":
            where_clauses.append("(rate_type = ? OR rate_type IS NULL)")
            params.append(target_rate_type.lower())
        
        where_sql = " AND ".join(where_clauses)
        
        cur.execute(f"""
            SELECT segment_id, segment_name, rate_class, rate_type, price_elasticity, avg_annual_kwh,
                   characteristics_json, demographics_summary_json,
                   (SELECT COUNT(*) FROM customer_segment_membership csm WHERE csm.segment_id = cs.segment_id) as customer_count
            FROM customer_segments cs
            WHERE {where_sql}
            ORDER BY segment_id
        """, params)
        
        rows = cur.fetchall()
        
        if not rows:
            _logger.warning("No segments found for target_state={}. Segments may need to be regenerated.", target_state)
            return {
                "ok": True,
                "segments": [],
                "rows_written": 0,
            }
        
        # Parse segments
        segments = []
        for row in rows:
            try:
                characteristics = json.loads(row["characteristics_json"]) if row["characteristics_json"] else {}
                demographics_summary = json.loads(row["demographics_summary_json"]) if row["demographics_summary_json"] else {}
            except (json.JSONDecodeError, TypeError):
                characteristics = {}
                demographics_summary = {}
            
            segments.append({
                "segment_id": row["segment_id"],
                "segment_name": row["segment_name"],
                "rate_class": row["rate_class"],
                "rate_type": row["rate_type"],
                "customer_count": int(row["customer_count"]) if row["customer_count"] else 0,
                "characteristics": characteristics,
                "price_elasticity": _safe_float(row["price_elasticity"]),
                "avg_annual_kwh": _safe_float(row["avg_annual_kwh"]),
                "demographics_summary": demographics_summary,
            })
        
        _logger.output("rate_case_build_customer_segments OUTPUT: segments={}", len(segments))
        return {
            "ok": True,
            "segments": segments,
            "rows_written": len(segments),
        }
    finally:
        conn.close()


@pipeline_tool(toolkit="rate_case", name="rate_case_get_baseline_rates")
def rate_case_get_baseline_rates(db_file: str, target_state: str) -> Dict[str, Any]:
    """
    Get baseline/current rate structures for the target state from the existing_rates table.
    Returns representative baseline rates (typically the most common residential rate) for use in rate design.
    """
    _logger.input("rate_case_get_baseline_rates INPUT: db_file={}, target_state={}", db_file, target_state)
    
    conn = _connect(db_file)
    try:
        cur = conn.cursor()
        
        # Get the most common residential rate for the target state (typically used as baseline)
        # Prefer flat rates, then tiered, then TOU
        cur.execute("""
            SELECT rate_name, rate_class, rate_type, fixed_charge, energy_charge,
                   tier_1_price, tier_1_limit_kwh, tier_2_price, tier_2_limit_kwh,
                   tou_peak_price, tou_offpeak_price, tou_peak_hours, demand_charge_per_kw,
                   description
            FROM existing_rates
            WHERE state = ? AND rate_class = 'residential'
            ORDER BY 
                CASE rate_type 
                    WHEN 'flat' THEN 1
                    WHEN 'tiered' THEN 2
                    WHEN 'time_of_use' THEN 3
                    ELSE 4
                END,
                fixed_charge ASC
            LIMIT 1
        """, [target_state])
        
        baseline_rate = dict(cur.fetchone() or {})
        
        if not baseline_rate:
            # Fallback: use hardcoded baseline if no rates found in database
            _logger.warning("No baseline rates found in database for state={}, using hardcoded baseline", target_state)
            baseline_rate = {
                "rate_name": "Default Baseline",
                "rate_class": "residential",
                "rate_type": "flat",
                "fixed_charge": 11.0,
                "energy_charge": 0.12,
                "description": "Default baseline rate (no rates found in database)"
            }
        else:
            # If energy_charge is None but we have tier prices, use tier_1_price as baseline energy charge
            if baseline_rate.get("energy_charge") is None and baseline_rate.get("tier_1_price"):
                baseline_rate["energy_charge"] = baseline_rate.get("tier_1_price")
        
        # Calculate representative baseline for flat rate comparison
        # Use fixed_charge and energy_charge (or tier_1_price if energy_charge is None)
        baseline_fixed = _safe_float(baseline_rate.get("fixed_charge"), 11.0)
        baseline_energy = _safe_float(baseline_rate.get("energy_charge") or baseline_rate.get("tier_1_price"), 0.12)
        
        out = {
            "ok": True,
            "target_state": target_state,
            "baseline_rate": baseline_rate,
            "baseline_fixed_charge": baseline_fixed,
            "baseline_energy_charge": baseline_energy,
            "guidance": {
                "for_plus_10_pct": {
                    "fixed_charge": round(baseline_fixed * 1.10, 2),
                    "energy_charge": round(baseline_energy * 1.10, 4)
                },
                "for_minus_10_pct": {
                    "fixed_charge": round(baseline_fixed * 0.90, 2),
                    "energy_charge": round(baseline_energy * 0.90, 4)
                },
                "for_zero_change": {
                    "fixed_charge": baseline_fixed,
                    "energy_charge": baseline_energy
                }
            }
        }
        
        _logger.output("rate_case_get_baseline_rates OUTPUT: baseline_fixed={}, baseline_energy={}", baseline_fixed, baseline_energy)
        return out
    finally:
        conn.close()


@pipeline_tool(toolkit="rate_case", name="rate_case_validate_options")
def rate_case_validate_options(
    db_file: str,
    target_state: str,
    rate_design_options: List[Dict[str, Any]],
    revenue_target: float = 5.0,
) -> Dict[str, Any]:
    """
    Validate rate design options by running quick simulations to estimate revenue and bill impacts.
    Options are validated based on how close they are to the revenue_target (default: 5.0% YoY growth).
    Closer to target is better - options that exceed the target significantly will be penalized.
    
    Returns validated options, rejected options with reasons, and options formatted for HITL gate.
    """
    _logger.input(
        "rate_case_validate_options INPUT: db_file={}, target_state={}, option_count={}",
        db_file,
        target_state,
        len(rate_design_options) if rate_design_options else 0,
    )
    
    if not rate_design_options:
        raise RuntimeError("rate_design_options is required and cannot be empty")
    
    conn = _connect(db_file)
    try:
        cur = conn.cursor()
        
        # Use the same sample size as full simulation (2500) to ensure validation accuracy
        # This ensures validation results match full simulation results
        sample_limit = 2500
        
        # Aggregate interval usage per customer in target state (same sample as full simulation)
        # Use ORDER BY to ensure deterministic sampling - same customers every time
        # Include current_rate_type, state, and demographics for detailed breakdowns
        q = """
            SELECT iu.customer_id,
                   cm.rate_class AS rate_class,
                   cm.current_rate_type AS current_rate_type,
                   cm.state AS state,
                   cm.income_qualified_flag AS income_qualified_flag,
                   de.senior_flag AS senior_flag,
                   de.housing_burden_index AS housing_burden_index,
                   SUM(iu.kwh) AS total_kwh,
                   MAX(iu.kwh) AS max_interval_kwh,
                   COUNT(*) AS interval_count
            FROM interval_usage iu
            INNER JOIN customer_master cm ON cm.customer_id = iu.customer_id
            LEFT JOIN demographics_equity de ON de.customer_id = cm.customer_id
            WHERE cm.state = ?
            GROUP BY iu.customer_id, cm.rate_class, cm.current_rate_type, cm.state, cm.income_qualified_flag,
                     de.senior_flag, de.housing_burden_index
            ORDER BY iu.customer_id
            LIMIT ?
        """
        cur.execute(q, [target_state, sample_limit])
        all_customers = [dict(r) for r in cur.fetchall()]
        
        if not all_customers:
            raise RuntimeError(f"No interval usage rows found for target_state={target_state}")
        
        validated_options: List[Dict[str, Any]] = []
        rejected_options: List[Dict[str, Any]] = []
        gate_options: List[Dict[str, Any]] = []
        
        for opt_data in rate_design_options:
            option_id = opt_data.get("option_id", "")
            option_name = opt_data.get("option_name", "")
            
            try:
                # Create rate option object
                # CRITICAL: Preserve rate_class from opt_data - don't default to "all" if it's missing
                # The rate designer should always provide rate_class, but if missing, preserve None to detect the issue
                opt_rate_class = opt_data.get("rate_class")
                if not opt_rate_class or opt_rate_class.lower() == "all":
                    # Only default to "all" if explicitly set to "all" or truly missing
                    opt_rate_class = opt_data.get("rate_class", "all")
                opt = _RateOption(
                    option_id=option_id,
                    option_name=option_name,
                    rate_class=opt_rate_class,
                    rate_type=opt_data.get("rate_type", "flat"),
                    fixed_charge=_safe_float(opt_data.get("fixed_charge")),
                    energy_charge=_safe_float(opt_data.get("energy_charge")),
                    tier_structure=opt_data.get("tier_structure") or {},
                    tou_structure=opt_data.get("tou_structure") or {},
                    demand_charge=_safe_float(opt_data.get("demand_charge")),
                    assumptions=opt_data.get("assumptions") or [],
                    description=opt_data.get("description") or "",
                )
                
                # Filter customers by rate type match (Option B: only customers on matching rate types are impacted)
                # Map rate_type: "time_of_use" -> "tou", others stay the same
                opt_rate_type = opt.rate_type.lower()
                if opt_rate_type == "time_of_use":
                    opt_rate_type = "tou"
                
                matching_customers = [
                    c for c in all_customers
                    if c.get("current_rate_type", "flat").lower() == opt_rate_type
                ]
                
                if not matching_customers:
                    _logger.warning("No customers found with matching rate type for option {} (rate_type={})", option_id, opt.rate_type)
                    # Still process but log warning
                    matching_customers = all_customers
                
                # Quick simulation for validation (only on matching customers)
                bills_before: List[float] = []
                bills_after: List[float] = []
                total_revenue_before = 0.0
                total_revenue_after = 0.0
                
                for c in matching_customers:
                    total_kwh = _safe_float(c.get("total_kwh"))
                    max_interval_kwh = _safe_float(c.get("max_interval_kwh"))
                    interval_count = int(_safe_float(c.get("interval_count")))
                    inc_q = int(_safe_float(c.get("income_qualified_flag")))
                    customer_state = c.get("state", target_state)
                    rate_class = c.get("rate_class", "residential")
                    current_rate_type = c.get("current_rate_type", "flat")
                    
                    # Get customer's current rate from existing_rates table
                    customer_rate = _get_customer_current_rate(conn, customer_state, rate_class, current_rate_type)
                    
                    bill_before = _bill_baseline(total_kwh, customer_rate, max_interval_kwh, interval_count)
                    
                    if opt.rate_type == "flat":
                        bill_after = _bill_flat(opt, total_kwh, inc_q)
                    elif opt.rate_type == "tiered":
                        bill_after = _bill_tiered(opt, total_kwh, inc_q)
                    else:
                        bill_after = _bill_tou(opt, total_kwh, max_interval_kwh, interval_count, inc_q)
                    
                    # Add demand charge if specified (applies to all rate types)
                    if opt.demand_charge > 0.0:
                        peak_demand_kw = max_interval_kwh  # max_interval_kwh is already peak demand in kW
                        bill_after += opt.demand_charge * peak_demand_kw
                    
                    bills_before.append(bill_before)
                    bills_after.append(bill_after)
                    total_revenue_before += bill_before
                    total_revenue_after += bill_after
                
                avg_bill_before = sum(bills_before) / len(bills_before) if bills_before else 0.0
                avg_bill_after = sum(bills_after) / len(bills_after) if bills_after else 0.0
                avg_bill_change_pct = ((avg_bill_after - avg_bill_before) / avg_bill_before * 100.0) if avg_bill_before > 0 else 0.0
                revenue_change_pct = ((total_revenue_after - total_revenue_before) / total_revenue_before * 100.0) if total_revenue_before > 0 else 0.0
                
                # Enhanced validation criteria based on revenue_target:
                # 1. Revenue should be close to revenue_target (within ±5% of target)
                # 2. Minimum impact threshold: Must have at least ±1% impact (reject 0% or near-0% rates)
                # 3. Additional quality checks:
                #    - Revenue distance from target (closer to target is better)
                #    - Bill impact distribution (check for extreme outliers)
                #    - Rate structure complexity (simpler is better for customer satisfaction)
                
                # Minimum impact threshold: reject rates with <1% impact (too close to baseline)
                MIN_IMPACT_THRESHOLD = 1.0  # At least ±1% impact required
                has_minimum_impact = abs(revenue_change_pct) >= MIN_IMPACT_THRESHOLD or abs(avg_bill_change_pct) >= MIN_IMPACT_THRESHOLD
                
                # Calculate distance from revenue_target
                revenue_distance_from_target = abs(revenue_change_pct - revenue_target)
                
                # Validation: revenue should be within ±2 percentage points of target, and have minimum impact
                # Bill impact limit removed - no longer rejecting based on bill impact
                basic_validated = (
                    revenue_distance_from_target <= 2.0 and  # Within ±2 percentage points of revenue_target (e.g., if target is 12%, valid range is 10% to 14%)
                    has_minimum_impact  # Must have at least ±1% impact
                )
                
                # Calculate quality scores for ranking
                # Revenue score: Based on distance from revenue_target (closer is better)
                # CRITICAL: Options that EXCEED the target are penalized more than options below target
                # This ensures "not more than target" preference
                if revenue_change_pct <= revenue_target:
                    # Below or at target: normal distance scoring
                    if revenue_distance_from_target <= 1.0:
                        revenue_score = 100.0 - (revenue_distance_from_target * 5.0)  # 95-100 for 0-1% distance
                    elif revenue_distance_from_target <= 3.0:
                        revenue_score = 95.0 - ((revenue_distance_from_target - 1.0) * 5.0)  # 80-95 for 1-3% distance
                    elif revenue_distance_from_target <= 5.0:
                        revenue_score = 80.0 - ((revenue_distance_from_target - 3.0) * 2.5)  # 75-80 for 3-5% distance
                    else:
                        # Beyond ±5% of target - harsher penalty
                        revenue_score = max(0.0, 75.0 - ((revenue_distance_from_target - 5.0) * 3.0))
                else:
                    # EXCEEDS target: apply additional penalty (prefer options below target)
                    # Example: if target is 8%, then 5.3% scores better than 10% even though 10% is closer
                    excess_penalty = (revenue_change_pct - revenue_target) * 3.0  # 3 points per % over target
                    if revenue_distance_from_target <= 1.0:
                        base_score = 100.0 - (revenue_distance_from_target * 5.0)
                    elif revenue_distance_from_target <= 3.0:
                        base_score = 95.0 - ((revenue_distance_from_target - 1.0) * 5.0)
                    elif revenue_distance_from_target <= 5.0:
                        base_score = 80.0 - ((revenue_distance_from_target - 3.0) * 2.5)
                    else:
                        base_score = max(0.0, 75.0 - ((revenue_distance_from_target - 5.0) * 3.0))
                    revenue_score = max(0.0, base_score - excess_penalty)
                
                # Bill score: More lenient scoring to produce 80-100 for validated options
                # Target: 80-100 for bill change ±10%
                abs_bill_change = abs(avg_bill_change_pct)
                if abs_bill_change <= 5.0:
                    bill_score = 100.0 - (abs_bill_change * 0.4)  # 98-100 for 0-5%
                elif abs_bill_change <= 10.0:
                    bill_score = 98.0 - ((abs_bill_change - 5.0) * 1.6)  # 90-98 for 5-10%
                else:
                    # Outside ±10% but still calculate for ranking
                    bill_score = max(0.0, 90.0 - ((abs_bill_change - 10.0) * 2.0))
                
                # Complexity score: simpler rate structures score higher
                complexity_penalty = 0.0
                if opt.rate_type == "flat":
                    complexity_score = 100.0  # Simplest
                elif opt.rate_type == "tiered":
                    complexity_score = 85.0  # Moderate complexity
                elif opt.rate_type == "time_of_use":
                    # Check if it's hybrid (tiered + TOU)
                    if opt.tier_structure:
                        complexity_score = 70.0  # Most complex
                    else:
                        complexity_score = 80.0  # TOU only
                else:
                    complexity_score = 60.0
                
                # Calculate bill distribution quality (penalize if many customers see large changes)
                # This is a proxy for equity - we want balanced impacts
                # More lenient: only penalize if >30% see extreme changes (>15%)
                large_increases = 0
                large_decreases = 0
                for idx, bill_after in enumerate(bills_after):
                    if idx < len(bills_before) and bills_before[idx] > 0:
                        bill_change_pct = ((bill_after - bills_before[idx]) / bills_before[idx] * 100.0)
                        if bill_change_pct > 15.0:
                            large_increases += 1
                        elif bill_change_pct < -15.0:
                            large_decreases += 1
                extreme_impact_pct = ((large_increases + large_decreases) / len(bills_after) * 100.0) if bills_after else 0.0
                # More lenient: start at 100, only penalize if >30% see extreme changes
                if extreme_impact_pct <= 30.0:
                    equity_proxy_score = 100.0 - (extreme_impact_pct * 1.0)  # 70-100 for 0-30%
                else:
                    equity_proxy_score = max(0.0, 70.0 - ((extreme_impact_pct - 30.0) * 1.5))  # Harsher penalty above 30%
                
                # Composite quality score (weighted)
                # Revenue: 35%, Bill: 35%, Complexity: 15%, Equity proxy: 15%
                quality_score = (
                    (0.35 * revenue_score) +
                    (0.35 * bill_score) +
                    (0.15 * complexity_score) +
                    (0.15 * equity_proxy_score)
                )
                
                # Enhanced validation: must pass basic criteria AND have quality score >= 70
                is_validated = basic_validated and quality_score >= 70.0
                
                # Build rejection reasons if not validated
                rejection_reasons = []
                if not basic_validated:
                    # Check minimum impact first
                    if abs(revenue_change_pct) < MIN_IMPACT_THRESHOLD and abs(avg_bill_change_pct) < MIN_IMPACT_THRESHOLD:
                        rejection_reasons.append("impact_too_low")
                    else:
                        # Check distance from revenue_target
                        if revenue_distance_from_target > 2.0:
                            if revenue_change_pct > revenue_target:
                                rejection_reasons.append("revenue_too_high_above_target")
                            else:
                                rejection_reasons.append("revenue_too_low_below_target")
                        # Bill impact limit removed - no longer rejecting based on bill impact
                if quality_score < 70.0:
                    rejection_reasons.append("quality_score_too_low")
                
                # Build option result with validation metadata and scores
                option_result = {
                    **opt_data,  # Include all original option data
                    "estimated_revenue_change_pct": round(revenue_change_pct, 2),
                    "estimated_avg_bill_change_pct": round(avg_bill_change_pct, 2),
                    "validated": is_validated,
                    "rejection_reasons": rejection_reasons if not is_validated else [],
                    "quality_score": round(quality_score, 2),
                    "revenue_score": round(revenue_score, 2),
                    "bill_score": round(bill_score, 2),
                    "complexity_score": round(complexity_score, 2),
                    "equity_proxy_score": round(equity_proxy_score, 2),
                }
                
                if is_validated:
                    validated_options.append(option_result)
                else:
                    rejected_options.append(option_result)
                
                # Format for HITL gate
                status_label = "✅ Validated" if is_validated else "❌ Rejected"
                reason_text = ""
                if rejection_reasons:
                    reason_parts = []
                    if "impact_too_low" in rejection_reasons:
                        reason_parts.append(f"Impact too low (Revenue {revenue_change_pct:+.1f}%, Bill {avg_bill_change_pct:+.1f}% - must be at least ±1%)")
                    else:
                        if "revenue_too_high_above_target" in rejection_reasons:
                            reason_parts.append(f"Revenue {revenue_change_pct:+.1f}% (target: {revenue_target:.1f}%, too far above)")
                        elif "revenue_too_low_below_target" in rejection_reasons:
                            reason_parts.append(f"Revenue {revenue_change_pct:+.1f}% (target: {revenue_target:.1f}%, too far below)")
                        if "bill_too_high" in rejection_reasons:
                            reason_parts.append(f"Bill +{avg_bill_change_pct:.1f}% (too high)")
                        elif "bill_too_low" in rejection_reasons:
                            reason_parts.append(f"Bill {avg_bill_change_pct:.1f}% (too low)")
                    reason_text = "; ".join(reason_parts)
                
                # Build description with quality score and ranking info
                description = f"{status_label}"
                if is_validated:
                    # Will be updated with rank after sorting
                    description += f": Revenue {revenue_change_pct:+.1f}% (target: {revenue_target:.1f}%, distance: {revenue_distance_from_target:.1f}%), Bill {avg_bill_change_pct:+.1f}%, Quality Score {quality_score:.1f}"
                else:
                    description += f": {reason_text}"
                    if quality_score < 70.0:
                        description += f" (Quality Score: {quality_score:.1f})"
                
                gate_options.append({
                    "value": option_id,
                    "label": f"{option_id} - {option_name}",
                    "description": description,
                    "selected": False,  # Will be updated to only select top 3 after ranking
                    "is_validated": is_validated,  # Store validation status
                    "quality_score": round(quality_score, 2),  # Store quality_score for all options (validated and rejected)
                    "rank": None,  # Will be set after ranking (all options will get ranks)
                    "revenue_impact_pct": round(revenue_change_pct, 2),
                    # Calculate uncertainty range for preliminary estimate
                    # Use fixed ±3 percentage points OR ±30% of estimate (whichever is larger), minimum ±2%
                    # This accounts for validation being a quick check that may differ from final simulation
                    "revenue_impact_range_min": round(revenue_change_pct - max(2.0, max(3.0, abs(revenue_change_pct) * 0.30)), 1),
                    "revenue_impact_range_max": round(revenue_change_pct + max(2.0, max(3.0, abs(revenue_change_pct) * 0.30)), 1),
                    # Note: bill_impact_pct removed - it's always the same as revenue_impact_pct and was redundant
                    "rate_class": opt.rate_class,  # Store rate class for display
                    "rate_type": opt.rate_type,  # Store rate type for display
                })
                
            except Exception as e:
                _logger.error("Error validating option {}: {}", option_id, e)
                
                # Mark as rejected with error reason
                rejected_options.append({
                    **opt_data,
                    "validated": False,
                    "rejection_reasons": ["validation_error"],
                    "error": str(e),
                })
                gate_options.append({
                    "value": option_id,
                    "label": f"{option_id} - {option_name}",
                    "description": f"❌ Rejected: Validation error - {str(e)}",
                    "selected": False,
                    "is_validated": False,  # Store validation status
                    "rank": None,  # Will be set after ranking
                    "quality_score": None,
                    "revenue_impact_pct": None,
                    "revenue_impact_range_min": None,
                    "revenue_impact_range_max": None,
                    # Note: bill_impact_pct removed - it's always the same as revenue_impact_pct
                })
        
        # Rank ALL options (validated + rejected) by quality score (highest first)
        # Combine all options with their validation status for ranking
        all_options_for_ranking = []
        for opt in validated_options:
            all_options_for_ranking.append({
                "option_id": opt.get("option_id"),
                "quality_score": opt.get("quality_score", 0.0),
                "is_validated": True,
                "option_data": opt
            })
        for opt in rejected_options:
            all_options_for_ranking.append({
                "option_id": opt.get("option_id"),
                "quality_score": opt.get("quality_score", 0.0),
                "is_validated": False,
                "option_data": opt
            })
        
        # Sort all options by quality score (highest first)
        all_options_for_ranking.sort(key=lambda x: x.get("quality_score", 0.0), reverse=True)
        
        # Create a mapping of option_id to rank and validation status
        # IMPORTANT: Rank ALL options by quality score (highest first), regardless of validation status
        # This allows users to see the relative quality of all options, even if they don't meet validation criteria
        option_rank_map = {}
        rank_counter = 1
        for opt_info in all_options_for_ranking:
            option_id = str(opt_info.get("option_id", ""))
            is_validated = opt_info.get("is_validated", False)
            
            # Assign ranks to ALL options (validated and rejected) by quality score
            option_rank_map[option_id] = {
                "rank": rank_counter,
                "is_validated": is_validated,
                "option_data": opt_info.get("option_data", {})
            }
            rank_counter += 1
        
        # Update gate options with ranking info for ALL options
        for gate_opt in gate_options:
            option_id = str(gate_opt.get("value", ""))
            rank_info = option_rank_map.get(option_id)
            
            if rank_info:
                rank = rank_info["rank"]
                is_validated = rank_info["is_validated"]
                opt_data = rank_info["option_data"]
                
                # Set rank for ALL options (validated and rejected)
                if rank is not None:
                    gate_opt["rank"] = int(rank)
                else:
                    gate_opt["rank"] = None
                gate_opt["is_validated"] = is_validated  # Store validation status
                gate_opt["quality_score"] = round(opt_data.get("quality_score", 0.0), 2)
                # CRITICAL: Preserve existing revenue_impact_pct from gate_opt if it exists, otherwise use opt_data
                # This ensures we don't lose the original value that was set when creating gate_options
                existing_revenue_pct = gate_opt.get("revenue_impact_pct")
                if existing_revenue_pct is not None:
                    revenue_pct = round(float(existing_revenue_pct), 2)
                else:
                    revenue_pct = round(opt_data.get("estimated_revenue_change_pct", 0.0), 2)
                gate_opt["revenue_impact_pct"] = revenue_pct
                # CRITICAL: Always recalculate uncertainty range for preliminary estimate
                # Use fixed ±3 percentage points OR ±30% of estimate (whichever is larger), minimum ±2%
                # This ensures range is always present and correct
                if revenue_pct is not None and isinstance(revenue_pct, (int, float)):
                    uncertainty_pct = max(2.0, max(3.0, abs(float(revenue_pct)) * 0.30))
                    gate_opt["revenue_impact_range_min"] = round(float(revenue_pct) - uncertainty_pct, 1)
                    gate_opt["revenue_impact_range_max"] = round(float(revenue_pct) + uncertainty_pct, 1)
                    _logger.debug("Updated range for option {}: {:.1f}% - {:.1f}% (revenue_pct={:.2f}%)", 
                                 option_id, gate_opt["revenue_impact_range_min"], 
                                 gate_opt["revenue_impact_range_max"], revenue_pct)
                else:
                    _logger.warning("Option {} has invalid revenue_pct during ranking update (value={}, type={})", 
                                 option_id, revenue_pct, type(revenue_pct).__name__)
                    gate_opt["revenue_impact_range_min"] = None
                    gate_opt["revenue_impact_range_max"] = None
                # Note: bill_impact_pct removed - it's always the same as revenue_impact_pct and was redundant
                # CRITICAL: Preserve rate_class from the original opt_data (from rate designer)
                # The option_result includes **opt_data, so rate_class should be in opt_data
                # Only update if we have a valid rate_class from the original option data AND gate_opt doesn't already have a valid one
                original_rate_class = opt_data.get("rate_class")
                existing_rate_class = gate_opt.get("rate_class")
                # If we have a valid rate_class from opt_data (not "all"), use it
                if original_rate_class and original_rate_class.lower() != "all":
                    gate_opt["rate_class"] = original_rate_class
                # If gate_opt already has a valid rate_class (not "all"), preserve it
                elif existing_rate_class and existing_rate_class.lower() != "all":
                    # Keep existing rate_class
                    pass
                # Only default to "all" if neither exists
                elif "rate_class" not in gate_opt or not gate_opt.get("rate_class"):
                    gate_opt["rate_class"] = "all"
                
                original_rate_type = opt_data.get("rate_type")
                if original_rate_type and original_rate_type.lower() != "all":
                    gate_opt["rate_type"] = original_rate_type
                elif "rate_type" not in gate_opt:
                    gate_opt["rate_type"] = "flat"
                
                # Update option name to show actual calculated impact instead of design target
                # Remove design target from option name (e.g., "(+1.5% Revenue)", "(-2% Revenue)", "+10 bill", "_+ 10 bill")
                # Note: We no longer add revenue percentages or bill impacts to option names as they are misleading (validation estimates may differ significantly from final simulation)
                original_name = opt_data.get('option_name', '')
                # Remove design target patterns like:
                # - "(+1.5% Revenue)" or "(-2% Revenue)" - simple pattern
                # - "(0-500/501+ kWh, +6% Revenue)" - pattern with additional text before revenue %
                # - "+10 bill", "_+ 10 bill", "+10% bill" - bill impact patterns
                # Strategy: Find revenue % and bill % patterns and remove them along with any preceding comma/space within parentheses
                # First, handle cases where revenue % is at the end of parentheses with preceding text
                base_name = re.sub(r',\s*[+-]?\d+\.?\d*%\s*[Rr]evenue\s*\)', ')', original_name)
                # Then, handle standalone revenue % patterns in parentheses
                base_name = re.sub(r'\s*\([+-]?\d+\.?\d*%\s*[Rr]evenue\)', '', base_name)
                # Remove bill impact patterns: "+10 bill", "_+ 10 bill", "+10% bill", "(+10 bill)", etc.
                base_name = re.sub(r'[_\s]*[+-]\s*\d+\.?\d*%?\s*[Bb]ill\b', '', base_name, flags=re.IGNORECASE)
                base_name = re.sub(r'\([+-]?\s*\d+\.?\d*%?\s*[Bb]ill\)', '', base_name, flags=re.IGNORECASE)
                # Clean up any trailing spaces or empty parentheses
                base_name = re.sub(r'\(\s*\)', '', base_name)
                base_name = base_name.strip()
                # Use base name without revenue suffix (revenue estimates shown in table column instead)
                updated_name = base_name
                
                # Only pre-select top 3 validated options
                if is_validated and rank is not None and rank <= 3:
                    gate_opt["selected"] = True
                    rank_badge = " 🏆" if rank == 1 else (" 🥈" if rank == 2 else " 🥉")
                    gate_opt["label"] = f"{option_id} - {updated_name}{rank_badge}"
                    gate_opt["description"] = gate_opt.get("description", "").replace("✅ Validated:", f"✅ Validated (Top {rank}):")
                else:
                    gate_opt["selected"] = False
                    # Update label for all options, not just top 3
                    gate_opt["label"] = f"{option_id} - {updated_name}"
                
                # Ensure all options have consistent label format (without revenue suffix)
                if not gate_opt.get("label") or (gate_opt["label"].startswith(f"{option_id} - ") and not any(badge in gate_opt["label"] for badge in ["🏆", "🥈", "🥉"])):
                    gate_opt["label"] = f"{option_id} - {updated_name}"
                
                _logger.debug("Updated gate option {} with rank {} (validated={}) and selected={}, revenue_impact={}", 
                            option_id, rank, is_validated, gate_opt.get("selected"), gate_opt.get("revenue_impact_pct"))
            else:
                # Even if no rank info, still update the name and ensure range values are set
                _logger.warning("Could not find rank info for option_id: {} (checked {} options), updating name anyway", option_id, len(option_rank_map))
                # Get revenue impact from gate_opt if available
                revenue_pct = gate_opt.get("revenue_impact_pct", 0.0)
                # Find original option data to get base name and rate_class
                original_opt_data = next((opt for opt in rate_design_options if opt.get("option_id") == option_id), None)
                if revenue_pct is not None:
                    if original_opt_data:
                        original_name = original_opt_data.get('option_name', '')
                        # Remove design target patterns (same logic as above)
                        # First, handle cases where revenue % is at the end of parentheses with preceding text
                        base_name = re.sub(r',\s*[+-]?\d+\.?\d*%\s*[Rr]evenue\s*\)', ')', original_name)
                        # Then, handle standalone revenue % patterns in parentheses
                        base_name = re.sub(r'\s*\([+-]?\d+\.?\d*%\s*[Rr]evenue\)', '', base_name)
                        # Remove bill impact patterns: "+10 bill", "_+ 10 bill", "+10% bill", "(+10 bill)", etc.
                        base_name = re.sub(r'[_\s]*[+-]\s*\d+\.?\d*%?\s*[Bb]ill\b', '', base_name, flags=re.IGNORECASE)
                        base_name = re.sub(r'\([+-]?\s*\d+\.?\d*%?\s*[Bb]ill\)', '', base_name, flags=re.IGNORECASE)
                        # Clean up any trailing spaces or empty parentheses
                        base_name = re.sub(r'\(\s*\)', '', base_name)
                        base_name = base_name.strip()
                        # Use base name without revenue suffix (revenue estimates shown in table column instead)
                        updated_name = base_name
                        gate_opt["label"] = f"{option_id} - {updated_name}"
                
                # Ensure range values are set if revenue_impact_pct exists but range doesn't
                if revenue_pct is not None and (gate_opt.get("revenue_impact_range_min") is None or gate_opt.get("revenue_impact_range_max") is None):
                    uncertainty_pct = max(2.0, max(3.0, abs(revenue_pct) * 0.30))
                    gate_opt["revenue_impact_range_min"] = round(revenue_pct - uncertainty_pct, 1)
                    gate_opt["revenue_impact_range_max"] = round(revenue_pct + uncertainty_pct, 1)
                
                # Ensure rate_class is preserved from original option data (don't default to "all" if original had a specific class)
                if original_opt_data and original_opt_data.get("rate_class") and original_opt_data.get("rate_class").lower() != "all":
                    gate_opt["rate_class"] = original_opt_data.get("rate_class")
                elif "rate_class" not in gate_opt:
                    gate_opt["rate_class"] = "all"  # Only default to "all" if not set at all
        
        # Sort gate options: validated options first (by rank), then rejected options (by quality score)
        # Validated options should always appear before rejected options
        gate_options.sort(key=lambda x: (
            0 if x.get("is_validated", False) else 1,  # Validated first (0), rejected second (1)
            x.get("rank", 999) if x.get("is_validated", False) else 999,  # Then by rank for validated
            -x.get("quality_score", 0.0) if not x.get("is_validated", False) else 0  # Then by quality score (desc) for rejected
        ))
        
        # Log sorted order for debugging
        _logger.debug("Gate options sorted by rank: {}", [f"{opt.get('value')} (rank={opt.get('rank')})" for opt in gate_options[:5]])
        
        # Final verification: ensure only top 3 validated options have selected=True
        # Get validated options sorted by rank
        validated_with_rank = []
        for gate_opt in gate_options:
            option_id = str(gate_opt.get("value", ""))
            rank_info = option_rank_map.get(option_id)
            if rank_info and rank_info.get("is_validated", False):
                validated_with_rank.append((gate_opt, rank_info["rank"]))
        
        validated_with_rank.sort(key=lambda x: x[1])  # Sort by rank
        for idx, (gate_opt, rank) in enumerate(validated_with_rank, start=1):
            if idx <= 3:
                gate_opt["selected"] = True
            else:
                gate_opt["selected"] = False
        
        # Select top 3 recommendations with rationale
        # CRITICAL: Use validated_with_rank (sorted by rank) instead of validated_options[:3] (processing order)
        # This ensures top_recommendations matches the actual top 3 ranked validated options
        top_recommendations = []
        for idx, (gate_opt, rank) in enumerate(validated_with_rank[:3], start=1):
            option_id = str(gate_opt.get("value", ""))
            rank_info = option_rank_map.get(option_id)
            if not rank_info:
                continue
            
            opt = rank_info.get("option_data", {})
            rationale_parts = []
            if opt.get("revenue_score", 0.0) >= 90.0:
                rationale_parts.append("excellent revenue stability")
            if opt.get("bill_score", 0.0) >= 90.0:
                rationale_parts.append("minimal bill impact")
            if opt.get("complexity_score", 0.0) >= 90.0:
                rationale_parts.append("simple rate structure")
            if opt.get("equity_proxy_score", 0.0) >= 80.0:
                rationale_parts.append("balanced customer impacts")
            
            rationale = "; ".join(rationale_parts) if rationale_parts else "meets all validation criteria"
            
            top_recommendations.append({
                "rank": rank,  # Use actual rank from ranking, not enumeration index
                "option_id": opt.get("option_id"),
                "option_name": opt.get("option_name"),
                "quality_score": opt.get("quality_score", 0.0),
                "rationale": rationale,
                "estimated_revenue_change_pct": opt.get("estimated_revenue_change_pct", 0.0),
                "estimated_avg_bill_change_pct": opt.get("estimated_avg_bill_change_pct", 0.0),
            })
        
        validation_summary = {
            "total_generated": len(rate_design_options),
            "validated_count": len(validated_options),
            "rejected_count": len(rejected_options),
            "validation_criteria": {
                "revenue_change_max_pct": 10.0,
                "avg_bill_change_max_pct": 10.0,
                "min_quality_score": 70.0,
            },
            "top_recommendations": top_recommendations,  # Top 3 ranked options
        }
        
        # Verify gate options have correct structure and ensure all have range values
        # NOTE: Keep all options (validated + rejected) - user wants to see why options are rejected
        for gate_opt in gate_options:
            if gate_opt.get("rank") is not None:
                _logger.debug("Gate option {} has rank {} and selected={}", gate_opt.get("value"), gate_opt.get("rank"), gate_opt.get("selected"))
            
            # CRITICAL: Ensure all options with revenue_impact_pct have range values
            # Always recalculate range to ensure it's present and correct (for both validated and rejected)
            revenue_pct = gate_opt.get("revenue_impact_pct")
            if revenue_pct is not None and isinstance(revenue_pct, (int, float)) and float(revenue_pct) != 0.0:
                # Calculate uncertainty range: ±3 percentage points OR ±30% of estimate (whichever is larger), minimum ±2%
                uncertainty_pct = max(2.0, max(3.0, abs(float(revenue_pct)) * 0.30))
                range_min = round(float(revenue_pct) - uncertainty_pct, 1)
                range_max = round(float(revenue_pct) + uncertainty_pct, 1)
                # CRITICAL: Ensure values are floats (not strings or other types) for Jinja2 template
                gate_opt["revenue_impact_range_min"] = float(range_min)
                gate_opt["revenue_impact_range_max"] = float(range_max)
                _logger.info("Set range values for option {}: {:.1f}% - {:.1f}% (from revenue_pct={:.2f}%, uncertainty={:.2f}%)", 
                             gate_opt.get("value"), range_min, range_max, revenue_pct, uncertainty_pct)
            elif revenue_pct is not None and isinstance(revenue_pct, (int, float)) and float(revenue_pct) == 0.0:
                # Special case: 0.0 revenue - still set a range
                uncertainty_pct = 3.0  # Use minimum uncertainty
                range_min = round(0.0 - uncertainty_pct, 1)
                range_max = round(0.0 + uncertainty_pct, 1)
                gate_opt["revenue_impact_range_min"] = float(range_min)
                gate_opt["revenue_impact_range_max"] = float(range_max)
                _logger.info("Set range values for option {} with 0.0 revenue: {:.1f}% - {:.1f}%", 
                             gate_opt.get("value"), range_min, range_max)
            else:
                # For rejected options without revenue_pct, set range to None
                gate_opt["revenue_impact_range_min"] = None
                gate_opt["revenue_impact_range_max"] = None
                _logger.debug("Option {} has no revenue_impact_pct (value={}, type={}), setting range to None", 
                             gate_opt.get("value"), revenue_pct, type(revenue_pct).__name__ if revenue_pct is not None else "None")
        
        # Final verification: Log all options with their range values
        for gate_opt in gate_options:
            opt_id = gate_opt.get("value", "unknown")
            revenue_pct = gate_opt.get("revenue_impact_pct")
            range_min = gate_opt.get("revenue_impact_range_min")
            range_max = gate_opt.get("revenue_impact_range_max")
            _logger.info("Final check - Option {}: revenue_pct={} (type={}), range_min={} (type={}), range_max={} (type={})", 
                         opt_id, revenue_pct, type(revenue_pct).__name__ if revenue_pct is not None else "None",
                         range_min, type(range_min).__name__ if range_min is not None else "None",
                         range_max, type(range_max).__name__ if range_max is not None else "None")
        
        out = {
            "ok": True,
            "validated_options": validated_options,  # All validated options, sorted by quality score
            "rejected_options": rejected_options,
            "validation_summary": validation_summary,
            "options": gate_options,  # Formatted for HITL selection gate (SORTED BY RANK: validated options with rank 1,2,3... first, then rejected options with no rank; top 3 pre-selected)
        }
        
        _logger.output(
            "rate_case_validate_options OUTPUT: validated={}, rejected={}",
            len(validated_options),
            len(rejected_options),
        )
        
        return out
    finally:
        conn.close()


@pipeline_tool(toolkit="rate_case", name="rate_case_run_simulation")
def rate_case_run_simulation(db_file: str, target_state: str, option_id: str, rate_design_option: Dict[str, Any], sample_limit: Optional[int] = 2500, run_id: Optional[str] = None, revenue_target: float = 5.0) -> Dict[str, Any]:
    """Run deterministic per-customer billing simulation for one option for 3 years with growth modeling. Requires rate_design_option from context (no database reads)."""
    _logger.input(
        "rate_case_run_simulation INPUT: db_file={}, target_state={}, option_id={}, sample_limit={}, run_id={}",
        db_file,
        target_state,
        option_id,
        sample_limit,
        run_id,
    )

    if not rate_design_option or rate_design_option.get("option_id") != option_id:
        raise RuntimeError(f"Rate design option not found in context for option_id={option_id}. Ensure rate_case_rate_designer has run and option exists.")

    conn = _connect(db_file)
    try:
        cur = conn.cursor()
        # Use context data instead of database read
        opt = _RateOption(
            option_id=rate_design_option["option_id"],
            option_name=rate_design_option["option_name"],
            rate_class=rate_design_option.get("rate_class", "all"),
            rate_type=rate_design_option["rate_type"],
            fixed_charge=_safe_float(rate_design_option.get("fixed_charge")),
            energy_charge=_safe_float(rate_design_option.get("energy_charge")),
            tier_structure=rate_design_option.get("tier_structure") or {},
            tou_structure=rate_design_option.get("tou_structure") or {},
            demand_charge=_safe_float(rate_design_option.get("demand_charge")),
            assumptions=rate_design_option.get("assumptions") or [],
            description=rate_design_option.get("description") or "",
        )

        # Aggregate interval usage per customer in target state.
        # Use ORDER BY to ensure deterministic sampling - same customers every time
        # Include current_rate_type, state, and demographics for detailed breakdowns
        q = """
            SELECT iu.customer_id,
                   cm.rate_class AS rate_class,
                   cm.current_rate_type AS current_rate_type,
                   cm.state AS state,
                   cm.income_qualified_flag AS income_qualified_flag,
                   de.senior_flag AS senior_flag,
                   de.housing_burden_index AS housing_burden_index,
                   SUM(iu.kwh) AS total_kwh,
                   MAX(iu.kwh) AS max_interval_kwh,
                   COUNT(*) AS interval_count
            FROM interval_usage iu
            INNER JOIN customer_master cm ON cm.customer_id = iu.customer_id
            LEFT JOIN demographics_equity de ON de.customer_id = cm.customer_id
            WHERE cm.state = ?
            GROUP BY iu.customer_id, cm.rate_class, cm.current_rate_type, cm.state, cm.income_qualified_flag,
                     de.senior_flag, de.housing_burden_index
            ORDER BY iu.customer_id
        """
        if sample_limit and int(sample_limit) > 0:
            q += " LIMIT ?"
            params = [target_state, int(sample_limit)]
        else:
            params = [target_state]

        cur.execute(q, params)
        all_customers = [dict(r) for r in cur.fetchall()]
        if not all_customers:
            raise RuntimeError(f"No interval usage rows found for target_state={target_state}")
        
        # Filter customers by rate type match (Option B: only customers on matching rate types are impacted)
        # Map rate_type: "time_of_use" -> "tou", others stay the same
        opt_rate_type = opt.rate_type.lower()
        if opt_rate_type == "time_of_use":
            opt_rate_type = "tou"
        
        matching_customers = [
            c for c in all_customers
            if c.get("current_rate_type", "flat").lower() == opt_rate_type
        ]
        
        if not matching_customers:
            _logger.warning("No customers found with matching rate type for option {} (rate_type={}). Using all customers as fallback.", option_id, opt.rate_type)
            matching_customers = all_customers
        
        customers = matching_customers

        # System peak proxy (max single-interval kWh in state)
        cur.execute(
            """
            SELECT MAX(iu.kwh) AS system_max_interval_kwh
            FROM interval_usage iu
            INNER JOIN customer_master cm ON cm.customer_id = iu.customer_id
            WHERE cm.state = ?
            """,
            [target_state],
        )
        peak_row = cur.fetchone()
        system_peak_before = _safe_float(peak_row["system_max_interval_kwh"] if peak_row else 0.0)

        bills_before: List[float] = []
        bills_after: List[float] = []
        winners = losers = neutral = 0
        total_revenue_after = 0.0
        total_revenue_before = 0.0
        peak_after = 0.0

        dist = {"decrease_0_10": 0, "decrease_10_20": 0, "increase_0_10": 0, "increase_10_20": 0, "increase_20_plus": 0}
        
        # Track winners/losers by different dimensions
        winners_by_rate_type: Dict[str, int] = {"flat": 0, "tiered": 0, "tou": 0, "demand": 0}
        losers_by_rate_type: Dict[str, int] = {"flat": 0, "tiered": 0, "tou": 0, "demand": 0}
        winners_by_income_qualified: Dict[str, int] = {"qualified": 0, "not_qualified": 0}
        losers_by_income_qualified: Dict[str, int] = {"qualified": 0, "not_qualified": 0}
        winners_by_senior: Dict[str, int] = {"senior": 0, "non_senior": 0}
        losers_by_senior: Dict[str, int] = {"senior": 0, "non_senior": 0}
        winners_by_usage_level: Dict[str, int] = {"low": 0, "medium": 0, "high": 0}
        losers_by_usage_level: Dict[str, int] = {"low": 0, "medium": 0, "high": 0}
        
        # Calculate usage percentiles for categorization (low/medium/high)
        usage_p33 = 0.0
        usage_p67 = 0.0
        if customers:
            usage_values = sorted([_safe_float(c.get("total_kwh", 0)) for c in customers])
            if usage_values:
                p33_idx = len(usage_values) // 3
                p67_idx = (len(usage_values) * 2) // 3
                usage_p33 = usage_values[p33_idx] if p33_idx < len(usage_values) else usage_values[0]
                usage_p67 = usage_values[p67_idx] if p67_idx < len(usage_values) else usage_values[-1]

        for c in customers:
            total_kwh = _safe_float(c.get("total_kwh"))
            max_interval_kwh = _safe_float(c.get("max_interval_kwh"))
            interval_count = int(_safe_float(c.get("interval_count")))
            inc_q = int(_safe_float(c.get("income_qualified_flag")))
            customer_state = c.get("state", target_state)
            rate_class = c.get("rate_class", "residential")
            current_rate_type = c.get("current_rate_type", "flat")
            
            # Get customer's current rate from existing_rates table
            customer_rate = _get_customer_current_rate(conn, customer_state, rate_class, current_rate_type)
            
            bill_before = _bill_baseline(total_kwh, customer_rate, max_interval_kwh, interval_count)

            if opt.rate_type == "flat":
                bill_after = _bill_flat(opt, total_kwh, inc_q)
            elif opt.rate_type == "tiered":
                bill_after = _bill_tiered(opt, total_kwh, inc_q)
            else:
                bill_after = _bill_tou(opt, total_kwh, max_interval_kwh, interval_count, inc_q)
            
            # Add demand charge if specified (applies to all rate types)
            # Demand charge is per kW of peak demand (max_interval_kwh represents peak kW for the month)
            if opt.demand_charge > 0.0:
                # Convert max_interval_kwh to kW (assuming 1-hour intervals, max_interval_kwh is already in kW)
                # If intervals are different durations, this would need adjustment
                peak_demand_kw = max_interval_kwh  # max_interval_kwh is already peak demand in kW
                bill_after += opt.demand_charge * peak_demand_kw

            pct = ((bill_after - bill_before) / bill_before * 100.0) if bill_before > 0 else 0.0
            
            # Categorize customer attributes for breakdown
            rate_type_key = (current_rate_type or "flat").lower()
            if rate_type_key == "time_of_use":
                rate_type_key = "tou"
            
            income_status = "qualified" if inc_q == 1 else "not_qualified"
            senior_status = "senior" if int(c.get("senior_flag") or 0) == 1 else "non_senior"
            
            # Categorize usage level
            if total_kwh < usage_p33:
                usage_level = "low"
            elif total_kwh < usage_p67:
                usage_level = "medium"
            else:
                usage_level = "high"
            
            if abs(pct) < 0.1:
                neutral += 1
            elif pct < 0:
                winners += 1
                # Track by dimensions
                if rate_type_key in winners_by_rate_type:
                    winners_by_rate_type[rate_type_key] += 1
                winners_by_income_qualified[income_status] += 1
                winners_by_senior[senior_status] += 1
                winners_by_usage_level[usage_level] += 1
                
                if pct > -10:
                    dist["decrease_0_10"] += 1
                else:
                    dist["decrease_10_20"] += 1
            else:
                losers += 1
                # Track by dimensions
                if rate_type_key in losers_by_rate_type:
                    losers_by_rate_type[rate_type_key] += 1
                losers_by_income_qualified[income_status] += 1
                losers_by_senior[senior_status] += 1
                losers_by_usage_level[usage_level] += 1
                
                if pct <= 10:
                    dist["increase_0_10"] += 1
                elif pct <= 20:
                    dist["increase_10_20"] += 1
                else:
                    dist["increase_20_plus"] += 1

            bills_before.append(bill_before)
            bills_after.append(bill_after)
            total_revenue_before += bill_before
            total_revenue_after += bill_after
            if max_interval_kwh > peak_after:
                peak_after = max_interval_kwh

        avg_bill_before = sum(bills_before) / len(bills_before) if bills_before else 0.0
        avg_bill_after = sum(bills_after) / len(bills_after) if bills_after else 0.0
        avg_bill_change_pct = ((avg_bill_after - avg_bill_before) / avg_bill_before * 100.0) if avg_bill_before > 0 else 0.0
        revenue_change_pct = ((total_revenue_after - total_revenue_before) / total_revenue_before * 100.0) if total_revenue_before > 0 else 0.0
        peak_load_reduction_pct = ((system_peak_before - peak_after) / system_peak_before * 100.0) if system_peak_before > 0 else 0.0

        # Validate that winners + losers + neutral = total customers
        total_customers = len(customers)
        calculated_total = winners + losers + neutral
        if calculated_total != total_customers:
            _logger.warning(
                "Winners/losers/neutral count mismatch: winners={}, losers={}, neutral={}, total={}, expected={}",
                winners, losers, neutral, calculated_total, total_customers
            )

        # 3-Year Simulation with Growth Modeling
        # Growth factors: customer base growth (2% per year), usage growth (1% per year)
        CUSTOMER_GROWTH_RATE = 0.02  # 2% customer base growth per year
        USAGE_GROWTH_RATE = 0.01  # 1% usage growth per year
        
        # Year 1: Baseline (already calculated above)
        revenue_year_1 = total_revenue_after
        revenue_before_year_1 = total_revenue_before
        revenue_change_pct_year_1 = revenue_change_pct
        target_met_year_1 = abs(revenue_change_pct_year_1 - revenue_target) <= 1.0  # Within 1% of target
        
        # Year 2: Apply growth factors
        # Customer base grows by 2%, usage per customer grows by 1%
        customer_count_year_2 = total_customers * (1.0 + CUSTOMER_GROWTH_RATE)
        usage_multiplier_year_2 = 1.0 + USAGE_GROWTH_RATE
        revenue_year_2 = revenue_year_1 * (1.0 + CUSTOMER_GROWTH_RATE) * usage_multiplier_year_2
        revenue_before_year_2 = revenue_before_year_1 * (1.0 + CUSTOMER_GROWTH_RATE) * usage_multiplier_year_2
        # IMPORTANT: For Years 2 and 3, report TRUE YoY growth (vs prior year under new rate),
        # not uplift vs baseline. This keeps the table aligned with revenue_target semantics.
        revenue_change_pct_year_2 = ((revenue_year_2 - revenue_year_1) / revenue_year_1 * 100.0) if revenue_year_1 > 0 else 0.0
        target_met_year_2 = abs(revenue_change_pct_year_2 - revenue_target) <= 1.0
        
        # Year 3: Apply growth factors again
        customer_count_year_3 = customer_count_year_2 * (1.0 + CUSTOMER_GROWTH_RATE)
        usage_multiplier_year_3 = usage_multiplier_year_2 * (1.0 + USAGE_GROWTH_RATE)
        revenue_year_3 = revenue_year_2 * (1.0 + CUSTOMER_GROWTH_RATE) * (1.0 + USAGE_GROWTH_RATE)
        revenue_before_year_3 = revenue_before_year_2 * (1.0 + CUSTOMER_GROWTH_RATE) * (1.0 + USAGE_GROWTH_RATE)
        revenue_change_pct_year_3 = ((revenue_year_3 - revenue_year_2) / revenue_year_2 * 100.0) if revenue_year_2 > 0 else 0.0
        target_met_year_3 = abs(revenue_change_pct_year_3 - revenue_target) <= 1.0

        simulation_id = f"SIM-{option_id}-{_utc_iso()}"

        bill_impact_summary = {
            "avg_bill_before": avg_bill_before, 
            "avg_bill_after": avg_bill_after, 
            "avg_bill_change_pct": avg_bill_change_pct,  # Include in summary for clarity
            "bill_change_distribution": dist,
            "winners_by_rate_type": winners_by_rate_type,
            "losers_by_rate_type": losers_by_rate_type,
            "winners_by_income_qualified": winners_by_income_qualified,
            "losers_by_income_qualified": losers_by_income_qualified,
            "winners_by_senior": winners_by_senior,
            "losers_by_senior": losers_by_senior,
            "winners_by_usage_level": winners_by_usage_level,
            "losers_by_usage_level": losers_by_usage_level,
            "total_customers": total_customers,  # Include for validation
        }
        revenue_impact_summary = {
            "revenue_before": total_revenue_before, 
            "revenue_after": total_revenue_after, 
            "revenue_change_pct": revenue_change_pct
        }
        
        # 3-Year Revenue Performance
        three_year_performance = {
            "year_1": {
                "revenue": revenue_year_1,
                "revenue_before": revenue_before_year_1,
                "revenue_change_pct": revenue_change_pct_year_1,
                "target_met": target_met_year_1,
                "distance_from_target": abs(revenue_change_pct_year_1 - revenue_target)
            },
            "year_2": {
                "revenue": revenue_year_2,
                "revenue_before": revenue_before_year_2,
                "revenue_change_pct": revenue_change_pct_year_2,
                "target_met": target_met_year_2,
                "distance_from_target": abs(revenue_change_pct_year_2 - revenue_target),
                "customer_count": customer_count_year_2,
                "usage_growth_factor": usage_multiplier_year_2
            },
            "year_3": {
                "revenue": revenue_year_3,
                "revenue_before": revenue_before_year_3,
                "revenue_change_pct": revenue_change_pct_year_3,
                "target_met": target_met_year_3,
                "distance_from_target": abs(revenue_change_pct_year_3 - revenue_target),
                "customer_count": customer_count_year_3,
                "usage_growth_factor": usage_multiplier_year_3
            },
            "revenue_target": revenue_target,
            "growth_assumptions": {
                "customer_growth_rate_pct": CUSTOMER_GROWTH_RATE * 100.0,
                "usage_growth_rate_pct": USAGE_GROWTH_RATE * 100.0
            }
        }
        
        load_impact_summary = {"peak_load_before": system_peak_before, "peak_load_after": peak_after, "peak_hours_shifted": []}

        # Database writes removed - data flows through context only
        out = {
            "ok": True,
            "simulation_id": simulation_id,
            "option_id": option_id,
            "total_revenue": total_revenue_after,
            "avg_bill_change_pct": avg_bill_change_pct,
            "revenue_change_pct": revenue_change_pct,  # Explicitly include for clarity
            "peak_load_kw": peak_after,
            "peak_load_reduction_pct": peak_load_reduction_pct,
            "winners_count": winners,
            "losers_count": losers,
            "neutral_count": neutral,
            "total_customers": total_customers,  # Include for validation
            "bill_impact_summary": bill_impact_summary,
            "revenue_impact_summary": revenue_impact_summary,
            "three_year_performance": three_year_performance,  # New: 3-year performance data
            "load_impact_summary": load_impact_summary,
        }
        _logger.output("rate_case_run_simulation OUTPUT: simulation_id={}", simulation_id)
        return out
    finally:
        conn.close()


@pipeline_tool(toolkit="rate_case", name="rate_case_run_equity_assessment")
def rate_case_run_equity_assessment(
    db_file: str,
    target_state: str,
    option_id: str,
    simulation_result: Dict[str, Any],
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Compute deterministic equity summary using simulation outputs and demographic data. Requires simulation_result from context (no database reads)."""
    _logger.input(
        "rate_case_run_equity_assessment INPUT: db_file={}, target_state={}, option_id={}, run_id={}",
        db_file,
        target_state,
        option_id,
        run_id,
    )

    conn = _connect(db_file)
    try:
        cur = conn.cursor()
        # Extract simulation data from context parameter
        # Defensive: Handle case where simulation_result might be a JSON string or Python repr
        if isinstance(simulation_result, str):
            # Try JSON first
            try:
                simulation_result = json.loads(simulation_result)
                _logger.debug("Parsed simulation_result from JSON string")
            except (json.JSONDecodeError, TypeError):
                # If JSON fails, try Python eval (for Python dict repr strings like "{'key': 'value'}")
                try:
                    import ast
                    simulation_result = ast.literal_eval(simulation_result)
                    _logger.debug("Parsed simulation_result from Python repr string")
                except (ValueError, SyntaxError) as e:
                    _logger.error("Failed to parse simulation_result: JSON error, Python repr also failed: {}", e)
                    _logger.error("simulation_result value (first 200 chars): {}", simulation_result[:200] if len(simulation_result) > 200 else simulation_result)
                    raise ValueError(f"simulation_result must be a dict or valid JSON/Python repr string, got: {type(simulation_result)}")
        
        if not isinstance(simulation_result, dict):
            _logger.error("simulation_result is not a dict: type={}, value (first 200 chars)={}", type(simulation_result), str(simulation_result)[:200] if len(str(simulation_result)) > 200 else simulation_result)
            raise ValueError(f"simulation_result must be a dict, got: {type(simulation_result)}")
        
        bill_summary = simulation_result.get("bill_impact_summary", {})
        if isinstance(bill_summary, str):
            bill_summary = json.loads(bill_summary)
        avg_bill_change_pct = _safe_float(simulation_result.get("avg_bill_change_pct"))

        # Deterministic equity score heuristic: penalize broad increases.
        losers = int(simulation_result.get("losers_count", 0))
        winners = int(simulation_result.get("winners_count", 0))
        neutral = int(simulation_result.get("neutral_count", 0))
        total = max(1, losers + winners + neutral)
        loser_rate = losers / total
        winner_rate = winners / total

        # Incorporate housing burden prevalence in target state (simple).
        cur.execute(
            """
            SELECT de.income_band, de.senior_flag, de.housing_burden_index, cm.income_qualified_flag
            FROM demographics_equity de
            INNER JOIN customer_master cm ON cm.customer_id = de.customer_id
            WHERE cm.state = ?
            LIMIT 5000
            """,
            [target_state],
        )
        demo = [dict(r) for r in cur.fetchall()]
        high_burden = sum(1 for r in demo if _safe_float(r.get("housing_burden_index")) >= 0.30)
        high_burden_rate = (high_burden / max(1, len(demo))) if demo else 0.0

        # Equity score 0-100 (demo): higher is better. More lenient scoring with higher floor.
        # Base 60, less harsh bill change penalty (0.5x instead of 1.5x), less harsh loser penalty
        equity_score = max(40.0, min(100.0, 60.0 - (avg_bill_change_pct * 0.5) - (loser_rate * 15.0) - (high_burden_rate * 5.0) + (winner_rate * 10.0)))

        hardship_risk_count = 0
        hardship_details: List[Dict[str, Any]] = []
        if avg_bill_change_pct >= 20:
            hardship_risk_count = min(25, int(total * 0.02))
            hardship_details = [{"customer_id": "", "bill_increase_pct": avg_bill_change_pct, "risk_factors": ["high_avg_increase"], "severity": "high"}]

        winners_losers_summary = {"winners": winners, "losers": losers, "neutral": neutral}
        demographic_impact = {
            "summary": "Deterministic demo equity heuristic based on avg bill change, loser share, and housing burden prevalence.",
            "by_income": {},
            "by_income_qualified": {},
        }
        recommendations = [
            {
                "recommendation": "If increases concentrate on high housing-burden customers, consider targeted credits or phased-in transitions.",
                "priority": "medium" if avg_bill_change_pct < 15 else "high",
                "rationale": "Protect vulnerable customers while meeting revenue and reliability goals.",
            }
        ]

        assessment_id = f"EQ-{option_id}-{_utc_iso()}"
        # Database writes removed - data flows through context only

        out = {
            "ok": True,
            "assessment_id": assessment_id,
            "option_id": option_id,
            "equity_score": equity_score,
            "hardship_risk_count": hardship_risk_count,
            "hardship_risk_details": hardship_details,
            "winners_losers_summary": winners_losers_summary,
            "demographic_impact": demographic_impact,
            "recommendations": recommendations,
        }
        _logger.output("rate_case_run_equity_assessment OUTPUT: assessment_id={}", assessment_id)
        return out
    finally:
        conn.close()


@pipeline_tool(toolkit="rate_case", name="rate_case_run_state_comparison")
def rate_case_run_state_comparison(db_file: str, target_state: str, option_id: str, rate_design_option: Dict[str, Any], repeat_instance_id: str, run_id: Optional[str] = None) -> Dict[str, Any]:
    """Compare proposed option to existing rates in target + 2 benchmark states. Requires rate_design_option from context (no database reads)."""
    _logger.input(
        "rate_case_run_state_comparison INPUT: db_file={}, target_state={}, option_id={}, repeat_instance_id={}, run_id={}",
        db_file,
        target_state,
        option_id,
        repeat_instance_id,
        run_id,
    )
    
    if not rate_design_option or rate_design_option.get("option_id") != option_id:
        raise RuntimeError(f"Rate design option not found in context for option_id={option_id}. Ensure rate_case_rate_designer has run and option exists.")
    
    conn = _connect(db_file)
    try:
        cur = conn.cursor()
        # Use context data instead of database read
        opt = rate_design_option

        cur.execute("SELECT DISTINCT state FROM existing_rates WHERE state != ?", [target_state])
        other_states = [r["state"] for r in cur.fetchall()]
        if len(other_states) >= 2:
            benchmarks = random.sample(other_states, 2)
        else:
            benchmarks = other_states

        cur.execute(
            "SELECT rate_name, rate_class, rate_type, fixed_charge, energy_charge, tou_peak_price, tou_offpeak_price FROM existing_rates WHERE state = ?",
            [target_state],
        )
        target_rates = [dict(r) for r in cur.fetchall()]

        bench_rates: List[Dict[str, Any]] = []
        if benchmarks:
            placeholders = ", ".join(["?"] * len(benchmarks))
            cur.execute(
                f"SELECT state, rate_name, rate_class, rate_type, fixed_charge, energy_charge, tou_peak_price, tou_offpeak_price FROM existing_rates WHERE state IN ({placeholders})",
                benchmarks,
            )
            bench_rates = [dict(r) for r in cur.fetchall()]

        proposed = {
            "option_id": option_id,
            "rate_type": opt.get("rate_type"),
            "fixed_charge": _safe_float(opt.get("fixed_charge")),
            "energy_charge": _safe_float(opt.get("energy_charge")),
        }

        # Build a compact markdown table (browser friendly).
        lines = ["| State | Rate Name | Fixed Charge | Energy Charge | TOU Peak | TOU Off-Peak |", "|---|---|---:|---:|---:|---:|"]
        for r in bench_rates:
            lines.append(
                f"| {r.get('state')} | {r.get('rate_name')} | {_safe_float(r.get('fixed_charge')):.2f} | {_safe_float(r.get('energy_charge')):.3f} | {_safe_float(r.get('tou_peak_price')):.3f} | {_safe_float(r.get('tou_offpeak_price')):.3f} |"
            )
        for r in target_rates:
            lines.append(
                f"| {target_state} | {r.get('rate_name')} | {_safe_float(r.get('fixed_charge')):.2f} | {_safe_float(r.get('energy_charge')):.3f} | {_safe_float(r.get('tou_peak_price')):.3f} | {_safe_float(r.get('tou_offpeak_price')):.3f} |"
            )
        lines.append(f"| Proposed | {option_id} | {proposed['fixed_charge']:.2f} | {proposed['energy_charge']:.3f} | N/A | N/A |")
        table_md = "\n".join(lines)

        score = max(0.0, min(100.0, 70.0 + (10.0 - proposed["fixed_charge"]) * 2.0))
        competitive_positioning = {
            "vs_target_state": "Deterministic comparison based on fixed/energy charges (demo).",
            "vs_benchmark_states": "Benchmarked to 2 other states' existing rates (demo).",
            "market_position": "Demo positioning; interpret as illustrative.",
        }
        benchmark_states_comparison = {"states": benchmarks, "comparison_table": table_md, "summary": "See table."}
        target_state_comparison = {"existing_rates": target_rates[:5], "proposed_rate": proposed, "comparison_summary": opt["description"] or ""}

        comparison_id = f"SC-{option_id}-{repeat_instance_id}"
        # Database writes removed - data flows through context only
        out = {
            "ok": True,
            "comparison_id": comparison_id,
            "option_id": option_id,
            "target_state_comparison": target_state_comparison,
            "benchmark_states_comparison": benchmark_states_comparison,
            "competitive_positioning": competitive_positioning,
            "rate_competitiveness_score": score,
            "comparison_summary": f"Benchmarks: {benchmarks}.",
        }
        _logger.output("rate_case_run_state_comparison OUTPUT: comparison_id={}", comparison_id)
        return out
    finally:
        conn.close()


@pipeline_tool(toolkit="rate_case", name="rate_case_build_recommendations")
def rate_case_build_recommendations(
    db_file: str,
    target_state: str,
    run_id: Optional[str] = None,
    rate_design_options: Optional[List[Dict[str, Any]]] = None,
    simulation_results: Optional[Dict[str, Any]] = None,
    equity_assessments: Optional[Dict[str, Any]] = None,
    state_comparisons: Optional[Dict[str, Any]] = None,
    revenue_target: float = 5.0,
) -> Dict[str, Any]:
    """
    Deterministically rank options using simulation + equity + state comparison.
    Requires context data from rate designer and repeat pattern results (no database reads).
    """
    _logger.input("rate_case_build_recommendations INPUT: db_file={}, target_state={}, run_id={}", db_file, target_state, run_id)
    _logger.debug("rate_case_build_recommendations parameter types: simulation_results={}, equity_assessments={}, state_comparisons={}", 
                  type(simulation_results).__name__, type(equity_assessments).__name__, type(state_comparisons).__name__)

    if not rate_design_options:
        raise RuntimeError("Missing required context data: rate_design_options must be provided from rate_case_rate_designer output.")
    if not simulation_results or not equity_assessments or not state_comparisons:
        raise RuntimeError("Missing required context data: simulation_results, equity_assessments, and state_comparisons must be provided from repeat pattern results.")

    # CRITICAL: Handle case where complex parameters might be passed as JSON strings (OAK framework issue)
    # Parse JSON strings to dictionaries if needed
    import json
    if isinstance(simulation_results, str):
        try:
            _logger.warning("simulation_results received as string, attempting JSON parse")
            simulation_results = json.loads(simulation_results)
        except json.JSONDecodeError as e:
            _logger.error("Failed to parse simulation_results JSON: {}", e)
            raise RuntimeError(f"simulation_results must be a dictionary or valid JSON string, got: {type(simulation_results).__name__}")
    
    if isinstance(equity_assessments, str):
        try:
            _logger.warning("equity_assessments received as string, attempting JSON parse")
            equity_assessments = json.loads(equity_assessments)
        except json.JSONDecodeError as e:
            _logger.error("Failed to parse equity_assessments JSON: {}", e)
            raise RuntimeError(f"equity_assessments must be a dictionary or valid JSON string, got: {type(equity_assessments).__name__}")
    
    if isinstance(state_comparisons, str):
        try:
            _logger.warning("state_comparisons received as string, attempting JSON parse")
            state_comparisons = json.loads(state_comparisons)
        except json.JSONDecodeError as e:
            _logger.error("Failed to parse state_comparisons JSON: {}", e)
            raise RuntimeError(f"state_comparisons must be a dictionary or valid JSON string, got: {type(state_comparisons).__name__}")
    
    # Validate that all parameters are dictionaries after parsing
    if not isinstance(simulation_results, dict):
        raise RuntimeError(f"simulation_results must be a dictionary after parsing, got: {type(simulation_results).__name__}")
    if not isinstance(equity_assessments, dict):
        raise RuntimeError(f"equity_assessments must be a dictionary after parsing, got: {type(equity_assessments).__name__}")
    if not isinstance(state_comparisons, dict):
        raise RuntimeError(f"state_comparisons must be a dictionary after parsing, got: {type(state_comparisons).__name__}")

    conn = _connect(db_file)
    try:
        cur = conn.cursor()
        # Use context data instead of database read
        options = [{"option_id": opt.get("option_id"), "option_name": opt.get("option_name"), "description": opt.get("description", "")} for opt in rate_design_options]
        if not options:
            raise RuntimeError("No rate_design_options found in context. Ensure rate_case_rate_designer has run.")

        # Map context data by option_id
        sims: Dict[str, Dict[str, Any]] = {}
        for opt in options:
            oid = opt["option_id"]
            # Find matching simulation result by option_id
            # Handle both direct dict access and nested structures from repeat pattern
            if isinstance(simulation_results, dict):
                for sim_key, sim_data in simulation_results.items():
                    # Handle nested structure: simulation_results might be {instance_id: {agent_id: result}}
                    if isinstance(sim_data, dict):
                        # Check if sim_data is the result directly or nested
                        if sim_data.get("option_id") == oid:
                            sims[oid] = sim_data
                            break
                        # Check nested structure (e.g., {instance_id: {rate_case_scenario_simulator: {...}}})
                        for nested_key, nested_data in sim_data.items():
                            if isinstance(nested_data, dict) and nested_data.get("option_id") == oid:
                                sims[oid] = nested_data
                                break
                        if oid in sims:
                            break

        equities: Dict[str, Dict[str, Any]] = {}
        for opt in options:
            oid = opt["option_id"]
            if isinstance(equity_assessments, dict):
                for eq_key, eq_data in equity_assessments.items():
                    if isinstance(eq_data, dict):
                        if eq_data.get("option_id") == oid:
                            equities[oid] = eq_data
                            break
                        # Check nested structure
                        for nested_key, nested_data in eq_data.items():
                            if isinstance(nested_data, dict) and nested_data.get("option_id") == oid:
                                equities[oid] = nested_data
                                break
                        if oid in equities:
                            break

        comps: Dict[str, Dict[str, Any]] = {}
        for opt in options:
            oid = opt["option_id"]
            if isinstance(state_comparisons, dict):
                for comp_key, comp_data in state_comparisons.items():
                    if isinstance(comp_data, dict):
                        if comp_data.get("option_id") == oid:
                            comps[oid] = comp_data
                            break
                        # Check nested structure
                        for nested_key, nested_data in comp_data.items():
                            if isinstance(nested_data, dict) and nested_data.get("option_id") == oid:
                                comps[oid] = nested_data
                                break
                        if oid in comps:
                            break

        scored: List[Tuple[str, float, Dict[str, Any]]] = []
        for opt in options:
            oid = opt["option_id"]
            sim = sims.get(oid) or {}
            eq = equities.get(oid) or {}
            comp = comps.get(oid) or {}

            avg_bill_change_pct = _safe_float(sim.get("avg_bill_change_pct"))
            total_rev = _safe_float(sim.get("total_revenue"))
            # Extract revenue_change_pct from JSON field
            rev_summary_str = sim.get("revenue_impact_summary") or "{}"
            rev_summary = json.loads(rev_summary_str) if isinstance(rev_summary_str, str) else (rev_summary_str if isinstance(rev_summary_str, dict) else {})
            revenue_change_pct = _safe_float(rev_summary.get("revenue_change_pct", 0.0), 0.0)
            
            # Equity score: adjusted for bill changes with tighter scoring for ±5-10% range
            # Target range: 80-100 for validated options (bill change ±10%)
            raw_equity_score = _safe_float(eq.get("equity_score"), None)
            if raw_equity_score is None or raw_equity_score == 0.0:
                # If missing or zero, calculate based on bill impact with improved scoring
                if avg_bill_change_pct <= 5.0:
                    equity_score = 85.0  # Excellent: minimal bill impact
                elif avg_bill_change_pct <= 10.0:
                    equity_score = 75.0  # Good: within acceptable range
                elif avg_bill_change_pct <= 20.0:
                    equity_score = 60.0  # Moderate: some impact
                elif avg_bill_change_pct <= 30.0:
                    equity_score = 50.0  # Poor: significant impact
                else:
                    equity_score = 40.0  # Very poor: high impact
            else:
                # Use calculated score but adjust for bill changes outside ±10%
                base_equity = max(40.0, min(100.0, raw_equity_score))
                # Penalize if bill change exceeds ±10%
                if abs(avg_bill_change_pct) > 10.0:
                    penalty = (abs(avg_bill_change_pct) - 10.0) * 0.5
                    equity_score = max(40.0, base_equity - penalty)
                else:
                    equity_score = base_equity
            
            comp_score = _safe_float(comp.get("rate_competitiveness_score"), 50.0)

            # Revenue score: based on distance from revenue_target (closer is better)
            # CRITICAL: Options that EXCEED the target are penalized more than options below target
            # This ensures "not more than target" preference
            revenue_distance_from_target = abs(revenue_change_pct - revenue_target)
            if revenue_change_pct <= revenue_target:
                # Below or at target: normal distance scoring
                if revenue_distance_from_target <= 1.0:
                    # Excellent (within 1% of target): score 95-100
                    revenue_score = 100.0 - (revenue_distance_from_target * 5.0)
                elif revenue_distance_from_target <= 3.0:
                    # Good (1-3% from target): score 80-95
                    revenue_score = 95.0 - ((revenue_distance_from_target - 1.0) * 7.5)
                elif revenue_distance_from_target <= 5.0:
                    # Moderate (3-5% from target): score 65-80
                    revenue_score = 80.0 - ((revenue_distance_from_target - 3.0) * 7.5)
                elif revenue_distance_from_target <= 10.0:
                    # Poor (5-10% from target): score 40-65
                    revenue_score = 65.0 - ((revenue_distance_from_target - 5.0) * 5.0)
                else:
                    # Very poor (>10% from target): score 20-40
                    revenue_score = max(20.0, 40.0 - ((revenue_distance_from_target - 10.0) * 2.0))
            else:
                # EXCEEDS target: apply additional penalty (prefer options below target)
                # Example: if target is 8%, then 5.3% scores better than 10% even though 10% is closer
                excess_penalty = (revenue_change_pct - revenue_target) * 4.0  # 4 points per % over target
                if revenue_distance_from_target <= 1.0:
                    base_score = 100.0 - (revenue_distance_from_target * 5.0)
                elif revenue_distance_from_target <= 3.0:
                    base_score = 95.0 - ((revenue_distance_from_target - 1.0) * 7.5)
                elif revenue_distance_from_target <= 5.0:
                    base_score = 80.0 - ((revenue_distance_from_target - 3.0) * 7.5)
                elif revenue_distance_from_target <= 10.0:
                    base_score = 65.0 - ((revenue_distance_from_target - 5.0) * 5.0)
                else:
                    base_score = max(20.0, 40.0 - ((revenue_distance_from_target - 10.0) * 2.0))
                revenue_score = max(20.0, min(100.0, base_score - excess_penalty))
            revenue_score = max(20.0, min(100.0, revenue_score))  # Floor at 20, cap at 100
            
            # Bill penalty: increased penalty for bill changes outside ±10%
            # Target range: 80-100 for validated options (bill change ±10%)
            abs_bill_change = abs(avg_bill_change_pct)
            if abs_bill_change <= 10.0:
                # Within acceptable range: no penalty
                bill_penalty = 0.0
            else:
                # Outside ±10%: penalty increases with distance from 10%
                bill_penalty = (abs_bill_change - 10.0) * 0.5
                bill_penalty = max(0.0, min(30.0, bill_penalty))  # Cap at 30 points (was 10)
            
            # Overall score: weighted combination
            # Target range: 80-100 for validated options (revenue ±10%, bill ±10%)
            # Weights: equity (30%), competitive (25%), revenue (25%), load management (10%), customer satisfaction (10%)
            # Load management: base score of 60, can be enhanced with actual peak reduction data
            peak_reduction = _safe_float(sim.get("peak_load_reduction_pct"), 0.0)
            if peak_reduction > 0:
                load_mgmt_score = min(100.0, 60.0 + (peak_reduction * 2.0))  # Reward peak reduction
            else:
                load_mgmt_score = 60.0  # Default for no reduction
            
            # Customer satisfaction: starts at 100, penalized by bill changes outside ±10%
            customer_sat_score = max(0.0, min(100.0, 100.0 - bill_penalty))
            
            overall = max(0.0, min(100.0, 
                (0.30 * equity_score) + 
                (0.25 * comp_score) + 
                (0.25 * revenue_score) + 
                (0.10 * load_mgmt_score) + 
                (0.10 * customer_sat_score)))
            
            # Flag poor quality options (score < 60) - these should ideally be filtered out during validation
            # Target range: 80-100 for validated options (revenue ±10%, bill ±10%)
            quality_flag = "good" if overall >= 80.0 else ("moderate" if overall >= 60.0 else "poor")
            
            detail = {
                "option_id": oid,
                "option_name": opt.get("option_name"),
                "overall_score": overall,
                "revenue_score": revenue_score,
                "equity_score": equity_score,
                "customer_satisfaction_score": customer_sat_score,
                "load_management_score": load_mgmt_score,
                "avg_bill_change_pct": avg_bill_change_pct,
                "quality_flag": quality_flag,  # "good" (>=80), "moderate" (60-79), "poor" (<60)
            }
            scored.append((oid, overall, detail))

        scored.sort(key=lambda x: x[1], reverse=True)
        recommendations_out: List[Dict[str, Any]] = []
        now = _utc_iso()
        
        for idx, (_oid, _score, detail) in enumerate(scored, start=1):
            recommendation_id = f"REC-{detail['option_id']}-{now}"
            tradeoffs = {
                "notes": "Deterministic demo tradeoffs computed from aggregate metrics.",
                "avg_bill_change_pct": detail.get("avg_bill_change_pct"),
            }
            rationale = f"Ranked by composite score emphasizing equity and competitiveness; penalizes high bill increases."
            
            # Calculate per-option confidence score based on score quality and data completeness
            overall_score = detail.get("overall_score", 0.0)
            
            # Check data completeness
            has_simulation = bool(sims.get(_oid))
            has_equity = bool(equities.get(_oid))
            has_comparison = bool(comps.get(_oid))
            data_completeness = sum([has_simulation, has_equity, has_comparison])
            
            # Get competitive score for this option (from outer loop scope, need to recalculate)
            comp_data = comps.get(_oid) or {}
            comp_score_for_option = _safe_float(comp_data.get("rate_competitiveness_score"), 50.0)
            
            # Check score consistency (how close component scores are to each other)
            component_scores = [
                detail.get("revenue_score", 0.0),
                detail.get("equity_score", 0.0),
                detail.get("load_management_score", 0.0),
                detail.get("customer_satisfaction_score", 0.0),
                comp_score_for_option,
            ]
            if component_scores:
                score_range = max(component_scores) - min(component_scores)
                is_consistent = score_range <= 20.0  # All scores within 20 points
            else:
                is_consistent = False
            
            # Calculate confidence for this option
            # Improved formula to get >95% for good options (score >= 80)
            # Base: 70.0 (higher starting point)
            option_confidence = 70.0
            
            # Score quality boost: higher scores = higher confidence
            if overall_score >= 80.0:
                # Excellent scores (80-100): high confidence (95-100%)
                option_confidence = 85.0 + ((overall_score - 80.0) * 0.75)  # 85-100 for 80-100 score
            elif overall_score >= 70.0:
                # Good scores (70-80): good confidence (85-95%)
                option_confidence = 80.0 + ((overall_score - 70.0) * 0.5)  # 80-85 for 70-80 score
            elif overall_score >= 50.0:
                # Moderate scores (50-70): moderate confidence (70-85%)
                option_confidence = 70.0 + ((overall_score - 50.0) * 0.75)  # 70-85 for 50-70 score
            else:
                # Lower scores: lower confidence
                option_confidence = 50.0 + (overall_score * 0.4)  # 50-70 for 0-50 score
            
            # Data completeness boost: +5 if all data present, +3 if partial
            if data_completeness == 3:
                option_confidence += 5.0
            elif data_completeness == 2:
                option_confidence += 3.0
            
            # Consistency boost: +3 if all component scores within 20 points
            if is_consistent:
                option_confidence += 3.0
            
            # Cap at 100.0
            option_confidence = max(50.0, min(100.0, option_confidence))
            
            # Database writes removed - data flows through context only
            # Ensure option_name is always a string
            option_name = detail.get("option_name") or detail["option_id"]
            if not isinstance(option_name, str):
                option_name = str(option_name) if option_name else str(detail["option_id"])
            
            recommendations_out.append(
                {
                    "recommendation_id": recommendation_id,
                    "option_id": str(detail["option_id"]),  # Ensure string
                    "option_name": option_name,  # Guaranteed string
                    "rank": idx,
                    "overall_score": detail["overall_score"],
                    "revenue_score": detail["revenue_score"],
                    "equity_score": detail["equity_score"],
                    "load_management_score": detail["load_management_score"],
                    "competitive_score": comp_score_for_option,
                    "customer_satisfaction_score": detail["customer_satisfaction_score"],
                    "confidence_score": round(option_confidence, 2),  # Per-option confidence
                    "tradeoffs": tradeoffs,
                    "rationale": rationale,
                }
            )

        # Database writes removed - data flows through context only
        top = recommendations_out[0] if recommendations_out else None
        if top:
            # Calculate confidence score based on score separation and absolute score
            # Target: >95% confidence for good options (score >= 80)
            # Improved formula to consistently produce >95% for validated options
            top_score = top.get("overall_score", 0.0)
            top_per_option_confidence = top.get("confidence_score", 0.0)  # Per-option confidence from above
            confidence_score = 75.0  # Higher base default
            
            if len(recommendations_out) > 1:
                second_score = recommendations_out[1].get("overall_score", 0.0) if len(recommendations_out) > 1 else top_score
                score_gap = top_score - second_score
                
                # Improved confidence calculation for better options
                if top_score >= 80.0:
                    # High quality options: start at 90%, boost with gap and score quality
                    base_confidence = 90.0
                    gap_boost = min(8.0, score_gap * 2.0)  # Up to 8 points for gap
                    score_boost = (top_score - 80.0) * 0.5  # Up to 10 points for score quality
                    confidence_score = min(100.0, base_confidence + gap_boost + score_boost)
                elif top_score >= 70.0:
                    # Good quality options: start at 85%, boost with gap
                    base_confidence = 85.0
                    gap_boost = min(10.0, score_gap * 2.0)
                    score_boost = (top_score - 70.0) * 0.5
                    confidence_score = min(98.0, base_confidence + gap_boost + score_boost)
                else:
                    # Lower scores: use adjusted formula
                    gap_boost = min(15.0, score_gap * 3.0)
                    score_quality_boost = max(0.0, (top_score - 50.0) * 0.6) if top_score > 50.0 else 0.0
                    confidence_score = max(60.0, min(90.0, 75.0 + gap_boost + score_quality_boost))
            else:
                # Single option: base confidence on absolute score quality
                if top_score >= 80.0:
                    # High quality single option = high confidence (>95%)
                    confidence_score = min(100.0, 90.0 + (top_score - 80.0) * 0.5)
                elif top_score >= 70.0:
                    # Good quality single option = good confidence (85-95%)
                    confidence_score = min(95.0, 85.0 + (top_score - 70.0) * 1.0)
                else:
                    # Lower scores = lower confidence
                    confidence_score = max(60.0, min(85.0, 70.0 + (top_score - 50.0) * 0.75)) if top_score >= 50.0 else max(60.0, min(70.0, 60.0 + top_score * 0.2))
            
            # Ensure option_name is always a string
            top_option_name = top.get("option_name") or top["option_id"]
            if not isinstance(top_option_name, str):
                top_option_name = str(top_option_name) if top_option_name else str(top["option_id"])
            
            # Use per-option confidence from recommendations_out for consistency
            # The top recommendation should use the same confidence score as shown in the table
            top_per_option_confidence = top.get("confidence_score", 0.0)  # This is the per-option confidence from recommendations_out[0]
            
            top = {
                "option_id": str(top["option_id"]),  # Ensure string
                "option_name": top_option_name,  # Guaranteed string
                "overall_score": top.get("overall_score", 0.0),
                "confidence_score": top_per_option_confidence,  # Use per-option confidence for consistency
                "rationale": top.get("rationale", "No rationale provided."),
            }
        out = {
            "ok": True,
            "recommendations": recommendations_out,
            "top_recommendation": top,
        }
        _logger.output("rate_case_build_recommendations OUTPUT: recommendation_count={}", len(recommendations_out))
        return out
    finally:
        conn.close()


@pipeline_tool(toolkit="rate_case", name="rate_case_complete_pipeline_run")
def rate_case_complete_pipeline_run(
    db_file: str,
    run_id: str,
    summary: str,
    file_path: str,
    recommended_option_id: Optional[str] = None,
    recommended_option_name: Optional[str] = None,
    final_option_id: Optional[str] = None,
    final_option_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Complete a pipeline run by updating pipeline_runs table with final artifacts and marking as completed.
    This should be called by the artifact generator agent after generating the consolidated report.
    
    Args:
        db_file: Database file path
        run_id: The run_id to update (from rate_case_data_summarizer.run_id)
        summary: Required. Summary of the pipeline execution and results.
        file_path: Path to the consolidated report file (relative from project_dir)
        recommended_option_id: Optional. The option_id that was recommended
        recommended_option_name: Optional. The option_name that was recommended
        final_option_id: Optional. The option_id that was finally selected
        final_option_name: Optional. The option_name that was finally selected
    """
    _logger.input(
        "rate_case_complete_pipeline_run INPUT: db_file={}, run_id={}, file_path={}",
        db_file,
        run_id,
        file_path,
    )
    if not summary or not summary.strip():
        raise ValueError("summary is required and cannot be empty")
    if not file_path or not file_path.strip():
        raise ValueError("file_path is required and cannot be empty")
    
    conn = _connect(db_file)
    try:
        cur = conn.cursor()
        # Check if run_id exists
        cur.execute("SELECT run_id FROM pipeline_runs WHERE run_id = ?", [run_id])
        existing = cur.fetchone()
        if not existing:
            raise RuntimeError(f"Pipeline run not found: {run_id}. Call rate_case_record_pipeline_run first.")
        
        # Update entry with completion details
        cur.execute(
            """
            UPDATE pipeline_runs
            SET status = 'completed',
                summary = ?,
                file_path = ?,
                recommended_option_id = ?,
                recommended_option_name = ?,
                final_option_id = ?,
                final_option_name = ?,
                completed_at = CURRENT_TIMESTAMP
            WHERE run_id = ?
            """,
            [
                summary,
                file_path,
                recommended_option_id,
                recommended_option_name,
                final_option_id,
                final_option_name,
                run_id,
            ],
        )
        conn.commit()
        out = {"ok": True, "run_id": run_id, "status": "completed"}
        _logger.output("rate_case_complete_pipeline_run OUTPUT: ok=true, run_id={}", run_id)
        return out
    finally:
        conn.close()

