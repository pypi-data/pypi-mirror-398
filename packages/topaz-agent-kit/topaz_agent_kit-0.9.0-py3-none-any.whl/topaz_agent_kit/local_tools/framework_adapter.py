"""Framework adapters for pipeline-local tools.

Converts ToolSpec objects into framework-compatible tool objects
for each supported framework (agno, langgraph, crewai, adk, sk, oak, maf).
"""

from typing import List, Any, Dict, Optional
import inspect
import traceback
from functools import partial

from topaz_agent_kit.local_tools.registry import ToolSpec
from topaz_agent_kit.utils.logger import Logger


class FrameworkToolAdapter:
    """Adapts ToolSpec objects to framework-specific tool formats."""
    
    def __init__(self, framework: str, logger: Optional[Logger] = None):
        """Initialize adapter.
        
        Args:
            framework: Framework name (agno, langgraph, crewai, adk, sk, oak, maf)
            logger: Logger instance (creates one if not provided)
        """
        self.framework = framework
        self.logger = logger or Logger(f"FrameworkToolAdapter({framework})")
    
    def adapt_tools(self, tool_specs: List[ToolSpec]) -> List[Any]:
        """Convert ToolSpec objects to framework-compatible tool objects.
        
        Args:
            tool_specs: List of ToolSpec objects to adapt
        
        Returns:
            List of framework-compatible tool objects
        """
        if not tool_specs:
            return []
        
        if self.framework == "agno":
            return self._adapt_for_agno(tool_specs)
        elif self.framework == "langgraph":
            return self._adapt_for_langgraph(tool_specs)
        elif self.framework == "crewai":
            return self._adapt_for_crewai(tool_specs)
        elif self.framework == "adk":
            return self._adapt_for_adk(tool_specs)
        elif self.framework == "sk":
            return self._adapt_for_sk(tool_specs)
        elif self.framework == "oak":
            return self._adapt_for_oak(tool_specs)
        elif self.framework == "maf":
            return self._adapt_for_maf(tool_specs)
        else:
            self.logger.warning("Unknown framework {}, returning raw functions", self.framework)
            return [spec.func for spec in tool_specs]
    
    def _adapt_for_agno(self, tool_specs: List[ToolSpec]) -> List[Any]:
        """Adapt tools for Agno framework.
        
        Agno accepts tools as a list of callables or tool objects.
        For now, return functions directly (Agno can wrap them if needed).
        """
        # Agno can accept functions directly or wrapped in tool objects
        # For v1, return functions - Agno SDK will handle wrapping
        return [spec.func for spec in tool_specs]
    
    def _adapt_for_langgraph(self, tool_specs: List[ToolSpec]) -> List[Any]:
        """Adapt tools for LangGraph framework.
        
        LangGraph expects tools as LangChain BaseTool objects.
        We'll create simple function tools with JSON parsing for complex types.
        """
        try:
            from langchain_core.tools import StructuredTool
            from typing import get_origin, get_args
            from typing import Dict, List, Optional
            import json
            
            def create_wrapper(func, sig):
                """Create wrapper that parses JSON strings for complex type parameters."""
                complex_params = set()
                
                # Detect complex type parameters
                from typing import Union
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                    param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
                    origin = get_origin(param_type)
                    
                    # Handle Optional[T] which is actually Union[T, None]
                    if origin is Union:
                        args = get_args(param_type)
                        non_none_args = [arg for arg in args if arg is not type(None)]
                        if non_none_args:
                            for inner_type in non_none_args:
                                inner_origin = get_origin(inner_type)
                                if inner_origin in (dict, list):
                                    complex_params.add(param_name)
                                    break
                                elif str(inner_type).startswith('typing.Dict') or str(inner_type).startswith('typing.List'):
                                    complex_params.add(param_name)
                                    break
                    elif origin in (dict, list):
                        complex_params.add(param_name)
                    # Fallback: check string representation
                    elif hasattr(param_type, '__name__') and param_type.__name__ in ('Dict', 'List'):
                        complex_params.add(param_name)
                    elif str(param_type).startswith('typing.Dict') or str(param_type).startswith('typing.List'):
                        complex_params.add(param_name)
                
                if not complex_params:
                    # No complex types, return function as-is
                    return func
                
                # Create wrapper that parses JSON strings
                def wrapper(*args, **kwargs):
                    # Parse JSON strings for complex type parameters
                    parsed_kwargs = {}
                    for key, value in kwargs.items():
                        if key in complex_params and isinstance(value, str):
                            try:
                                parsed_kwargs[key] = json.loads(value)
                            except (json.JSONDecodeError, TypeError):
                                try:
                                    import ast
                                    parsed_kwargs[key] = ast.literal_eval(value)
                                except (ValueError, SyntaxError):
                                    parsed_kwargs[key] = value
                        else:
                            parsed_kwargs[key] = value
                    return func(*args, **parsed_kwargs)
                
                # Preserve function signature and metadata
                wrapper.__signature__ = sig
                wrapper.__name__ = func.__name__
                wrapper.__doc__ = func.__doc__
                # Also preserve annotations so StructuredTool/Pydantic can see parameter types
                try:
                    wrapper.__annotations__ = getattr(func, "__annotations__", {}).copy()
                except Exception:
                    # Best-effort; if this fails, StructuredTool will fall back to defaults
                    pass
                return wrapper
            
            tools = []
            for spec in tool_specs:
                # Create LangChain tool from function
                # Use just the tool name (no pipeline/toolkit prefix)
                tool_name = spec.name
                
                # Create wrapper for complex type handling
                sig = inspect.signature(spec.func)
                wrapped_func = create_wrapper(spec.func, sig)
                
                # Use StructuredTool.from_function() to create tool with custom name and description
                # This is the correct way to programmatically create LangChain tools
                langchain_tool_obj = StructuredTool.from_function(
                    func=wrapped_func,
                    name=tool_name,
                    description=spec.description or f"Tool: {spec.name}"
                )
                tools.append(langchain_tool_obj)
            
            return tools
        except ImportError as e:
            self.logger.error("langchain_core not available for LangGraph tools: {}", e)
            return []
        except Exception as e:
            self.logger.error("Failed to adapt tools for LangGraph: {}", e)
            self.logger.error("Traceback: {}", traceback.format_exc())
            return []
    
    def _adapt_for_crewai(self, tool_specs: List[ToolSpec]) -> List[Any]:
        """Adapt tools for CrewAI framework.
        
        CrewAI expects tools as CrewAI Tool objects or compatible callables.
        We add JSON parsing for complex types to handle serialization.
        """
        try:
            from crewai.tools import tool as crewai_tool
            from typing import get_origin, get_args
            from typing import Dict, List, Optional
            import json
            
            def create_wrapper(func, sig):
                """Create wrapper that parses JSON strings for complex type parameters."""
                complex_params = set()
                
                # Detect complex type parameters
                from typing import Union
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                    param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
                    origin = get_origin(param_type)
                    
                    # Handle Optional[T] which is actually Union[T, None]
                    if origin is Union:
                        args = get_args(param_type)
                        non_none_args = [arg for arg in args if arg is not type(None)]
                        if non_none_args:
                            for inner_type in non_none_args:
                                inner_origin = get_origin(inner_type)
                                if inner_origin in (dict, list):
                                    complex_params.add(param_name)
                                    break
                                elif str(inner_type).startswith('typing.Dict') or str(inner_type).startswith('typing.List'):
                                    complex_params.add(param_name)
                                    break
                    elif origin in (dict, list):
                        complex_params.add(param_name)
                    # Fallback: check string representation
                    elif hasattr(param_type, '__name__') and param_type.__name__ in ('Dict', 'List'):
                        complex_params.add(param_name)
                    elif str(param_type).startswith('typing.Dict') or str(param_type).startswith('typing.List'):
                        complex_params.add(param_name)
                
                if not complex_params:
                    # No complex types, return function as-is
                    return func
                
                # Create wrapper that parses JSON strings
                def wrapper(*args, **kwargs):
                    # Parse JSON strings for complex type parameters
                    parsed_kwargs = {}
                    for key, value in kwargs.items():
                        if key in complex_params and isinstance(value, str):
                            try:
                                parsed_kwargs[key] = json.loads(value)
                            except (json.JSONDecodeError, TypeError):
                                parsed_kwargs[key] = value
                        else:
                            parsed_kwargs[key] = value
                    return func(*args, **parsed_kwargs)
                
                # Preserve function signature and metadata
                wrapper.__signature__ = sig
                wrapper.__name__ = func.__name__
                wrapper.__doc__ = func.__doc__
                return wrapper
            
            tools = []
            for spec in tool_specs:
                # Create CrewAI tool from function
                # Use just the tool name (no pipeline/toolkit prefix)
                tool_name = spec.name
                
                # Create wrapper for complex type handling
                sig = inspect.signature(spec.func)
                wrapped_func = create_wrapper(spec.func, sig)
                
                # Ensure the wrapped function exposes the correct name and description
                wrapped_func.__name__ = tool_name
                if spec.description:
                    wrapped_func.__doc__ = spec.description
                
                # CrewAI @tool decorator syntax: @tool("Tool Name")
                crewai_tool_obj = crewai_tool(tool_name)(wrapped_func)
                tools.append(crewai_tool_obj)
            
            return tools
        except ImportError as e:
            self.logger.error("crewai not available for CrewAI tools: {}", e)
            return []
        except Exception as e:
            self.logger.error("Failed to adapt tools for CrewAI: {}", e)
            self.logger.error("Traceback: {}", traceback.format_exc())
            return []
    
    def _adapt_for_adk(self, tool_specs: List[ToolSpec]) -> List[Any]:
        """Adapt tools for ADK framework.
        
        ADK accepts tools as a list of callables or tool objects.
        Return functions directly for now.
        """
        return [spec.func for spec in tool_specs]
    
    def _adapt_for_sk(self, tool_specs: List[ToolSpec]) -> List[Any]:
        """Adapt tools for Semantic Kernel framework.
        
        SK expects tools as Kernel plugins (collections of functions).
        We create a plugin class with all tools as kernel functions.
        We add JSON parsing for complex types to handle serialization.
        """
        try:
            from semantic_kernel.functions import kernel_function, KernelPlugin
            from typing import get_origin, get_args
            from typing import Dict, List, Optional
            import json
            
            def create_sk_wrapper(func, tool_name, description, sig):
                """Create SK kernel function wrapper with proper closure capture and JSON parsing."""
                complex_params = set()
                
                # Detect complex type parameters
                from typing import Union
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                    param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
                    origin = get_origin(param_type)
                    
                    # Handle Optional[T] which is actually Union[T, None]
                    if origin is Union:
                        args = get_args(param_type)
                        non_none_args = [arg for arg in args if arg is not type(None)]
                        if non_none_args:
                            for inner_type in non_none_args:
                                inner_origin = get_origin(inner_type)
                                if inner_origin in (dict, list):
                                    complex_params.add(param_name)
                                    break
                                elif str(inner_type).startswith('typing.Dict') or str(inner_type).startswith('typing.List'):
                                    complex_params.add(param_name)
                                    break
                    elif origin in (dict, list):
                        complex_params.add(param_name)
                    # Fallback: check string representation
                    elif hasattr(param_type, '__name__') and param_type.__name__ in ('Dict', 'List'):
                        complex_params.add(param_name)
                    elif str(param_type).startswith('typing.Dict') or str(param_type).startswith('typing.List'):
                        complex_params.add(param_name)
                
                # CRITICAL: Create a function with the exact same signature as the original
                # SK inspects the function signature to generate the schema, and if we use (*args, **kwargs),
                # SK will incorrectly treat 'kwargs' as a required parameter.
                # Solution: Create a wrapper that preserves the original signature by using functools.wraps
                # and explicitly setting __signature__ BEFORE the decorator is applied.
                import functools
                
                # Create the actual wrapper function that handles nested args/kwargs
                def _wrapper_impl(*args, **kwargs):
                    # SK may pass arguments nested under 'args' or 'kwargs' keys: {"args": {...}, "kwargs": {...}}
                    # Handle both cases and merge if both exist
                    actual_kwargs = {}
                    
                    # Check for nested arguments in 'kwargs' key first (SK sometimes uses this)
                    nested_kwargs = kwargs.get('kwargs', {})
                    nested_args = kwargs.get('args', {})
                    
                    # If both exist, merge them (kwargs takes priority)
                    if isinstance(nested_kwargs, dict) and len(nested_kwargs) > 0:
                        actual_kwargs.update(nested_kwargs)
                    if isinstance(nested_args, dict) and len(nested_args) > 0:
                        # Merge args into kwargs (kwargs values take priority if there are conflicts)
                        for k, v in nested_args.items():
                            if k not in actual_kwargs:
                                actual_kwargs[k] = v
                    
                    # If we found nested arguments, use them
                    if actual_kwargs:
                        # Merge with any other top-level kwargs (excluding 'args' and 'kwargs' keys)
                        for key, value in kwargs.items():
                            if key not in ('args', 'kwargs'):
                                actual_kwargs[key] = value
                        kwargs = actual_kwargs
                    # If no nested arguments found but 'args' or 'kwargs' keys exist (even if empty),
                    # remove them and use direct kwargs
                    elif 'args' in kwargs or 'kwargs' in kwargs:
                        kwargs = {k: v for k, v in kwargs.items() if k not in ('args', 'kwargs')}
                    
                    # Parse JSON strings for complex type parameters
                    if complex_params:
                        parsed_kwargs = {}
                        for key, value in kwargs.items():
                            if key in complex_params and isinstance(value, str):
                                try:
                                    parsed_kwargs[key] = json.loads(value)
                                except (json.JSONDecodeError, TypeError):
                                    try:
                                        import ast
                                        parsed_kwargs[key] = ast.literal_eval(value)
                                    except (ValueError, SyntaxError):
                                        parsed_kwargs[key] = value
                            else:
                                parsed_kwargs[key] = value
                        return func(*args, **parsed_kwargs)
                    return func(*args, **kwargs)
                
                # CRITICAL: Set signature BEFORE applying decorator so SK sees the correct signature
                # Use functools.wraps to copy metadata, then override signature
                _wrapper_impl = functools.wraps(func)(_wrapper_impl)
                _wrapper_impl.__signature__ = sig
                _wrapper_impl.__name__ = tool_name
                
                # Apply the kernel_function decorator AFTER setting signature
                sk_wrapper = kernel_function(
                    name=tool_name,
                    description=description or f"Tool: {tool_name}"
                )(_wrapper_impl)
                
                # Ensure signature is still set after decoration (some decorators may reset it)
                sk_wrapper.__signature__ = sig
                
                return sk_wrapper
            
            # Create a plugin class dynamically with all tools as methods
            # SK expects plugins to be classes with @kernel_function decorated methods
            plugin_methods = {}
            for spec in tool_specs:
                # Use just the tool name (no pipeline/toolkit prefix)
                tool_name = spec.name
                
                # Get function signature for complex type detection
                sig = inspect.signature(spec.func)
                
                # Create wrapper with proper closure capture and JSON parsing
                sk_wrapper = create_sk_wrapper(spec.func, tool_name, spec.description, sig)
                
                # Add as a method to the plugin class
                plugin_methods[tool_name] = sk_wrapper
            
            # Create a plugin class dynamically
            # Use a generic plugin name since we're bundling all local tools together
            PluginClass = type('LocalToolsPlugin', (object,), plugin_methods)
            
            # Create plugin instance
            plugin_instance = PluginClass()
            
            # Wrap in KernelPlugin to make it compatible with SK
            # KernelPlugin expects a class or dict of functions
            plugin = KernelPlugin(name="local_tools", functions=plugin_methods)
            
            return [plugin]
        except ImportError:
            self.logger.error("semantic_kernel not available for SK tools")
            return []
    
    def _adapt_for_oak(self, tool_specs: List[ToolSpec]) -> List[Any]:
        """Adapt tools for OAK framework.
        
        OAK expects tools as FunctionTool objects or function_tool decorated functions.
        Since Dict[str, Any] return types cause strict Pydantic schema issues,
        we use FunctionTool directly with a flexible JSON schema.
        """
        try:
            from agents import FunctionTool, RunContextWrapper
            import inspect
            import json
            from typing import Any as TypingAny
            
            tools = []
            for spec in tool_specs:
                # For OAK, use just the tool name (no pipeline/toolkit prefix)
                # This makes it easier for agents to call tools and avoids OpenAI's 64-char limit
                # Tools are already scoped to the agent/pipeline context
                tool_name = spec.name
                
                # Ensure it doesn't exceed OpenAI's 64 character limit
                if len(tool_name) > 64:
                    tool_name = tool_name[:64]
                    self.logger.warning("Tool name truncated to 64 chars: {} -> {}", spec.name, tool_name)
                
                original_func = spec.func
                is_async = inspect.iscoroutinefunction(original_func)
                
                # Get function signature for parameter schema
                sig = inspect.signature(original_func)
                params = {}
                complex_params = set()  # Track parameters that are dict/list types
                
                # Import typing helpers to detect complex types
                from typing import get_origin, get_args, Union
                from typing import Dict, List, Optional
                
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                    param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
                    
                    # Check if it's a complex type (Dict, List, Optional[Dict], Optional[List[Dict]], etc.)
                    origin = get_origin(param_type)
                    is_complex = False
                    
                    # Handle Optional[T] which is actually Union[T, None]
                    if origin is Union:
                        # Optional[Dict] or Optional[List[Dict]] -> Union[Dict, None] or Union[List[Dict], None]
                        args = get_args(param_type)
                        # Filter out None from union args
                        non_none_args = [arg for arg in args if arg is not type(None)]
                        if non_none_args:
                            # Check if any non-None arg is a complex type
                            for inner_type in non_none_args:
                                inner_origin = get_origin(inner_type)
                                # Check if inner type is dict/list (builtin types)
                                if inner_origin in (dict, list):
                                    is_complex = True
                                    break
                                # Also check string representation for nested types like List[Dict]
                                elif str(inner_type).startswith('typing.Dict') or str(inner_type).startswith('typing.List'):
                                    is_complex = True
                                    break
                    elif origin in (dict, list):
                        # Dict[str, Any] -> origin is dict, List[str] -> origin is list
                        is_complex = True
                    # Fallback: check string representation for typing.Dict, typing.List
                    elif hasattr(param_type, '__name__') and param_type.__name__ in ('Dict', 'List'):
                        is_complex = True
                    elif str(param_type).startswith('typing.Dict') or str(param_type).startswith('typing.List'):
                        is_complex = True
                    
                    # Convert type to JSON schema type
                    if param_type == str or param_type == TypingAny:
                        params[param_name] = {"type": "string"}
                    elif param_type == int:
                        params[param_name] = {"type": "integer"}
                    elif param_type == float:
                        params[param_name] = {"type": "number"}
                    elif param_type == bool:
                        params[param_name] = {"type": "boolean"}
                    else:
                        # Default to string for complex types (OAK will pass as JSON string)
                        params[param_name] = {"type": "string"}
                        if is_complex:
                            complex_params.add(param_name)
                
                # Create JSON schema for parameters
                params_schema = {
                    "type": "object",
                    "properties": params,
                    "required": [name for name, p in sig.parameters.items() 
                                if p.default == inspect.Parameter.empty and name != 'self'],
                    "additionalProperties": False
                }
                
                # Log detected complex parameters for debugging
                if complex_params:
                    self.logger.info("OAK tool {} has complex params: {}", tool_name, complex_params)
                else:
                    # Log all parameters to help debug why complex params aren't detected
                    all_params = {name: (param.annotation, get_origin(param.annotation) if param.annotation != inspect.Parameter.empty else None) 
                                 for name, param in sig.parameters.items() if name != 'self'}
                    self.logger.warning("OAK tool {} params (no complex detected): {}", tool_name, all_params)
                    # Also log the function signature for debugging
                    self.logger.warning("OAK tool {} full signature: {}", tool_name, sig)
                
                # Create invoke handler factory to properly capture function in closure
                def create_invoke_handler(func, is_async_func, complex_param_names):
                    def parse_complex_args(args_dict):
                        """Parse JSON strings or Python repr strings for complex type parameters."""
                        # Log what we're trying to parse
                        if complex_param_names:
                            self.logger.debug("OAK parse_complex_args: complex_param_names={}, received keys={}", complex_param_names, list(args_dict.keys()))
                        parsed = {}
                        for key, value in args_dict.items():
                            if key in complex_param_names:
                                # Log what we received
                                self.logger.debug("OAK parsing complex param {}: type={}, value (first 100 chars)={}", key, type(value), str(value)[:100] if isinstance(value, str) else value)
                                # For complex types, try to parse if it's a string
                                if isinstance(value, str):
                                    # Try JSON first
                                    try:
                                        parsed_value = json.loads(value)
                                        parsed[key] = parsed_value
                                        self.logger.info("OAK parsed complex param {}: JSON str -> {}", key, type(parsed_value))
                                    except (json.JSONDecodeError, TypeError) as e:
                                        # If JSON fails, try Python ast.literal_eval (for Python dict repr strings)
                                        try:
                                            import ast
                                            parsed_value = ast.literal_eval(value)
                                            parsed[key] = parsed_value
                                            self.logger.info("OAK parsed complex param {}: Python repr str -> {}", key, type(parsed_value))
                                        except (ValueError, SyntaxError) as e2:
                                            # If both fail, log and keep as string (will cause error downstream)
                                            self.logger.error("OAK failed to parse complex param {}: JSON error={}, Python repr error={}", key, e, e2)
                                            self.logger.error("OAK complex param {} value (first 200 chars): {}", key, value[:200] if len(value) > 200 else value)
                                            parsed[key] = value
                                elif isinstance(value, (dict, list)):
                                    # Already parsed, use as-is
                                    self.logger.debug("OAK complex param {} already parsed: {}", key, type(value))
                                    parsed[key] = value
                                else:
                                    # Other types, use as-is
                                    self.logger.warning("OAK complex param {} has unexpected type: {}", key, type(value))
                                    parsed[key] = value
                            else:
                                parsed[key] = value
                        return parsed
                    
                    if is_async_func:
                        async def handler(ctx: RunContextWrapper[TypingAny], args: str) -> str:
                            parsed_args = json.loads(args)
                            # Parse complex type parameters from JSON strings
                            parsed_args = parse_complex_args(parsed_args)
                            result = await func(**parsed_args)
                            # Serialize result to JSON string
                            if isinstance(result, (dict, list)):
                                return json.dumps(result)
                            return str(result)
                    else:
                        async def handler(ctx: RunContextWrapper[TypingAny], args: str) -> str:
                            parsed_args = json.loads(args)
                            # Parse complex type parameters from JSON strings
                            parsed_args = parse_complex_args(parsed_args)
                            result = func(**parsed_args)
                            # Serialize result to JSON string
                            if isinstance(result, (dict, list)):
                                return json.dumps(result)
                            return str(result)
                    return handler
                
                # Create FunctionTool directly
                oak_tool = FunctionTool(
                    name=tool_name,
                    description=spec.description or f"Tool: {spec.name}",
                    params_json_schema=params_schema,
                    on_invoke_tool=create_invoke_handler(original_func, is_async, complex_params)
                )
                
                tools.append(oak_tool)
                
                self.logger.debug("Adapted OAK tool: {} (async={})", tool_name, is_async)
            
            return tools
        except ImportError:
            self.logger.error("agents package not available for OAK tools")
            return []
        except Exception as e:
            self.logger.error("Failed to adapt tools for OAK: {}", e)
            return []
    
    def _adapt_for_maf(self, tool_specs: List[ToolSpec]) -> List[Any]:
        """Adapt tools for MAF framework.
        
        MAF accepts tools as a list of callables or tool objects.
        MAF's ChatAgent generates Pydantic models from function signatures.
        
        Note: Annotations are resolved at decoration time by the @pipeline_tool decorator
        (similar to how FastMCP's @mcp.tool handles it), so we can return functions directly.
        """
        # Annotations are already resolved by @pipeline_tool decorator at decoration time
        # This ensures Pydantic sees resolved type objects instead of strings
        return [spec.func for spec in tool_specs]

