from enum import Enum
from typing import Optional, Dict, Any
from functools import wraps

class ToolTimeout(Enum):
    QUICK = "quick"        # 5 seconds
    MEDIUM = "medium"      # 30 seconds
    LONG = "long"          # 2 minutes
    VERY_LONG = "very_long" # 5 minutes
    UNLIMITED = "unlimited"  # No timeout

def tool_metadata(timeout: Optional[ToolTimeout] = None):
    """Decorator for tool metadata with timeout configuration"""
    def decorator(func):
        func._tool_metadata = {
            'timeout': timeout
        }
        return func
    return decorator