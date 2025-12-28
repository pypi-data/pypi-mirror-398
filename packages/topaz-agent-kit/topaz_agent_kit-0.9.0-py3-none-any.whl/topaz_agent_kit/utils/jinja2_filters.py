"""
Jinja2 filter functions for template rendering.

These filters can be used in:
- HITL gate descriptions
- Agent YAML input templates
- Pattern descriptions
- Any Jinja2 template in the system
"""

from typing import Any, Optional, Dict, List, Tuple
from datetime import datetime


# ============================================================================
# NUMBER FORMATTING
# ============================================================================

def format_currency(value: Any, decimals: int = 2) -> str:
    """
    Format number as currency with commas and decimal places.
    
    Args:
        value: Number to format
        decimals: Number of decimal places (default: 2)
        
    Returns:
        Formatted string (e.g., "125,000.00")
        
    Examples:
        {{ 125000 | format_currency }}  # "125,000.00"
        {{ 125000.5 | format_currency }}  # "125,000.50"
        {{ None | format_currency }}  # "N/A"
    """
    if value is None:
        return "N/A"
    try:
        num = float(value)
        formatted = f"{num:,.{decimals}f}"
        return formatted
    except (ValueError, TypeError):
        return str(value) if value else "N/A"




def format_number(value: Any, decimals: int = 0, thousands_sep: str = ",") -> str:
    """
    Format number with optional decimals and thousands separator.
    
    Args:
        value: Number to format
        decimals: Number of decimal places (default: 0)
        thousands_sep: Thousands separator (default: ",")
        
    Returns:
        Formatted string
        
    Examples:
        {{ 1250000 | format_number }}  # "1,250,000"
        {{ 1250.5 | format_number(decimals=2) }}  # "1,250.50"
        {{ 1250 | format_number(decimals=2) }}  # "1,250.00"
    """
    if value is None:
        return "N/A"
    try:
        num = float(value)
        if thousands_sep:
            formatted = f"{num:,.{decimals}f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", thousands_sep)
        else:
            formatted = f"{num:.{decimals}f}"
        return formatted
    except (ValueError, TypeError):
        return str(value) if value else "N/A"


def format_percentage(value: Any, decimals: int = 1, multiply: bool = True) -> str:
    """
    Format number as percentage.
    
    Args:
        value: Number to format (0.85 for 85% or 85 for 85%)
        decimals: Number of decimal places (default: 1)
        multiply: If True, multiply by 100 (default: True for 0.85 -> 85%)
        
    Returns:
        Formatted string with % symbol
        
    Examples:
        {{ 0.85 | format_percentage }}  # "85.0%"
        {{ 85 | format_percentage(multiply=False) }}  # "85.0%"
        {{ 0.8523 | format_percentage(decimals=2) }}  # "85.23%"
    """
    if value is None:
        return "N/A"
    try:
        num = float(value)
        if multiply:
            num = num * 100
        formatted = f"{num:.{decimals}f}%"
        return formatted
    except (ValueError, TypeError):
        return str(value) if value else "N/A"


# ============================================================================
# SCORE/RISK COLOR CODING
# ============================================================================

def score_color(
    value: Any,
    thresholds: Optional[List[Tuple[float, str]]] = None,
    low_is_better: bool = False
) -> str:
    """
    Get color code for a score based on thresholds.
    
    Args:
        value: Score value
        thresholds: List of (threshold, color) tuples in ascending order.
                   Default: [(85, "#22c55e"), (70, "#f59e0b"), (50, "#ef4444"), (0, "#dc2626")]
        low_is_better: If True, lower scores are better (default: False)
        
    Returns:
        Hex color code
        
    Examples:
        # High is better (default)
        {{ 90 | score_color }}  # "#22c55e" (green)
        {{ 75 | score_color }}  # "#f59e0b" (amber)
        {{ 45 | score_color }}  # "#dc2626" (dark red)
        
        # Low is better (for risk scores)
        {{ 15 | score_color(low_is_better=True) }}  # "#22c55e" (green)
        {{ 35 | score_color(low_is_better=True) }}  # "#f59e0b" (amber)
        {{ 80 | score_color(low_is_better=True) }}  # "#dc2626" (dark red)
        
        # Custom thresholds
        {{ 75 | score_color(thresholds=[(80, "#green"), (60, "#yellow"), (0, "#red")]) }}
    """
    if value is None:
        return "#6b7280"  # Gray for N/A
    
    try:
        score = float(value)
    except (ValueError, TypeError):
        return "#6b7280"
    
    # Default thresholds: 85+ green, 70-84 amber, 50-69 red, <50 dark red
    if thresholds is None:
        thresholds = [(85, "#22c55e"), (70, "#f59e0b"), (50, "#ef4444"), (0, "#dc2626")]
    
    # For low_is_better, invert the logic
    if low_is_better:
        # Invert score: 100 becomes 0, 0 becomes 100
        score = 100 - score
        # Reverse thresholds order
        thresholds = sorted(thresholds, reverse=True)
    
    # Find matching threshold (first threshold that score >= threshold)
    for threshold, color in thresholds:
        if score >= threshold:
            return color
    
    # Fallback to last threshold color
    return thresholds[-1][1] if thresholds else "#6b7280"


def risk_score_color(value: Any) -> str:
    """
    Get color code for risk score where lower is better (0-100 scale).
    
    Common use case: Risk scores where 0-25 is good, 76-100 is bad.
    
    Args:
        value: Risk score (0-100, lower is better)
        
    Returns:
        Hex color code
        
    Examples:
        {{ 15 | risk_score_color }}  # "#22c55e" (green - low risk)
        {{ 35 | risk_score_color }}  # "#f59e0b" (amber - medium risk)
        {{ 65 | risk_score_color }}  # "#ef4444" (red - high risk)
        {{ 85 | risk_score_color }}  # "#dc2626" (dark red - very high risk)
    """
    if value is None:
        return "#6b7280"  # Gray for N/A
    
    try:
        score = float(value)
    except (ValueError, TypeError):
        return "#6b7280"
    
    # Risk score thresholds: 0-25 green, 26-50 amber, 51-75 red, 76-100 dark red
    # Thresholds are in descending order for "first match >= threshold" logic
    thresholds = [(76, "#dc2626"), (51, "#ef4444"), (26, "#f59e0b"), (0, "#22c55e")]
    
    # Find matching threshold (first threshold that score >= threshold)
    for threshold, color in thresholds:
        if score >= threshold:
            return color
    
    # Fallback to green (lowest risk)
    return "#22c55e"


def credit_score_color(value: Any) -> str:
    """
    Get color code for credit/quality score where higher is better (0-100 scale).
    
    Common use case: Credit scores, quality scores where 85-100 is excellent.
    
    Args:
        value: Score (0-100, higher is better)
        
    Returns:
        Hex color code
        
    Examples:
        {{ 90 | credit_score_color }}  # "#22c55e" (green - excellent)
        {{ 75 | credit_score_color }}  # "#f59e0b" (amber - good)
        {{ 55 | credit_score_color }}  # "#ef4444" (red - fair)
        {{ 35 | credit_score_color }}  # "#dc2626" (dark red - poor)
    """
    return score_color(value, low_is_better=False)


def status_color(value: Any, custom_mapping: Optional[dict] = None) -> str:
    """
    Get color code for status/state values (text-based).
    
    Maps common status strings to appropriate colors:
    - Risk/Level: low (green), medium (amber), high (red), critical (dark red)
    - Validation: valid (green), invalid (red), pending (amber)
    - Test/Check: pass/passed (green), fail/failed (red), warning (amber), error (red)
    - Coverage: covered (green), not covered/uncovered (red), partial (amber)
    - General: yes/true (green), no/false (red), unknown/n/a (gray)
    
    Args:
        value: Status value (string, boolean, or None)
        custom_mapping: Optional dict to override default mappings
        
    Returns:
        Hex color code
        
    Examples:
        {{ "low" | status_color }}  # "#22c55e" (green)
        {{ "high" | status_color }}  # "#ef4444" (red)
        {{ "valid" | status_color }}  # "#22c55e" (green)
        {{ "invalid" | status_color }}  # "#ef4444" (red)
        {{ "pass" | status_color }}  # "#22c55e" (green)
        {{ "fail" | status_color }}  # "#ef4444" (red)
        {{ "warning" | status_color }}  # "#f59e0b" (amber)
        {{ "covered" | status_color }}  # "#22c55e" (green)
        {{ "not covered" | status_color }}  # "#ef4444" (red)
        {{ True | status_color }}  # "#22c55e" (green)
        {{ False | status_color }}  # "#ef4444" (red)
        
        # In markdown tables (safe - filters don't introduce whitespace):
        | Status | Value |
        |--------|-------|
        | Validation | <span style="color: {{ status | status_color }};">{{ status }}</span> |
        
        # Custom mapping
        {{ "custom_status" | status_color(custom_mapping={"custom_status": "#blue"}) }}
        
    Note: Filters themselves don't introduce whitespace. However, if you use Jinja2 tags
    (like {% set %}) in table cells, use whitespace control ({%- and -%}) to prevent
    markdown table formatting issues.
    """
    if value is None:
        return "#6b7280"  # Gray for N/A
    
    # Convert to string and normalize (lowercase, strip whitespace)
    status_str = str(value).lower().strip()
    
    # Default color mappings
    default_mapping = {
        # Risk/Level indicators
        "low": "#22c55e",  # green
        "medium": "#f59e0b",  # amber
        "high": "#ef4444",  # red
        "critical": "#dc2626",  # dark red
        "severe": "#dc2626",  # dark red
        
        # Validation status
        "valid": "#22c55e",  # green
        "invalid": "#ef4444",  # red
        "pending": "#f59e0b",  # amber
        "in_progress": "#f59e0b",  # amber
        "processing": "#f59e0b",  # amber
        
        # Test/Check results
        "pass": "#22c55e",  # green
        "passed": "#22c55e",  # green
        "fail": "#ef4444",  # red
        "failed": "#ef4444",  # red
        "warning": "#f59e0b",  # amber
        "warn": "#f59e0b",  # amber
        "error": "#ef4444",  # red
        "success": "#22c55e",  # green
        "successful": "#22c55e",  # green
        
        # Coverage status
        "covered": "#22c55e",  # green
        "not covered": "#ef4444",  # red
        "uncovered": "#ef4444",  # red
        "partial": "#f59e0b",  # amber
        "partially covered": "#f59e0b",  # amber
        
        # Boolean values
        "yes": "#22c55e",  # green
        "true": "#22c55e",  # green
        "no": "#ef4444",  # red
        "false": "#ef4444",  # red
        
        # Unknown/undefined
        "unknown": "#6b7280",  # gray
        "n/a": "#6b7280",  # gray
        "na": "#6b7280",  # gray
        "none": "#6b7280",  # gray
        "undefined": "#6b7280",  # gray
    }
    
    # Merge custom mapping with defaults (custom takes precedence)
    mapping = {**default_mapping, **(custom_mapping or {})}
    
    # Try exact match first
    if status_str in mapping:
        return mapping[status_str]
    
    # Try partial matches for compound statuses (e.g., "not covered" contains "covered")
    # Check for longest matching key first (to prioritize "not covered" over "covered")
    matched_key = None
    for key in sorted(mapping.keys(), key=len, reverse=True):
        # Only match if the key is contained in the status string (not the other way around)
        # This ensures "not covered" matches "not covered" but "covered" doesn't match "not covered"
        if key in status_str:
            matched_key = key
            break
    
    if matched_key:
        return mapping[matched_key]
    
    # Fallback to gray for unknown status
    return "#6b7280"


# ============================================================================
# TEXT FORMATTING
# ============================================================================

def truncate_text(value: Any, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix.
    
    Args:
        value: Text to truncate
        max_length: Maximum length (default: 100)
        suffix: Suffix to add when truncated (default: "...")
        
    Returns:
        Truncated text
        
    Examples:
        {{ "Very long text here" | truncate_text(10) }}  # "Very long..."
        {{ "Short" | truncate_text(10) }}  # "Short"
    """
    if value is None:
        return ""
    
    text = str(value)
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def pluralize(value: Any, singular: str, plural: Optional[str] = None) -> str:
    """
    Return singular or plural form based on count.
    
    Args:
        value: Count value
        singular: Singular form (e.g., "item")
        plural: Plural form (default: singular + "s")
        
    Returns:
        Singular or plural form
        
    Examples:
        {{ 1 | pluralize("item") }}  # "item"
        {{ 5 | pluralize("item") }}  # "items"
        {{ 1 | pluralize("child", "children") }}  # "child"
        {{ 5 | pluralize("child", "children") }}  # "children"
    """
    if plural is None:
        plural = singular + "s"
    
    try:
        count = int(value)
        return singular if count == 1 else plural
    except (ValueError, TypeError):
        return plural


# ============================================================================
# DATE/TIME FORMATTING
# ============================================================================

def format_date(value: Any, format_str: str = "%Y-%m-%d") -> str:
    """
    Format date/datetime value.
    
    Args:
        value: Date string, datetime object, or timestamp
        format_str: strftime format string (default: "%Y-%m-%d")
        
    Returns:
        Formatted date string
        
    Examples:
        {{ "2025-01-28" | format_date }}  # "2025-01-28"
        {{ "2025-01-28" | format_date("%B %d, %Y") }}  # "January 28, 2025"
        {{ datetime_obj | format_date("%Y-%m-%d %H:%M") }}
    """
    if value is None:
        return "N/A"
    
    try:
        # Try parsing as datetime string
        if isinstance(value, str):
            # Try common formats
            for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"]:
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.strftime(format_str)
                except ValueError:
                    continue
            # If parsing fails, return as-is
            return value
        
        # Try as datetime object
        if isinstance(value, datetime):
            return value.strftime(format_str)
        
        # Try as timestamp
        if isinstance(value, (int, float)):
            dt = datetime.fromtimestamp(value)
            return dt.strftime(format_str)
        
        return str(value)
    except Exception:
        return str(value) if value else "N/A"


# ============================================================================
# FILE SIZE FORMATTING
# ============================================================================

def format_file_size(value: Any, binary: bool = False) -> str:
    """
    Format bytes as human-readable file size.
    
    Args:
        value: Size in bytes
        binary: If True, use binary units (KiB, MiB) instead of decimal (KB, MB)
        
    Returns:
        Formatted string (e.g., "1.5 MB", "500 KB")
        
    Examples:
        {{ 1572864 | format_file_size }}  # "1.5 MB"
        {{ 1572864 | format_file_size(binary=True) }}  # "1.5 MiB"
        {{ 512 | format_file_size }}  # "512 B"
    """
    if value is None:
        return "N/A"
    
    try:
        size = int(value)
    except (ValueError, TypeError):
        return str(value) if value else "N/A"
    
    if binary:
        units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
        base = 1024
    else:
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        base = 1000
    
    if size == 0:
        return "0 B"
    
    unit_index = 0
    while size >= base and unit_index < len(units) - 1:
        size /= base
        unit_index += 1
    
    # Format with appropriate decimals
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    elif size < 10:
        return f"{size:.2f} {units[unit_index]}"
    elif size < 100:
        return f"{size:.1f} {units[unit_index]}"
    else:
        return f"{int(size)} {units[unit_index]}"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def safe_divide(numerator: Any, denominator: Any, default: Any = 0) -> Any:
    """
    Safely divide two numbers, returning default if denominator is zero or invalid.
    
    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value if division fails (default: 0)
        
    Returns:
        Division result or default
        
    Examples:
        {{ 10 | safe_divide(2) }}  # 5.0
        {{ 10 | safe_divide(0) }}  # 0
        {{ 10 | safe_divide(0, "N/A") }}  # "N/A"
    """
    try:
        num = float(numerator)
        den = float(denominator)
        if den == 0:
            return default
        return num / den
    except (ValueError, TypeError, ZeroDivisionError):
        return default


def default_if_none(value: Any, default: str = "N/A") -> Any:
    """
    Return default value if input is None.
    
    Args:
        value: Value to check
        default: Default value (default: "N/A")
        
    Returns:
        Value or default
        
    Examples:
        {{ None | default_if_none }}  # "N/A"
        {{ None | default_if_none("—") }}  # "—"
        {{ "value" | default_if_none }}  # "value"
    """
    return default if value is None else value


def mask_sensitive(value: Any, visible_chars: int = 4, mask_char: str = "*") -> str:
    """
    Mask sensitive data, showing only first N characters.
    
    Args:
        value: Value to mask
        visible_chars: Number of characters to show (default: 4)
        mask_char: Character to use for masking (default: "*")
        
    Returns:
        Masked string
        
    Examples:
        {{ "1234567890" | mask_sensitive }}  # "1234******"
        {{ "1234567890" | mask_sensitive(2) }}  # "12********"
        {{ "email@example.com" | mask_sensitive(5) }}  # "email***********"
    """
    if value is None:
        return "N/A"
    
    text = str(value)
    if len(text) <= visible_chars:
        return mask_char * len(text)
    
    return text[:visible_chars] + mask_char * (len(text) - visible_chars)


def format_phone(value: Any, format_str: str = "us") -> str:
    """
    Format phone number.
    
    Args:
        value: Phone number (string or number)
        format_str: Format style - "us" (default), "international", or "compact"
        
    Returns:
        Formatted phone number
        
    Examples:
        {{ "1234567890" | format_phone }}  # "(123) 456-7890"
        {{ "1234567890" | format_phone("international") }}  # "+1 123-456-7890"
        {{ "1234567890" | format_phone("compact") }}  # "123-456-7890"
    """
    if value is None:
        return "N/A"
    
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, str(value)))
    
    if not digits:
        return str(value)
    
    if format_str == "us" and len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif format_str == "international" and len(digits) >= 10:
        if len(digits) == 11 and digits[0] == "1":
            return f"+1 {digits[1:4]}-{digits[4:7]}-{digits[7:]}"
        elif len(digits) == 10:
            return f"+1 {digits[0:3]}-{digits[3:6]}-{digits[6:]}"
    elif format_str == "compact" and len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    
    # Fallback: return with dashes every 3 digits
    if len(digits) >= 7:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    
    return digits


def format_duration(seconds: Any, compact: bool = False) -> str:
    """
    Format duration in seconds as human-readable string.
    
    Args:
        seconds: Duration in seconds
        compact: If True, use compact format (default: False)
        
    Returns:
        Formatted duration string
        
    Examples:
        {{ 3665 | format_duration }}  # "1 hour 1 minute 5 seconds"
        {{ 3665 | format_duration(compact=True) }}  # "1h 1m 5s"
        {{ 90 | format_duration }}  # "1 minute 30 seconds"
    """
    if seconds is None:
        return "N/A"
    
    try:
        total_seconds = int(float(seconds))
    except (ValueError, TypeError):
        return str(seconds) if seconds else "N/A"
    
    if total_seconds < 0:
        return "0 seconds"
    
    if total_seconds == 0:
        return "0 seconds" if not compact else "0s"
    
    # Calculate time components
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    
    parts = []
    
    if days > 0:
        parts.append(f"{days} {'day' if days == 1 else 'days'}" if not compact else f"{days}d")
    if hours > 0:
        parts.append(f"{hours} {'hour' if hours == 1 else 'hours'}" if not compact else f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes} {'minute' if minutes == 1 else 'minutes'}" if not compact else f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs} {'second' if secs == 1 else 'seconds'}" if not compact else f"{secs}s")
    
    if compact:
        return " ".join(parts)
    else:
        if len(parts) == 1:
            return parts[0]
        elif len(parts) == 2:
            return f"{parts[0]} and {parts[1]}"
        else:
            return ", ".join(parts[:-1]) + f", and {parts[-1]}"


def highlight_text(value: Any, search_terms: Any, highlight_class: str = "highlight") -> str:
    """
    Highlight search terms in text (basic implementation).
    
    Note: This is a simple implementation. For complex highlighting,
    consider doing it in the frontend or with more sophisticated logic.
    
    Args:
        value: Text to search in
        search_terms: Single term or list of terms to highlight
        highlight_class: CSS class name for highlighting (default: "highlight")
        
    Returns:
        Text with highlighted terms wrapped in <mark> tags
        
    Examples:
        {{ "Hello world" | highlight_text("world") }}  # "Hello <mark>world</mark>"
        {{ text | highlight_text(["term1", "term2"]) }}
    """
    if value is None:
        return ""
    
    text = str(value)
    
    if not search_terms:
        return text
    
    # Convert single term to list
    if isinstance(search_terms, str):
        search_terms = [search_terms]
    
    # Simple case-insensitive highlighting
    for term in search_terms:
        if term:
            import re
            pattern = re.escape(str(term))
            text = re.sub(
                f"({pattern})",
                f'<mark class="{highlight_class}">\\1</mark>',
                text,
                flags=re.IGNORECASE
            )
    
    return text


# ============================================================================
# REGISTRATION FUNCTION
# ============================================================================

def register_jinja2_filters(env) -> None:
    """
    Register all Jinja2 filters on an Environment.
    
    Args:
        env: Jinja2 Environment instance
        
    Usage:
        from jinja2 import Environment
        from topaz_agent_kit.utils.jinja2_filters import register_jinja2_filters
        
        env = Environment()
        register_jinja2_filters(env)
    """
    filters = {
        # Number formatting
        "format_currency": format_currency,
        "format_number": format_number,
        "format_percentage": format_percentage,
        
        # Score/risk color coding
        "score_color": score_color,
        "risk_score_color": risk_score_color,
        "credit_score_color": credit_score_color,
        "status_color": status_color,
        
        # Text formatting
        "truncate_text": truncate_text,
        "pluralize": pluralize,
        "highlight_text": highlight_text,
        
        # Date/time formatting
        "format_date": format_date,
        "format_duration": format_duration,
        
        # File size formatting
        "format_file_size": format_file_size,
        
        # Data masking
        "mask_sensitive": mask_sensitive,
        "format_phone": format_phone,
        
        # Utility functions
        "safe_divide": safe_divide,
        "default_if_none": default_if_none,
    }
    
    for name, func in filters.items():
        env.filters[name] = func

