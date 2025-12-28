"""
SK framework base class implementing the BaseAgent interface.
Uses Microsoft SK SDK for agent creation and management.
"""

from typing import Any, Dict

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.contents import AuthorRole, ChatMessageContent, ImageContent, TextContent

from topaz_agent_kit.agents.base.base_agent import BaseAgent
from topaz_agent_kit.core.exceptions import AgentError
from topaz_agent_kit.utils.file_utils import FileUtils
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.mcp_utils import matches_tool_patterns


class SKBaseAgent(BaseAgent):
    """
    Base class for SK agents using official SDK patterns.
    Handles SK-specific initialization, tool management, and execution.
    Uses the unified architecture for model and MCP tool management.
    """
    
    def __init__(self, agent_id: str, **kwargs):
        super().__init__(agent_id, "sk", **kwargs)
        
        # Override logger with framework-specific name
        self.logger = Logger(f"SKAgent({agent_id})")
        
        # SK-specific attributes
        self.kernel = None
        # Store filtered tool names for each plugin (since plugins don't support filtering)
        self._filtered_mcp_tool_names = {}

    def _initialize_agent(self):
        """Initialize SK agent"""
        # no specific initialization needed for SK

    def _setup_environment(self):
        """Setup SK-specific environment variables based on model preference"""
        # no specific environment setup needed for Agno

    async def _filter_mcp_tools(self) -> None:
        """Filter MCP tools for SK framework using pattern matching"""
        try:
            self.logger.debug("Filtering MCP tools for SK agent: {}", self.agent_id)
            
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
            
            # For SK, tools are MCPStreamableHttpPlugin wrapper objects
            # We need to query the MCP server to check which tools match patterns
            # If no tools match, we should remove the plugin
            # Note: SK's plugin doesn't support filtering at plugin level, so we store
            # the filtered tool names for later use in _log_tool_details
            filtered_tools = []
            self._filtered_mcp_tool_names = {}  # Clear previous filtered names
            
            for tool in self.tools:
                # Handle dictionary-based tools (legacy) - check first
                if isinstance(tool, dict) and 'name' in tool:
                    if matches_tool_patterns(tool['name'], all_patterns, all_toolkits):
                        filtered_tools.append(tool)
                        self.logger.debug(f"Keeping SK tool: {tool['name']}")
                    else:
                        self.logger.debug(f"Filtering out SK tool: {tool['name']}")
                    continue
                
                # Handle MCPStreamableHttpPlugin objects (new MCP setup)
                # Try to get tools directly from the tool object
                all_tool_objects = []
                
                # Try different methods to get tools from SK's plugin object
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
                    self.logger.debug(f"Filtering out SK MCP plugin (could not get tools from tool object)")
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
                    self.logger.debug(f"Keeping SK MCP plugin (matched {len(matching_tool_names)} tools)")
                else:
                    self.logger.debug(f"Filtering out SK MCP plugin (no tools matched patterns)")
            
            self.tools = filtered_tools
            
        except Exception as e:
            self.logger.error("Failed to filter MCP tools for SK: {}", e)
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
        """Log filtered tool details for SK framework"""
        if not self.tools:
            self.logger.info("No tools attached")
            return
        
        # For SK, tools are MCPStreamableHttpPlugin wrapper objects
        # Use the filtered tool names stored during _filter_mcp_tools
        # Note: Filtering already happened in _filter_mcp_tools, so we just log what's already filtered
        all_tool_names = []
        
        for tool in self.tools:
            if hasattr(tool, 'url'):
                # This is an MCPStreamableHttpPlugin - use stored filtered tool names
                tool_id = id(tool)
                if tool_id in self._filtered_mcp_tool_names:
                    # Use the filtered tool names from filtering
                    all_tool_names.extend(self._filtered_mcp_tool_names[tool_id])
                else:
                    # Fallback: if we don't have stored names, fall back to plugin name
                    self.logger.debug(f"No stored filtered tool names for plugin {tool.name if hasattr(tool, 'name') else type(tool).__name__}")
                    all_tool_names.append(tool.name if hasattr(tool, 'name') else type(tool).__name__)
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
        """Create SK agent instance using official SDK"""
        try:
            self.logger.debug("Creating SK agent with LLM: {} (type: {})", self.llm, type(self.llm))
            self.logger.debug("SK agent instruction: {}", self.prompt["instruction"])

            # Create kernel
            self.kernel = Kernel()
            
            # Add the LLM service that was created by the unified factory
            self.kernel.add_service(self.llm)
            
            # Merge local tools with MCP tools (plugins)
            all_plugins = list(self.tools) + list(self.local_tools)
            if self.local_tools:
                self.logger.success("Added {} local tools to SK agent", len(self.local_tools))
            
            # Create SK agent
            self.agent = ChatCompletionAgent(
                kernel=self.kernel,
                name=self.agent_id,
                instructions=self.prompt["instruction"],
                plugins=all_plugins  # Merge MCP plugins and local tools
            )
            
            self.logger.success("Created SK agent: {}", self.name)
            self.logger.info("Agent tools: {} tools available", len(self.tools))
            
        except Exception as e:
            raise AgentError(f"Failed to create SK agent: {e}")
    

    def _build_multimodal_content(self, rendered_inputs: str, context: Dict[str, Any]) -> Any:
        """
        Build multimodal content list for SK ChatMessageContent.
        
        Args:
            rendered_inputs: Rendered prompt text
            context: Execution context containing user_files_data
            
        Returns:
            ChatMessageContent with items (TextContent, ImageContent)
        """
        items = []
        user_files_data = context.get("user_files_data", {})
        
        # Check if the agent's prompt template uses user_files variable
        # If not, skip file processing to avoid unnecessary data processing
        if not self._should_process_files():
            if rendered_inputs and rendered_inputs.strip():
                items.append(TextContent(text=rendered_inputs))
            return ChatMessageContent(role=AuthorRole.USER, items=items)
        
        # Add text content (always present)
        if rendered_inputs and rendered_inputs.strip():
            items.append(TextContent(text=rendered_inputs))
        
        # Add image files from user_files_data (as ImageContent with data URL)
        images = user_files_data.get("images", [])
        for image_data in images:
            try:
                # SK ImageContent with Azure OpenAI expects data URL format: data:image/png;base64,...
                base64_data = FileUtils.encode_bytes_to_base64(image_data["data"])
                data_url = f"data:{image_data['metadata']['mime_type']};base64,{base64_data}"
                items.append(ImageContent(uri=data_url))
                self.logger.debug("Added image to SK message: {}", image_data["name"])
            except Exception as e:
                self.logger.error("Failed to add image {} to SK message: {}", image_data.get("name", "unknown"), e)
                raise  # Fail agent execution on error
        
        # Add document files from user_files_data
        # SK vision API only supports actual images (PNG, JPEG, GIF, WEBP) - NOT PDFs/documents
        documents = user_files_data.get("documents", [])
        for doc_data in documents:
            try:
                # If document has extracted text, add as TextContent
                # SK's ImageContent (vision API) does NOT support PDFs/documents
                if doc_data.get("text"):
                    items.append(TextContent(text=f"\n\nDocument: {doc_data['name']}\n{doc_data['text']}"))
                    self.logger.debug("Added document text to SK message: {}", doc_data["name"])
                else:
                    # For documents without extracted text, log and skip
                    self.logger.warning(
                        "Skipping document {} - no extracted text available and mime_type {} not supported by vision API",
                        doc_data["name"], doc_data["metadata"]["mime_type"]
                    )
            except Exception as e:
                self.logger.error("Failed to add document {} to SK message: {}", doc_data.get("name", "unknown"), e)
                raise  # Fail agent execution on error
        
        # Add URLs from user_files_data (as ImageContent with URI)
        urls = user_files_data.get("urls", [])
        for url_data in urls:
            url_type = url_data.get("type")
            if url_type == "image":  # SK primarily supports images
                try:
                    # Pass URL as string, not ParseResult
                    items.append(ImageContent(uri=url_data["url"]))
                    self.logger.debug("Added image URL to SK message: {}", url_data["url"])
                except Exception as e:
                    self.logger.error("Failed to add image URL {} to SK message: {}", url_data.get("url", "unknown"), e)
                    raise  # Fail agent execution on error
        
        # Create ChatMessageContent with items
        return ChatMessageContent(role=AuthorRole.USER, items=items)

    async def _execute_agent(self, context: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute with SK agent. This method handles the actual LLM execution.
        Supports multimodal inputs (text, images, documents, URLs) using SK ChatMessageContent format.
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
            message = self._build_multimodal_content(rendered_inputs, context)
            
            # Create a thread to hold the conversation
            # If no thread is provided, a new thread will be 
            # created and returned with the initial response
            thread: ChatHistoryAgentThread | None = None
            
            # Execute with SK agent
            self.logger.info("Executing SK workflow with multimodal content")
            
            # Use invoke() method with ChatMessageContent - this properly uses MCP tools
            result_generator = self.agent.invoke(message)
            result = None
            async for chunk in result_generator:
                result = chunk

            self.logger.success("SK agent execution completed")
            
            # Return raw result - base_agent.execute() will parse it
            return result
            
        except Exception as e:
            self.logger.error("SK agent execution failed: {}", e)
            raise AgentError(f"SK agent execution failed: {e}")
    