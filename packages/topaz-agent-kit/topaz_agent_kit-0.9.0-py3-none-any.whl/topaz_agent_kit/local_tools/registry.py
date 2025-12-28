"""Tool registry for pipeline-specific local tools.

Provides decorator and module-level registry for discovering tools
defined in project-specific tool modules.
"""

from typing import Callable, Dict, Any, Optional, List
from dataclasses import dataclass
from functools import wraps
import inspect


@dataclass
class ToolSpec:
    """Metadata for a registered pipeline tool."""
    
    func: Callable
    toolkit: str
    name: str
    description: Optional[str] = None
    module_name: Optional[str] = None
    pipeline_id: Optional[str] = None
    
    def get_canonical_name(self) -> str:
        """Get canonical tool name: pipeline__toolkit__name"""
        if self.pipeline_id:
            return f"{self.pipeline_id}__{self.toolkit}__{self.name}"
        return f"{self.toolkit}__{self.name}"
    
    def get_dotted_name(self) -> str:
        """Get dotted tool name: pipeline.toolkit.name"""
        if self.pipeline_id:
            return f"{self.pipeline_id}.{self.toolkit}.{self.name}"
        return f"{self.toolkit}.{self.name}"


# Module-level registry: maps module_name -> list of ToolSpec
_module_registry: Dict[str, List[ToolSpec]] = {}


def pipeline_tool(
    toolkit: str,
    name: Optional[str] = None,
    description: Optional[str] = None
):
    """Decorator to register a function or class method as a pipeline-local tool.
    
    Can be used in two ways:
    1. As a function decorator:
        @pipeline_tool(toolkit="db", name="get_case")
        def get_case(db_path: str, case_id: str) -> dict:
            ...
    
    2. As a class decorator (registers all methods decorated with @pipeline_tool):
        @pipeline_tool(toolkit="db")
        class DatabaseTools:
            @pipeline_tool(toolkit="db", name="get_case")
            def get_case(self, db_path: str, case_id: str) -> dict:
                ...
    
    Args:
        toolkit: Toolkit identifier (e.g., "db", "navigator", "sim")
        name: Tool name (defaults to function/method name if not provided)
        description: Tool description (defaults to function docstring if not provided)
    """
    def decorator(obj: Any) -> Any:
        # Check if decorating a class
        if inspect.isclass(obj):
            # Class decorator: register all methods that are also decorated
            # This allows nested decorators like:
            # @pipeline_tool(toolkit="db")
            # class MyTools:
            #     @pipeline_tool(toolkit="db", name="tool1")
            #     def tool1(self): ...
            # 
            # The class decorator just marks the class; methods are registered individually
            # Return class unchanged
            return obj
        
        # Function/method decorator
        func = obj
        
        # Use function name if name not provided
        tool_name = name or func.__name__
        
        # Use docstring if description not provided
        tool_description = description or (inspect.getdoc(func) or "")
        
        # Get module name for registry
        module_name = func.__module__ if hasattr(func, '__module__') else None
        
        # Resolve annotations at decoration time (similar to FastMCP's @mcp.tool)
        # This ensures Pydantic (used by MAF) sees resolved type objects instead of strings
        # when modules use `from __future__ import annotations`
        try:
            from typing import get_type_hints, Optional
            func_module = inspect.getmodule(func)
            if func_module is not None:
                # Ensure Optional is available in module namespace
                if not hasattr(func_module, 'Optional'):
                    setattr(func_module, 'Optional', Optional)
                
                # Resolve string annotations to actual type objects
                resolved_hints = get_type_hints(func, globalns=func_module.__dict__)
                
                # Filter out 'return' key - __annotations__ only contains parameter annotations
                param_annotations = {k: v for k, v in resolved_hints.items() if k != 'return'}
                
                # Update function's __annotations__ with resolved types
                func.__annotations__ = param_annotations
        except Exception:
            # If annotation resolution fails, continue with original annotations
            # This allows tools to still work even if resolution fails
            pass
        
        # Wrap function with logging wrapper to track calls
        wrapped_func = _create_logging_wrapper(func, tool_name)
        
        # Create tool spec
        spec = ToolSpec(
            func=wrapped_func,
            toolkit=toolkit,
            name=tool_name,
            description=tool_description,
            module_name=module_name
        )
        
        # Register in module-level registry
        if module_name not in _module_registry:
            _module_registry[module_name] = []
        _module_registry[module_name].append(spec)
        
        # Return wrapped function
        return wrapped_func
    
    return decorator


def _create_logging_wrapper(func: Callable, tool_name: str) -> Callable:
    """Create a wrapper function that adds logging for tool calls.
    
    This wrapper logs when tools are called and completed, helping debug
    whether tools are being invoked by the framework.
    
    Args:
        func: Original function to wrap
        tool_name: Name of the tool (for logging)
    
    Returns:
        Wrapped function with logging (preserves original signature via @wraps)
    """
    from topaz_agent_kit.utils.logger import Logger
    
    # Create logger for this tool
    logger = Logger(f"Tool({tool_name})")
    
    # Check if function is async
    is_async = inspect.iscoroutinefunction(func)
    
    if is_async:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Log tool call (concise - don't log full args/kwargs as they may be large)
            logger.debug("Tool called: {}", tool_name)
            try:
                result = await func(*args, **kwargs)
                logger.debug("Tool completed: {}", tool_name)
                return result
            except Exception as e:
                logger.error("Tool failed: {} -> {}", tool_name, e)
                raise
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Log tool call (concise - don't log full args/kwargs as they may be large)
            logger.debug("Tool called: {}", tool_name)
            try:
                result = func(*args, **kwargs)
                logger.debug("Tool completed: {}", tool_name)
                return result
            except Exception as e:
                logger.error("Tool failed: {} -> {}", tool_name, e)
                raise
        return sync_wrapper


def get_registered_tools(module_name: Optional[str] = None) -> List[ToolSpec]:
    """Get all registered tools, optionally filtered by module name.
    
    Args:
        module_name: If provided, only return tools from this module.
                    If None, return all registered tools.
    
    Returns:
        List of ToolSpec objects
    """
    if module_name:
        return _module_registry.get(module_name, []).copy()
    
    # Return all tools from all modules
    all_tools = []
    for tools in _module_registry.values():
        all_tools.extend(tools)
    return all_tools


def clear_registry():
    """Clear the tool registry (mainly for testing)."""
    global _module_registry
    _module_registry = {}

