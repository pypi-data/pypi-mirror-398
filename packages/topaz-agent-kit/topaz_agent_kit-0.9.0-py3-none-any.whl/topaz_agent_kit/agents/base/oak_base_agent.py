"""
OAK framework base class implementing the BaseAgent interface.
Uses Microsoft OAK SDK for agent creation and management.
"""
import os
from typing import Any, Dict, List, Optional

from agents import Agent, Runner, set_default_openai_client, SQLiteSession, set_tracing_disabled, OpenAIChatCompletionsModel

from topaz_agent_kit.agents.base.base_agent import BaseAgent
from topaz_agent_kit.core.exceptions import AgentError
from topaz_agent_kit.utils.file_utils import FileUtils
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.mcp_utils import matches_tool_patterns


class OAKBaseAgent(BaseAgent):
    """
    Base class for OAK agents using official SDK patterns.
    Handles OAK-specific initialization, tool management, and execution.
    Uses the unified architecture for model and MCP tool management.
    """
    
    def __init__(self, agent_id: str, **kwargs):
        super().__init__(agent_id, "oak", **kwargs)
        
        # Override logger with framework-specific name
        self.logger = Logger(f"OAKAgent({agent_id})")

        # OAK-specific attributes
        # self.session = SQLiteSession(agent_id)

        # Store filtered tool names for each plugin (since plugins don't support filtering)
        self._filtered_mcp_tool_names = {}

    def _initialize_agent(self):
        """Initialize OAK agent"""
        set_tracing_disabled(True)

    def _setup_environment(self):
        """Setup OAK-specific environment variables based on model preference"""
        # no specific environment setup needed for OAK

    async def _filter_mcp_tools(self) -> None:
        """Filter MCP tools for OAK framework using pattern matching"""
        try:
            self.logger.debug("Filtering MCP tools for OAK agent: {}", self.agent_id)
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
            
            # For OAK, tools are MCPServerStreamableHttp wrapper objects
            # We need to query the MCP server to check which tools match patterns
            # If no tools match, we should remove the plugin
            # Note: OAK's plugin doesn't support filtering at plugin level, so we store
            # the filtered tool names for later use in _log_tool_details
            filtered_tools = []
            self._filtered_mcp_tool_names = {}  # Clear previous filtered names
            
            for tool in self.tools:
                # Handle MCPServerStreamableHttp objects (new MCP setup)
                if hasattr(tool, 'list_tools'):
                    # Tool is already connected by connect_framework_mcp_tools, just list tools
                    try:
                        # List tools (tool is already connected)
                        tools_result = await tool.list_tools()
                        
                        # Extract tools from result
                        all_tool_objects = []
                        if hasattr(tools_result, 'tools'):
                            all_tool_objects = tools_result.tools
                        elif isinstance(tools_result, list):
                            all_tool_objects = tools_result
                    except Exception as e:
                        self.logger.warning(f"Exception getting tools from OAK plugin: {e}")
                        filtered_tools.append(tool)
                        self._filtered_mcp_tool_names[id(tool)] = []
                        continue
                    
                    if not all_tool_objects:
                        filtered_tools.append(tool)
                        self._filtered_mcp_tool_names[id(tool)] = []
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
                        self.logger.debug(f"Keeping OAK MCP plugin (matched {len(matching_tool_names)} tools)")
                    else:
                        self.logger.debug(f"Filtering out OAK MCP plugin (no tools matched patterns)")
                # Handle dictionary-based tools (legacy)
                elif isinstance(tool, dict) and 'name' in tool:
                    if matches_tool_patterns(tool['name'], all_patterns, all_toolkits):
                        filtered_tools.append(tool)
                        self.logger.debug(f"Keeping OAK tool: {tool['name']}")
                    else:
                        self.logger.debug(f"Filtering out OAK tool: {tool['name']}")
                else:
                    # Unknown tool type - keep it for safety
                    filtered_tools.append(tool)
                    self.logger.debug(f"Keeping OAK tool of unknown type: {type(tool).__name__}")
            
            self.tools = filtered_tools
            
        except Exception as e:
            self.logger.error("Failed to filter MCP tools for OAK: {}", e)
            self.tools = []  # Clear tools on error
    
    def _extract_tool_name(self, tool_obj: Any) -> str:
        """Extract tool name from tool object"""
        if hasattr(tool_obj, 'name'):
            return tool_obj.name
        elif isinstance(tool_obj, dict) and 'name' in tool_obj:
            return tool_obj['name']
        return str(tool_obj)
    
    async def _log_tool_details(self) -> None:
        """Log filtered tool details for OAK framework"""
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
        """Create OAK agent instance using official SDK"""
        try:
            self.logger.debug("Creating OAK agent with LLM: {} (type: {})", self.llm, type(self.llm))
            self.logger.debug("OAK agent instruction: {}", self.prompt["instruction"])
            
            # OAK supports both mcp_servers (for MCP) and tools (for local tools)
            # Keep MCP servers separate, add local tools via tools= parameter
            mcp_servers = self.tools if self.tools else None
            local_tools = self.local_tools if self.local_tools else None
            
            if self.local_tools:
                self.logger.success("Added {} local tools to OAK agent", len(self.local_tools))
            
            # Create OAK agent
            # Note: OAK Agent() accepts both mcp_servers= and tools= parameters
            agent_kwargs = {
                "name": self.agent_id,
                "model": OpenAIChatCompletionsModel(model=os.getenv("AZURE_OPENAI_MODEL"), openai_client=self.llm),
                "instructions": self.prompt["instruction"],
            }
            
            # Add mcp_servers if available
            if mcp_servers:
                agent_kwargs["mcp_servers"] = mcp_servers
            
            # Add local tools if available
            if local_tools:
                agent_kwargs["tools"] = local_tools
            
            self.agent = Agent(**agent_kwargs)
            
            self.logger.success("Created OAK agent: {}", self.name)
            self.logger.info("Agent tools: {} tools available", len(self.tools))
            
        except Exception as e:
            raise AgentError(f"Failed to create OAK agent: {e}")
    
    def _build_multimodal_content(self, rendered_inputs: str, context: Dict[str, Any]) -> Optional[list[Dict[str, Any]]]:
        """
        Build multimodal content list for OAK Runner using ResponseInputItemParam format.
        
        OAK's Runner.run() accepts input as str | list[TResponseInputItem], where
        TResponseInputItem (ResponseInputItemParam) uses OpenAI Responses API format:
        - For EasyInputMessage: {"role": "user", "content": str | list[ResponseInputContentParam]}
        - ResponseInputContentParam can be:
          - {"type": "input_text", "text": "..."}
          - {"type": "input_image", "image_url": "..."}  # image_url is a string, not nested dict
        
        Args:
            rendered_inputs: Rendered prompt text
            context: Execution context containing user_files_data
            
        Returns:
            None if text-only (use plain string), or list of ResponseInputItemParam-compatible dicts for multimodal
        """
        content = []
        user_files_data = context.get("user_files_data", {})
        self.logger.debug("Building OAK multimodal content - user_files_data keys: {}", list(user_files_data.keys()) if user_files_data else "None")
        
        # Check if the agent's prompt template uses user_files variable
        # If not, skip file processing to avoid unnecessary data processing
        if not self._should_process_files():
            return None  # Return None to signal text-only mode
        
        # Add text content (always present)
        # OAK uses Responses API format: "input_text" not "text"
        if rendered_inputs and rendered_inputs.strip():
            content.append({"type": "input_text", "text": rendered_inputs})
        
        # Add image files from user_files_data (as base64 data URLs)
        # OAK uses Responses API format: "input_image" with "image_url" field (not "image_url" type)
        images = user_files_data.get("images", [])
        self.logger.debug("Found {} image(s) in user_files_data", len(images))
        for image_data in images:
            try:
                # Convert bytes to base64 data URL
                base64_data = FileUtils.encode_bytes_to_base64(image_data["data"])
                data_url = f"data:{image_data['metadata']['mime_type']};base64,{base64_data}"
                content.append({
                    "type": "input_image",
                    "image_url": data_url  # Direct string, not nested dict
                })
                self.logger.debug("Added image to OAK message: {}", image_data["name"])
            except Exception as e:
                self.logger.error("Failed to add image {} to OAK message: {}", image_data.get("name", "unknown"), e)
                raise  # Fail agent execution on error
        
        # Add document files from user_files_data
        # OAK vision API only supports actual images (PNG, JPEG, GIF, WEBP) - NOT PDFs/documents
        documents = user_files_data.get("documents", [])
        for doc_data in documents:
            try:
                # If document has extracted text, add as text content
                if doc_data.get("text"):
                    content.append({"type": "input_text", "text": f"\n\nDocument: {doc_data['name']}\n{doc_data['text']}"})
                    self.logger.debug("Added document text to OAK message: {}", doc_data["name"])
                else:
                    # For documents without extracted text, log and skip
                    # Vision APIs don't support PDFs/documents - only actual images
                    self.logger.warning(
                        "Skipping document {} - no extracted text available and mime_type {} not supported by vision API",
                        doc_data["name"], doc_data["metadata"]["mime_type"]
                    )
            except Exception as e:
                self.logger.error("Failed to add document {} to OAK message: {}", doc_data.get("name", "unknown"), e)
                raise  # Fail agent execution on error
        
        # Add URLs from user_files_data
        urls = user_files_data.get("urls", [])
        for url_data in urls:
            url_type = url_data.get("type")
            if url_type == "image":  # OAK primarily supports images
                try:
                    content.append({
                        "type": "input_image",
                        "image_url": url_data["url"]  # Direct string, not nested dict
                    })
                    self.logger.debug("Added image URL to OAK message: {}", url_data["url"])
                except Exception as e:
                    self.logger.error("Failed to add image URL {} to OAK message: {}", url_data.get("url", "unknown"), e)
                    raise  # Fail agent execution on error
        
        # Determine if we have multimodal content (images/document URLs)
        has_multimodal = len(content) > 1 or any(item.get("type") != "input_text" for item in content)
        
        if not has_multimodal and len(content) == 1:
            # Text-only: return None to signal we should use plain string
            # We'll handle this in _execute_agent by passing the string directly
            return None
        
        # Multimodal: return list format with content as list of dicts
        # OAK requires content to be a list when multimodal
        return [{
            "role": "user",
            "content": content  # Always a list of content dicts for multimodal
        }]

    async def _execute_agent(self, context: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute with OAK agent. This method handles the actual LLM execution.
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
            input_items = self._build_multimodal_content(rendered_inputs, context)
            
            # OAK accepts: str | list[TResponseInputItem]
            # - String for text-only input
            # - List of message dicts for multimodal input
            if input_items is None:
                # Text-only: pass string directly
                self.logger.debug("OAK input: text-only (plain string)")
                runner_input = rendered_inputs
            else:
                # Multimodal: pass list format
                self.logger.debug("OAK input: multimodal ({} message(s))", len(input_items))
                runner_input = input_items
            
            # Execute with OAK agent
            self.logger.info("Executing OAK workflow{}", " with multimodal content" if input_items else "")
            
            result = await Runner.run(
                starting_agent=self.agent, 
                input=runner_input,  # String for text-only, list for multimodal
                # session=self.session,
            )

            self.logger.success("OAK agent execution completed")
            
            # Return raw result - base_agent.execute() will parse it
            return result.final_output
            
        except Exception as e:
            self.logger.error("OAK agent execution failed: {}", e)
            raise AgentError(f"OAK agent execution failed: {e}")
    