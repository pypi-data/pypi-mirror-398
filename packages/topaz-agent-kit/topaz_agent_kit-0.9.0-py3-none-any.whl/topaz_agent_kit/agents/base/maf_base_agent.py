"""
MAF framework base class implementing the BaseAgent interface.
Uses Microsoft Agent Framework SDK for agent creation and management.
"""

from typing import Any, Dict, List

from agent_framework import ChatAgent
from agent_framework import ChatMessage, Role
from agent_framework import TextContent, UriContent, DataContent

from topaz_agent_kit.agents.base.base_agent import BaseAgent
from topaz_agent_kit.core.exceptions import AgentError
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.mcp_utils import matches_tool_patterns


class MAFBaseAgent(BaseAgent):
    """
    Base class for MAF agents using official SDK patterns.
    Handles MAF-specific initialization, tool management, and execution.
    Uses the unified architecture for model and MCP tool management.
    """
    
    def __init__(self, agent_id: str, **kwargs):
        super().__init__(agent_id, "maf", **kwargs)
        
        # Override logger with framework-specific name
        self.logger = Logger(f"MAFAgent({agent_id})")
        
        # Store filtered tool names for each plugin (since plugins don't support filtering)
        self._filtered_mcp_tool_names = {}
        

    def _initialize_agent(self):
        """Initialize MAF agent"""
        # no specific initialization needed for MAF

    def _setup_environment(self):
        """Setup MAF-specific environment variables based on model preference"""
        # no specific environment setup needed for MAF

    async def _filter_mcp_tools(self) -> None:
        """Filter MCP tools for MAF framework using pattern matching"""
        try:
            self.logger.debug("Filtering MCP tools for MAF agent: {}", self.agent_id)
            if not self.tools:
                return
                
            mcp_config = self.agent_config.get("mcp", {})
            servers_config = mcp_config.get("servers", [])
            
            if not servers_config:
                # No MCP config, filter out all tools
                self.logger.debug("No MCP server configuration found, filtering out all tools")
                self.tools = []
                return
                
            # Aggregate wildcard patterns and toolkits from pipeline.yml
            all_patterns = []
            all_toolkits = []
            for server in servers_config:
                all_patterns.extend(server.get("tools", []))
                all_toolkits.extend(server.get("toolkits", []))
            # De-duplicate while preserving order
            all_patterns = list(dict.fromkeys(all_patterns))
            all_toolkits = list(dict.fromkeys(all_toolkits))
            self.logger.info(f"Allowed tool patterns from pipeline.yml: {all_patterns}")
            self.logger.info(f"Allowed toolkits from pipeline.yml: {all_toolkits}")
            
            # Log count before filtering
            original_count = len(self.tools)
            self.logger.info(f"MCP tools count before filtering: {original_count}")
            
            # For MAF, tools are MCPStreamableHTTPTool wrapper objects
            # We need to query the MCP server to check which tools match patterns
            # If no tools match, we should remove the plugin
            # Note: MAF's plugin doesn't support filtering at plugin level, so we store
            # the filtered tool names for later use in _log_tool_details
            filtered_tools = []
            self._filtered_mcp_tool_names = {}  # Clear previous filtered names
            
            for tool in self.tools:
                # Handle dictionary-based tools (legacy) - check first
                if isinstance(tool, dict) and 'name' in tool:
                    if matches_tool_patterns(tool['name'], all_patterns, all_toolkits):
                        filtered_tools.append(tool)
                        self.logger.debug(f"Keeping MAF tool: {tool['name']}")
                    else:
                        self.logger.debug(f"Filtering out MAF tool: {tool['name']}")
                    continue
                
                # Handle MCPStreamableHTTPTool objects (new MCP setup)
                # Try to get tools directly from the tool object
                all_tool_objects = []
                
                # Try different methods to get tools from MAF's tool object
                if hasattr(tool, 'list_tools'):
                    # Direct list_tools method
                    try:
                        tools_result = await tool.list_tools()
                        all_tool_objects = self._extract_tools_from_result(tools_result)
                    except Exception as e:
                        self.logger.debug(f"tool.list_tools() failed: {e}")
                
                # Try accessing internal client/session if available
                if not all_tool_objects:
                    try:
                        # Check for _client or client attribute
                        client = getattr(tool, '_client', None) or getattr(tool, 'client', None)
                        if client and hasattr(client, 'list_tools'):
                            tools_result = await client.list_tools()
                            all_tool_objects = self._extract_tools_from_result(tools_result)
                    except Exception as e:
                        self.logger.debug(f"Could not get tools from tool.client: {e}")
                
                if not all_tool_objects:
                    try:
                        # Check for _session or session attribute
                        session = getattr(tool, '_session', None) or getattr(tool, 'session', None)
                        if session and hasattr(session, 'list_tools'):
                            tools_result = await session.list_tools()
                            all_tool_objects = self._extract_tools_from_result(tools_result)
                    except Exception as e:
                        self.logger.debug(f"Could not get tools from tool.session: {e}")
                
                # If we couldn't get tools from the tool object, filter it out
                if not all_tool_objects:
                    self.logger.debug("Filtering out MAF MCP plugin (could not get tools from tool object)")
                    continue
                
                # Extract tool names and filter
                matching_tool_names = []
                for tool_obj in all_tool_objects:
                    tool_name = self._extract_tool_name(tool_obj)
                    if tool_name and matches_tool_patterns(tool_name, all_patterns, all_toolkits):
                        matching_tool_names.append(tool_name)
                
                # Only keep plugin if at least one tool matches
                if matching_tool_names:
                    filtered_tools.append(tool)
                    self._filtered_mcp_tool_names[id(tool)] = matching_tool_names
                    self.logger.debug(f"Keeping MAF MCP plugin (matched {len(matching_tool_names)} tools)")
                else:
                    self.logger.debug("Filtering out MAF MCP plugin (no tools matched patterns)")
            
            self.tools = filtered_tools
            
        except Exception as e:
            self.logger.error("Failed to filter MCP tools for MAF: {}", e)
            self.tools = []  # Clear tools on error
    
    def _extract_tools_from_result(self, tools_result: Any) -> list:
        """Extract list of tool objects from tools_result"""
        if hasattr(tools_result, 'tools'):
            return tools_result.tools
        elif isinstance(tools_result, list):
            return tools_result
        return []
    
    def _extract_tool_name(self, tool_obj: Any) -> str:
        """Extract tool name from tool object"""
        if hasattr(tool_obj, 'name'):
            return tool_obj.name
        elif isinstance(tool_obj, dict) and 'name' in tool_obj:
            return tool_obj['name']
        return str(tool_obj)
    
    async def _log_tool_details(self) -> None:
        """Log filtered tool details for MAF framework"""
        if not self.tools:
            self.logger.info("No tools attached")
            return
        
        # Use stored filtered tool names from _filter_mcp_tools
        all_tool_names = []
        for tool in self.tools:
            tool_id = id(tool)
            if tool_id in self._filtered_mcp_tool_names:
                # Use the stored filtered names (may be empty list if filtering failed)
                all_tool_names.extend(self._filtered_mcp_tool_names[tool_id])
            elif isinstance(tool, dict) and 'name' in tool:
                # Legacy dictionary tool
                all_tool_names.append(tool['name'])
            elif hasattr(tool, 'name'):
                all_tool_names.append(tool.name)
            else:
                all_tool_names.append(type(tool).__name__)
        
        total_after = len(all_tool_names)
 
        self.logger.success(f"MCP tools count after filtering: {total_after}")
        for name in sorted(set(all_tool_names)):
            self.logger.success(f"  - {name}")

    def _create_agent(self) -> None:
        """Create MAF agent instance using official SDK"""
        try:
            self.logger.debug("Creating MAF agent with LLM: {} (type: {})", self.llm, type(self.llm))
            self.logger.debug("MAF agent instruction: {}", self.prompt["instruction"])
            
            # Create MAF agent
            self.agent = ChatAgent(
                chat_client=self.llm,
                name=self.agent_id,
                instructions=self.prompt["instruction"],
                tools=self.tools
            )
            
            self.logger.success("Created MAF agent: {}", self.name)
            self.logger.info("Agent tools: {} tools available", len(self.tools))
            
        except Exception as e:
            raise AgentError(f"Failed to create MAF agent: {e}")
    

    def _build_multimodal_content(self, rendered_inputs: str, context: Dict[str, Any]) -> List[Any]:
        """
        Build multimodal content list for MAF ChatMessage.
        
        Args:
            rendered_inputs: Rendered prompt text
            context: Execution context containing user_files_data
            
        Returns:
            List of Content objects (TextContent, DataContent, UriContent)
        """
        contents = []
        user_files_data = context.get("user_files_data", {})
        
        # Check if the agent's prompt template uses user_files variable
        # If not, skip file processing to avoid unnecessary data processing
        if not self._should_process_files():
            return [TextContent(text=rendered_inputs or "")]
        
        # Add text content (always present, even if empty)
        contents.append(TextContent(text=rendered_inputs or ""))
        
        # Add image files from user_files_data
        images = user_files_data.get("images", [])
        for image_data in images:
            try:
                contents.append(DataContent(
                    data=image_data["data"],  # bytes
                    media_type=image_data["metadata"]["mime_type"]
                ))
                self.logger.debug("Added image to MAF message: {}", image_data["name"])
            except Exception as e:
                self.logger.error("Failed to add image {} to MAF message: {}", image_data.get("name", "unknown"), e)
                raise  # Fail agent execution on error
        
        # Add document files from user_files_data
        # Use DataContent for documents (PDFs, DOCX, etc.) - MAF supports this
        documents = user_files_data.get("documents", [])
        for doc_data in documents:
            try:
                contents.append(DataContent(
                    data=doc_data["data"],  # bytes
                    media_type=doc_data["metadata"]["mime_type"]
                ))
                self.logger.debug("Added document to MAF message: {}", doc_data["name"])
            except Exception as e:
                self.logger.error("Failed to add document {} to MAF message: {}", doc_data.get("name", "unknown"), e)
                raise  # Fail agent execution on error
        
        # Add URLs from user_files_data (images and documents)
        urls = user_files_data.get("urls", [])
        for url_data in urls:
            url_type = url_data.get("type")
            if url_type in ["image", "document"]:
                try:
                    contents.append(UriContent(
                        uri=url_data["url"],
                        media_type=url_data.get("media_type", "application/octet-stream")
                    ))
                    self.logger.debug("Added {} URL to MAF message: {}", url_type, url_data["url"])
                except Exception as e:
                    self.logger.error("Failed to add {} URL {} to MAF message: {}", url_type, url_data.get("url", "unknown"), e)
                    raise  # Fail agent execution on error
        
        return contents

    async def _execute_agent(self, context: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute with MAF agent. This method handles the actual LLM execution.
        Supports multimodal inputs (text, images, documents, URLs) using MAF ChatMessage format.
        Generated classes can override this for custom logic, or call super() to use this implementation.
        """
        try:
            # Use pre-rendered inputs from base_agent.execute() (stored in self._rendered_inputs)
            rendered_inputs = self._rendered_inputs if hasattr(self, '_rendered_inputs') else None
            if not rendered_inputs:
                # Fallback: render if not available (shouldn't happen in normal flow)
                rendered_inputs = self._render_prompt_with_variables(self.prompt["inputs"], variables)
            self.logger.debug(f"Agent {self.agent_id} Inputs: {rendered_inputs}")
            
            # Build multimodal content
            contents = self._build_multimodal_content(rendered_inputs, context)
            
            # Execute with MAF agent
            message = ChatMessage(role=Role.USER, contents=contents)
            text_count = len([c for c in contents if isinstance(c, TextContent)])
            data_count = len([c for c in contents if isinstance(c, DataContent)])
            uri_count = len([c for c in contents if isinstance(c, UriContent)])
            self.logger.info("Executing MAF workflow with multimodal input ({} text, {} files via DataContent, {} URLs)", 
                           text_count, data_count, uri_count)
            
            result = await self.agent.run(message)

            self.logger.success("MAF agent execution completed")
            
            # Return raw result - base_agent.execute() will parse it
            return result
            
        except Exception as e:
            self.logger.error("MAF agent execution failed: {}", e)
            raise AgentError(f"MAF agent execution failed: {e}")
    