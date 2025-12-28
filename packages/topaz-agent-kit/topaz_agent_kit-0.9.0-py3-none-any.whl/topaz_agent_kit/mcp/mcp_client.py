import asyncio
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional

from topaz_agent_kit.core.exceptions import MCPError
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.mcp.tool_config import ToolConfig

class MCPClient:
    """Minimal MCP client using the official streamable-http transport."""

    def __init__(self, base_url: str, request_timeout_sec: int = 20):
        self._logger = Logger("MCPClient")

        parsed = urlparse(base_url)
        if not parsed.path or parsed.path == "/":
            self.base_url = (base_url.rstrip("/") + "/mcp").rstrip("/")
            self._logger.debug("Normalized MCP base URL to {}", self.base_url)
        else:
            self.base_url = base_url.rstrip("/")
        self.request_timeout_sec = request_timeout_sec
        self._session: Optional[Any] = None
        self._session_cm: Optional[Any] = None
        self._transport_cm: Optional[Any] = None

    async def _ensure_session(self) -> None:
        if self._session is not None:
            return
        try:
            from mcp.client.streamable_http import streamablehttp_client  # type: ignore
            from mcp.client.session import ClientSession  # type: ignore
        except Exception as e:
            raise MCPError(
                "MCP client libraries not available. Install/upgrade 'mcp>=1.13.0'."
            ) from e

        # Enter both transport and session context managers and keep them for closing
        transport_cm = streamablehttp_client(self.base_url)
        incoming, outgoing, _get_id = await transport_cm.__aenter__()
        session_cm = ClientSession(incoming, outgoing)
        session = await session_cm.__aenter__()
        self._transport_cm = transport_cm
        self._session_cm = session_cm
        self._session = session
        # Initialize once
        try:
            if hasattr(self._session, "initialize"):
                await self._session.initialize()
        except Exception:
            pass

    async def list_tools(self) -> List[Any]:
        """List available MCP tools using official MCP protocol"""
        try:
            await self._ensure_session()
            tools = await self._session.list_tools()
            return tools.tools if hasattr(tools, 'tools') else tools
        except Exception as e:
            self._logger.warning("Failed to list MCP tools: {}", e)
            return []

    async def call_tool(self, name: str, arguments: Dict[str, Any], func=None, timeout_seconds: Optional[int] = None) -> str:
        """Call an MCP tool with timeout support using official MCP protocol
        
        Args:
            name: Tool name
            arguments: Tool arguments
            func: Optional function object for timeout resolution
            timeout_seconds: Optional explicit timeout override (in seconds)
        """
        
        # Resolve tool timeout configuration
        if timeout_seconds is None:
            timeout_seconds = self._get_tool_timeout(func)
        
        try:
            if timeout_seconds:
                # Use timeout for the tool call
                return await asyncio.wait_for(
                    self._execute_tool_call(name, arguments),
                    timeout=timeout_seconds
                )
            else:
                # No timeout
                return await self._execute_tool_call(name, arguments)
                
        except asyncio.TimeoutError:
            raise MCPError(f"Tool '{name}' timed out after {timeout_seconds} seconds")
        except Exception as e:
            self._logger.error("Failed to call MCP tool {}: {}", name, e)
            return f"Tool call error: {str(e)}"
    
    async def _execute_tool_call(self, name: str, arguments: Dict[str, Any]) -> str:
        """Execute the actual MCP tool call"""
        try:
            await self._ensure_session()
            result = await self._session.call_tool(name, arguments)
            
            # Extract text content from MCP response
            if hasattr(result, 'content') and result.content:
                content = result.content[0] if isinstance(result.content, list) else result.content
                if hasattr(content, 'text'):
                    return content.text
                return str(content)
            return str(result)
        except Exception as e:
            self._logger.error("Failed to call MCP tool {}: {}", name, e)
            return f"Tool call error: {str(e)}"
    
    def _get_tool_timeout(self, func=None) -> Optional[int]:
        """Get timeout for a tool based on its metadata"""
        try:
            if func:
                config = ToolConfig.resolve_tool_config(func)
                return config.get('timeout_seconds')
            else:
                # No decorator = use default QUICK timeout (5 seconds)
                return ToolConfig.get_timeout_seconds(ToolConfig.DEFAULT_TIMEOUT)
        except Exception as e:
            self._logger.warning("Failed to resolve timeout for tool: {}", e)
            # Fallback to default QUICK timeout
            return ToolConfig.get_timeout_seconds(ToolConfig.DEFAULT_TIMEOUT)

    # Proper async interface - no broken sync wrappers
    def get_tools_metadata(self) -> List[Any]:
        """Get tools metadata in a way that works with existing sync code"""
        try:
            try:
                loop = asyncio.get_running_loop()
                # In async context, we can't use asyncio.run()
                # Try to run in a new thread with a new event loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._get_tools_in_new_loop)
                    return future.result(timeout=10)
            except RuntimeError:
                # No event loop, we can create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self.list_tools())
                finally:
                    loop.close()
        except Exception as e:
            self._logger.warning("Failed to get MCP tools metadata: {}", e)
            return []
    
    def _get_tools_in_new_loop(self) -> List[Any]:
        """Helper to get tools in a new event loop (for use in thread)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.list_tools())
        finally:
            loop.close()

    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Execute tool in a way that works with existing sync code"""
        try:
            try:
                loop = asyncio.get_running_loop()
                # In async context, prefer using the async API directly
                self._logger.debug("MCP tool called from async context")
                return "Tool call error: called from async context; use async call_tool instead"
            except RuntimeError:
                # No event loop, we can create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self.call_tool(name, arguments))
                finally:
                    loop.close()
        except Exception as e:
            self._logger.error("Failed to execute MCP tool {}: {}", name, e)
            return f"Tool call error: {str(e)}"

    async def close(self):
        """Close the MCP session"""
        if self._session_cm is not None:
            try:
                await self._session_cm.__aexit__(None, None, None)
            except Exception:
                pass
        if self._transport_cm is not None:
            try:
                await self._transport_cm.__aexit__(None, None, None)
            except Exception:
                pass
        self._session = None
        self._session_cm = None
        self._transport_cm = None

