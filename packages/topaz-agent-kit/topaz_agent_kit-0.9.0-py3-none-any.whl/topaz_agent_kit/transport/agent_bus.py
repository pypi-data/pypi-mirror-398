from typing import Any, Dict, Optional

from topaz_agent_kit.core.exceptions import AgentError, PipelineError
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.transport.types import TransportMode, Protocol
from topaz_agent_kit.transport.dual_client import DualTransportClient

class AgentBus:
    """
    Unified agent-to-agent transport that chooses local or remote execution
    per recipient agent configuration. Intended to be placed into the runtime
    context so agents can call next agents uniformly.
    """

    def __init__(
        self,
        *,
        agents_by_id: Dict[str, Any],
        config: Dict[str, Any],
        emitter: Optional[Any] = None,
    ) -> None:
        self._agents_by_id = agents_by_id
        self._config = config or {}
        self._emitter = emitter
        self._logger = Logger("AgentBus")

    def _extract_base_agent_id(self, agent_id: str, context: Dict[str, Any]) -> str:
        """Extract base agent ID from instance ID using context or pattern matching.
        
        Args:
            agent_id: Agent ID (may be instance ID like math_repeater_solver_0)
            context: Execution context containing instance metadata
            
        Returns:
            Base agent ID for config lookup
        """
        # First, try to get base_agent_id from context (most reliable)
        base_agent_id_from_context = context.get("_base_agent_id")
        if base_agent_id_from_context:
            return base_agent_id_from_context
        
        # Try to use agent_factory to check if agent_id exists as config
        agent_factory = context.get("agent_factory")
        if agent_factory:
            # Check if agent_id has a config
            agent_config = agent_factory.get_agent_config(agent_id)
            if agent_config:
                # Found config with this ID, it's not an instance ID
                return agent_id
            
            # No config found, try extracting base using template from context
            instance_id_template = context.get("_instance_id_template")
            if instance_id_template:
                # Use template to extract base
                import re
                template_pattern = r'\{\{node_id\}\}(.*?)\{\{index\}\}'
                match = re.search(template_pattern, instance_id_template)
                if match:
                    separator = re.escape(match.group(1))
                    instance_pattern = rf'^(.+?){separator}(\d+)$'
                    instance_match = re.match(instance_pattern, agent_id)
                    if instance_match:
                        return instance_match.group(1)
        
        # Fallback: pattern matching without template
        import re
        match = re.search(r'^(.+?)_(\d+)$', agent_id)
        if match:
            potential_base = match.group(1)
            if '_' in potential_base:
                return potential_base
        
        # No pattern matched, return as-is
        return agent_id

    def _get_agent_cfg(self, agent_id: str) -> Dict[str, Any]:
        try:
            # Look for agent in independent agents section (flat structure)
            if "independent_agents" in self._config:
                for agent in self._config["independent_agents"]:
                    if isinstance(agent, dict) and agent.get("id") == agent_id:
                        # Load from config_file
                        if "config_file" in agent:
                            return self._load_agent_config_from_file(agent["config_file"])
            
            # Look for agent in new pattern-only structure (MVP-6.0) - fallback
            if "nodes" in self._config:
                for node in self._config["nodes"]:
                    if isinstance(node, dict) and node.get("id") == agent_id:
                        # Check if config is embedded
                        if "config" in node:
                            return node.get("config", {})
                        # Otherwise, load from config_file
                        elif "config_file" in node:
                            return self._load_agent_config_from_file(node["config_file"])
            
        except Exception as e:
            self._logger.warning("Failed to get agent config for {}: {}", agent_id, e)
        return {}
    
    def _load_agent_config_from_file(self, config_file: str) -> Dict[str, Any]:
        """Load agent configuration from individual config file"""
        try:
            import yaml
            from pathlib import Path
            
            # Debug logging
            self._logger.debug("Loading agent config file: {}", config_file)
            self._logger.debug("AgentBus config keys: {}", list(self._config.keys()))
            self._logger.debug("AgentBus project_dir: {}", self._config.get("project_dir"))
            
            # Resolve config file path relative to project directory
            # With flat structure, all agent configs are under config/agents/
            project_dir = self._config.get("project_dir")
            
            if not project_dir:
                self._logger.error("No project_dir provided in AgentBus config")
                return {}
            
            # All agent configs are directly under config/ directory in flat structure
            config_path = Path(project_dir) / "config" / config_file
            self._logger.debug("Using flat structure path: {}", config_path)
            
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            else:
                self._logger.error("Agent config file not found: {}", config_path)
                return {}
        except Exception as e:
            self._logger.error("Failed to load agent config from {}: {}", config_file, e)
            return {}


    async def route_agent_call(
        self,
        *,
        sender: str,
        recipient: str,
        content: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Route agent-to-agent communication based on configuration.
        
        Args:
            sender: ID of the calling agent
            recipient: ID of the agent to call
            content: Content data to pass to the agent (includes nested context)
            context: Full execution context for protocol determination
            
        Returns:
            Result from the called agent
            
        Raises:
            AgentError: If the agent call fails
        """
        mode = None  # Initialize to avoid UnboundLocalError in exception handler
        try:
            # Store current context for protocol extraction
            self._current_context = context
            
            # Determine transport mode and protocol
            mode = self._get_transport_mode(recipient, context)
            protocol = self._extract_edge_protocol(sender, recipient, context)
            base_url = self._get_base_url(recipient, context, mode, protocol)

             # Extract remote configuration for the recipient agent
            remote_config = self._get_remote_config(recipient, context)
            
            # Create transport client
            client = DualTransportClient(
                base_url=base_url,
                agents_by_id=self._agents_by_id,
                mode=mode,
                emitter=self._emitter,
                config=remote_config
            )
            self._logger.debug("Route {} -> {} via {} using {}", sender, recipient, protocol.value, mode.value)
            
            # Make the call
            resp = await client.send(
                protocol=protocol.value,
                sender=sender,
                recipient=recipient,
                content=content,
            )
            
            # Handle response

            if isinstance(resp, dict) and "content" in resp:
                unwrapped = resp["content"]
            else:
                unwrapped = resp
            
            if isinstance(unwrapped, dict) and "error" in unwrapped and unwrapped["error"]:
                error_msg = unwrapped["error"]
                self._logger.error("Agent {} returned error: {}", recipient, error_msg)
                raise AgentError(f"Agent {recipient} error: {error_msg}")
            
            # Note: agent_inputs stay in context, no need to merge from response
            self._logger.success("Successfully routed agent {} from {} via {}", recipient, sender, mode.value)
            return unwrapped
            
        except Exception as e:
            mode_str = mode.value if mode else "unknown"
            self._logger.error("Failed to route agent {} from {} via {}: {}", recipient, sender, mode_str, e)
            raise AgentError(f"Failed to route agent {recipient} from {sender} via {mode_str}: {e}")

    def _extract_edge_protocol(self, sender: str, recipient: str, context: Dict[str, Any]) -> Protocol:
        """Extract protocol based on agent run_mode (A2A only for remote)"""
        
        # Check if agent is local - if so, always return "in-proc"
        try:
            # Extract base agent ID if recipient is an instance ID
            base_agent_id = self._extract_base_agent_id(recipient, context)
            agent_info = self._get_agent_cfg(base_agent_id)
            run_mode = agent_info.get("run_mode", "").lower()
            
            if run_mode == "local":
                self._logger.debug("Agent {} (base: {}) is local, using IN_PROC protocol", recipient, base_agent_id)
                return Protocol.IN_PROC
        except Exception as e:
            self._logger.warning("Failed to check run_mode for {}: {}", recipient, e)
        
        # For remote agents, always use A2A
        self._logger.debug("Agent {} is remote, using A2A protocol", recipient)
        return Protocol.A2A

    def _get_agent_url(self, agent_id: str, context: Dict[str, Any] = None) -> str:
        """Get the endpoint URL for an agent (A2A only)"""
        # Extract base agent ID if agent_id is an instance ID
        base_agent_id = agent_id
        if context:
            base_agent_id = self._extract_base_agent_id(agent_id, context)
        else:
            # Fallback: simple pattern matching
            import re
            match = re.search(r'^(.+?)_(\d+)$', agent_id)
            if match:
                potential_base = match.group(1)
                if '_' in potential_base:
                    base_agent_id = potential_base
        
        agent_config = self._get_agent_cfg(base_agent_id)
        remote_config = agent_config.get("remote", {})
        
        # Get URL from remote config
        url = remote_config.get("url")
        if not url:
            raise AgentError(f"Agent '{agent_id}' has no URL configured in remote.url")
        
        # Normalize URL: convert 0.0.0.0 to 127.0.0.1 for client connections
        # 0.0.0.0 is a bind address (listen on all interfaces), not a destination address
        if "0.0.0.0" in url:
            url = url.replace("0.0.0.0", "127.0.0.1")
            self._logger.debug("Normalized agent URL from 0.0.0.0 to 127.0.0.1: {}", url)
        
        return url

    def _get_transport_mode(self, recipient: str, context: Dict[str, Any]) -> TransportMode:
        """Determine transport mode for agent (local vs remote)"""
        # Extract base agent ID if recipient is an instance ID
        base_agent_id = self._extract_base_agent_id(recipient, context)
        
        # Use base_agent_id for config lookup (instance IDs don't have separate configs)
        cfg = self._get_agent_cfg(base_agent_id)
        run_mode = cfg.get("run_mode")
        
        if not run_mode:
            self._logger.error("No run_mode specified for agent {} (base: {})", recipient, base_agent_id)
            raise AgentError(f"No run_mode specified for agent {recipient} (base: {base_agent_id})")
        
        run_mode = run_mode.lower()
        if run_mode == "remote":
            return TransportMode.REMOTE
        elif run_mode == "local":
            return TransportMode.LOCAL
        else:
            self._logger.error("Unknown run_mode '{}' for agent {}", run_mode, recipient)
            raise AgentError(f"Unknown run_mode '{run_mode}' for agent {recipient}")
    
    def _get_base_url(self, recipient: str, context: Dict[str, Any], mode: TransportMode, protocol: Protocol) -> str:
        """Determine base_url for agent (only needed for remote)"""
        if mode == TransportMode.REMOTE:
            # Get URL from remote config (always A2A)
            try:
                return self._get_agent_url(recipient, context)
            except Exception as e:
                self._logger.error("Failed to get URL for agent {}: {}", recipient, e)
                raise AgentError(f"Failed to get URL for agent {recipient}: {e}")
        else:
            return ""  # No base_url needed for local
    
    def _get_remote_config(self, recipient: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract remote configuration for the recipient agent"""
        # Extract base agent ID if recipient is an instance ID
        base_agent_id = self._extract_base_agent_id(recipient, context)
        cfg = self._get_agent_cfg(base_agent_id)
        remote_cfg = cfg.get("remote", {})
        
        # Extract timeout and retry_attempts from remote config
        config = {}
        if "timeout" in remote_cfg:
            config["timeout"] = remote_cfg["timeout"]
        if "retry_attempts" in remote_cfg:
            config["retry_attempts"] = remote_cfg["retry_attempts"]
        
        return config

