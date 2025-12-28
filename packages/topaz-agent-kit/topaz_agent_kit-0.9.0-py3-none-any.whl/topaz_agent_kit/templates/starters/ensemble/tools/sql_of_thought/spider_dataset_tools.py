"""
Spider Dataset Tools - Pipeline-specific local tools for SQL-of-Thought.

Provides tools for accessing Spider 1.0 dev dataset:
- Loading dev examples
- Getting database paths
- Accessing schema information
- Getting gold SQL for validation

Note: Query execution is handled by SQLite MCP tools, not these tools.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from topaz_agent_kit.local_tools.registry import pipeline_tool
from topaz_agent_kit.utils.logger import Logger

_logger = Logger("SpiderDatasetTools")


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------

def _get_spider_data_path(project_dir: str) -> Path:
    """Get the path to data/sot/spider_data directory."""
    project_path = Path(project_dir)
    spider_data_path = project_path / "data" / "sot" / "spider_data"
    return spider_data_path


def _load_json_file(file_path: Path) -> Any:
    """Load JSON file with error handling."""
    if not file_path.exists():
        _logger.error("File not found: {}", file_path)
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        _logger.error("Invalid JSON in file {}: {}", file_path, e)
        raise ValueError(f"Invalid JSON in file {file_path}: {e}")


def _get_dev_json_path(project_dir: str) -> Path:
    """Get path to dev.json file."""
    return _get_spider_data_path(project_dir) / "dev.json"


def _get_tables_json_path(project_dir: str) -> Path:
    """Get path to tables.json file."""
    return _get_spider_data_path(project_dir) / "tables.json"


def _get_database_dir(project_dir: str) -> Path:
    """Get path to database directory."""
    return _get_spider_data_path(project_dir) / "database"


# ---------------------------------------------------------------------
# Pipeline Tools
# ---------------------------------------------------------------------

@pipeline_tool(toolkit="spider_dataset", name="get_dev_examples")
def get_dev_examples(project_dir: str) -> List[Dict[str, Any]]:
    """
    Get all dev examples from dev.json.
    
    Args:
        project_dir: Absolute path to project root directory
        
    Returns:
        List of dev examples, each containing db_id, question, query, sql, etc.
    """
    try:
        dev_path = _get_dev_json_path(project_dir)
        examples = _load_json_file(dev_path)
        _logger.info("Loaded {} dev examples from {}", len(examples), dev_path)
        return examples
    except Exception as e:
        _logger.error("Failed to load dev examples: {}", e)
        raise


@pipeline_tool(toolkit="spider_dataset", name="get_example_by_index")
def get_example_by_index(project_dir: str, index: int) -> Dict[str, Any]:
    """
    Get a specific dev example by index.
    
    Args:
        project_dir: Absolute path to project root directory
        index: Zero-based index of the example
        
    Returns:
        Dev example dictionary
    """
    try:
        examples = get_dev_examples(project_dir)
        if index < 0 or index >= len(examples):
            raise IndexError(f"Index {index} out of range (0-{len(examples)-1})")
        return examples[index]
    except Exception as e:
        _logger.error("Failed to get example by index {}: {}", index, e)
        raise


@pipeline_tool(toolkit="spider_dataset", name="get_examples_by_db_id")
def get_examples_by_db_id(project_dir: str, db_id: str) -> List[Dict[str, Any]]:
    """
    Get all examples for a specific database ID.
    
    Args:
        project_dir: Absolute path to project root directory
        db_id: Database identifier (e.g., "concert_singer")
        
    Returns:
        List of examples for the specified database
    """
    try:
        examples = get_dev_examples(project_dir)
        filtered = [ex for ex in examples if ex.get("db_id") == db_id]
        _logger.info("Found {} examples for db_id: {}", len(filtered), db_id)
        return filtered
    except Exception as e:
        _logger.error("Failed to get examples for db_id {}: {}", db_id, e)
        raise


@pipeline_tool(toolkit="spider_dataset", name="get_database_path")
def get_database_path(project_dir: str, db_id: str) -> str:
    """
    Get absolute path to .sqlite file for a database ID.
    
    Args:
        project_dir: Absolute path to project root directory
        db_id: Database identifier (e.g., "concert_singer")
        
    Returns:
        Absolute path to the .sqlite file
    """
    try:
        db_dir = _get_database_dir(project_dir)
        db_file = db_dir / db_id / f"{db_id}.sqlite"
        
        if not db_file.exists():
            _logger.error("Database file not found: {}", db_file)
            raise FileNotFoundError(f"Database file not found: {db_file}")
        
        abs_path = str(db_file.resolve())
        _logger.debug("Database path for {}: {}", db_id, abs_path)
        return abs_path
    except Exception as e:
        _logger.error("Failed to get database path for {}: {}", db_id, e)
        raise


@pipeline_tool(toolkit="spider_dataset", name="get_schema_info")
def get_schema_info(project_dir: str, db_id: str) -> Dict[str, Any]:
    """
    Get schema information from tables.json for a database ID.
    
    Maps primary key indices to actual [table, column] pairs for easier use.
    
    Args:
        project_dir: Absolute path to project root directory
        db_id: Database identifier (e.g., "concert_singer")
        
    Returns:
        Schema information dictionary with tables, columns, foreign keys, etc.
        Includes `primary_keys_mapped` field with [table, column] pairs using original names.
    """
    try:
        tables_path = _get_tables_json_path(project_dir)
        all_tables = _load_json_file(tables_path)
        
        # Find schema for this db_id
        schema = None
        for table_info in all_tables:
            if table_info.get("db_id") == db_id:
                schema = table_info.copy()  # Make a copy to avoid modifying original
                break
        
        if not schema:
            _logger.error("Schema not found for db_id: {}", db_id)
            raise ValueError(f"Schema not found for db_id: {db_id}")
        
        # Map primary key indices to [table, column] pairs
        primary_keys_mapped = []
        if "primary_keys" in schema and "column_names_original" in schema:
            column_names_original = schema.get("column_names_original", [])
            primary_key_indices = schema.get("primary_keys", [])
            
            for pk_index in primary_key_indices:
                if 0 <= pk_index < len(column_names_original):
                    # column_names_original is a list of [table, column] pairs
                    table_col_pair = column_names_original[pk_index]
                    if isinstance(table_col_pair, list) and len(table_col_pair) == 2:
                        primary_keys_mapped.append(table_col_pair)
                    else:
                        _logger.warning("Invalid column_names_original format at index {}: {}", pk_index, table_col_pair)
                else:
                    _logger.warning("Primary key index {} out of range for column_names_original (length: {})", pk_index, len(column_names_original))
        
        # Add mapped primary keys to schema
        schema["primary_keys_mapped"] = primary_keys_mapped
        
        _logger.debug("Found schema for db_id: {}, mapped {} primary keys", db_id, len(primary_keys_mapped))
        return schema
    except Exception as e:
        _logger.error("Failed to get schema info for {}: {}", db_id, e)
        raise


@pipeline_tool(toolkit="spider_dataset", name="get_all_db_ids")
def get_all_db_ids(project_dir: str) -> List[str]:
    """
    Get list of all unique database IDs in the dev set.
    
    Args:
        project_dir: Absolute path to project root directory
        
    Returns:
        List of unique database IDs
    """
    try:
        examples = get_dev_examples(project_dir)
        db_ids = list(set(ex.get("db_id") for ex in examples if ex.get("db_id")))
        db_ids.sort()
        _logger.info("Found {} unique database IDs", len(db_ids))
        return db_ids
    except Exception as e:
        _logger.error("Failed to get database IDs: {}", e)
        raise


@pipeline_tool(toolkit="spider_dataset", name="get_gold_sql")
def get_gold_sql(project_dir: str, question_index: int) -> str:
    """
    Get gold SQL query for a question by index.
    
    Args:
        project_dir: Absolute path to project root directory
        question_index: Zero-based index of the question in dev.json
        
    Returns:
        Gold SQL query string
    """
    try:
        example = get_example_by_index(project_dir, question_index)
        gold_sql = example.get("query")
        if not gold_sql:
            raise ValueError(f"No gold SQL found for question index {question_index}")
        return gold_sql
    except Exception as e:
        _logger.error("Failed to get gold SQL for index {}: {}", question_index, e)
        raise

