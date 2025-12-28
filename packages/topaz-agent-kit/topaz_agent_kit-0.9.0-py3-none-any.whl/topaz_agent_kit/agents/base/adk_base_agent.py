"""
ADK framework base class implementing the BaseAgent interface.
Uses official ADK SDK for agent creation and management.
"""

import os
from typing import Any, Dict

from topaz_agent_kit.agents.base.base_agent import BaseAgent
from topaz_agent_kit.core.exceptions import AgentError
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.mcp_utils import matches_tool_patterns

from google.adk.agents import LlmAgent
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
from google.adk.runners import Runner


class ADKBaseAgent(BaseAgent):
    """
    Base class for ADK agents using official SDK patterns.
    Handles ADK-specific initialization, tool management, and execution.
    Uses the unified architecture for model and MCP tool management.
    """
    
    def __init__(self, agent_id: str, **kwargs):
        super().__init__(agent_id, "adk", **kwargs)

        # Override logger with framework-specific name
        self.logger = Logger(f"ADKAgent({agent_id})")
        
    def _initialize_agent(self):
        """Initialize ADK agent"""

        self.logger.info("Initializing ADK agent: {}", self.agent_id)
        # Ensure generate_content_config is set to avoid missing modality issues
        try:
            if getattr(self.agent, "generate_content_config", None) is None:
                self.agent.generate_content_config = types.GenerateContentConfig()
                self.logger.debug("Initialized generate_content_config on ADK agent")
        except Exception:
            pass

    def _setup_environment(self):
        """Setup ADK-specific environment variables based on model preference"""
        try:
            # Environment variables are already loaded by Orchestrator
            model_type = self.agent_config.get("model", "")
            
            if model_type == "azure_openai":
                self._setup_azure_openai_env()
            elif model_type == "google_gemini25_flash":
                self._setup_google_gemini_env()
            elif model_type.startswith("ollama_"):
                self._setup_ollama_env()
            else:
                self.logger.warning("Unknown model type for ADK: {}", model_type)
                
        except Exception as e:
            self.logger.error("Failed to setup ADK environment: {}", e)
            raise AgentError(f"ADK environment setup failed: {e}")
    
    def _setup_azure_openai_env(self):
        """Setup Azure OpenAI environment variables (following CrewAI pattern)"""
        
        # Set LiteLLM's expected variables
        os.environ["AZURE_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
        os.environ["AZURE_API_BASE"] = os.getenv("AZURE_OPENAI_API_BASE")
        os.environ["AZURE_API_VERSION"] = os.getenv("AZURE_OPENAI_API_VERSION")

        if not os.environ["AZURE_API_KEY"] or not os.environ["AZURE_API_BASE"] or not os.environ["AZURE_API_VERSION"]:
            raise AgentError("Missing required Azure OpenAI environment variables")
        
        self.logger.info("Azure OpenAI environment variables configured")
    
    def _setup_google_gemini_env(self):
        """Setup Google Gemini environment variables"""

        # Set LiteLLM's expected variables
        os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = os.getenv("GOOGLE_GENAI_USE_VERTEXAI")

        if not os.environ["GOOGLE_API_KEY"] or not os.environ["GOOGLE_GENAI_USE_VERTEXAI"]:
            raise AgentError("Missing required Google Gemini environment variables")
        
        self.logger.info("Google Gemini environment variables configured")
    
    def _setup_ollama_env(self):
        """Setup Ollama environment variables"""

        # Set LiteLLM's expected variables
        os.environ["OLLAMA_API_BASE"] = os.getenv("OLLAMA_BASE_URL")

        if not os.environ["OLLAMA_API_BASE"]:
            raise AgentError("Missing required Ollama environment variables")
        
        self.logger.info("Ollama environment variables configured")

    async def _filter_mcp_tools(self) -> None:
        """Filter MCP tools for ADK framework using pattern matching"""
        try:
            self.logger.debug("Filtering MCP tools for ADK agent: {}", self.agent_id)
            
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
            
            # Create a ToolPredicate function that filters based on our patterns
            def create_tool_predicate(patterns: list[str], toolkits: list[str]):
                """Create a ToolPredicate function for filtering tools"""
                def tool_predicate(tool, readonly_context=None):
                    """Predicate function that matches tool names against patterns"""
                    if hasattr(tool, 'name'):
                        return matches_tool_patterns(tool.name, patterns, toolkits)
                    return False
                return tool_predicate
            
            # Set tool_filter on each McpToolset to apply filtering
            filtered_tools = []
            for tool in self.tools:
                if tool is None:
                    continue
                
                # Check if this is a McpToolset (has tool_filter attribute)
                if hasattr(tool, 'tool_filter'):
                    # Set tool_filter to our predicate function
                    tool.tool_filter = create_tool_predicate(all_patterns, all_toolkits)
                    filtered_tools.append(tool)
                    self.logger.debug("Applied tool_filter to McpToolset")
                else:
                    # Keep non-toolset tools as-is
                    filtered_tools.append(tool)
                    self.logger.debug(f"Keeping non-toolset tool: {type(tool).__name__}")
            
            self.tools = filtered_tools
            
        except Exception as e:
            self.logger.error("Failed to filter MCP tools for ADK: {}", e)
            self.tools = []  # Clear tools on error
    
    async def _log_tool_details(self) -> None:
        """Log filtered tool details for ADK framework"""
        if not self.tools:
            self.logger.info("No tools attached")
            return
        
        # For ADK, tools are McpToolset wrapper objects
        # Use get_tools() method from McpToolset to get actual tool names
        # Note: get_tools() will apply the tool_filter we set in _filter_mcp_tools
        all_filtered_tools = []
        for tool in self.tools:
            # Check if this is a McpToolset with get_tools() method (async)
            if hasattr(tool, "get_tools") and callable(tool.get_tools):
                try:
                    # get_tools() is async and will apply tool_filter automatically
                    tools_list = await tool.get_tools()
                    
                    # Extract tool names from the returned tools (already filtered)
                    if tools_list:
                        for tool_item in tools_list:
                            if hasattr(tool_item, 'name'):
                                all_filtered_tools.append(tool_item.name)
                            elif hasattr(tool_item, '__name__'):
                                all_filtered_tools.append(tool_item.__name__)
                            else:
                                all_filtered_tools.append(str(tool_item))
                except Exception as e:
                    self.logger.debug("Exception calling get_tools() on McpToolset: {}", e)
                    # Fallback to type name
                    all_filtered_tools.append(type(tool).__name__)
            # Check if this is a toolset with functions dict (similar to Agno)
            elif hasattr(tool, "functions") and isinstance(tool.functions, dict):
                all_filtered_tools.extend(list(tool.functions.keys()))
            else:
                # Fallback for tools with name attribute
                if hasattr(tool, 'name'):
                    all_filtered_tools.append(tool.name)
                else:
                    all_filtered_tools.append(type(tool).__name__)
        
        total_after = len(all_filtered_tools)

        self.logger.success(f"MCP tools count after filtering: {total_after}")
        for name in sorted(set(all_filtered_tools)):
                self.logger.success(f"  - {name}")

    def _create_agent(self) -> None:
        """Create ADK agent instance using official SDK"""
        try:
            # Debug: Log the LLM state
            self.logger.debug("Creating ADK agent with LLM: {} (type: {})", self.llm, type(self.llm))
            self.logger.debug("ADK agent instruction: {}", self.prompt["instruction"])

            # Create ADK agent with tools
            self.agent = LlmAgent(
                model=self.llm,  
                name=self.agent_id,
                instruction=self.prompt["instruction"], 
                tools=self.tools  
            )
            
            self.logger.success("Created ADK agent: {}", self.name)
            self.logger.info("Agent tools: {} tools available", len(self.tools))
            
        except Exception as e:
            raise AgentError(f"Failed to create ADK agent: {e}")
    
    def _build_multimodal_content(self, rendered_inputs: str, context: Dict[str, Any]) -> types.Content:
        """
        Build multimodal content for ADK using types.Content and types.Part.
        
        Args:
            rendered_inputs: Rendered prompt text
            context: Execution context containing user_files_data
            
        Returns:
            types.Content object with parts (text, inline_data for images/documents)
        """
        parts = []
        user_files_data = context.get("user_files_data", {})
        
        # Check if the agent's prompt template uses user_files variable
        # If not, skip file processing to avoid unnecessary data processing
        if not self._should_process_files():
            if rendered_inputs and rendered_inputs.strip():
                parts.append(types.Part(text=rendered_inputs))
            return types.Content(role='user', parts=parts)
        
        # Add text content (always present)
        if rendered_inputs and rendered_inputs.strip():
            parts.append(types.Part(text=rendered_inputs))
        
        # Add image files from user_files_data (as inline_data)
        images = user_files_data.get("images", [])
        for image_data in images:
            try:
                # ADK uses inline_data with Blob for binary content
                parts.append(types.Part(
                    inline_data=types.Blob(
                        data=image_data["data"],  # bytes
                        mime_type=image_data["metadata"]["mime_type"]
                    )
                ))
                self.logger.debug("Added image to ADK message: {}", image_data["name"])
            except Exception as e:
                self.logger.error("Failed to add image {} to ADK message: {}", image_data.get("name", "unknown"), e)
                raise  # Fail agent execution on error
        
        # Add document files from user_files_data (as inline_data)
        documents = user_files_data.get("documents", [])
        for doc_data in documents:
            try:
                parts.append(types.Part(
                    inline_data=types.Blob(
                        data=doc_data["data"],  # bytes
                        mime_type=doc_data["metadata"]["mime_type"]
                    )
                ))
                self.logger.debug("Added document to ADK message: {}", doc_data["name"])
            except Exception as e:
                self.logger.error("Failed to add document {} to ADK message: {}", doc_data.get("name", "unknown"), e)
                raise  # Fail agent execution on error
        
        # Add URLs from user_files_data
        # Let ADK handle URL fetching - use file_data for URLs
        urls = user_files_data.get("urls", [])
        for url_data in urls:
            url_type = url_data.get("type")
            if url_type in ["image", "document"]:
                try:
                    # Use file_data to let ADK handle the URL
                    parts.append(types.Part(
                        file_data=types.FileData(
                            file_uri=url_data["url"],
                            mime_type=url_data.get("media_type", "application/octet-stream")
                        )
                    ))
                    self.logger.debug("Added {} URL to ADK message (ADK will fetch): {}", url_type, url_data["url"])
                except Exception as e:
                    self.logger.error("Failed to add {} URL {} to ADK message: {}", url_type, url_data.get("url", "unknown"), e)
                    raise  # Fail agent execution on error
        
        return types.Content(role='user', parts=parts)

    async def _execute_agent(self, context: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute with ADK agent. This method handles the actual LLM execution.
        Supports multimodal inputs (text, images, documents, URLs) using ADK Content format.
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
            content = self._build_multimodal_content(rendered_inputs, context)

            # Build Session
            session_service = InMemorySessionService()
            session = await session_service.create_session(state={}, app_name="topaz", user_id="local")

            # Run the agent asynchronously
            runner = Runner(
                agent=self.agent,
                session_service=session_service,
                app_name=session.app_name
            )
            
            self.logger.info("Executing ADK agent with multimodal content")
            response = runner.run_async(
                session_id=session.id,
                user_id=session.user_id,
                new_message=content
            )

            result: str = ""
            async for message in response:
                if message.content and message.content.parts and message.content.parts[0].text:
                    result = message.content.parts[0].text

            self.logger.debug("ADK agent response: {}", result)
            self.logger.success("ADK agent execution completed")
            
            # Return raw result - base_agent.execute() will parse it
            return result
            
        except Exception as e:
            self.logger.error("ADK agent execution failed: {}", e)
            raise AgentError(f"ADK agent execution failed: {e}")
    
    
