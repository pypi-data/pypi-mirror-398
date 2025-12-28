"""
CrewAI framework base class implementing the BaseAgent interface.
Uses official CrewAI SDK for agent creation and management.
"""

from typing import Any, Dict

import os

from crewai import Agent, Crew, Task

from topaz_agent_kit.agents.base.base_agent import BaseAgent
from topaz_agent_kit.core.exceptions import AgentError
from topaz_agent_kit.utils.file_utils import FileUtils
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.mcp_utils import matches_tool_patterns


class CrewAIBaseAgent(BaseAgent):
    """
    Base class for CrewAI agents using official SDK patterns.
    Handles CrewAI-specific initialization, tool management, and execution.
    """
    
    def __init__(self, agent_id: str, **kwargs):
        # Ensure agent_config is in kwargs before calling parent
        if "agent_config" not in kwargs:
            raise AgentError("CrewAI agent requires agent_config in constructor")
        
        super().__init__(agent_id, "crewai", **kwargs)
        
        # Override logger with framework-specific name
        self.logger = Logger(f"CrewAIAgent({agent_id})")
        
        # CrewAI-specific attributes only
        self.crew = None
        self.role = ""
        self.goal = ""
        self.backstory = ""
        self.task = None
        self.task_description = ""
        self.task_expected_output = ""
        
    def _setup_environment(self):
        """Setup CrewAI environment"""
        self._setup_azure_openai_env()

    def _setup_azure_openai_env(self) -> None:
        """Simplified Azure environment setup - just sets required variables without checks"""

        # Set LiteLLM's expected variables
        os.environ["AZURE_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
        os.environ["AZURE_API_BASE"] = os.getenv("AZURE_OPENAI_API_BASE")
        os.environ["AZURE_API_VERSION"] = os.getenv("AZURE_OPENAI_API_VERSION")
    
    def _initialize_agent(self) -> None:
        """Initialize CrewAI agent"""
            
        self.logger.info("Initializing CrewAI agent: {}", self.agent_id)
        
        try:
            # Load CrewAI fields (role, goal, backstory) with support for inline/file/jinja
            # Ensure all fields are strings (CrewAI Agent expects strings, not dicts)
            role_loaded = self._prompt_loader.load_prompt(spec=self._prompt_spec.get("role"))
            goal_loaded = self._prompt_loader.load_prompt(spec=self._prompt_spec.get("goal"))
            backstory_loaded = self._prompt_loader.load_prompt(spec=self._prompt_spec.get("backstory"))
            
            # Ensure all are strings (handle edge cases where load_prompt might return dict)
            self.role = str(role_loaded) if not isinstance(role_loaded, str) else role_loaded
            self.goal = str(goal_loaded) if not isinstance(goal_loaded, str) else goal_loaded
            self.backstory = str(backstory_loaded) if not isinstance(backstory_loaded, str) else backstory_loaded
            
            if not self.role or not self.goal or not self.backstory:
                self.logger.error("CrewAI agent missing required fields: role, goal, backstory")
                raise AgentError("CrewAI agent missing required fields: role, goal, backstory")
            
            self.logger.debug("Loaded CrewAI fields - role: {} chars, goal: {} chars, backstory: {} chars", len(self.role), len(self.goal), len(self.backstory))
            
            # Load task description and expected output 
            self._task_spec = self._prompt_spec.get("task")
            if not self._task_spec:
                raise AgentError("CrewAI agent missing required field: task")
            
            self.task_description = self._prompt_loader.load_prompt(spec=self._task_spec.get("description"))
            expected_output_spec = self._task_spec.get("expected_output")
            
            # Handle expected_output: could be None, string, or dict spec
            if expected_output_spec is None:
                self.task_expected_output = ""
            elif isinstance(expected_output_spec, str):
                # Direct string in YAML (e.g., expected_output: "some string")
                self.task_expected_output = expected_output_spec
            else:
                # Dict spec (e.g., expected_output: {inline: "..."})
                loaded_expected_output = self._prompt_loader.load_prompt(spec=expected_output_spec)
                # load_prompt always returns a string, but double-check
                if isinstance(loaded_expected_output, str):
                    self.task_expected_output = loaded_expected_output
                else:
                    self.logger.warning("CrewAI expected_output loaded as non-string, converting to string")
                    self.task_expected_output = str(loaded_expected_output) if loaded_expected_output else ""
            
            if not self.task_description:
                self.logger.error("CrewAI agent missing required field: task_description")
                raise AgentError("CrewAI agent missing required field: task_description")
                
            if not self.task_expected_output:
                self.logger.warning("CrewAI agent missing optional field: task_expected_output")
            
        except Exception as e:
            self.logger.error("Failed to initialize CrewAI agent: {}", e)
            raise
    
    
    async def _log_tool_details(self) -> None:
        """Log filtered tool details for CrewAI framework"""
        if not hasattr(self, '_filtered_individual_tools') or not self._filtered_individual_tools:
            self.logger.info("No tools attached")
            return
        
        # After-filter format: count + one-per-line names
        names = []
        for tool in self._filtered_individual_tools:
            if hasattr(tool, 'name'):
                names.append(tool.name)
            else:
                names.append(type(tool).__name__)
        
        self.logger.success(f"MCP tools count after filtering: {len(names)}")
        for name in sorted(set(names)):
            self.logger.success(f"  - {name}")
    
    
    async def _filter_mcp_tools(self) -> None:
        """Single function to filter MCP tools (handles both wrappers and individual tools)"""
        if not self.tools:
            return
            
        mcp_config = self.agent_config.get("mcp", {})
        servers_config = mcp_config.get("servers", [])
        
        if not servers_config:
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
        
        # Handle CrewAI MCP tools (returned directly as list from framework_mcp_manager)
        # Following working example: adapter.tools returns list of tools directly
        if self.tools:
            original_count = len(self.tools)
            self.logger.info(f"MCP tools count before filtering: {original_count}")
            
            # Filter tools using wildcard matcher
            filtered_tools = []
            seen_tool_names = set()  # Prevent duplicates
            
            for tool in self.tools:
                if hasattr(tool, 'name'):
                    tool_name = tool.name
                    
                    # Check if this tool is allowed via wildcard patterns
                    if matches_tool_patterns(tool_name, all_patterns, all_toolkits) and tool_name not in seen_tool_names:
                        filtered_tools.append(tool)
                        seen_tool_names.add(tool_name)
                        self.logger.debug(f"Keeping tool: {tool_name}")
                    else:
                        self.logger.debug(f"Filtering out tool: {tool_name}")
                else:
                    self.logger.warning(f"Tool {type(tool).__name__} has no name attribute, filtering it out")
            
            # Store filtered tools for use in _create_agent
            self._filtered_individual_tools = filtered_tools
        else:
            self._filtered_individual_tools = []
            self.logger.info("No MCP tools to filter")
    
    
    def _create_agent(self) -> None:
        """Create CrewAI agent and crew - single unified approach"""
        try:
            self.logger.debug("Creating CrewAI agent with LLM: {} (type: {})", self.llm, type(self.llm))
            self.logger.debug("CrewAI agent goal: {}", self.goal)

            # Handle MCP tools - use filtered tools from _filter_mcp_tools
            # Tools are returned directly as a list from framework_mcp_manager (adapter.tools)
            if hasattr(self, '_filtered_individual_tools') and self._filtered_individual_tools:
                self._mcp_tools = self._filtered_individual_tools
                self.logger.success("Using native CrewAI MCP tools ({} tools)", len(self._mcp_tools))
            else:
                self._mcp_tools = []
                self.logger.info("No MCP tools found, proceeding without MCP tools")

            # Merge local tools with MCP tools
            all_tools = list(self._mcp_tools) + list(self.local_tools)
            if self.local_tools:
                self.logger.success("Added {} local tools to CrewAI agent", len(self.local_tools))

            # Create agent with filtered tools (empty list is fine if no tools)
            # Always set multimodal=True to enable multimodal support when images are present
            # (No performance impact for text-only tasks)
            self.agent = Agent(
                role=self.role,
                goal=self.goal,
                backstory=self.backstory,
                tools=all_tools,
                llm=self.llm,
                multimodal=True,  # Enable multimodal support for images
                verbose=True
            )
            
            self.logger.success("Created CrewAI components: agent, task, crew")
            self.logger.info("Agent tools: {} tools available (added dynamically)", len(self.tools))
    
        except Exception as e:
            raise AgentError(f"Failed to create CrewAI components: {e}")
    
    def _build_multimodal_content(self, rendered_inputs: str, context: Dict[str, Any]) -> str:
        """
        Build enhanced task description for CrewAI with embedded multimodal content.
        
        CrewAI multimodal support:
        - ✅ Image URLs: Direct HTTP/HTTPS URLs work reliably with AddImageTool
        - ⚠️ Local images: Not fully supported (see known limitations)
        - ✅ Documents: Extracted text included directly in description
        
        Args:
            rendered_inputs: Rendered prompt text
            context: Execution context containing user_files_data
            
        Returns:
            Enhanced task description with embedded multimodal content
        """
        description_parts = [rendered_inputs] if rendered_inputs else []
        user_files_data = context.get("user_files_data", {})
        
        # Check if the agent's prompt template uses user_files variable
        # If not, skip file processing to avoid unnecessary data processing
        # Note: CrewAI uses "task" instead of "inputs" for prompt key
        if not self._should_process_files(prompt_key="task"):
            return rendered_inputs or ""
        
        # Add image URLs - these work reliably with CrewAI's AddImageTool
        # Format matches CrewAI examples: "Please analyze this image: {url}"
        urls = user_files_data.get("urls", [])
        for url_data in urls:
            url_type = url_data.get("type")
            url = url_data["url"]
            try:
                if url_type == "image":
                    description_parts.append(f"\n\nPlease analyze this image: {url}")
                    self.logger.debug("Added image URL to CrewAI task description: {}", url)
                elif url_type == "document":
                    description_parts.append(f"\n\nPlease analyze this document: {url}")
                    self.logger.debug("Added document URL to CrewAI task description: {}", url)
            except Exception as e:
                self.logger.error("Failed to add {} URL {} to CrewAI task: {}", url_type, url, e)
                raise  # Fail agent execution on error
        
        # Add local images - marked as limitation, but attempt base64 for basic support
        # Note: Local image processing has known compatibility issues with Azure OpenAI
        images = user_files_data.get("images", [])
        if images:
            self.logger.warning("Local images detected - CrewAI has known limitations with local image processing")
            for idx, img in enumerate(images, 1):
                try:
                    # Attempt base64 data URL (may not work reliably)
                    base64_data = FileUtils.encode_bytes_to_base64(img["data"])
                    data_url = f"data:{img['metadata']['mime_type']};base64,{base64_data}"
                    if len(images) > 1:
                        description_parts.append(f"\n\nHere is image {idx}: {data_url}")
                    else:
                        description_parts.append(f"\n\nHere is an image: {data_url}")
                    self.logger.debug("Added local image to CrewAI task description (may not process correctly): {}", img["name"])
                except Exception as e:
                    self.logger.error("Failed to add local image {} to CrewAI task: {}", img.get("name", "unknown"), e)
                    raise  # Fail agent execution on error
        
        # Add local documents
        # For text-based documents: include extracted text directly
        # For binary documents: include reference (agent can use MCP tools if needed)
        documents = user_files_data.get("documents", [])
        for doc in documents:
            try:
                if doc.get("text"):
                    # Include extracted text directly in description
                    description_parts.append(f"\n\nDocument: {doc['name']}\n{doc['text']}")
                    self.logger.debug("Added document text to CrewAI task description: {}", doc["name"])
                else:
                    # For binary documents without extractable text, include reference
                    # Agent can use common_read_document MCP tool if needed
                    description_parts.append(
                        f"\n\nDocument reference: {doc['name']} "
                        f"({doc['metadata']['mime_type']}, {doc['metadata']['size_bytes']} bytes). "
                        f"File path: {doc['path']}"
                    )
                    self.logger.debug("Added document reference to CrewAI task description: {}", doc["name"])
            except Exception as e:
                self.logger.error("Failed to add document {} to CrewAI task: {}", doc.get("name", "unknown"), e)
                raise  # Fail agent execution on error
        
        return "\n".join(description_parts)

    async def _execute_agent(self, context: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute CrewAI workflow - create new Task and Crew with rendered description.
        Uses persistent MCP tools.
        """
        try:
            # Use pre-rendered inputs from base_agent.execute() (stored in self._rendered_inputs)
            rendered_inputs = self._rendered_inputs if hasattr(self, '_rendered_inputs') else None
            if not rendered_inputs:
                # Fallback: render if not available (shouldn't happen in normal flow)
                rendered_inputs = self._render_prompt_with_variables(self.task_description, variables)
            self.logger.debug(f"Agent {self.agent_id} Inputs: {rendered_inputs}")

            # Build multimodal content (embeds images/documents/URLs in description)
            enhanced_description = self._build_multimodal_content(rendered_inputs, context)

            # Create new task with enhanced description (includes multimodal content)
            # Ensure expected_output is a string (not dict) to avoid CrewAI internal .get() errors
            expected_output_str = self.task_expected_output
            if isinstance(expected_output_str, dict):
                # If expected_output is a dict, convert to string description
                self.logger.warning(f"Task expected_output is dict, converting to string for CrewAI compatibility")
                expected_output_str = str(expected_output_str)
            elif expected_output_str is None:
                expected_output_str = ""
            
            self.task = Task(
                description=enhanced_description,
                agent=self.agent,
                expected_output=expected_output_str
            )
                    
            # Create new crew with persistent MCP tools
            self.crew = Crew(
                agents=[self.agent],
                tasks=[self.task],
                verbose=True
            )
                    
            # Execute crew with persistent MCP tools
            try:
                result = self.crew.kickoff()
            except Exception as e:
                # Log full traceback to understand where the error occurs
                import traceback
                import sys
                full_traceback = traceback.format_exc()
                exc_type, exc_value, exc_traceback = sys.exc_info()
                
                self.logger.error("=" * 80)
                self.logger.error("CrewAI execution failed with full traceback:")
                self.logger.error(full_traceback)
                self.logger.error("=" * 80)
                self.logger.error(f"Error type: {type(e).__name__}")
                self.logger.error(f"Error message: {str(e)}")
                
                # Extract the last few frames of the traceback to see where it's coming from
                if exc_traceback:
                    tb_lines = traceback.format_tb(exc_traceback)
                    self.logger.error("Last 5 traceback frames:")
                    for line in tb_lines[-5:]:
                        self.logger.error(line.strip())
                
                # Check if the error is about .get() being called on a string
                error_msg = str(e)
                if "'str' object has no attribute 'get'" in error_msg:
                    self.logger.error(
                        "CrewAI error: 'str' object has no attribute 'get' - this suggests CrewAI is trying to call .get() on a string. "
                        "This might be caused by CrewAI expecting a dict but receiving a string in its internal processing."
                    )
                    # Try to get the raw output if available
                    if hasattr(self.crew, "tasks") and self.crew.tasks:
                        task = self.crew.tasks[0]
                        if hasattr(task, "output"):
                            output = task.output
                            self.logger.info("Attempting to use task.output as fallback")
                            if isinstance(output, str):
                                return output
                            elif isinstance(output, dict):
                                return output
                raise
            
            self.logger.success("CrewAI workflow execution completed successfully")
            
            # CrewAI kickoff() can return different types:
            # - String: Direct task output
            # - Dict: Structured response (in some versions)
            # - Object with .raw or .content attributes
            # Normalize to ensure consistent handling
            if isinstance(result, str):
                # String result - return as-is (AgentOutputParser will handle it)
                return result
            elif isinstance(result, dict):
                # Dict result - return as-is
                return result
            elif hasattr(result, "raw"):
                # CrewAI object with .raw attribute
                raw_value = result.raw
                if isinstance(raw_value, str):
                    return raw_value
                elif isinstance(raw_value, dict):
                    return raw_value
                else:
                    return str(raw_value)
            elif hasattr(result, "content"):
                # Object with .content attribute
                content_value = result.content
                if isinstance(content_value, str):
                    return content_value
                elif isinstance(content_value, dict):
                    return content_value
                else:
                    return str(content_value)
            else:
                # Unknown type - convert to string
                self.logger.warning(f"CrewAI returned unexpected type: {type(result)}, converting to string")
                return str(result)
            
        except Exception as e:
            # This outer handler catches any exceptions from the entire _execute_agent method
            # Log full traceback here as well in case inner handler didn't catch it
            import traceback
            import sys
            full_traceback = traceback.format_exc()
            exc_type, exc_value, exc_traceback = sys.exc_info()
            
            self.logger.error("=" * 80)
            self.logger.error("CrewAI _execute_agent() outer exception handler caught error:")
            self.logger.error(f"Error type: {type(e).__name__}")
            self.logger.error(f"Error message: {str(e)}")
            self.logger.error("Full traceback:")
            self.logger.error(full_traceback)
            
            # Extract the last 10 frames to see where it's coming from
            if exc_traceback:
                tb_lines = traceback.format_tb(exc_traceback)
                self.logger.error("Last 10 traceback frames:")
                for line in tb_lines[-10:]:
                    self.logger.error(line.strip())
            
            self.logger.error("=" * 80)
            raise AgentError(f"CrewAI execution failed: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup MCP resources"""
        # MCPServerAdapter manages its own lifecycle, no explicit cleanup needed
        # Just call parent cleanup
        await super().cleanup()
 