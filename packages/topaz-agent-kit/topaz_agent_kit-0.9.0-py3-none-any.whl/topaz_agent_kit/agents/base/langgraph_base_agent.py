"""
LangGraph framework base class implementing the BaseAgent interface.
Uses official LangGraph SDK for agent creation and management.
"""

from typing import Any, Dict
from topaz_agent_kit.utils.mcp_utils import matches_tool_patterns

from topaz_agent_kit.agents.base.base_agent import BaseAgent
from topaz_agent_kit.core.exceptions import AgentError
from topaz_agent_kit.utils.logger import Logger

from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import create_react_agent

class LangGraphBaseAgent(BaseAgent):
    """
    Base class for LangGraph agents using official SDK patterns.
    Handles LangGraph-specific initialization, tool management, and execution.
    """
    
    def __init__(self, agent_id: str, **kwargs):
        super().__init__(agent_id, "langgraph", **kwargs)
        
        # Override logger with framework-specific name
        self.logger = Logger(f"LangGraphAgent({agent_id})")
        
        # LangGraph-specific attributes only
        self.state_graph = None
        self.tool_node = None

    def _initialize_agent(self):
        """Initialize LangGraph agent"""
        
        self.logger.info("Initializing LangGraph agent: {}", self.agent_id)
        
        # Create LangGraph components using official SDK
        self.logger.debug("Creating LangGraph components...")
        self._create_langgraph_components()
        self.logger.debug("LangGraph components created")

    def _setup_environment(self):
        """Setup LangGraph environment"""
        # no specific environment setup needed for LangGraph
    
    async def _log_tool_details(self) -> None:
        """Log filtered tool details for LangGraph framework"""
        if not self.tools:
            self.logger.info("No tools attached")
            return
        
        # After-filter format: count + one-per-line names
        names = []
        for tool in self.tools:
            if hasattr(tool, 'name'):
                names.append(tool.name)
            else:
                names.append(type(tool).__name__)
        
        self.logger.success(f"MCP tools count after filtering: {len(names)}")
        for name in sorted(set(names)):
            self.logger.success(f"  - {name}")
    
    async def _filter_mcp_tools(self) -> None:
        """Filter MCP tools per server to avoid duplicates"""
        if not self.tools:
            return
            
        mcp_config = self.agent_config.get("mcp", {})
        servers_config = mcp_config.get("servers", [])
        
        if not servers_config:
            return
            
        # Create a mapping of server URL to allowed patterns and toolkits
        server_entries = []
        for server in servers_config:
            server_url = server["url"]
            # Normalize URL (remove /mcp suffix for comparison)
            normalized_url = server_url.replace("/mcp", "")
            server_entries.append({
                "url": normalized_url,
                "patterns": server.get("tools", []),
                "toolkits": server.get("toolkits", []),
            })
        
        # Filter tools and eliminate duplicates
        filtered_tools = []
        seen_tool_names = set()
        
        for tool in self.tools:
            if hasattr(tool, 'name'):
                tool_name = tool.name
                
                # Check if this tool name is already seen (avoid duplicates)
                if tool_name in seen_tool_names:
                    self.logger.debug(f"Skipping duplicate tool: {tool_name}")
                    continue
                    
                # Check if this tool is allowed in any server config using wildcard matcher
                tool_allowed = False
                for entry in server_entries:
                    if matches_tool_patterns(tool_name, entry["patterns"], entry["toolkits"]):
                        tool_allowed = True
                        break
                
                if tool_allowed:
                    filtered_tools.append(tool)
                    seen_tool_names.add(tool_name)
                    self.logger.debug(f"Keeping tool: {tool_name}")
                else:
                    self.logger.debug(f"Filtering out tool: {tool_name}")
            else:
                # If tool doesn't have a name attribute, keep it for safety
                self.logger.warning(f"Tool {type(tool).__name__} has no name attribute, keeping it")
                filtered_tools.append(tool)
        
        # Replace the tools list with filtered version
        original_count = len(self.tools)
        # Before-filter format: count only
        self.logger.info(f"MCP tools count before filtering: {original_count}")
        self.tools = filtered_tools
        # After details are logged in _log_tool_details()
        
    def _create_langgraph_components(self) -> None:
        """Create LangGraph components using official SDK"""
        try:
            # Create state graph
            self.state_graph = StateGraph(dict)
            
            # Always use direct tools (flattened during initialization)
            self.logger.info("Using direct tools (flattened during initialization): {} tools", len(self.tools))
            self.tool_node = ToolNode(self.tools)
            
            self.logger.info(f"Created LangGraph components for agent: {self.name}")
            
        except Exception as e:
            raise AgentError(f"Failed to create LangGraph components: {e}")
    

    def _create_agent(self) -> None:
        """Create LangGraph agent instance using official SDK"""
        try:
            # Debug: Log the LLM state
            self.logger.debug("Creating LangGraph agent with LLM: {} (type: {})", self.llm, type(self.llm))
            self.logger.debug("LangGraph agent instruction: {}", self.prompt["instruction"])

            # Create LangGraph agent with tools
            self.agent = create_react_agent(
                name=self.agent_id,
                prompt=self.prompt["instruction"],
                model=self.llm,
                tools=self.tools
            )
    
            self.logger.success("Created LangGraph agent: {}", self.name)
            self.logger.info("Agent tools: {} tools available", len(self.tools))
            
        except Exception as e:
            raise AgentError(f"Failed to create LangGraph agent: {e}")

    def _build_multimodal_content(self, rendered_inputs: str, context: Dict[str, Any]) -> Any:
        """
        Build multimodal content list for LangGraph HumanMessage.
        
        Args:
            rendered_inputs: Rendered prompt text
            context: Execution context containing user_files_data
            
        Returns:
            HumanMessage with multimodal content
        """
        from langchain_core.messages import HumanMessage
        
        from topaz_agent_kit.utils.file_utils import FileUtils
        
        content = []
        user_files_data = context.get("user_files_data", {})
        
        # Check if the agent's prompt template uses user_files variable
        # If not, skip file processing to avoid unnecessary data processing
        if not self._should_process_files():
            if rendered_inputs and rendered_inputs.strip():
                content.append({"type": "text", "text": rendered_inputs})
            return HumanMessage(content=content)
        
        # Add text content (always present)
        if rendered_inputs and rendered_inputs.strip():
            content.append({"type": "text", "text": rendered_inputs})
        
        # Add image files from user_files_data (as base64 data URLs)
        images = user_files_data.get("images", [])
        for image_data in images:
            try:
                # Convert bytes to base64 data URL
                base64_data = FileUtils.encode_bytes_to_base64(image_data["data"])
                data_url = f"data:{image_data['metadata']['mime_type']};base64,{base64_data}"
                content.append({
                    "type": "image_url",
                    "image_url": {"url": data_url}
                })
                self.logger.debug("Added image to LangGraph message: {}", image_data["name"])
            except Exception as e:
                self.logger.error("Failed to add image {} to LangGraph message: {}", image_data.get("name", "unknown"), e)
                raise  # Fail agent execution on error
        
        # Add document files from user_files_data
        # LangGraph vision API only supports actual images (PNG, JPEG, GIF, WEBP) - NOT PDFs/documents
        documents = user_files_data.get("documents", [])
        for doc_data in documents:
            try:
                # If document has extracted text, add as text content
                # LangGraph (OpenAI format) vision API does NOT support PDFs/documents
                if doc_data.get("text"):
                    content.append({"type": "text", "text": f"\n\nDocument: {doc_data['name']}\n{doc_data['text']}"})
                    self.logger.debug("Added document text to LangGraph message: {}", doc_data["name"])
                else:
                    # For documents without extracted text, log and skip
                    self.logger.warning(
                        "Skipping document {} - no extracted text available and mime_type {} not supported by vision API",
                        doc_data["name"], doc_data["metadata"]["mime_type"]
                    )
            except Exception as e:
                self.logger.error("Failed to add document {} to LangGraph message: {}", doc_data.get("name", "unknown"), e)
                raise  # Fail agent execution on error
        
        # Add URLs from user_files_data
        urls = user_files_data.get("urls", [])
        for url_data in urls:
            url_type = url_data.get("type")
            if url_type == "image":  # LangGraph primarily supports images
                try:
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": url_data["url"]}
                    })
                    self.logger.debug("Added image URL to LangGraph message: {}", url_data["url"])
                except Exception as e:
                    self.logger.error("Failed to add image URL {} to LangGraph message: {}", url_data.get("url", "unknown"), e)
                    raise  # Fail agent execution on error
        
        return HumanMessage(content=content)

    async def _execute_agent(self, context: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute with LangGraph agent using the official SDK.
        Supports multimodal inputs (text, images, documents, URLs) using LangChain HumanMessage format.
        This method creates a proper LangGraph workflow and executes the LLM with tools.
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
            
            # Execute the workflow with the multimodal message
            self.logger.info("Executing LangGraph workflow with multimodal content")
            result = await self.agent.ainvoke({
                "messages": [message]
            })
            
            self.logger.success("LangGraph workflow execution completed successfully")
            
            # Extract the final message for parsing
            # Return the content that needs to be parsed
            if "messages" in result and result["messages"]:
                final_message = result["messages"][-1]
                if hasattr(final_message, 'content'):
                    return final_message.content
                else:
                    return final_message
            else:
                return result
            
        except Exception as e:
            self.logger.error("LangGraph execution failed: {}", e)
            raise AgentError(f"LangGraph execution failed: {e}")

    
 