"""Framework-specific MCP integration management"""

import traceback
from typing import List, Any, Dict

from topaz_agent_kit.core.exceptions import MCPError
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.frameworks.framework_config_manager import FrameworkConfigManager

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StreamableHttpConnection
from crewai_tools import MCPServerAdapter
from semantic_kernel.connectors.mcp import MCPStreamableHttpPlugin
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from agents.mcp import MCPServerStreamableHttp, MCPServerStreamableHttpParams
from agent_framework import MCPStreamableHTTPTool

class FrameworkMCPManager:
    """Framework-specific MCP integration management"""
    
    _logger = Logger("FrameworkMCPManager")
    
    @classmethod
    async def create_framework_mcp_tools(cls, framework: str, mcp_url: str, **config) -> List[Any]:
        """Create MCP tools appropriate for the specified framework"""
        
        cls._logger.info("Creating MCP tools for {} framework: {}", framework, mcp_url)
        
        # Get framework-specific MCP integration details
        framework_config = FrameworkConfigManager()
        mcp_integration = framework_config.get_mcp_integration(framework)
        
        if framework == "agno":
            return cls._create_agno_mcp_tools(mcp_url, mcp_integration, **config)
        elif framework == "langgraph":
            return await cls._create_langgraph_mcp_tools(mcp_url, mcp_integration, **config)
        elif framework == "crewai":
            return await cls._create_crewai_mcp_tools(mcp_url, mcp_integration, **config)
        elif framework == "sk":
            return await cls._create_sk_mcp_tools(mcp_url, mcp_integration, **config)
        elif framework == "adk":
            return await cls._create_adk_mcp_tools(mcp_url, mcp_integration, **config)
        elif framework == "oak":
            return await cls._create_oak_mcp_tools(mcp_url, mcp_integration, **config)
        elif framework == "maf":
            return await cls._create_maf_mcp_tools(mcp_url, mcp_integration, **config)
        else:
            raise ValueError(f"Unsupported framework: {framework}")
    
    @classmethod
    async def connect_framework_mcp_tools(cls, mcp_tools: List[Any]) -> None:
        """Connect and initialize MCP tools asynchronously"""
        for tool in mcp_tools:
            try:
                if hasattr(tool, 'connect'):
                    await tool.connect()
                    cls._logger.success("Connected MCP tool: {}", type(tool).__name__)
                
                if hasattr(tool, 'initialize'):
                    await tool.initialize()
                    cls._logger.success("Initialized MCP tool: {}", type(tool).__name__)
                    
            except Exception as e:
                cls._logger.warning("Failed to connect/initialize MCP tool: {}", e)
    
    @classmethod
    async def cleanup_framework_mcp_tools(cls, mcp_tools: List[Any]) -> None:
        """Cleanup and close MCP tools asynchronously"""
        for tool in mcp_tools:
            try:
                # Check if this is our MCPToolsWrapper (LangGraph/CrewAI)
                if hasattr(tool, 'cleanup') and hasattr(tool, '_mcp_client'):
                    # This is our wrapper, use its cleanup method
                    tool.cleanup()
                    cls._logger.info("Cleaned up MCP tools wrapper: {}", type(tool).__name__)
                elif hasattr(tool, 'close'):
                    await tool.close()
                    cls._logger.info("Closed MCP tool: {}", type(tool).__name__)
                elif hasattr(tool, 'disconnect'):
                    await tool.disconnect()
                    cls._logger.info("Disconnected MCP tool: {}", type(tool).__name__)
                elif hasattr(tool, 'cleanup'):
                    await tool.cleanup()
                    cls._logger.info("Cleaned up MCP tool: {}", type(tool).__name__)
                    
            except Exception as e:
                cls._logger.warning("Failed to cleanup MCP tool: {}", e)
    
    @classmethod
    def _create_agno_mcp_tools(cls, mcp_url: str, mcp_integration: Dict[str, Any], **config) -> List[Any]:
        """Create Agno MCP tools using framework configuration"""
        try:
            transport = mcp_integration.get("transport", "streamable-http")
            tool_class = mcp_integration.get("tool_class", "agno.tools.mcp.MCPTools")
            params_class = mcp_integration.get("params_class", "agno.tools.mcp.StreamableHTTPClientParams")
            timeout = mcp_integration.get("timeout", 300)

            # Import required classes
            tool_module, tool_name = tool_class.rsplit(".", 1)
            tool_module_obj = __import__(tool_module, fromlist=[tool_name])
            tool_class_obj = getattr(tool_module_obj, tool_name)
            
            params_module, params_name = params_class.rsplit(".", 1)
            params_module_obj = __import__(params_module, fromlist=[params_name])
            params_class_obj = getattr(params_module_obj, params_name)
            
            # Create MCP tools with timeout configuration
            server_params = params_class_obj(url=mcp_url, timeout=timeout)        
            
            mcp_tools = tool_class_obj(
                transport=transport,
                server_params=server_params,
                timeout_seconds=timeout
            )
            
            cls._logger.success("Created Agno MCPTools with {} transport", transport)
            return [mcp_tools]
            
        except Exception as e:
            cls._logger.error("Failed to create Agno MCPTools: {}", e)
            raise MCPError(f"Failed to create Agno MCPTools: {e}")
    
    @classmethod
    async def _create_langgraph_mcp_tools(cls, mcp_url: str, mcp_integration: Dict[str, Any], **config) -> List[Any]:
        """Create LangGraph MCP tools using langchain-mcp-adapters"""
        try:
            # Extract transport type from integration config
            transport = mcp_integration.get("transport", "streamable-http")
            timeout = mcp_integration.get("timeout")
            cls._logger.info("Using transport: {} for MCP server: {}", transport, mcp_url)
            
            # Configure MCP client for the server using proper connection types
            # For now, we'll use a single server configuration
            # This can be extended to support multiple servers later
            server_config = {
                "mcp_server": StreamableHttpConnection(
                    transport="streamable_http",
                    url=mcp_url,
                    timeout=timeout  
                )
            }
            
            cls._logger.info("Server config: {}", server_config)
            
            # Create MCP client
            mcp_client = MultiServerMCPClient(server_config)
            cls._logger.success("MCP client created successfully")
            
            # Get tools as LangChain BaseTool instances
            tools = await mcp_client.get_tools()
            
            cls._logger.success("Created LangGraph MCP tools using langchain-mcp-adapters: {} tools", len(tools))
            
            # Create a wrapper that holds both tools and MCP client for cleanup
            # This ensures we can properly cleanup the MCP client later
            class MCPToolsWrapper:
                def __init__(self, tools_list, mcp_client_instance):
                    self.tools = tools_list
                    self._mcp_client = mcp_client_instance
                
                def __len__(self):
                    return len(self.tools)
                
                def __getitem__(self, index):
                    return self.tools[index]
                
                def __iter__(self):
                    return iter(self.tools)
                
                def __contains__(self, item):
                    return item in self.tools
                
                async def cleanup(self):
                    """Cleanup MCP client resources"""
                    try:
                        if hasattr(self._mcp_client, 'close'):
                            await self._mcp_client.close()
                        elif hasattr(self._mcp_client, 'disconnect'):
                            await self._mcp_client.disconnect()
                        cls._logger.info("Cleaned up LangGraph MCP client")
                    except Exception as e:
                        cls._logger.warning("Failed to cleanup LangGraph MCP client: {}", e)
            
            # Return the wrapper instead of raw tools
            return MCPToolsWrapper(tools, mcp_client)
            
        except ImportError as e:
            cls._logger.error("langchain-mcp-adapters not available: {}", e)
            cls._logger.error("Install with: uv add langchain-mcp-adapters")
            raise MCPError("langchain-mcp-adapters package required for LangGraph MCP integration")
        except Exception as e:
            cls._logger.error("Failed to create LangGraph MCP tools: {}", e)
            cls._logger.error("Full error details: {}", str(e))
            cls._logger.error("Traceback: {}", traceback.format_exc())
            raise MCPError(f"Failed to create LangGraph MCP tools: {e}")
    
    @classmethod
    async def _create_crewai_mcp_tools(cls, mcp_url: str, mcp_integration: Dict[str, Any], **config) -> List[Any]:
        """Create CrewAI MCP tools using native MCPServerAdapter"""
        try:    
            cls._logger.info("Using CrewAI MCPServerAdapter: {}", mcp_url)
            timeout = mcp_integration.get("timeout", 300)  # Default to 300 seconds if not specified

            # Create server parameters as a dictionary (CrewAI expects this format)
            # MCP library expects "streamable-http" (with hyphen), not "streamable_http" (with underscore)
            # MCPServerAdapter accepts either a dict (single server) or list of dicts (multiple servers)
            server_params = {
                "url": mcp_url,
                "transport": "streamable-http",
                "timeout": timeout,
            }
            
            cls._logger.info("Created CrewAI native MCP server parameters for {}", mcp_url)
            
            # Create adapter and return tools directly (following working example pattern)
            # MCPServerAdapter has a .tools property that returns the list of tools
            # The adapter manages its own lifecycle internally
            adapter = MCPServerAdapter(server_params)
            
            # Access .tools property to get the list of tools
            # This initializes the adapter and fetches tools from the MCP server
            tools = adapter.tools
            
            cls._logger.success("Created CrewAI MCPServerAdapter and extracted {} tools", len(tools))
            
            # Return tools directly as a list (similar to LangGraph pattern)
            # The base agent will filter these tools based on patterns
            return tools
            
        except ImportError as e:
            cls._logger.error("crewai-tools not available or missing MCP support: {}", e)
            cls._logger.error("Install with: uv add 'crewai-tools[mcp]'")
            raise MCPError("crewai-tools package with MCP support required for CrewAI MCP integration")
        except Exception as e:
            cls._logger.error("Failed to create CrewAI native MCP tools: {}", e)
            raise MCPError(f"Failed to create CrewAI native MCP tools: {e}")
    
    @classmethod
    async def _create_sk_mcp_tools(cls, mcp_url: str, mcp_integration: Dict[str, Any], **config) -> List[Any]:
        """Create MCP tools for SK framework using plugin-based integration"""
        cls._logger.info("Creating SK MCP tools for mcp_url: {}", mcp_url)
        
        try:
            # Create the plugin (no explicit initialization needed)
            plugin = MCPStreamableHttpPlugin(
                name="sk_mcp_plugin",
                description="SK MCP Plugin",
                url=mcp_url, 
                timeout=mcp_integration.get("timeout", 300),
            )
            
            # Return the plugin wrapper
            return [plugin]
            
        except Exception as e:
            cls._logger.error("Failed to create SK MCP tools: {}", e)
            raise MCPError(f"Failed to create SK MCP tools: {e}")
    
    @classmethod
    async def _create_adk_mcp_tools(cls, mcp_url: str, mcp_integration: Dict[str, Any], **config) -> List[Any]:
        """Create MCP tools for ADK framework using streamable HTTP connection"""
        cls._logger.info("Creating ADK MCP tools for mcp_url: {}", mcp_url)
        
        try:
            # Create connection parameters
            connection_params = StreamableHTTPConnectionParams(
                url=mcp_url,
                timeout=mcp_integration.get("timeout", 300)
            )
            
            # Create MCP toolset (ADK manages sessions internally; no explicit initialize)
            mcp_toolset = McpToolset(connection_params=connection_params)
            
            cls._logger.success("ADK MCP toolset created successfully")
            
            # Return the toolset wrapper
            return [mcp_toolset]
            
        except ImportError as e:
            cls._logger.error("ADK MCP tools not available: {}", e)
            cls._logger.error("Ensure google-adk-tools is installed with MCP support")
            raise MCPError("ADK MCP tools package required for ADK MCP integration")
        except Exception as e:
            cls._logger.error("Failed to create ADK MCP tools: {}", e)
            raise MCPError(f"Failed to create ADK MCP tools: {e}")
    
    @classmethod
    async def _create_oak_mcp_tools(cls, mcp_url: str, mcp_integration: Dict[str, Any], **config) -> List[Any]:
        """Create MCP tools for OAK framework using streamable HTTP connection"""
        cls._logger.info("Creating OAK MCP tools for mcp_url: {}", mcp_url)
        
        try:
            # Create connection parameters
            connection_params = MCPServerStreamableHttpParams(
                url=mcp_url,
                timeout=mcp_integration.get("timeout", 300)
            )
            
            mcp_tools = MCPServerStreamableHttp(
                params=connection_params,
                client_session_timeout_seconds=mcp_integration.get("timeout", 300)
            )
            
            cls._logger.success("OAK MCP tools created successfully")
            return [mcp_tools]
            
        except ImportError as e:
            cls._logger.error("OAK MCP tools not available: {}", e)
            raise MCPError("OAK MCP tools package required for OAK MCP integration")
        except Exception as e:
            cls._logger.error("Failed to create OAK MCP tools: {}", e)
            raise MCPError(f"Failed to create OAK MCP tools: {e}")

    @classmethod
    async def _create_oak_mcp_tools(cls, mcp_url: str, mcp_integration: Dict[str, Any], **config) -> List[Any]:
        """Create MCP tools for OAK framework using streamable HTTP connection"""
        cls._logger.info("Creating OAK MCP tools for mcp_url: {}", mcp_url)
        
        try:
            # Create connection parameters
            connection_params = MCPServerStreamableHttpParams(
                url=mcp_url,
                timeout=mcp_integration.get("timeout", 300)
            )
            
            mcp_tools = MCPServerStreamableHttp(
                params=connection_params,
                client_session_timeout_seconds=mcp_integration.get("timeout", 300)
            )
            
            cls._logger.success("OAK MCP tools created successfully")
            return [mcp_tools]
            
        except ImportError as e:
            cls._logger.error("OAK MCP tools not available: {}", e)
            raise MCPError("OAK MCP tools package required for OAK MCP integration")
        except Exception as e:
            cls._logger.error("Failed to create OAK MCP tools: {}", e)
            raise MCPError(f"Failed to create OAK MCP tools: {e}")

    @classmethod
    async def _create_maf_mcp_tools(cls, mcp_url: str, mcp_integration: Dict[str, Any], **config) -> List[Any]:
        """Create MCP tools for MAF framework using streamable HTTP connection"""
        cls._logger.info("Creating MAF MCP tools for mcp_url: {}", mcp_url)
        
        try:    
            mcp_tools = MCPStreamableHTTPTool(
                name="maf_mcp_tools",
                url=mcp_url,
                timeout=mcp_integration.get("timeout", 300)
            )
            
            cls._logger.success("MAF MCP tools created successfully")
            return [mcp_tools]
            
        except ImportError as e:
            cls._logger.error("MAF MCP tools not available: {}", e)
            raise MCPError("agent_framework package required for MAF MCP integration")
        except Exception as e:
            cls._logger.error("Failed to create MAF MCP tools: {}", e)
            raise MCPError(f"Failed to create MAF MCP tools: {e}")