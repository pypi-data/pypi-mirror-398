"""
Agent Factory for creating agents using validated configuration.
This factory creates agents using the new clean architecture with framework-specific base classes.
"""

from typing import Any, Dict, Optional, List
import importlib.util
from pathlib import Path

from topaz_agent_kit.agents.base import BaseAgent
from topaz_agent_kit.agents.base import AgnoBaseAgent, LangGraphBaseAgent, CrewAIBaseAgent, ADKBaseAgent, SKBaseAgent, OAKBaseAgent, MAFBaseAgent
from topaz_agent_kit.core.configuration_engine import ConfigurationResult
from topaz_agent_kit.core.exceptions import AgentError
from topaz_agent_kit.utils.logger import Logger


class AgentFactory:
    """
    Factory for creating agents using validated configuration.
    Creates framework-specific agents with proper initialization.
    """
    
    def __init__(self, config_result: ConfigurationResult):
        # FIXED: Validate config_result before proceeding
        if not config_result:
            raise ValueError("ConfigurationResult cannot be None")
        
        if not hasattr(config_result, 'is_valid'):
            raise ValueError("ConfigurationResult must have 'is_valid' attribute")
        
        if not hasattr(config_result, 'pipeline_config'):
            raise ValueError("ConfigurationResult must have 'pipeline_config' attribute")
        
        self.config_result = config_result
        self.logger = Logger("AgentFactory")
        
        # Framework mapping for base classes (fallback)
        self._framework_map = {
            "agno": AgnoBaseAgent,
            "langgraph": LangGraphBaseAgent,
            "crewai": CrewAIBaseAgent,
            "adk": ADKBaseAgent,
            "sk": SKBaseAgent,
            "oak": OAKBaseAgent,
            "maf": MAFBaseAgent
        }
        
        # Generated agent classes (will be populated dynamically)
        self._generated_agents = {}
        
        # Try to load generated agents from project directory
        self._load_generated_agents()
        
        # FIXED: Check validity before proceeding
        if not config_result.is_valid:
            error_msgs = []
            if hasattr(config_result, 'errors') and config_result.errors:
                # errors are already strings, no need to extract .file and .message
                error_msgs = config_result.errors
            else:
                error_msgs = ["Configuration validation failed"]
            
            raise ValueError(
                f"Configuration validation failed. Cannot create agents with invalid config.\n"
                f"Errors: {error_msgs}"
            )
    
    def _load_generated_agents(self) -> None:
        """Dynamically load generated agent classes from project directory"""
        try:
            # Get the project directory from configuration
            project_dir = self.config_result.project_dir
            if not project_dir:
                self.logger.warning("No project directory found, using base classes only")
                return
            
            agents_dir = project_dir / "agents"
            if not agents_dir.exists():
                self.logger.warning(f"Agents directory not found: {agents_dir}")
                return
            
            # Look for generated agent files (flat structure)
            for agent_file in agents_dir.rglob("*_agent.py"):
                try:
                    # Extract agent ID from filename (no framework prefix)
                    # e.g., "planner_agent.py" -> id="planner"
                    filename = agent_file.stem  # Remove .py extension
                    if filename.endswith("_agent"):
                        agent_id = filename[:-6]  # Remove "_agent" suffix
                        
                        # Load the agent's config file to get framework type
                        agent_config = self._find_agent_config(agent_id)
                        if not agent_config:
                            self.logger.warning(f"No config found for agent: {agent_id}")
                            continue
                        
                        agent_type = agent_config.get("type")
                        if not agent_type:
                            self.logger.warning(f"No type found in config for agent: {agent_id}")
                            continue
                        
                        # Load the module
                        spec = importlib.util.spec_from_file_location(filename, agent_file)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            
                            # Find the agent class (should be the only class in the file)
                            for attr_name in dir(module):
                                attr = getattr(module, attr_name)
                                if (isinstance(attr, type) and 
                                    issubclass(attr, BaseAgent) and 
                                    attr != BaseAgent and
                                    attr not in [ADKBaseAgent, AgnoBaseAgent, LangGraphBaseAgent, CrewAIBaseAgent, SKBaseAgent, OAKBaseAgent, MAFBaseAgent]):
                                    # Found the generated agent class (not a base class)
                                    self._generated_agents[agent_id] = attr
                                    self.logger.debug(f"Loaded generated agent class: {agent_id} -> {attr.__name__} (type: {agent_type})")
                                    break
                                        
                except Exception as e:
                    self.logger.warning(f"Failed to load agent from {agent_file}: {e}")
                    continue
                    
            self.logger.debug(f"Loaded {len(self._generated_agents)} generated agent classes")
            
        except Exception as e:
            self.logger.error(f"Failed to load generated agents: {e}")
            self.logger.error("Will use base classes as fallback")
    
    def create_agent(self, agent_id: str, **kwargs) -> BaseAgent:
        """
        Create an agent instance based on configuration.
        
        Args:
            agent_id: ID of the agent to create
            **kwargs: Additional arguments for agent creation
            
        Returns:
            Initialized agent instance
            
        Raises:
            AgentError: If agent_id not found or invalid configuration
            AgentError: If agent creation fails
        """
        # Find agent configuration
        agent_config = self._find_agent_config(agent_id)
        if not agent_config:
            raise AgentError(f"Agent '{agent_id}' not found in configuration")
        
        # Get agent type
        agent_type = agent_config.get("type")
        if not agent_type:
            raise AgentError(f"Agent '{agent_id}' missing 'type' field")
        
        # Try to use generated agent class first, fallback to base class
        agent_class = self._generated_agents.get(agent_id)
        if not agent_class:
            # Fallback to base framework class
            agent_class = self._framework_map.get(agent_type)
            if not agent_class:
                raise AgentError(f"Unsupported agent type: {agent_type}. Supported types: {list(self._framework_map.keys())}")
            self.logger.info(f"Using base class for agent '{agent_id}' (no generated class found)")
        else:
            self.logger.info(f"Using generated class for agent '{agent_id}': {agent_class.__name__}")
        
        # Create agent instance
        try:
            # Prepare agent configuration
            agent_kwargs = {
                "agent_config": agent_config,
                **kwargs
            }
            
            # NEW: MCP is enabled by presence of config, not enabled flag
            mcp_config = agent_config.get("mcp", {})
            if mcp_config:  # Changed from mcp_config.get("enabled", False)
                # Validate MCP configuration
                if not mcp_config.get("servers"):
                    self.logger.warning(f"Agent '{agent_id}' has MCP config but no servers configured")
                else:
                    server_count = len(mcp_config["servers"])
                    self.logger.info(f"Agent '{agent_id}' MCP configuration: {server_count} servers configured")
                    
                    # Validate each server has required fields
                    for i, server in enumerate(mcp_config["servers"]):
                        if not server.get("url"):
                            self.logger.warning(f"Agent '{agent_id}' server {i+1} missing URL")
                        if not server.get("toolkits"):
                            self.logger.warning(f"Agent '{agent_id}' server {i+1} missing toolkits")
                        if not server.get("tools"):
                            self.logger.warning(f"Agent '{agent_id}' server {i+1} missing tools")
                    
                    # Pass MCP config to agent creation
                    agent_kwargs["mcp_config"] = mcp_config
                    self.logger.debug(f"Agent '{agent_id}' MCP config: {mcp_config}")
            else:
                self.logger.debug(f"Agent '{agent_id}' has no MCP configuration")
            
            # Debug: Log what we're passing
            self.logger.debug("Creating agent '{}' with kwargs: {}", agent_id, agent_kwargs)
            self.logger.debug("agent_config being passed: {}", agent_config)
            
            # Create agent
            agent = agent_class(agent_id, **agent_kwargs)
            
            self.logger.info(f"Created {agent_type} agent: {agent_id}")
            return agent
            
        except Exception as e:
            self.logger.error(f"Failed to create agent '{agent_id}': {e}")
            raise AgentError(f"Agent creation failed for '{agent_id}': {e}")
    
    def create_all_agents(self, **kwargs) -> Dict[str, BaseAgent]:
        """
        Create all agents defined in the configuration.
        
        Args:
            **kwargs: Additional arguments for agent creation
            
        Returns:
            Dictionary mapping agent_id to agent instance
        """
        agents = {}
        pipeline_config = self.config_result.pipeline_config
        
        if not pipeline_config:
            self.logger.warning("No pipeline configuration found")
            return agents
        
        # Get agents from nodes (MVP-6.0 pattern-only structure)
        agents_to_create = []
        
        if "nodes" in pipeline_config:
            for node in pipeline_config["nodes"]:
                if isinstance(node, dict) and "config" in node:
                    agents_to_create.append(node["config"])
        
        if not agents_to_create:
            self.logger.warning("No agents defined in configuration")
            return agents
        
        for agent_config in agents_to_create:
            agent_id = agent_config.get("id")
            if agent_id:
                try:
                    agent = self.create_agent(agent_id, **kwargs)
                    agents[agent_id] = agent
                except Exception as e:
                    self.logger.error(f"Failed to create agent '{agent_id}': {e}")
                    # Continue with other agents
                    continue
        
        self.logger.info(f"Created {len(agents)} agents")
        return agents
    
    def _find_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Find agent configuration by ID"""
        pipeline_config = self.config_result.pipeline_config
        if not pipeline_config:
            return None
        
        # Check independent_agents section first (for ensemble-style configurations)
        if "independent_agents" in pipeline_config:
            for agent_ref in pipeline_config["independent_agents"]:
                if isinstance(agent_ref, dict) and agent_ref.get("id") == agent_id:
                    config_file = agent_ref.get("config_file")
                    if config_file:
                        # Load agent config from file (independent agents are in config/agents/)
                        # Pass None for pipeline_dir since config_file already includes the full path
                        return self._load_agent_config_from_file(config_file, None)
        
        # Find agent config_file reference in nodes (MVP-6.0 pattern-only structure)
        if "nodes" in pipeline_config:
            for node in pipeline_config["nodes"]:
                if isinstance(node, dict) and node.get("id") == agent_id:
                    config_file = node.get("config_file")
                    if config_file:
                        # Load agent config from file with project directory info
                        project_dir = getattr(self.config_result, 'project_dir', None)
                        if not project_dir:
                            self.logger.error("Project directory not set in config result")
                            return None
                        return self._load_agent_config_from_file(config_file, project_dir)
        
        # For multi-pipeline structure, search individual pipelines
        if "pipelines" in pipeline_config:
            for pipeline_ref in pipeline_config["pipelines"]:
                if isinstance(pipeline_ref, dict) and "config_file" in pipeline_ref:
                    pipeline_file = pipeline_ref["config_file"]
                    agent_config = self._find_agent_config_in_pipeline_file(agent_id, pipeline_file)
                    if agent_config:
                        return agent_config
        
        return None
    
    def _load_agent_config_from_file(self, config_file: str, base_dir: Optional[Path]) -> Optional[Dict[str, Any]]:
        """Load agent configuration from file"""
        try:
            import yaml
            from topaz_agent_kit.utils.env_substitution import env_substitution
            
            # Get project directory from config_result
            project_dir = self.config_result.project_dir
            
            # Resolve agent config path
            # If config_file already includes directory (e.g., "agents/rag_query.yml"), use it directly
            # Otherwise, resolve relative to base directory or fallback to config/
            if "/" in config_file:
                agent_config_path = project_dir / "config" / config_file
            elif base_dir:
                agent_config_path = base_dir / config_file
            else:
                # Fallback: assume config_file is just the filename and look in config/agents/
                agent_config_path = project_dir / "config" / "agents" / config_file
            
            if not agent_config_path.exists():
                self.logger.error("Agent config file not found: {}", agent_config_path)
                return None
            
            with open(agent_config_path, 'r', encoding='utf-8') as f:
                agent_config = yaml.safe_load(f)
                agent_config = env_substitution.substitute_env_vars(agent_config)
            
            return agent_config
            
        except Exception as e:
            self.logger.error("Failed to load agent config from {}: {}", config_file, e)
            return None
    
    def _find_agent_config_in_pipeline_file(self, agent_id: str, pipeline_file: str) -> Optional[Dict[str, Any]]:
        """Find agent config in individual pipeline file"""
        try:
            import yaml
            from topaz_agent_kit.utils.env_substitution import env_substitution
            
            project_dir = self.config_result.project_dir
            pipeline_path = project_dir / "config" / pipeline_file
            
            if not pipeline_path.exists():
                return None
            
            with open(pipeline_path, 'r', encoding='utf-8') as f:
                pipeline_config = yaml.safe_load(f)
                pipeline_config = env_substitution.substitute_env_vars(pipeline_config)
            
            # Search for agent in this pipeline's nodes (MVP-6.0 pattern-only structure)
            if "nodes" in pipeline_config:
                for node in pipeline_config["nodes"]:
                    if isinstance(node, dict) and node.get("id") == agent_id:
                        config_file = node.get("config_file")
                        if config_file:
                            # Use project directory from config result
                            project_dir = getattr(self.config_result, 'project_dir', None)
                            if not project_dir:
                                self.logger.error("No project_dir available in config result")
                                return None
                            return self._load_agent_config_from_file(config_file, project_dir)
            
            return None
            
        except Exception as e:
            self.logger.error("Failed to search agent config in pipeline {}: {}", pipeline_file, e)
            return None
    
    def get_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get full agent configuration by ID"""
        return self._find_agent_config(agent_id)
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get information about an agent without creating it"""
        agent_config = self._find_agent_config(agent_id)
        if not agent_config:
            return None
        
        # Extract model if available (either `model` or nested `llm.model`)
        model_name = None
        try:
            if isinstance(agent_config.get("model"), str):
                model_name = agent_config.get("model")
            elif isinstance(agent_config.get("llm"), dict):
                model_name = agent_config.get("llm", {}).get("model")
        except Exception:
            model_name = None

        return {
            "id": agent_id,
            "type": agent_config.get("type"),
            "name": agent_config.get("name"),
            "model": model_name,
            "run_mode": agent_config.get("run_mode"),
            "remote": agent_config.get("remote"),
            "has_prompt": "prompt" in agent_config,
            "has_role": "role" in agent_config,
            "has_goal": "goal" in agent_config,
            "has_backstory": "backstory" in agent_config,
            "has_task": "task" in agent_config
        }
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents defined in configuration"""
        pipeline_config = self.config_result.pipeline_config
        if not pipeline_config:
            return []
        
        # Get agents from nodes (MVP-6.0 pattern-only structure)
        agents_to_list = []
        
        if "nodes" in pipeline_config:
            for node in pipeline_config["nodes"]:
                if isinstance(node, dict) and "config" in node:
                    agents_to_list.append(node["config"])
        
        agents = []
        for agent_config in agents_to_list:
            agent_info = self.get_agent_info(agent_config.get("id"))
            if agent_info:
                agents.append(agent_info)
        
        return agents 