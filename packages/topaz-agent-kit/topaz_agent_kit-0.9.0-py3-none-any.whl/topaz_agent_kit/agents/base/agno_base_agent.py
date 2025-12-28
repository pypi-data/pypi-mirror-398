"""
Agno framework base class implementing the BaseAgent interface.
Uses official Agno SDK for agent creation and management.
"""

from typing import Any, Dict, List, Optional, Sequence

from agno.agent import Agent
from agno.media import File, Image

from topaz_agent_kit.agents.base.base_agent import BaseAgent
from topaz_agent_kit.core.exceptions import AgentError
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.mcp_utils import matches_tool_patterns


class AgnoBaseAgent(BaseAgent):
    """
    Base class for Agno agents using official SDK patterns.
    Handles Agno-specific initialization, tool management, and execution.
    Uses the new unified architecture for model and MCP tool management.
    """
    
    def __init__(self, agent_id: str, **kwargs):
        super().__init__(agent_id, "agno", **kwargs)
        
        # Override logger with framework-specific name
        self.logger = Logger(f"AgnoAgent({agent_id})")

    def _initialize_agent(self):
        """Initialize Agno agent"""
        # no specific initialization needed for Agno

    
    def _setup_environment(self):
        """Setup Agno-specific environment variables based on model preference"""
        # no specific environment setup needed for Agno
        
            
    async def _filter_mcp_tools(self) -> None:
        """Filter MCP tools based on agent's pipeline.yml configuration - aggregate patterns from all servers"""
        if not self.tools:
            self.logger.warning("No MCP tools found")
            return
            
        mcp_config = self.agent_config.get("mcp", {})
        servers_config = mcp_config.get("servers", [])
        
        if not servers_config:
            self.logger.warning("No MCP servers found")
            return
            
        # Aggregate wildcard patterns and toolkits from pipeline.yml (same approach as other frameworks)
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
        
        # Filter each MCPTools instance using aggregated patterns
        for tool in self.tools:
            if hasattr(tool, 'functions') and hasattr(tool, 'server_params'):
                # Log count before filtering
                original_count = len(tool.functions) if hasattr(tool, "functions") and isinstance(tool.functions, dict) else 0
                self.logger.info(f"MCP tools count before filtering: {original_count}")
                
                # Debug: Log first few tool names to see what we're working with
                if hasattr(tool, "functions") and isinstance(tool.functions, dict):
                    sample_tool_names = list(tool.functions.keys())[:5]
                    self.logger.debug(f"Sample tool names (first 5): {sample_tool_names}")

                # Filter functions using aggregated patterns from all servers
                # Note: Agno tool names have leading underscores (e.g., _doc_rag_list_documents)
                # Strip leading underscore for pattern matching, but keep original name in dict
                filtered_functions = {}
                for name, fn in tool.functions.items():
                    # Strip leading underscore for pattern matching (Agno-specific)
                    name_for_matching = name.lstrip('_') if name.startswith('_') else name
                    matches = matches_tool_patterns(name_for_matching, all_patterns, all_toolkits)
                    if matches:
                        filtered_functions[name] = fn
                        self.logger.debug(f"Keeping tool: {name}")
                    else:
                        self.logger.debug(f"Filtering out tool: {name}")
                tool.functions = filtered_functions
    
    
    async def _log_tool_details(self) -> None:
        """Log filtered tool details for Agno framework"""
        if not self.tools:
            self.logger.info("No tools attached")
            return
        
        # For Agno, tools are wrapper objects with functions dict
        total_after = 0
        all_filtered_tools = []
        
        for tool in self.tools:
            if hasattr(tool, "functions") and isinstance(tool.functions, dict):
                # Note: original_count is no longer available here, so we'll just log the filtered count
                filtered_count = len(tool.functions)
                total_after += filtered_count
                all_filtered_tools.extend(list(tool.functions.keys()))
            else:
                # Fallback for non-MCP tools
                name = getattr(tool, "name", type(tool).__name__)
                all_filtered_tools.append(name)
                total_after += 1
        
        self.logger.success(f"MCP tools count after filtering: {total_after}")
        for name in sorted(all_filtered_tools):
            self.logger.success(f"  - {name}")

    
    def _create_agent(self) -> None:
        """Create Agno agent instance using official SDK"""
        try:
            # Debug: Log the LLM state
            self.logger.debug("Creating Agno agent with LLM: {} (type: {})", self.llm, type(self.llm))
            self.logger.debug("Agno agent instruction: {}", self.prompt["instruction"])

            # Create Agno agent with tools
            # Note: agno >= 2.2.8 uses 'id' parameter instead of 'agent_id'
            self.agent = Agent(
                model=self.llm,
                tools=self.tools,
                name=self.name,
                instructions=self.prompt["instruction"],
                id=self.agent_id
            )
            
            self.logger.success("Created Agno agent: {}", self.name)
            
        except Exception as e:
            raise AgentError(f"Failed to create Agno agent: {e}")
    
    def _build_multimodal_content(
        self, 
        rendered_inputs: str, 
        context: Dict[str, Any]
    ) -> tuple[str, Optional[Sequence[Image]], Optional[Sequence[File]]]:
        """
        Build multimodal content for Agno agent using Image and File objects.
        
        Agno's agent.arun() accepts:
        - message: Optional[Union[str, List, Dict, Message, BaseModel]]
        - images: Optional[Sequence[Image]]
        - videos: Optional[Sequence[Video]]
        - files: Optional[Sequence[File]]
        
        Image/File support:
        - Image: url | filepath | content (bytes) - exactly one required
        - File: url | filepath | content (bytes) | external - at least one required
        
        Args:
            rendered_inputs: Rendered prompt text
            context: Execution context containing user_files_data
            
        Returns:
            Tuple of (message_text, images_list, files_list)
        """
        images_list: List[Image] = []
        files_list: List[File] = []
        user_files_data = context.get("user_files_data", {})
        
        # Check if the agent's prompt template uses user_files variable
        # If not, skip file processing to avoid Azure OpenAI file_id errors
        if not self._should_process_files():
            return (rendered_inputs, None, None)
        
        # Add image files from user_files_data
        images = user_files_data.get("images", [])
        for image_data in images:
            try:
                # Agno Image supports: url | filepath | content (bytes)
                # Use content (bytes) for local files
                images_list.append(Image(
                    content=image_data["data"],  # bytes
                    format=image_data["metadata"].get("format", "png")
                ))
                self.logger.debug("Added image to Agno message: {}", image_data["name"])
            except Exception as e:
                self.logger.error("Failed to add image {} to Agno message: {}", image_data.get("name", "unknown"), e)
                raise  # Fail agent execution on error
        
        # Add document files from user_files_data
        documents = user_files_data.get("documents", [])
        for doc_data in documents:
            try:
                # Agno File supports: url | filepath | content (bytes) | external
                # Use content (bytes) for local files
                # Note: File class validates mime_type against allowed list, so only include if valid
                file_kwargs = {
                    "content": doc_data["data"],  # bytes
                    "name": doc_data["name"]
                }
                mime_type = doc_data["metadata"].get("mime_type")
                # Map common invalid mime_types to valid ones, or skip if not mappable
                if mime_type:
                    # Map text/markdown to text/md (Agno accepts text/md)
                    if mime_type == "text/markdown":
                        mime_type = "text/md"
                    
                    # Only include if it's in Agno's valid list (will be validated by File class)
                    # Valid types: application/pdf, application/x-javascript, text/javascript,
                    # application/x-python, text/x-python, text/plain, text/html, text/css,
                    # text/md, text/csv, text/xml, text/rtf
                    valid_mime_types = [
                        "application/pdf", "application/x-javascript", "text/javascript",
                        "application/x-python", "text/x-python", "text/plain", "text/html",
                        "text/css", "text/md", "text/csv", "text/xml", "text/rtf"
                    ]
                    if mime_type in valid_mime_types:
                        file_kwargs["mime_type"] = mime_type
                    else:
                        self.logger.warning(
                            "Skipping invalid mime_type '{}' for file {} (not in Agno's allowed list)",
                            mime_type, doc_data["name"]
                        )
                
                files_list.append(File(**file_kwargs))
                self.logger.debug("Added document to Agno message: {}", doc_data["name"])
            except Exception as e:
                self.logger.error("Failed to add document {} to Agno message: {}", doc_data.get("name", "unknown"), e)
                raise  # Fail agent execution on error
        
        # Add URLs from user_files_data
        urls = user_files_data.get("urls", [])
        for url_data in urls:
            url_type = url_data.get("type")
            url = url_data["url"]
            try:
                if url_type == "image":
                    # Use url parameter for image URLs
                    images_list.append(Image(url=url))
                    self.logger.debug("Added image URL to Agno message: {}", url)
                elif url_type == "document":
                    # Use url parameter for document URLs
                    # Only set mime_type if provided and valid (File validates mime_type against allowed list)
                    file_kwargs = {"url": url}
                    media_type = url_data.get("media_type")
                    if media_type:
                        # Only include mime_type if provided (it's validated by File class)
                        file_kwargs["mime_type"] = media_type
                    files_list.append(File(**file_kwargs))
                    self.logger.debug("Added document URL to Agno message: {}", url)
            except Exception as e:
                self.logger.error("Failed to add {} URL {} to Agno message: {}", url_type, url, e)
                raise  # Fail agent execution on error
        
        return (
            rendered_inputs,
            images_list if images_list else None,
            files_list if files_list else None
        )

    async def _execute_agent(self, context: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute with Agno agent. This method handles the actual LLM execution.
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
            message_text, images, files = self._build_multimodal_content(rendered_inputs, context)

            # Execute with Agno agent (with multimodal support)
            self.logger.info("Executing Agno agent with multimodal content")
            result = await self.agent.arun(
                input=message_text,
                images=images,
                files=files
            )
            
            self.logger.success("Agno agent execution completed")

            # Return raw result - base_agent.execute() will parse it
            return result
            
        except Exception as e:
            self.logger.error("Agno agent execution failed: {}", e)
            raise AgentError(f"Agno agent execution failed: {e}")

    
    
 