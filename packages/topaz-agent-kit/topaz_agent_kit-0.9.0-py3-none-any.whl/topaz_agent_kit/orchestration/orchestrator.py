"""
Consolidated Orchestrator using the clean architecture with Agent Factory and Configuration Engine.
This orchestrator replaces both the old OrchestratorTemplate and NewOrchestrator, providing
a single, robust implementation that works everywhere.
"""

import yaml
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv
from topaz_agent_kit.core.ag_ui_event_emitter import AGUIEventEmitter
from topaz_agent_kit.core.pipeline_runner import PipelineRunner
from topaz_agent_kit.core.agent_runner import AgentRunner
from topaz_agent_kit.core.configuration_engine import ConfigurationEngine
from topaz_agent_kit.agents.agent_factory import AgentFactory
from topaz_agent_kit.frameworks.framework_mcp_manager import FrameworkMCPManager
from topaz_agent_kit.orchestration.summary_renderer import render_summary
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.json_utils import JSONUtils
from topaz_agent_kit.mcp.mcp_client import MCPClient
from topaz_agent_kit.core.database_manager import DatabaseManager
from topaz_agent_kit.core.exceptions import (
    ConfigurationError,
    DatabaseError,
    FileError,
    MCPError,
    PipelineError,
    PipelineStoppedByUser,
)
import traceback


# REMOVED: Module-level logger - this was created at import time before global level was set
# logger = Logger("Orchestrator")


class Orchestrator:
    """
    Consolidated orchestrator using clean architecture with Agent Factory and Configuration Engine.
    This replaces both OrchestratorTemplate and NewOrchestrator, providing a single robust implementation.
    """

    def __init__(self, config: Dict[str, Any], project_dir: str):
        self.logger = Logger("Orchestrator")

        # Store configuration
        self.raw_config = config
        self._project_dir = project_dir

        # Initialize Configuration Engine and Agent Factory first (needed for LLM creation)
        try:
            project_path = Path(project_dir)

            # Load environment variables once at the top level
            load_dotenv(project_path / ".env")
            self.logger.debug(
                "Loaded environment variables from: {}", project_path / ".env"
            )

            self.config_engine = ConfigurationEngine(project_path)
            config_result = self.config_engine.load_and_validate()

            # FIXED: Handle actual ConfigurationResult structure where errors are strings
            if not config_result or not config_result.is_valid:
                error_msgs = []
                if (
                    config_result
                    and hasattr(config_result, "errors")
                    and config_result.errors
                ):
                    # errors are already strings, no need to extract .file and .message
                    error_msgs = config_result.errors
                else:
                    error_msgs = [
                        "Configuration validation failed - no result returned"
                    ]

                raise ConfigurationError(
                    "Configuration validation failed:\n" + "\n".join(error_msgs)
                )

            # FIXED: Ensure config_result has required attributes before proceeding
            if not hasattr(config_result, "pipeline_config") or not hasattr(
                config_result, "ui_config"
            ):
                raise ConfigurationError(
                    "Configuration result missing required attributes"
                )

            self.agent_factory = AgentFactory(config_result)
            self.validated_config = config_result
            self.logger.success(
                "Configuration Engine and Agent Factory initialized successfully"
            )

            # Initialize new architecture components
            try:
                self.framework_mcp_manager = FrameworkMCPManager()
                self.logger.success(
                    "Architecture components (FrameworkMCPManager) initialized successfully"
                )
            except Exception as e:
                self.logger.warning(
                    "Failed to initialize new architecture components: {}", e
                )
                self.framework_mcp_manager = None
        except Exception as e:
            self.logger.error("Failed to initialize configuration system: {}", e)
            raise ConfigurationError(f"Configuration system error: {e}")

        # NEW: Context storage initialization
        self._session_manager = None
        self._database_manager = None
        if self.validated_config and hasattr(self.validated_config, "chatdb_path"):
            try:
                from topaz_agent_kit.core.chat_storage import ChatStorage
                from topaz_agent_kit.core.session_manager import SessionManager

                db_path = self.validated_config.chatdb_path
                # Resolve path relative to project directory
                if self._project_dir and not Path(db_path).is_absolute():
                    db_path = str(Path(self._project_dir) / db_path)
                chat_storage = ChatStorage(db_path)
                session_manager = SessionManager(chat_storage)
                self._database_manager = DatabaseManager(chat_storage, session_manager)
                self.logger.success("Database manager initialized: {}", db_path)
            except Exception as e:
                self.logger.warning("Failed to initialize database manager: {}", e)
                self._database_manager = None

        # NEW: Multi-server MCP client management (one per server)
        self._mcp_clients = {}  # server_url -> MCPClient
        self._mcp_tools_cache = {}  # server_url -> List[tools]

        # Session-based agent caching
        self._session_agents = {}  # session_id -> agents cache

        # Initialize AgentRunner for independent agent execution
        self.agent_runner = None
        if self.validated_config:
            try:
                self.agent_runner = AgentRunner(self.validated_config)
                self.logger.success("AgentRunner initialized successfully")
            except Exception as e:
                self.logger.warning("Failed to initialize AgentRunner: {}", e)
                self.agent_runner = None

        # Initialize other components

        # Log level is controlled ONLY by CLI --log-level argument, not overridden by defaults/settings
        # This ensures consistent behavior across all services

        self.logger.success("Orchestrator initialized successfully")

    async def _initialize_mcp_clients(
        self, agent_configs: List[Dict[str, Any]]
    ) -> None:
        """Initialize MCP clients for all unique servers from agent configurations"""
        try:
            # Extract unique MCP servers from all agent configurations
            unique_servers = set()
            for agent_config in agent_configs:
                mcp_config = agent_config.get("mcp", {})
                if mcp_config.get("enabled", False):
                    for server_config in mcp_config.get("servers", []):
                        server_url = server_config.get("url")
                        if server_url:
                            unique_servers.add(server_url)

            if not unique_servers:
                self.logger.info(
                    "No MCP servers configured, skipping MCP client initialization"
                )
                return

            self.logger.info(
                "Initializing MCP clients for {} unique servers: {}",
                len(unique_servers),
                list(unique_servers),
            )

            # Create one MCPClient per unique server
            for server_url in unique_servers:
                try:
                    self.logger.info(
                        "Initializing MCP client for server: {}", server_url
                    )
                    client = MCPClient(server_url)

                    # Discover tools for this server
                    tools = await client.list_tools()
                    self.logger.info(
                        "Discovered {} tools from server: {}", len(tools), server_url
                    )

                    # Store client and tools
                    self._mcp_clients[server_url] = client
                    self._mcp_tools_cache[server_url] = tools

                except Exception as e:
                    # Fail fast - if any server fails, stop the entire pipeline
                    error_msg = f"Failed to connect to MCP server {server_url}: {e}"
                    self.logger.error(error_msg)
                    raise MCPError(error_msg)

            self.logger.success(
                "Successfully initialized MCP clients for all {} servers",
                len(unique_servers),
            )

        except Exception as e:
            self.logger.error("Failed to initialize MCP clients: {}", e)
            # Clear any partially initialized clients
            self._mcp_clients = {}
            self._mcp_tools_cache = {}
            raise MCPError(f"Failed to initialize MCP clients: {e}")

    async def _discover_all_mcp_tools(self) -> None:
        """Discover all available MCP tools from all configured servers"""
        try:
            if not self._mcp_clients:
                self.logger.warning("No MCP clients available for tool discovery")
                self._mcp_tools_cache = {}
                return

            self.logger.debug(
                "Starting MCP tool discovery for {} servers...", len(self._mcp_clients)
            )

            # Tools are already discovered during client initialization
            total_tools = sum(len(tools) for tools in self._mcp_tools_cache.values())
            self.logger.info(
                "MCP tool discovery completed: {} total tools from {} servers",
                total_tools,
                len(self._mcp_clients),
            )

        except Exception as e:
            self.logger.warning("Failed to discover MCP tools: {}", e)
            self.logger.debug("MCP discovery traceback: {}", traceback.format_exc())
            self._mcp_tools_cache = {}
            self.logger.info("Continuing with empty tools cache")

    def _filter_tools_by_patterns(
        self, tools: List[Any], toolkits: List[str], tool_patterns: List[str]
    ) -> List[Any]:
        """Filter tools based on toolkit and tool pattern requirements"""
        if not toolkits and not tool_patterns:
            # If no filtering specified, return all tools
            return tools

        filtered_tools = []

        for tool in tools:
            tool_name = getattr(tool, "name", str(tool))

            # Check if tool matches any toolkit requirement
            toolkit_match = False
            if toolkits:
                for toolkit in toolkits:
                    if tool_name.startswith(f"{toolkit}."):
                        toolkit_match = True
                        break
            else:
                toolkit_match = True  # No toolkit requirement

            # Check if tool matches any tool pattern requirement
            pattern_match = False
            if tool_patterns:
                for pattern in tool_patterns:
                    if self._tool_matches_pattern(tool_name, pattern):
                        pattern_match = True
                        break
            else:
                pattern_match = True  # No pattern requirement

            # Tool must match both toolkit and pattern requirements
            if toolkit_match and pattern_match:
                filtered_tools.append(tool)

        return filtered_tools

    def _tool_matches_pattern(self, tool_name: str, pattern: str) -> bool:
        """Check if a tool name matches a pattern (supports wildcards)"""
        if pattern == "*":
            return True

        # Convert wildcard pattern to regex
        import re

        regex_pattern = pattern.replace(".", "\\.").replace("*", ".*")

        try:
            return bool(re.match(regex_pattern, tool_name))
        except re.error:
            # If regex fails, fall back to exact match
            return tool_name == pattern

    async def _get_filtered_tools_for_agent(
        self, agent_config: Dict[str, Any]
    ) -> List[Any]:
        """Get filtered MCP tools for a specific agent based on their MCP configuration"""
        try:
            # Get agent's MCP configuration
            mcp_config = agent_config.get("mcp", {})

            if not mcp_config or not mcp_config.get("enabled", False):
                self.logger.debug("Agent has no MCP configuration or MCP is disabled")
                return []

            # Collect tools from all configured servers for this agent
            all_tools = []
            for server_config in mcp_config.get("servers", []):
                server_url = server_config.get("url")
                if server_url in self._mcp_tools_cache:
                    server_tools = self._mcp_tools_cache[server_url]

                    # Filter tools based on toolkit and tool patterns
                    filtered_tools = self._filter_tools_by_patterns(
                        server_tools,
                        server_config.get("toolkits", []),
                        server_config.get("tools", []),
                    )
                    all_tools.extend(filtered_tools)

                    self.logger.debug(
                        "Agent {} gets {} tools from server {}",
                        agent_config.get("id", "unknown"),
                        len(filtered_tools),
                        server_url,
                    )
                else:
                    self.logger.warning(
                        "Server {} not found in MCP cache for agent {}",
                        server_url,
                        agent_config.get("id", "unknown"),
                    )

            self.logger.info(
                "Agent {} receives {} total MCP tools",
                agent_config.get("id", "unknown"),
                len(all_tools),
            )
            return all_tools

        except Exception as e:
            self.logger.warning("Failed to get MCP tools for agent: {}", e)
            return []

    async def _get_or_build_agents(
        self, session_id: str, emitter: AGUIEventEmitter
    ) -> Dict[str, Any]:
        """Get cached agents or build new ones if needed"""
        if session_id in self._session_agents:
            self.logger.debug("Reusing cached agents for session: {}", session_id)
            return self._session_agents[session_id]

        # Build new agents for this session
        self.logger.debug("Building new agents for session: {}", session_id)
        agents = await self._build_agents_sequentially(emitter)

        if agents:
            self._session_agents[session_id] = agents
            self.logger.debug(
                "Cached {} agents for session: {}", len(agents), session_id
            )

        return agents

    async def _build_agents_sequentially(
        self, emitter: AGUIEventEmitter
    ) -> Dict[str, Any]:
        """Build agents sequentially based on pipeline dependencies"""
        self.logger.debug("Building agents sequentially using dependency order")

        if not self.agent_factory:
            self.logger.error(
                "Agent Factory not available, falling back to empty agents"
            )
            return {}

        # NEW: Initialize MCP clients for all configured servers
        try:
            # Get all agent configurations to extract MCP server information
            agent_configs = []
            pipeline_agents = self.validated_config.pipeline_config.get("agents", [])
            for agent_entry in pipeline_agents:
                agent_configs.append(agent_entry)

            # Initialize MCP clients for all unique servers
            await self._initialize_mcp_clients(agent_configs)

            # Discover all MCP tools from configured servers
            await self._discover_all_mcp_tools()

        except Exception as e:
            self.logger.warning("MCP initialization failed: {}", e)
            self.logger.warning("Continuing without MCP tools")
            # Clear any partially initialized clients
            self._mcp_clients = {}
            self._mcp_tools_cache = {}

        try:
            # Build from pattern-only config: initialize all declared nodes
            nodes = self.validated_config.pipeline_config.get("nodes", [])

            # Initialize agents without dependency ordering (no edges in MVP-6.0)
            agents = {}
            for node in nodes:
                node_id = node.get("id") if isinstance(node, dict) else str(node)
                if not node_id:
                    continue
                self.logger.info("Building agent: {}", node_id)

                # Build this agent
                try:
                    agent = self.agent_factory.create_agent(node_id, emitter=emitter)
                    agents[node_id] = agent
                    self.logger.success("Successfully built agent: {}", node_id)

                    # Configure and initialize the agent immediately after creation
                    try:
                        # Get agent configuration for additional setup
                        agent_info = self.agent_factory.get_agent_info(node_id)

                        # Set name attribute (but NOT role - that's framework-specific)
                        setattr(agent, "name", node_id)

                        # NEW: Pass MCP configuration to agent initialization
                        # Agent will handle MCP tool discovery internally using FrameworkMCPManager

                        # Create context with MCP configuration for agent initialization
                        init_context = {
                            "mcp_config": agent_info.get("mcp", {}),  # Pass MCP config
                            "mcp_tools_cache": self._mcp_tools_cache,  # Add full cache for agent access
                            "mcp_clients": self._mcp_clients,  # Add clients for agent access
                            "project_dir": self._project_dir,
                            "emitter": emitter,
                        }

                        self.logger.debug(
                            "Agent {}: Init context created with MCP configuration",
                            node_id,
                        )

                        # Initialize the agent
                        if hasattr(agent, "initialize"):
                            self.logger.debug(
                                "Agent {}: Calling initialize method...", node_id
                            )
                            await agent.initialize(init_context)
                            self.logger.debug(
                                "Agent {}: Initialize method completed", node_id
                            )
                        else:
                            self.logger.debug(
                                "Agent {}: No initialize method found", node_id
                            )

                    except Exception as e:
                        self.logger.error(
                            "Failed to configure/initialize agent {}: {}", node_id, e
                        )
                        # Stop building - can't continue without this agent properly initialized
                        # Build failed during agent configuration
                        raise ConfigurationError(
                            f"Failed to configure agent {node_id}: {e}"
                        )

                except Exception as e:
                    self.logger.error("Failed to build agent {}: {}", node_id, e)
                    # Stop building - can't continue without this agent
                    # Build failed during agent creation
                    raise ConfigurationError(f"Failed to build agent {node_id}: {e}")

            self.logger.info(
                "Initialized {} agents from nodes: {}", len(agents), list(agents.keys())
            )
            return agents

        except Exception as e:
            self.logger.error("Failed to build agents sequentially: {}", e)
            raise ConfigurationError(f"Failed to build agents sequentially: {e}")

    async def _build_agents(self, emitter: AGUIEventEmitter) -> Dict[str, Any]:
        """Build agents using the new Agent Factory (legacy method - now calls sequential)"""
        agents = await self._build_agents_sequentially(emitter)

        if not agents:
            return {}

        # Set additional attributes for compatibility with existing orchestrator
        for agent_id, agent in agents.items():
            self.logger.debug("Configuring agent: {}", agent_id)
            try:
                # Get agent configuration for additional setup
                agent_info = self.agent_factory.get_agent_info(agent_id)

                # Set name attribute (but NOT role - that's framework-specific)
                setattr(agent, "name", agent_id)
                # Note: role is framework-specific (e.g., CrewAI) and should NOT be overwritten

                # NEW: Pass MCP configuration to agent initialization
                # Agent will handle MCP tool discovery internally using FrameworkMCPManager

                # Create context with MCP configuration for agent initialization
                init_context = {
                    "mcp_config": agent_info.get("mcp", {}),  # Pass MCP config
                    "mcp_tools_cache": self._mcp_tools_cache,  # Add full cache for agent access
                    "mcp_clients": self._mcp_clients,  # Add clients for agent access
                    "project_dir": self._project_dir,
                    "emitter": emitter,
                }

                self.logger.debug(
                    "Agent {}: Init context created with MCP configuration", agent_id
                )

                # Initialize the agent
                if hasattr(agent, "initialize"):
                    self.logger.debug(
                        "Agent {}: Calling initialize method...", agent_id
                    )
                    await agent.initialize(init_context)
                    self.logger.debug("Agent {}: Initialize method completed", agent_id)

                    # NEW: MCP tools are handled internally by the agent
                    # No need to check external MCP tool attributes
                    self.logger.debug(
                        "Agent {}: MCP tools handled internally", agent_id
                    )
                else:
                    self.logger.debug("Agent {}: No initialize method found", agent_id)

            except Exception as e:
                self.logger.error("Failed to configure agent {}: {}", agent_id, e)
                raise ConfigurationError(f"Failed to configure agent {agent_id}: {e}")

        self.logger.success(
            "Successfully built {} agents: {}", len(agents), list(agents.keys())
        )
        return agents

    async def execute_pipeline(
        self,
        pipeline_id: str,  # NEW: receives pre-determined pipeline
        user_text: str,
        emitter: AGUIEventEmitter,  # Still needed for STEP/STATE/HITL
        session_id: Optional[str] = None,
        options: Dict[str, Any] = None,
        user_files: Optional[List[str]] = None,
        agui_service: Optional[
            Any
        ] = None,  # NEW: AGUIService for HITL gate registration
    ) -> Dict[str, Any]:
        """Execute pipeline - NO routing, NO run events"""

        self.logger.input(f"Executing pipeline: {pipeline_id}")
        self.logger.input(f"User text: {user_text}")
        self.logger.input(f"Session ID: {session_id}")
        if user_files:
            self.logger.input(f"User files: {user_files}")

        # Just execute and return results
        individual_pipelines = self.validated_config.individual_pipelines

        if pipeline_id not in individual_pipelines:
            return {
                "success": False,
                "error": f"Pipeline '{pipeline_id}' not found",
                "error_type": "pipeline_not_found",
            }

        pipeline_config = individual_pipelines[pipeline_id]
        pattern_cfg = pipeline_config.get("pattern", {})

        if not pattern_cfg:
            return {
                "success": False,
                "error": f"Pipeline '{pipeline_id}' has no pattern configuration",
                "error_type": "no_pattern_config",
            }

        # Extract pipeline_dir from the individual pipeline config
        pipeline_dir = pipeline_config.get("pipeline_dir")
        if not pipeline_dir:
            return {
                "success": False,
                "error": f"Pipeline '{pipeline_id}' configuration is incomplete",
                "error_type": "incomplete_config",
            }

        # Create a merged config that combines global (with orchestrator) + individual pipeline
        # This is necessary so PipelineRunner can access orchestrator.model from global config
        global_config = self.validated_config.pipeline_config  # Get BEFORE overwriting
        merged_config = global_config.copy()
        merged_config.update(pipeline_config)  # Individual overrides global

        # Create a modified config result with the merged config
        individual_config_result = self.validated_config
        individual_config_result.pipeline_config = merged_config
        individual_config_result.pipeline_dir = pipeline_dir

        runner = PipelineRunner(pattern_cfg, config_result=individual_config_result)

        # Prepare context for pipeline execution
        # NOTE: Both "pipeline" and "pipeline_id" are provided to ensure
        # downstream components (e.g., generic handoff orchestrator) can
        # reliably locate the correct UI manifest and configuration.
        context = {
            "user_text": user_text,
            "pipeline": pipeline_id,
            "pipeline_id": pipeline_id,
            "pipeline_config": pipeline_config,
            "options": options or {},
            "emitter": emitter,  # For STEP/STATE/HITL only
            "agui_service": agui_service,  # NEW: For HITL gate registration
            "agent_factory": self.agent_factory,
            "project_dir": self._project_dir,
            "mcp_tools_cache": self._mcp_tools_cache,
            "mcp_clients": self._mcp_clients,
            "user_files": user_files or [],
        }

        # Pre-process user_files into structured multimodal data
        context["user_files_data"] = self._preprocess_user_files(user_files or [], user_text)

        # Inject user profiles defaults into initial context if available
        try:
            project_path = Path(self._project_dir)
            profiles_path = project_path / "config" / "user_profiles.yml"
            if profiles_path.exists():
                with open(profiles_path, "r", encoding='utf-8') as f:
                    profiles_cfg = yaml.safe_load(f) or {}
                default_profile = profiles_cfg.get("default_profile_id")
                default_payment = profiles_cfg.get("default_payment_id")
                # Choose traveler_ids: family group containing default_profile, else [default_profile]
                traveler_ids = []
                for fam in profiles_cfg.get("family", []):
                    ids = fam.get("traveler_ids", [])
                    if isinstance(ids, list) and (not default_profile or default_profile in ids):
                        traveler_ids = ids
                        break
                if not traveler_ids and default_profile:
                    traveler_ids = [default_profile]

                if default_profile:
                    context["profile_id"] = default_profile
                if traveler_ids:
                    context["traveler_ids"] = traveler_ids
                if default_payment:
                    context["payment_id"] = default_payment
                context["user_profiles"] = profiles_cfg
                self.logger.info("Loaded user_profiles defaults: profile_id={}, payment_id={} ({} travelers)", context.get("profile_id"), context.get("payment_id"), len(context.get("traveler_ids", [])))
        except Exception as e:
            self.logger.warning("Failed to load user_profiles.yml: {}", e)

        if self._database_manager and session_id:
            try:
                previous_turns = self._database_manager.get_turns_for_session(
                    session_id
                )
                context.update({"previous_turns": previous_turns})
            except Exception as e:
                self.logger.warning("Failed to include previous_turns: {}", e)

            # Execute pipeline
            try:
                result = await runner.run(context=context)
            except PipelineStoppedByUser as e:
                # User-initiated stop - treat as success
                self.logger.info(
                    "Pipeline stopped by user at gate {}: {}", e.gate_id, e.reason
                )
                return {
                    "success": True,
                    "pipeline": pipeline_id,
                    "result": None,
                    "summary": f"Pipeline stopped as requested at gate '{e.gate_id}'. {e.reason}",
                    "stopped_by_user": True,
                    "gate_id": e.gate_id,
                    "reason": e.reason,
                    "error": None,
                }
            except PipelineError as e:
                # Actual pipeline error
                self.logger.error("Pipeline execution failed: {}", e)
                return {
                    "success": False,
                    "pipeline": pipeline_id,
                    "result": None,
                    "summary": f"Pipeline execution failed: {e}",
                    "error": str(e),
                    "error_type": "pipeline_execution_failed",
                }

            # Check if the pipeline failed
            if isinstance(result, dict) and result.get("error"):
                error_msg = result.get("error", "Unknown pipeline error")
                return {
                    "success": False,
                    "error": error_msg,
                    "error_type": "pipeline_execution_failed",
                }

        # Use final_output from pipeline if available, otherwise render summary
        if isinstance(result, dict) and "final_output" in result:
            summary = result.pop("final_output")  # Extract and remove from result
            self.logger.info("Using final_output from pipeline: {} chars", len(summary))
        else:
            # Render summary (simplified for pattern-only execution)
            try:
                summary = render_summary(result, pipeline_config=pipeline_config)
            except Exception as e:
                self.logger.warning("Failed to render summary: {}", e)
                summary = "Pipeline completed but summary rendering failed"

        # Return structured result
        return {
            "success": True,
            "pipeline": pipeline_id,
            "result": result,
            "summary": summary,
            "error": None,
        }

    async def execute_agent(
        self,
        agent_id: str,
        user_text: str,
        emitter: AGUIEventEmitter,
        session_id: Optional[str] = None,
        options: Dict[str, Any] = None,
        user_files: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Execute independent agent - NO events"""

        self.logger.input(f"Executing agent: {agent_id}")
        self.logger.input(f"User text: {user_text}")
        self.logger.input(f"Session ID: {session_id}")
        if user_files:
            self.logger.input(f"User files: {user_files}")

        if not self.agent_runner or not self.agent_factory:
            return {
                "success": False,
                "error": "Agent system not initialized",
                "summary": "Agent system not initialized",
            }

        # Get agent config
        independent_agents = self.validated_config.pipeline_config.get(
            "independent_agents", []
        )
        agent_config = None
        for agent in independent_agents:
            if agent.get("id") == agent_id:
                config_file = agent.get("config_file")
                agent_config_path = Path(self._project_dir) / "config" / config_file
                with open(agent_config_path, "r", encoding='utf-8') as f:
                    agent_config = yaml.safe_load(f)
                break

        if not agent_config:
            return {
                "success": False,
                "error": f"Agent '{agent_id}' not found",
                "summary": f"Agent '{agent_id}' not found",
            }

        # Build and execute
        try:
            result = await self.agent_runner.execute_standalone_agent(
                agent_id=agent_id,
                user_text=user_text,
                emitter=emitter,
                session_id=session_id,
                agent_factory=self.agent_factory,
                mcp_tools_cache=self._mcp_tools_cache,
                mcp_clients=self._mcp_clients,
                project_dir=self._project_dir,
                additional_context=options or {},
                user_files=user_files or [],
            )
            return {
                "success": True,
                "agent": agent_id,
                "result": result,
                "summary": str(result),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "summary": f"Agent execution failed: {e}",
            }

    def _preprocess_user_files(self, user_files: List[str], user_text: str) -> Dict[str, Any]:
        """Pre-process user files into structured multimodal data"""
        from topaz_agent_kit.utils.file_utils import FileUtils
        
        result = {
            "images": [],
            "documents": [],
            "urls": []
        }
        
        # Process file paths
        for file_path in user_files:
            try:
                file_type = FileUtils.detect_file_type(file_path)
                if file_type == "image":
                    image_data = FileUtils.read_image_file(file_path)
                    result["images"].append(image_data)
                elif file_type == "document":
                    doc_data = FileUtils.read_document_file(file_path)
                    result["documents"].append(doc_data)
            except Exception as e:
                self.logger.error("Failed to pre-process file {}: {}", file_path, e)
                raise  # Fail agent execution on error
        
        # Detect URLs in user_text
        if user_text:
            urls = FileUtils.detect_urls(user_text)
            for url in urls:
                url_type = FileUtils.detect_url_type(url)
                if url_type in ["image", "document"]:
                    media_type = FileUtils.get_url_media_type(url, url_type)
                    result["urls"].append({
                        "url": url,
                        "type": url_type,
                        "media_type": media_type
                    })
        
        return result

    def _create_turn_context(
        self, user_text: str, pipeline_id: str, result: Dict[str, Any], session_id: str
    ) -> Dict[str, Any]:
        """Create turn context from execution results"""
        from datetime import datetime

        return {
            "user_text": user_text,
            "pipeline_id": pipeline_id,
            "execution_result": result,
            "timestamp": datetime.now().isoformat(),
            "agent_outputs": result.get("result", {}).get("results", {}),
            "pipeline_state": {
                "status": "completed" if "error" not in result else "failed",
                "summary": result.get("summary", ""),
                "error": result.get("error"),
            },
        }

    def _create_shared_context(
        self, previous_turns: List[Any], current_pipeline: str
    ) -> Dict[str, Any]:
        """Create shared context from previous pipeline executions"""
        shared_context = {}

        # 1. Cross-pipeline context from previous turns
        cross_pipeline_context = self._extract_cross_pipeline_context(
            previous_turns, current_pipeline
        )
        shared_context.update(cross_pipeline_context)

        # 2. Pipeline-specific context aggregation
        pipeline_context = self._aggregate_pipeline_context(
            previous_turns, current_pipeline
        )
        shared_context.update(pipeline_context)

        return shared_context

    def _extract_cross_pipeline_context(
        self, previous_turns: List[Any], current_pipeline: str
    ) -> Dict[str, Any]:
        """Extract context that can be shared across different pipelines"""
        cross_context = {
            "previous_pipeline_outputs": {},
            "shared_artifacts": {},
            "conversation_history": [],
            "cross_pipeline_insights": [],
        }

        for turn in previous_turns:
            if hasattr(turn, "turn_context") and turn.turn_context:
                turn_ctx = turn.turn_context

                # Extract agent outputs from previous pipelines
                agent_outputs = turn_ctx.get("agent_outputs", {})
                if agent_outputs:
                    pipeline_id = turn_ctx.get("pipeline_id", "unknown")
                    cross_context["previous_pipeline_outputs"][pipeline_id] = (
                        agent_outputs
                    )

                # Note: user artifacts are now stored in entries, not in turn_context

                # Build conversation history
                user_text = turn_ctx.get("user_text", "")
                summary = turn_ctx.get("pipeline_state", {}).get("summary", "")
                if user_text and summary:
                    cross_context["conversation_history"].append(
                        {
                            "user": user_text,
                            "assistant": summary,
                            "pipeline": turn_ctx.get("pipeline_id", "unknown"),
                            "timestamp": turn_ctx.get("timestamp", ""),
                        }
                    )

        return cross_context

    def _aggregate_pipeline_context(
        self, previous_turns: List[Any], current_pipeline: str
    ) -> Dict[str, Any]:
        """Aggregate context specific to the current pipeline type"""
        pipeline_context = {
            "pipeline_specific_context": {},
            "related_pipeline_outputs": {},
            "context_summary": "",
        }

        # Group turns by pipeline type
        pipeline_groups = {}
        for turn in previous_turns:
            if hasattr(turn, "turn_context") and turn.turn_context:
                pipeline_id = turn.turn_context.get("pipeline_id", "unknown")
                if pipeline_id not in pipeline_groups:
                    pipeline_groups[pipeline_id] = []
                pipeline_groups[pipeline_id].append(turn.turn_context)

        # Create context summary for current pipeline
        if current_pipeline in pipeline_groups:
            # Same pipeline - provide detailed context
            same_pipeline_turns = pipeline_groups[current_pipeline]
            pipeline_context["pipeline_specific_context"] = {
                "previous_executions": len(same_pipeline_turns),
                "last_execution": same_pipeline_turns[-1]
                if same_pipeline_turns
                else None,
                "execution_history": same_pipeline_turns,
            }
        else:
            # Different pipeline - provide related context
            related_context = {}
            for pipeline_id, turns in pipeline_groups.items():
                if pipeline_id != current_pipeline:
                    related_context[pipeline_id] = {
                        "execution_count": len(turns),
                        "last_output": turns[-1].get("agent_outputs", {})
                        if turns
                        else {},
                        "last_summary": turns[-1]
                        .get("pipeline_state", {})
                        .get("summary", "")
                        if turns
                        else "",
                    }
            pipeline_context["related_pipeline_outputs"] = related_context

        # Create context summary
        total_turns = len(previous_turns)
        pipeline_count = len(pipeline_groups)
        pipeline_context["context_summary"] = (
            f"Session has {total_turns} turns across {pipeline_count} pipelines"
        )

        return pipeline_context

    def _extract_insights_from_outputs(
        self, agent_outputs: Dict[str, Any], pipeline_id: str
    ) -> List[Dict[str, Any]]:
        """Extract insights from agent outputs for cross-pipeline sharing"""
        insights = []

        for agent_id, output in agent_outputs.items():
            if isinstance(output, dict):
                # Extract structured insights
                if "insights" in output:
                    for insight in output["insights"]:
                        insights.append(
                            {
                                "insight": insight,
                                "category": f"{pipeline_id}_{agent_id}",
                                "agent": agent_id,
                            }
                        )

                # Extract key findings
                if "findings" in output:
                    for finding in output["findings"]:
                        insights.append(
                            {
                                "insight": finding,
                                "category": f"{pipeline_id}_findings",
                                "agent": agent_id,
                            }
                        )

                # Extract recommendations
                if "recommendations" in output:
                    for rec in output["recommendations"]:
                        insights.append(
                            {
                                "insight": rec,
                                "category": f"{pipeline_id}_recommendations",
                                "agent": agent_id,
                            }
                        )

                # Extract data points
                if "data" in output and isinstance(output["data"], dict):
                    for key, value in output["data"].items():
                        if (
                            isinstance(value, (str, int, float))
                            and len(str(value)) < 200
                        ):
                            insights.append(
                                {
                                    "insight": f"{key}: {value}",
                                    "category": f"{pipeline_id}_data",
                                    "agent": agent_id,
                                }
                            )

        return insights

    def get_agent_info(self, agent_id: str) -> Dict[str, Any]:
        """Get information about a specific agent"""
        if self.agent_factory:
            return self.agent_factory.get_agent_info(agent_id)
        return {}

    # Context management methods
    def create_session(self, source: str = "cli") -> str:
        """Create a new session (flat schema)."""
        if not self._database_manager:
            raise DatabaseError("Database manager not initialized")
        return self._database_manager.create_session(source)

    def get_session(self, session_id: str) -> Optional[Any]:
        """Get a session by ID"""
        if not self._database_manager:
            raise DatabaseError("Database manager not initialized")

        return self._database_manager.get_session(session_id)

    def restore_session(self, session_id: str) -> Any:
        """Restore a session with full context and history"""
        if not self._database_manager:
            raise DatabaseError("Database manager not initialized")

        return self._database_manager.restore_session(session_id)

    def get_all_sessions(self, status: str = "active") -> List[Any]:
        """Get all sessions"""
        if not self._database_manager:
            raise DatabaseError("Database manager not initialized")

        return self._database_manager.get_all_sessions(status)

    def get_turns_for_session(self, session_id: str) -> List[Any]:
        """Get turns for a session"""
        if not self._database_manager:
            raise DatabaseError("Database manager not initialized")

        return self._database_manager.get_turns_for_session(session_id)
    
    def update_turn_entries(self, turn_id: str, entries: List[Dict[str, Any]]) -> bool:
        """Update entries for a turn"""
        if not self._database_manager:
            self.logger.warning("Database manager not initialized, skipping turn entries update")
            return False
        return self._database_manager.update_turn_entries(turn_id, entries)
    
    def get_turn_entries(self, turn_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get entries for a turn"""
        if not self._database_manager:
            return None
        return self._database_manager.get_turn_entries(turn_id)
    
    def get_all_session_entries(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all entries for a session (merged from all turns)"""
        if not self._database_manager:
            self.logger.warning("Database manager not initialized, returning empty list")
            return []
        return self._database_manager.get_all_session_entries(session_id)
    
    def get_turn_by_run_id(self, run_id: str) -> Optional[Any]:
        """Get turn by run ID"""
        if not self._database_manager:
            return None
        return self._database_manager.get_turn_by_run_id(run_id)
    
    # === SESSION STATE MANAGEMENT ===
    
    def update_session_thread_state(self, session_id: str, thread_state: str) -> bool:
        """Update session thread state in database"""
        if not self._database_manager:
            self.logger.warning("Database manager not initialized, skipping thread state update")
            return False
        return self._database_manager.update_session_thread_state(session_id, thread_state)
    
    def get_session_thread_state(self, session_id: str) -> Optional[str]:
        """Get session thread state from database"""
        if not self._database_manager:
            return None
        return self._database_manager.get_session_thread_state(session_id)
    
    def update_session_title(self, session_id: str, title: str) -> bool:
        """Update session title in database"""
        if not self._database_manager:
            self.logger.warning("Database manager not initialized, skipping title update")
            return False
        return self._database_manager.update_session_title(session_id, title)
    
    def get_session_title(self, session_id: str) -> Optional[str]:
        """Get session title from database"""
        if not self._database_manager:
            return None
        return self._database_manager.get_session_title(session_id)
    
    def update_session_pinned(self, session_id: str, pinned: bool, pinned_order: Optional[int] = None) -> bool:
        """Update session pinned status in database"""
        if not self._database_manager:
            return False
        return self._database_manager.update_session_pinned(session_id, pinned, pinned_order)
    
    def update_pinned_order(self, session_id: str, pinned_order: int) -> bool:
        """Update session pinned order in database"""
        if not self._database_manager:
            return False
        return self._database_manager.update_pinned_order(session_id, pinned_order)
    
    # === TURN MANAGEMENT ===
    
    def start_turn(self, session_id: str, user_message: str, pipeline_id: Optional[str] = None, run_id: Optional[str] = None) -> Tuple[int, str, str]:
        """Start a new turn and return (db_turn_id, turn_id, run_id)"""
        if not self._database_manager:
            raise DatabaseError("Database manager not initialized")
        return self._database_manager.start_turn(session_id, user_message, pipeline_id, run_id)
    
    def complete_turn(self, turn_id: str) -> bool:
        """Complete a chat turn"""
        if not self._database_manager:
            self.logger.warning("Database manager not initialized, skipping turn completion")
            return False
        return self._database_manager.complete_turn(
            turn_id=turn_id
        )
    
    def update_turn_status(self, turn_id: str, status: str, updates: Optional[Dict[str, Any]] = None) -> bool:
        """Update turn status and optional additional fields"""
        if not self._database_manager:
            self.logger.warning("Database manager not initialized, skipping turn status update")
            return False
        return self._database_manager.update_turn_status(turn_id, status, updates)
    
    # === CONTENT AWARENESS ===
    
    def get_available_content(self, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available content entries, optionally filtered by content_type"""
        if not self._database_manager:
            return []
        return self._database_manager.get_available_content(content_type)

    def list_agents(self) -> List[str]:
        """List all available agent IDs"""
        if self.agent_factory:
            return self.agent_factory.list_agents()
        return []

    async def cleanup(self) -> None:
        """Cleanup all agents and MCP resources"""
        try:
            self.logger.info("Starting orchestrator cleanup")

            # Cleanup all agents from all sessions
            for session_agents in self._session_agents.values():
                for agent in session_agents.values():
                    await agent.cleanup()

            # Cleanup MCP clients
            for client in self._mcp_clients.values():
                if hasattr(client, "close"):
                    await client.close()

            self.logger.info("Orchestrator cleanup completed successfully")

        except Exception as e:
            self.logger.warning("Orchestrator cleanup failed: {}", e)

    def _build_assistant_responses(
        self, summary_source: Dict[str, Any], pipeline_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Build assistant_responses from pipeline results including intermediate and final outputs"""
        assistant_responses = []

        # Get outputs configuration from pipeline config
        outputs_config = pipeline_config.get("outputs", {})
        intermediate_outputs = outputs_config.get("intermediate", [])
        final_output = outputs_config.get("final", {})

        # Add intermediate outputs
        for intermediate_config in intermediate_outputs:
            node_id = intermediate_config.get("node")
            selectors = intermediate_config.get("selectors", [])

            if node_id and node_id in summary_source:
                node_result = summary_source[node_id]

                # Try to extract content from each selector
                # Prioritize non-error content, but capture errors if that's all available
                non_error_content = None
                error_content = None

                for selector in selectors:
                    # Handle nested selectors (e.g., "research_report.summary")
                    if "." in selector:
                        parts = selector.split(".")
                        content = node_result
                        for part in parts:
                            if isinstance(content, dict) and part in content:
                                content = content[part]
                            else:
                                content = None
                                break
                    else:
                        content = (
                            node_result.get(selector)
                            if isinstance(node_result, dict)
                            else None
                        )

                    if content and isinstance(content, str) and content.strip():
                        if selector == "error":
                            error_content = content.strip()
                        else:
                            non_error_content = content.strip()
                            break  # Prefer non-error content

                # Use non-error content if available, otherwise use error content
                final_content = non_error_content or error_content
                if final_content:
                    assistant_responses.append(
                        {
                            "response": final_content,
                            "type": "intermediate_output",
                            "agent": node_id,
                        }
                    )

        # Add final output
        if final_output:
            final_node = final_output.get("node")
            final_selectors = final_output.get("selectors", [])

            if final_node and final_node in summary_source:
                final_result = summary_source[final_node]

                # Try to extract content from each selector
                # Prioritize non-error content, but capture errors if that's all available
                non_error_content = None
                error_content = None

                for selector in final_selectors:
                    # Handle nested selectors
                    if "." in selector:
                        parts = selector.split(".")
                        content = final_result
                        for part in parts:
                            if isinstance(content, dict) and part in content:
                                content = content[part]
                            else:
                                content = None
                                break
                    else:
                        content = (
                            final_result.get(selector)
                            if isinstance(final_result, dict)
                            else None
                        )

                    if content and isinstance(content, str) and content.strip():
                        if selector == "error":
                            error_content = content.strip()
                        else:
                            non_error_content = content.strip()
                            break  # Prefer non-error content

                # Use non-error content if available, otherwise use error content
                final_content = non_error_content or error_content
                if final_content:
                    assistant_responses.append(
                        {
                            "response": final_content,
                            "type": "final_output",
                            "agent": final_node,
                        }
                    )

        # If no outputs were found, add a fallback
        if not assistant_responses:
            assistant_responses.append(
                {
                    "response": "Pipeline completed successfully",
                    "type": "final_output",
                    "agent": "system",
                }
            )

        self.logger.debug("Built {} assistant responses", len(assistant_responses))
        return assistant_responses

    async def handle_file_upload(
        self,
        session_id: str,
        file_paths: List[str],
        emitter=None,
        user_message: Optional[str] = None,
        original_filenames: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Handle complete file upload flow: ingestion + analysis

        Args:
            session_id: Session ID for the upload
            file_paths: List of file paths to upload
            emitter: Event emitter for progress bars (CLI only) and AG-UI events
            user_message: Optional user message/question
            original_filenames: Optional list of original filenames (for temp files)

        Returns:
            Tuple of (success, summary, results)
        """
        try:
            from topaz_agent_kit.utils.file_upload import FileUploadHandler

            # Step 1: File Upload (CLI only)
            if emitter and hasattr(emitter, "step_started"):
                emitter.step_started(agent_name="file_uploader")

            # Initialize file upload handler
            upload_handler = FileUploadHandler(self, emitter)

            # Process files using the unified method
            upload_result = await upload_handler.process_files(
                session_id=session_id,
                file_paths=file_paths,
                user_message=user_message,
                original_filenames=original_filenames,
            )

            # Step 1 finished
            if emitter and hasattr(emitter, "step_finished"):
                emitter.step_finished("content_uploader")

            # Extract results
            success = upload_result.get("success", False)
            summary = upload_result.get("summary", "Unknown result")

            if success:
                self.logger.info("{}", summary)

                # Step 2: Content Analysis
                if emitter and hasattr(emitter, "step_started"):
                    emitter.step_started(agent_name="content_analyzer")

                # Trigger content analyzer for successfully processed files
                await self._trigger_content_analyzer_internal(
                    session_id, upload_result, emitter
                )

                return True, summary, upload_result
            else:
                self.logger.error("{}", summary)
                return False, summary, upload_result

        except Exception as e:
            self.logger.error("File upload failed: {}", e)
            return False, f"Upload failed: {str(e)}", None

    async def run_process_file_turn(
        self,
        session_id: str,
        file_paths: List[str],
        emitter: AGUIEventEmitter,
        user_message: Optional[str] = None,
        original_filenames: Optional[List[str]] = None,
        mode: str = "cli",
    ) -> Dict[str, Any]:
        """Run a complete file processing turn: upload → ingest → analyze

        Args:
            session_id: Session ID for the upload
            file_paths: List of file paths to upload
            emitter: Event emitter for AG-UI events
            user_message: Optional user message/question
            original_filenames: Optional list of original filenames (for temp files)

        Returns:
            Dict containing the processing results
        """
        self.logger.info("run_process_file_turn start")

        # Start the run first (common pattern with run_turn)
        run_id = emitter.run_started(session_id=session_id)

        try:
            from topaz_agent_kit.utils.content_uploader import ContentUploader
            from topaz_agent_kit.utils.file_upload import FileUploadHandler

            upload_results = {"success": True, "summary": "", "results": []}
            ingest_results = {"success": True, "summary": "", "results": []}

            # Step 1: content_uploader (CLI only - browser handles upload in FastAPI mode)
            if mode == "cli":
                if hasattr(emitter, "step_started"):
                    emitter.step_started(agent_name="content_uploader")
                try:
                    uploader = ContentUploader(emitter)
                    upload_results = uploader.upload_only(
                        file_paths, original_filenames
                    )
                    if not upload_results.get("success"):
                        raise FileError(
                            upload_results.get("summary") or "Upload failed"
                        )
                except Exception as e:
                    # Emit error state snapshot for uploader
                    if hasattr(emitter, "step_output"):
                        emitter.step_output(
                            node_id="content_uploader",
                            result={"status": "failed", "error": str(e)},
                            status="failed",
                            error_message=str(e),
                        )
                    if hasattr(emitter, "step_finished"):
                        emitter.step_finished("content_uploader", status="failed", error=str(e))
                    # Emit error message
                    message_id = emitter.text_message_start("assistant")
                    emitter.text_message_content(message_id, f"Upload failed: {str(e)}")
                    emitter.text_message_end(message_id)
                    emitter.run_error(run_id, str(e))
                    return {
                        "success": False,
                        "summary": f"Upload failed: {str(e)}",
                        "results": [],
                    }
                if hasattr(emitter, "step_finished"):
                    emitter.step_finished("content_uploader")

            # Step 2: content_ingester
            if hasattr(emitter, "step_started"):
                emitter.step_started(agent_name="content_ingester")
            try:
                # reuse existing ingester setup from handler (but only ingestion)
                handler = FileUploadHandler(self, emitter)
                ingest_results = await handler.process_files(
                    session_id=session_id,
                    file_paths=file_paths,
                    user_message=None,
                    original_filenames=original_filenames,
                )
                if not ingest_results.get("success"):
                    raise FileError(ingest_results.get("summary") or "Ingestion failed")
            except Exception as e:
                # Emit error state snapshot for ingester
                if hasattr(emitter, "step_output"):
                    emitter.step_output(
                        node_id="content_ingester",
                        result={"status": "failed", "error": str(e)},
                        status="failed",
                        error_message=str(e),
                    )
                if hasattr(emitter, "step_finished"):
                    emitter.step_finished("content_ingester", status="failed", error=str(e))
                # Emit error message
                message_id = emitter.text_message_start("assistant")
                emitter.text_message_content(message_id, f"Ingestion failed: {str(e)}")
                emitter.text_message_end(message_id)
                emitter.run_error(run_id, str(e))
                return {
                    "success": False,
                    "summary": f"Ingestion failed: {str(e)}",
                    "results": [],
                }
            if hasattr(emitter, "step_finished"):
                emitter.step_finished("content_ingester")

            # Step 3: content_analyzer (suppress agent-level step duplication)
            try:
                await self._trigger_content_analyzer_internal(
                    session_id, ingest_results, emitter
                )
                # Emit analyzer snapshot (compact)
                if hasattr(emitter, "step_output"):
                    emitter.step_output(
                        node_id="content_analyzer",
                        result={
                            "files_analyzed": len(ingest_results.get("results", [])),
                            "status": "completed",
                        },
                        status="completed",
                    )
            except Exception as e:
                # Emit error state snapshot for analyzer
                if hasattr(emitter, "step_output"):
                    emitter.step_output(
                        node_id="content_analyzer",
                        result={"status": "failed", "error": str(e)},
                        status="failed",
                        error_message=str(e),
                    )
                # Emit error message
                message_id = emitter.text_message_start("assistant")
                emitter.text_message_content(message_id, f"Analysis failed: {str(e)}")
                emitter.text_message_end(message_id)
                emitter.run_error(run_id, str(e))
                return {
                    "success": False,
                    "summary": f"Analysis failed: {str(e)}",
                    "results": [],
                }

            # Consolidate
            success = True
            summary = (
                f"{upload_results.get('summary', '').strip()}\n"
                if mode == "cli"
                else ""
            ) + (ingest_results.get("summary", "").strip())

            # Prepare result for run_finished
            result = {"success": success, "summary": summary, "results": ingest_results}

            # Emit text message events to inform user of results
            if success:
                message_id = emitter.text_message_start("assistant")
                emitter.text_message_content(
                    message_id, f"File upload completed successfully: {summary}"
                )
                emitter.text_message_end(message_id)
            else:
                message_id = emitter.text_message_start("assistant")
                emitter.text_message_content(
                    message_id, f"File upload failed: {summary}"
                )
                emitter.text_message_end(message_id)

            # Success - emit run_finished
            emitter.run_finished(run_id, result)
            return result

        except Exception as e:
            # Error - emit run_error
            emitter.run_error(run_id, str(e))
            raise

    async def _trigger_content_analyzer_internal(
        self,
        session_id: str,
        upload_results: Dict[str, Any],
        emitter: Optional[AGUIEventEmitter] = None,
    ) -> None:
        """Internal method to trigger content analyzer agent after successful file uploads"""
        try:
            # Extract files that need analysis (processed or skipped without analysis)
            files_needing_analysis = []
            results = upload_results.get("results", [])

            for result in results:
                file_status = result.get("status")
                filename = result.get("filename")

                if file_status == "processed":
                    # Newly processed files always need analysis
                    files_needing_analysis.append(result)
                elif file_status == "skipped":
                    # Check if skipped file already has analysis
                    existing_analysis = self._database_manager.get_available_content(
                        filename
                    )
                    if not existing_analysis:
                        # Skipped file exists in ChromaDB but has no analysis - needs analysis
                        files_needing_analysis.append(result)

            if not files_needing_analysis:
                self.logger.info("No files need analysis, skipping content analyzer")
                return

            self.logger.info(
                "Triggering content analyzer for {} files needing analysis",
                len(files_needing_analysis),
            )

            # Prepare files_to_analyze context variable - use the data already provided by process_files
            files_to_analyze = []

            for result in files_needing_analysis:
                try:
                    # Use the comprehensive data already provided by process_files
                    file_info = {
                        "file_id": result.get("file_id", ""),
                        "file_name": result.get("filename", ""),
                        "file_type": result.get("file_type", "unknown"),
                        "content_type": result.get("content_type", "unknown"),
                        "extracted_text": result.get("extracted_text", ""),
                        "word_count": result.get("word_count", 0),
                        "file_size": result.get("file_size", 0),
                    }

                    files_to_analyze.append(file_info)

                except Exception as e:
                    self.logger.warning(
                        "Failed to prepare file info for {}: {}",
                        result.get("filename", "unknown"),
                        e,
                    )
                    continue

            if not files_to_analyze:
                self.logger.warning("No files prepared for content analysis")
                return

            self.logger.input("Files to analyze: {}", files_to_analyze)

            enhanced_context = {"files_to_analyze": files_to_analyze}

            # Execute content analyzer agent using agent runner
            result = await self.agent_runner.execute_standalone_agent(
                agent_id="content_analyzer",
                user_text="analyze files",
                emitter=emitter,  # Use the same emitter as the main flow
                session_id=session_id,
                agent_factory=self.agent_factory,
                mcp_tools_cache=self._mcp_tools_cache,
                mcp_clients=self._mcp_clients,
                project_dir=Path(self._project_dir)
                if self._project_dir
                else Path.cwd(),
                additional_context=enhanced_context,
                suppress_step_events=True,
            )

            if result and result.get("result"):
                self.logger.info("Content analysis completed successfully")

                # Store analysis results in SQLite available_content table
                await self._store_analysis_results(result, files_to_analyze)
            else:
                self.logger.warning(
                    "Content analysis failed: {}", result.get("error", "Unknown error")
                )

        except Exception as e:
            self.logger.error("Failed to trigger content analyzer: {}", e)

    async def _store_analysis_results(
        self, agent_result: Dict[str, Any], files_to_analyze: List[Dict[str, Any]]
    ) -> None:
        """Store analysis results in SQLite available_content table"""
        try:
            if not self._database_manager:
                self.logger.error(
                    "Chat storage not available for storing analysis results"
                )
                return

            # Extract analysis results from agent output
            agent_output = agent_result.get("result", {})
            if not isinstance(agent_output, dict):
                self.logger.error("Invalid agent result format for analysis storage")
                return

            # Parse the JSON output from the content analyzer
            try:
                # The agent should return JSON in the result field
                if isinstance(agent_output, str):
                    # Use JSONUtils for robust JSON parsing with automatic fixes
                    # expect_json=True because content analysis should return structured JSON
                    analysis_data = JSONUtils.parse_json_from_text(
                        agent_output, expect_json=True
                    )
                else:
                    analysis_data = agent_output
            except ValueError as e:
                self.logger.error("Failed to parse agent result as JSON: {}", e)
                return

            # Extract results from the analysis
            analysis_results = analysis_data.get("results", [])
            if not analysis_results:
                self.logger.warning("No analysis results found in agent output")
                return

            # Create a mapping of file_name to file info for easy lookup
            file_info_map = {
                file_info["file_name"]: file_info for file_info in files_to_analyze
            }

            # Store each analysis result
            stored_count = 0
            for analysis_result in analysis_results:
                try:
                    file_name = analysis_result.get("file_name")
                    if not file_name:
                        self.logger.warning(
                            "Analysis result missing file_name, skipping"
                        )
                        continue

                    # Get file info for additional metadata
                    file_info = file_info_map.get(file_name, {})

                    # Extract analysis data
                    summary = analysis_result.get("summary", "")
                    topics = analysis_result.get("topics", [])
                    example_questions = analysis_result.get("example_questions", [])

                    # Extract file metadata
                    file_type = file_info.get("file_type", "unknown")
                    content_type = file_info.get("content_type", "unknown")
                    file_size = file_info.get("file_size")
                    word_count = file_info.get("word_count")

                    # Store in database
                    success = self._database_manager.create_available_content(
                        file_name=file_name,
                        file_type=file_type,
                        content_type=content_type,
                        summary=summary,
                        topics=topics,
                        example_questions=example_questions,
                        file_size=file_size,
                        word_count=word_count,
                    )

                    if success:
                        stored_count += 1
                        self.logger.info(
                            "Stored analysis results for file: {}", file_name
                        )
                    else:
                        self.logger.error(
                            "Failed to store analysis results for file: {}", file_name
                        )

                except Exception as e:
                    self.logger.error(
                        "Error storing analysis result for file {}: {}",
                        analysis_result.get("file_name", "unknown"),
                        e,
                    )
                    continue

            self.logger.info(
                "Successfully stored {} analysis results in available_content table",
                stored_count,
            )

        except Exception as e:
            self.logger.error("Failed to store analysis results: {}", e)
