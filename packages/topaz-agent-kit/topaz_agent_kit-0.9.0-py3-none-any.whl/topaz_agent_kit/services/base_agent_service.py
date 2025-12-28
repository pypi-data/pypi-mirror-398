"""
Base service class for remote agent services.
Handles common functionality like configuration loading, protocol routing, and request handling.
"""

from typing import Any, Dict, Type
from pathlib import Path
import yaml
import asyncio
from urllib.parse import urlparse
from fastapi import FastAPI
from topaz_agent_kit.core.exceptions import ConfigurationError
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.env_substitution import env_substitution
from topaz_agent_kit.services.base_a2a_service import BaseA2AService

class BaseAgentService:
    """Base class for remote agent services (A2A only)"""
    
    def __init__(self, agent_id: str, agent_class: Type, project_path: str | Path):
        """
        Initialize the base service
        
        Args:
            agent_id: ID of the agent this service represents
            agent_class: The agent class to instantiate
            project_path: Path to the project directory
        """
        self.agent_id = agent_id
        self.agent_class = agent_class
        self.project_path = Path(project_path)
        
        
        self.logger = Logger(f"{agent_id}Service")
        
        # Removed .env loading - all configuration now comes from pipeline.yml
        
        # Load configuration
        self.agent_config = self._load_agent_config()
        
        # Validate model configuration
        if "model" not in self.agent_config:
            raise ConfigurationError(f"Agent '{self.agent_id}' has no model configured")
        self.model = self.agent_config["model"]
        
        # Get the URL from remote configuration
        remote_config = self.agent_config.get("remote", {})
        if not remote_config or "url" not in remote_config:
            raise ConfigurationError(f"Agent '{self.agent_id}' has no URL configured in remote.url")
        self.remote_url = remote_config["url"]
        # Log level is controlled by the CLI --log-level argument when running via serve commands
        # For standalone services, the default INFO level is used
        
        # Create A2A service instance
        self.a2a_service = BaseA2AService(agent_id, agent_class, project_path, self.agent_config, self.logger)
        
        # Create FastAPI app for backward compatibility
        self.app = FastAPI(title=f"{agent_id} Service")
    
    # Removed .env loading - all configuration now comes from pipeline.yml
    
    def _load_agent_config(self) -> Dict[str, Any]:
        """Load agent-specific configuration from pipeline.yml or separate config file"""
        try:
            # Environment variables are already loaded by Orchestrator
            pipeline_file = self.project_path / "config" / "pipeline.yml"
            
            if not pipeline_file.exists():
                raise ConfigurationError(f"Pipeline file not found: {pipeline_file}")
            
            with open(pipeline_file, 'r', encoding='utf-8') as f:
                pipeline_config = yaml.safe_load(f)
                # Apply environment variable substitution
                pipeline_config = env_substitution.substitute_env_vars(pipeline_config)
            
            # Try to find agent config in multi-pipeline, single-pipeline, or independent_agents structure
            agent_config = None
            
            # First, check independent_agents section (agents not part of any pipeline)
            if "independent_agents" in pipeline_config:
                for agent in pipeline_config["independent_agents"]:
                    if isinstance(agent, dict) and agent.get("id") == self.agent_id:
                        if "config_file" in agent:
                            config_file = agent["config_file"]
                            config_dir = self.project_path / "config"
                            agent_config_path = config_dir / config_file
                            
                            if agent_config_path.exists():
                                with open(agent_config_path, 'r', encoding='utf-8') as f:
                                    agent_config = yaml.safe_load(f)
                                    agent_config = env_substitution.substitute_env_vars(agent_config)
                                self.logger.debug("Successfully loaded config for agent '{}'", self.agent_id)
                            else:
                                self.logger.error("Config file not found for agent '{}': {}", self.agent_id, agent_config_path)
                            break
            
            # If not found in independent_agents, check pipeline configs
            if not agent_config and "pipelines" in pipeline_config:
                # Multi-pipeline structure: search through individual pipeline files
                for pipeline in pipeline_config["pipelines"]:
                    if isinstance(pipeline, dict) and "config_file" in pipeline:
                        pipeline_file = pipeline["config_file"]
                        pipeline_path = self.project_path / "config" / pipeline_file
                        
                        if pipeline_path.exists():
                            with open(pipeline_path, 'r', encoding='utf-8') as f:
                                pipeline_config_data = yaml.safe_load(f)
                                pipeline_config_data = env_substitution.substitute_env_vars(pipeline_config_data)
                            
                            # Search for agent in this pipeline's nodes
                            if "nodes" in pipeline_config_data:
                                for node in pipeline_config_data["nodes"]:
                                    if isinstance(node, dict) and node.get("id") == self.agent_id:
                                        if "config" in node:
                                            agent_config = node["config"]
                                            break
                                        elif "config_file" in node:
                                            # Load from separate file
                                            config_file = node["config_file"]
                                            # Resolve path relative to the config directory (not pipeline directory)
                                            config_dir = self.project_path / "config"
                                            agent_config_path = config_dir / config_file
                                            
                                            if agent_config_path.exists():
                                                with open(agent_config_path, 'r', encoding='utf-8') as f:
                                                    agent_config = yaml.safe_load(f)
                                                    agent_config = env_substitution.substitute_env_vars(agent_config)
                                                self.logger.debug("Successfully loaded config for agent '{}'", self.agent_id)
                                            else:
                                                self.logger.error("Config file not found for agent '{}': {}", self.agent_id, agent_config_path)
                                            break
                            
                            if agent_config:
                                break
            
            if not agent_config:
                raise ConfigurationError(f"Agent '{self.agent_id}' not found in pipeline.yml")
            
            # Validate required fields
            required_fields = ["model", "type"]
            for field in required_fields:
                if field not in agent_config:
                    raise ConfigurationError(f"Agent '{self.agent_id}' missing required field: {field}")
            
            # NEW: Remote is enabled by presence of config, not enabled flag
            remote_config = agent_config.get("remote", {})
            if not remote_config:
                raise ConfigurationError(f"Agent '{self.agent_id}' has no remote configuration")
            
            if not remote_config.get("url"):
                raise ConfigurationError(f"Agent '{self.agent_id}' remote configuration missing URL")
            
            return agent_config
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load agent configuration: {e}")
    
    async def start_server(self, port: int = None, path: str = None) -> None:
        """Start A2A server"""
        await self.a2a_service.start_a2a_server(port, path)
    
    async def start_a2a_server(self, port: int = None, path: str = None) -> None:
        """Start A2A server with optional path"""
        if port is None:
            _, port = self.get_host_port()
        await self.a2a_service.start_a2a_server(port, path)
    
    
    def get_host_port(self) -> tuple[str, int]:
        """Extract host and port from remote URL"""
        parsed_url = urlparse(self.remote_url)
        if parsed_url.hostname is None:
            raise ConfigurationError(f"Agent '{self.agent_id}' URL '{self.remote_url}' missing hostname")
        if parsed_url.port is None:
            raise ConfigurationError(f"Agent '{self.agent_id}' URL '{self.remote_url}' missing port number")
        return parsed_url.hostname, parsed_url.port
    
    def run(self, host: str = None, port: int = None) -> None:
        """Run the service"""
        if host is None or port is None:
            host, port = self.get_host_port()
        
        self.logger.info(f"Starting {self.agent_id} service on {host}:{port}")
        self.logger.info(f"Protocol: A2A")
        self.logger.info(f"Model: {self.model}")
        
        asyncio.run(self.start_server(port))
    
