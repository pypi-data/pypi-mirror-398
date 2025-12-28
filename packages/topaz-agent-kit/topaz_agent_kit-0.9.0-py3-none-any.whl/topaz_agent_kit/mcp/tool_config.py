from topaz_agent_kit.mcp.decorators import ToolTimeout
from typing import Optional, Dict, Any

class ToolConfig:
    """Configuration for tool behavior based on timeout type"""
    
    TIMEOUTS = {
        ToolTimeout.QUICK: 5,        # 5 seconds
        ToolTimeout.MEDIUM: 30,      # 30 seconds
        ToolTimeout.LONG: 120,       # 2 minutes
        ToolTimeout.VERY_LONG: 300,  # 5 minutes
        ToolTimeout.UNLIMITED: None  # No timeout
    }
    
    DEFAULT_TIMEOUT = ToolTimeout.QUICK
    
    @classmethod
    def get_timeout_seconds(cls, timeout: ToolTimeout) -> Optional[int]:
        """Get timeout in seconds for a given timeout type"""
        return cls.TIMEOUTS[timeout]
    
    @classmethod
    def resolve_tool_config(cls, func) -> Dict[str, Any]:
        """Resolve final tool configuration from decorator or defaults"""
        metadata = getattr(func, '_tool_metadata', {})
        
        # Get timeout (from decorator or default)
        timeout = metadata.get('timeout', cls.DEFAULT_TIMEOUT)
        
        return {
            'timeout': timeout,
            'timeout_seconds': cls.get_timeout_seconds(timeout)
        }