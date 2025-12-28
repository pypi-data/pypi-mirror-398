"""
Configuration Engine for Topaz Agent Kit.

This module provides a centralized configuration loading and validation system
that handles pipeline.yml and ui_manifest.yml files together, with comprehensive
validation including syntax, semantics, and MCP tools.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.env_substitution import env_substitution
from topaz_agent_kit.core.exceptions import (
    ConfigurationError,
    create_error_context
)


def parse_start_node(start_spec: str) -> str:
    """
    Parse start_node specification (protocol suffix no longer required)
    
    Args:
        start_spec: String in format 'agent' (protocol suffix removed)
        
    Returns:
        agent_id string
    """
    # Remove protocol suffix if present (for backward compatibility during migration)
    if ':' in start_spec:
        agent_id, _ = start_spec.split(':', 1)
        return agent_id.strip()
    return start_spec.strip()


def parse_edge_to(to_spec) -> List[str]:
    """
    Parse 'to' specification - handles both single and multiple (protocol suffix no longer required)
    
    Args:
        to_spec: String or list of strings in 'agent' format
        
    Returns:
        List of agent_id strings
    """
    def parse_single(spec: str) -> str:
        # Remove protocol suffix if present (for backward compatibility during migration)
        if ':' in spec:
            agent_id, _ = spec.split(':', 1)
            return agent_id.strip()
        return spec.strip()
    
    if isinstance(to_spec, str):
        return [parse_single(to_spec)]
    elif isinstance(to_spec, list):
        return [parse_single(item) for item in to_spec]
    return []


@dataclass
class ConfigurationResult:
    """Result of configuration loading and validation."""
    is_valid: bool
    pipeline_config: Dict[str, Any]
    ui_config: Dict[str, Any]
    individual_pipelines: Dict[str, Dict[str, Any]]  # pipeline_id -> config
    individual_ui_manifests: Dict[str, Dict[str, Any]]  # pipeline_id -> config
    chatdb_path: str  # Path to SQLite database
    chromadb_path: str  # Path to ChromaDB storage directory
    rag_files_path: str  # Path to RAG file storage directory
    user_files_path: str  # Path to user file storage directory
    embedding_model: str  # Embedding model for document/image ingestion
    vision_model: Optional[str]  # Vision model for image/PDF text extraction
    errors: List[str]  # Just simple error strings
    warnings: List[str]
    project_dir: Path
    
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    def get_error_summary(self) -> str:
        if not self.errors:
            return "Configuration is valid."
        
        result = f"Configuration has {len(self.errors)} error(s):\n"
        for error in self.errors:
            result += f"  {error}\n"
        return result


class ConfigurationEngine:
    """
    Centralized configuration loading and validation system.
    
    This class handles:
    1. Loading pipeline.yml and ui_manifest.yml
    2. Comprehensive validation (syntax + semantics)
    3. MCP tool validation
    4. Path resolution and validation
    5. Error reporting with actionable suggestions
    """
    
    def __init__(self, project_dir: Path):
        """Initialize the configuration engine."""
        self.project_dir = project_dir
        self.logger = Logger("ConfigurationEngine")
        
        # Configuration file paths
        self.pipeline_file = project_dir / "config" / "pipeline.yml"
        self.ui_manifest_file = project_dir / "config" / "ui_manifest.yml"
        
        # Individual configuration directories (now dynamic based on config)
        self.pipelines_dir = project_dir / "config" / "pipelines"
        self.ui_manifests_dir = project_dir / "config" / "ui_manifests"
        # Remove hardcoded agents_dir - will be resolved dynamically per pipeline
        
        # Configuration-driven directories (set after loading config)
        # With flat structure, these are not needed
        
        # Validation results
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def __str__(self) -> str:
        """String representation of ConfigurationEngine."""
        return f"ConfigurationEngine(project_dir={self.project_dir})"
    
    def load_and_validate(self) -> ConfigurationResult:
        """
        Load and validate all configuration files.
        
        Returns:
            ConfigurationResult with validation status and any errors.
        """
        self.logger.info("Starting configuration validation for project: {}", self.project_dir)
        
        # Reset validation state
        self.errors.clear()
        self.warnings.clear()
        
        # Load main configuration files
        pipeline_config = self._load_pipeline_config()
        ui_config = self._load_ui_manifest_config()
        
        # Load individual pipeline and UI manifest files
        individual_pipelines = self._load_individual_pipelines()
        individual_ui_manifests = self._load_individual_ui_manifests()
        
        # Perform comprehensive validation
        if pipeline_config and ui_config:
            self._validate_pipeline_config(pipeline_config)
            self._validate_ui_manifest_config(ui_config)
            self._validate_individual_pipelines(individual_pipelines)
            self._validate_individual_ui_manifests(individual_ui_manifests)
            # Agent name uniqueness is enforced by flat structure (no duplicate filenames possible)
            self._validate_cross_references(pipeline_config, ui_config, individual_pipelines, individual_ui_manifests)
            self._validate_mcp_tools(pipeline_config)
            self._validate_paths(pipeline_config, ui_config)
        
        # Extract and validate chatdb_path from pipeline config
        chatdb_path = ""
        if pipeline_config and "chatdb_path" in pipeline_config:
            chatdb_path = pipeline_config["chatdb_path"]
            # Validate chatdb_path
            self._validate_chatdb_path(chatdb_path)
        else:
            self.errors.append("Missing required 'chatdb_path' in pipeline configuration")
        
        # Extract and validate chromadb_path from pipeline config
        chromadb_path = ""
        if pipeline_config and "chromadb_path" in pipeline_config:
            chromadb_path = pipeline_config["chromadb_path"]
            # Validate chromadb_path
            self._validate_chromadb_path(chromadb_path)
        else:
            self.errors.append("Missing required 'chromadb_path' in pipeline configuration")
        
        # Extract and validate embedding_model from pipeline config
        embedding_model = ""
        if pipeline_config and "embedding_model" in pipeline_config:
            embedding_model = pipeline_config["embedding_model"]
            # Validate embedding_model
            self._validate_embedding_model(embedding_model)
        else:
            self.errors.append("Missing required 'embedding_model' in pipeline configuration")
        
        # Extract and validate vision_model from pipeline config (optional)
        vision_model = None
        if pipeline_config and "vision_model" in pipeline_config:
            vision_model = pipeline_config["vision_model"]
            # Validate vision_model
            self._validate_vision_model(vision_model)
        
        # Extract and validate rag_files_path from pipeline config (default: ./data/rag_files)
        rag_files_path = "./data/rag_files"
        if pipeline_config and "rag_files_path" in pipeline_config:
            rag_files_path = pipeline_config["rag_files_path"]
        self._validate_files_path(rag_files_path)
        
        # Extract and validate user_files_path from pipeline config (default: ./data/user_files)
        user_files_path = "./data/user_files"
        if pipeline_config and "user_files_path" in pipeline_config:
            user_files_path = pipeline_config["user_files_path"]
        self._validate_files_path(user_files_path)
        
        # Create result
        result = ConfigurationResult(
            is_valid=len(self.errors) == 0,
            pipeline_config=pipeline_config or {},
            ui_config=ui_config or {},
            individual_pipelines=individual_pipelines,
            individual_ui_manifests=individual_ui_manifests,
            chatdb_path=chatdb_path,
            chromadb_path=chromadb_path,
            rag_files_path=rag_files_path,
            user_files_path=user_files_path,
            embedding_model=embedding_model,
            vision_model=vision_model,
            errors=self.errors.copy(),
            warnings=self.warnings.copy(),
            project_dir=self.project_dir
        )
        
        # Log results
        if result.is_valid:
            self.logger.success("Configuration validation successful")
        else:
            self.logger.error("Configuration validation failed with {} errors", len(self.errors))
            for error in self.errors:
                self.logger.error("  {}", error)
        
        return result
    
    def load_and_validate_or_raise(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Load and validate configuration, raising ConfigurationError if validation fails.
        
        Returns:
            Tuple of (pipeline_config, ui_config)
            
        Raises:
            ConfigurationError: If configuration validation fails
        """
        result = self.load_and_validate()
        
        if not result.is_valid:
            # Create standardized error with context
            context = create_error_context(
                component="ConfigurationEngine",
                operation="load_and_validate",
                project_dir=str(self.project_dir)
            )
            
            error_message = f"Configuration validation failed for project: {self.project_dir}"
            if result.errors:
                error_message += f"\nErrors: {[e for e in result.errors]}"
            
            raise ConfigurationError(
                message=error_message,
                context=context
            )
        
        return result.pipeline_config, result.ui_config
    
    def _load_pipeline_config(self) -> Optional[Dict[str, Any]]:
        """Load and parse pipeline.yml file with agent configurations."""
        try:
            # Environment variables are already loaded by Orchestrator
            if not self.pipeline_file.exists():
                self.errors.append(f"Pipeline configuration file not found: {self.pipeline_file}")
                return None
            
            # Use PipelineLoader to load complete configuration including agent files
            from .pipeline_loader import PipelineLoader
            loader = PipelineLoader(self.project_dir)
            pipeline_config, _ = loader.load()
            
            self.logger.success("Successfully loaded pipeline configuration with agent configs")
            return pipeline_config
            
        except Exception as e:
            self.errors.append(f"Failed to load pipeline configuration: {e}")
            return None
    
    def _load_ui_manifest_config(self) -> Optional[Dict[str, Any]]:
        """Load and parse ui_manifest.yml file."""
        try:
            # Environment variables are already loaded by Orchestrator
            if not self.ui_manifest_file.exists():
                self.errors.append(f"UI manifest configuration file not found: {self.ui_manifest_file}")
                return None
            
            with open(self.ui_manifest_file, 'r', encoding='utf-8') as f:
                content = f.read()
                config = yaml.safe_load(content)
                # Apply environment variable substitution
                config = env_substitution.substitute_env_vars(config)
                
            if not isinstance(config, dict):
                self.errors.append(f"UI manifest configuration must be a YAML object: {self.ui_manifest_file}")
                return None
            
            self.logger.success("Successfully loaded UI manifest configuration")
            return config
            
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML syntax in {self.ui_manifest_file}: {e}")
            return None
        except Exception as e:
            self.errors.append(f"Failed to load UI manifest configuration: {e}")
            return None
    
    def _load_individual_pipelines(self) -> Dict[str, Dict[str, Any]]:
        """Load individual pipeline configuration files with agent configurations."""
        individual_pipelines = {}
        
        try:
            if not self.pipelines_dir.exists():
                self.logger.debug("Pipelines directory does not exist: {}", self.pipelines_dir)
                return individual_pipelines
            
            # Environment variables are already loaded by Orchestrator
            # Find all YAML files in pipelines directory and subdirectories, excluding agent files
            all_yaml_files = list(self.pipelines_dir.rglob("*.yml")) + list(self.pipelines_dir.rglob("*.yaml"))
            # Filter out agent files (they should be in agents/ subdirectories)
            pipeline_files = [f for f in all_yaml_files if "agents" not in f.parts]
            
            if not pipeline_files:
                self.logger.debug("No pipeline files found in: {}", self.pipelines_dir)
                return individual_pipelines
            
            for pipeline_file in pipeline_files:
                try:
                    with open(pipeline_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        config = yaml.safe_load(content)
                        # Apply environment variable substitution
                        config = env_substitution.substitute_env_vars(config)
                    
                    if not isinstance(config, dict):
                        self.errors.append(f"Pipeline configuration must be a YAML object: {pipeline_file}")
                        continue
                    
                    # Load agent configurations for this pipeline
                    config = self._load_agent_configs_for_pipeline(config, pipeline_file)
                    
                    # Extract pipeline ID from filename (without extension)
                    pipeline_id = pipeline_file.stem
                    
                    # Add pipeline directory information for agent config resolution
                    # Extract pipeline_dir from the pipeline_file path relative to config/
                    # e.g., config/pipelines/math_compass/math_compass.yml -> pipelines/math_compass
                    config_dir = self.project_dir / "config"
                    pipeline_dir = pipeline_file.relative_to(config_dir).parent
                    config["pipeline_dir"] = str(pipeline_dir)
                    
                    individual_pipelines[pipeline_id] = config
                    
                    self.logger.debug("Successfully loaded individual pipeline: {}", pipeline_id)
                    
                except yaml.YAMLError as e:
                    self.errors.append(f"Invalid YAML syntax in {pipeline_file}: {e}")
                except Exception as e:
                    self.errors.append(f"Failed to load pipeline configuration {pipeline_file}: {e}")
            
            self.logger.success("Successfully loaded {} individual pipeline configurations with agent configs", len(individual_pipelines))
            return individual_pipelines
            
        except Exception as e:
            self.errors.append(f"Failed to load individual pipeline configurations: {e}")
            return individual_pipelines
    
    def _load_agent_configs_for_pipeline(self, pipeline_config: Dict[str, Any], pipeline_file: Path) -> Dict[str, Any]:
        """Load agent configurations for a specific pipeline."""
        try:
            # Check if pipeline has nodes (MVP-6.0 pattern-only structure)
            if "nodes" not in pipeline_config:
                self.logger.debug("Pipeline {} has no nodes, skipping agent loading", pipeline_file.stem)
                return pipeline_config
            
            nodes = pipeline_config["nodes"]
            if not isinstance(nodes, list):
                self.logger.debug("Pipeline {} nodes is not a list, skipping agent loading", pipeline_file.stem)
                return pipeline_config
            
            # Load agent configurations for each node (flat structure)
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                
                config_file = node.get("config_file")  # Use config_file to identify agent config
                
                if not config_file:
                    continue
                
                # Load agent configuration file from flat structure
                agent_config_path = self.project_dir / "config" / config_file
                
                if not agent_config_path.exists():
                    self.errors.append(f"Agent config file not found: {agent_config_path}")
                    continue
                
                try:
                    with open(agent_config_path, 'r', encoding='utf-8') as f:
                        agent_content = f.read()
                        agent_config = yaml.safe_load(agent_content)
                        # Apply environment variable substitution
                        agent_config = env_substitution.substitute_env_vars(agent_config)
                    
                    if not isinstance(agent_config, dict):
                        self.errors.append(f"Agent config must be a YAML object: {agent_config_path}")
                        continue
                    
                    # Extract agent_id from config_file path (OS-agnostic)
                    agent_id = Path(config_file).stem
                    
                    # Validate agent_id matches
                    if agent_config.get("id") != agent_id:
                        self.logger.warning("Agent ID mismatch in {}: expected {}, got {}", 
                                          agent_id, agent_id, agent_config.get("id"))
                    
                    # Note: Agent configs are loaded separately by AgentFactory when needed
                    # We don't embed them in the pipeline structure
                    
                    self.logger.debug("Successfully loaded agent config: {} -> {}", agent_id, agent_config_path)
                    
                except yaml.YAMLError as e:
                    self.errors.append(f"Invalid YAML syntax in agent config {agent_config_path}: {e}")
                except Exception as e:
                    self.errors.append(f"Failed to load agent config {agent_config_path}: {e}")
            
            return pipeline_config
            
        except Exception as e:
            self.errors.append(f"Failed to load agent configs for pipeline {pipeline_file.stem}: {e}")
            return pipeline_config
    
    def _load_individual_ui_manifests(self) -> Dict[str, Dict[str, Any]]:
        """Load individual UI manifest configuration files."""
        individual_ui_manifests = {}
        
        try:
            if not self.ui_manifests_dir.exists():
                self.logger.debug("UI manifests directory does not exist: {}", self.ui_manifests_dir)
                return individual_ui_manifests
            
            # Environment variables are already loaded by Orchestrator
            # Find all YAML files in ui_manifests directory
            ui_manifest_files = list(self.ui_manifests_dir.glob("*.yml")) + list(self.ui_manifests_dir.glob("*.yaml"))
            
            if not ui_manifest_files:
                self.logger.debug("No UI manifest files found in: {}", self.ui_manifests_dir)
                return individual_ui_manifests
            
            for ui_manifest_file in ui_manifest_files:
                try:
                    with open(ui_manifest_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        config = yaml.safe_load(content)
                        # Apply environment variable substitution
                        config = env_substitution.substitute_env_vars(config)
                    
                    if not isinstance(config, dict):
                        self.errors.append(f"UI manifest configuration must be a YAML object: {ui_manifest_file}")
                        continue
                    
                    # Extract pipeline ID from filename (without extension)
                    pipeline_id = ui_manifest_file.stem
                    individual_ui_manifests[pipeline_id] = config
                    
                    self.logger.debug("Successfully loaded individual UI manifest: {}", pipeline_id)
                    
                except yaml.YAMLError as e:
                    self.errors.append(f"Invalid YAML syntax in {ui_manifest_file}: {e}")
                except Exception as e:
                    self.errors.append(f"Failed to load UI manifest configuration {ui_manifest_file}: {e}")
            
            self.logger.success("Successfully loaded {} individual UI manifest configurations", len(individual_ui_manifests))
            return individual_ui_manifests
            
        except Exception as e:
            self.errors.append(f"Failed to load individual UI manifest configurations: {e}")
            return individual_ui_manifests
    
    def _validate_pipeline_config(self, config: Dict[str, Any]) -> None:
        """Validate global pipeline configuration structure and content."""
        # Validate required top-level sections for flat structure
        required_sections = ["name", "description", "servers", "pipelines", "chatdb_path", "assistant", "independent_agents"]
        for section in required_sections:
            if section not in config:
                self.errors.append(f"Required section '{section}' is missing in pipeline.yml: {self.pipeline_file}")
        
        # Validate pipelines section
        if "pipelines" in config:
            self._validate_pipelines_section(config["pipelines"])
        
        # Validate assistant section
        if "assistant" in config:
            self._validate_assistant_section(config["assistant"])
        
        
        # Validate servers section
        if "servers" in config:
            self._validate_servers_section(config["servers"])
        
        # Validate new configuration sections
        # With flat structure, agents, services, and ui are not needed at top level
        # Independent agents are handled separately
    
    
    def _validate_framework_config(self, agent: Dict[str, Any], agent_index: int) -> List[str]:
        """
        Validate framework-specific configuration for new architecture.
        
        This method validates that agents have the required fields and configuration
        for their specific framework (Agno, ADK, LangGraph, CrewAI, OAK, SK).
        
        Args:
            agent: Agent configuration dictionary
            agent_index: Index of agent in the agents list (for error reporting)
            
        Returns:
            List of error strings for any validation failures
        """
        errors = []
        agent_id = agent.get("id", f"agent_{agent_index}")
        agent_type = agent.get("type")
        
        # Validate agent type against new architecture
        if agent_type not in ["agno", "langgraph", "crewai", "adk", "oak", "sk", "maf"]:
            errors.append(f"Unsupported agent type: {agent_type} for agent '{agent_id}': {self.pipeline_file}")
            return errors  # Return early if type is invalid
        
        # Framework-specific validation
        if agent_type == "agno":
            errors.extend(self._validate_agno_agent_config(agent, agent_index))
        elif agent_type == "langgraph":
            errors.extend(self._validate_langgraph_agent_config(agent, agent_index))
        elif agent_type == "crewai":
            errors.extend(self._validate_crewai_agent_config(agent, agent_index))
        
        # Validate remote configuration and protocol support
        errors.extend(self._validate_remote_config(agent, agent_index))
        
        return errors
    
    def _validate_remote_config(self, agent: Dict[str, Any], agent_index: int) -> List[str]:
        """Validate remote configuration (A2A only)."""
        errors = []
        agent_id = agent.get("id", f"agent_{agent_index}")
        
        # Check if remote config exists (presence indicates remote capability)
        remote_config = agent.get("remote", {})
        if not remote_config:
            return errors  # No remote validation needed if not configured
        
        # Validate url is specified for remote agents
        url = remote_config.get("url")
        if not url:
            errors.append(f"Remote agent '{agent_id}' must specify 'url' in remote configuration: {self.pipeline_file}")
            return errors
        
        # Validate url is a string
        if not isinstance(url, str):
            errors.append(f"Remote agent '{agent_id}' remote.url must be a string: {self.pipeline_file}")
            return errors
        
        # Basic URL validation (must start with http:// or https://)
        if not url.startswith(('http://', 'https://')):
            errors.append(f"Remote agent '{agent_id}' remote.url must be a valid HTTP/HTTPS URL: {url}: {self.pipeline_file}")
        
        # Validate optional timeout
        if "timeout" in remote_config:
            timeout = remote_config["timeout"]
            if not isinstance(timeout, int) or timeout < 1000:
                errors.append(f"Remote agent '{agent_id}' remote.timeout must be an integer >= 1000: {self.pipeline_file}")
        
        # Validate optional retry_attempts
        if "retry_attempts" in remote_config:
            retry_attempts = remote_config["retry_attempts"]
            if not isinstance(retry_attempts, int) or retry_attempts < 0:
                errors.append(f"Remote agent '{agent_id}' remote.retry_attempts must be an integer >= 0: {self.pipeline_file}")
        
        return errors
    
    def _validate_agno_agent_config(self, agent: Dict[str, Any], agent_index: int) -> List[str]:
        """Validate Agno agent configuration for new architecture."""
        errors = []
        agent_id = agent.get("id", f"agent_{agent_index}")
        
        # Agno agents require a prompt configuration
        if "prompt" not in agent:
            errors.append(f"Agno agent '{agent_id}' requires a 'prompt' field: {self.pipeline_file}")
        else:
            # Validate prompt structure
            prompt = agent["prompt"]
            if not isinstance(prompt, dict):
                errors.append(f"Agno agent '{agent_id}' prompt must be a YAML object: {self.pipeline_file}")
        
        # Validate MCP tools if specified
        if "mcp_tools" in agent:
            mcp_tools = agent["mcp_tools"]
            if not isinstance(mcp_tools, list):
                errors.append(f"Agno agent '{agent_id}' mcp_tools must be a list: {self.pipeline_file}")
        
        return errors
    
    def _validate_langgraph_agent_config(self, agent: Dict[str, Any], agent_index: int) -> List[str]:
        """Validate LangGraph agent configuration for new architecture."""
        errors = []
        agent_id = agent.get("id", f"agent_{agent_index}")
        
        # LangGraph agents require a prompt configuration
        if "prompt" not in agent:
            errors.append(f"LangGraph agent '{agent_id}' requires a 'prompt' field: {self.pipeline_file}")
        else:
            # Validate prompt structure
            prompt = agent["prompt"]
            if not isinstance(prompt, dict):
                errors.append(f"LangGraph agent '{agent_id}' prompt must be a YAML object: {self.pipeline_file}")
        
        # Validate MCP tools if specified
        if "mcp_tools" in agent:
            mcp_tools = agent["mcp_tools"]
            if not isinstance(mcp_tools, list):
                errors.append(f"LangGraph agent '{agent_id}' mcp_tools must be a list: {self.pipeline_file}")
        
        return errors
    
    def _validate_crewai_agent_config(self, agent: Dict[str, Any], agent_index: int) -> List[str]:
        """Validate CrewAI agent configuration for new architecture."""
        errors = []
        agent_id = agent.get("id", f"agent_{agent_index}")
        
        # CrewAI agents require specific fields (already validated in _validate_crewai_agent)
        # But we can add additional new architecture specific validation here
        
        # Validate task configuration if specified
        if "task" in agent:
            task = agent["task"]
            if isinstance(task, dict) and "expected_output" in task:
                expected_output = task["expected_output"]
                # Support both string and object formats (inline/file/jinja)
                if isinstance(expected_output, str):
                    if not expected_output.strip():
                        errors.append(f"CrewAI agent '{agent_id}' expected_output string must be non-empty: {self.pipeline_file}")
                elif isinstance(expected_output, dict):
                    # Check if any of the supported formats have content
                    has_content = False
                    if "inline" in expected_output and expected_output["inline"]:
                        has_content = True
                    elif "file" in expected_output and expected_output["file"]:
                        has_content = True
                    elif "jinja" in expected_output and expected_output["jinja"]:
                        has_content = True
                    
                    if not has_content:
                        errors.append(f"CrewAI agent '{agent_id}' expected_output must have content in inline/file/jinja: {self.pipeline_file}")
                else:
                    errors.append(f"CrewAI agent '{agent_id}' expected_output must be string or object with inline/file/jinja: {self.pipeline_file}")
        
        # Validate MCP tools if specified
        if "mcp_tools" in agent:
            mcp_tools = agent["mcp_tools"]
            if not isinstance(mcp_tools, list):
                errors.append(f"CrewAI agent '{agent_id}' mcp_tools must be a list: {self.pipeline_file}")
        
        return errors
    
    def suggest_framework_config(self, agent_type: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest optimal framework configuration based on requirements"""
        try:
            from topaz_agent_kit.frameworks.framework_config_manager import FrameworkConfigManager
            
            framework_manager = FrameworkConfigManager()
            suggestions = framework_manager.suggest_framework_config(agent_type, requirements)
            
            # Add Topaz-specific suggestions
            if suggestions.get("recommended_framework"):
                suggestions["topaz_integration"] = {
                    "agent_base_class": f"topaz_agent_kit.agents.base.{suggestions['recommended_framework'].title()}BaseAgent",
                    "import_statement": f"from topaz_agent_kit.agents.base import {suggestions['recommended_framework'].title()}BaseAgent",
                    "example_usage": self._generate_example_usage(suggestions['recommended_framework'], requirements)
                }
            
            return suggestions
            
        except Exception as e:
            self.logger.error("Failed to suggest framework configuration: {}", e)
            return {
                "error": str(e),
                "suggestions": ["Check framework configuration and try again"]
            }
    
    def _generate_example_usage(self, framework: str, requirements: Dict[str, Any]) -> str:
        """Generate example usage code for a framework"""
        try:
            if framework == "agno":
                return """
# Example Agno agent configuration
agent_config = {
    "name": "Example Agent",
    "prompt": {
        "inline": "You are a helpful AI assistant. {question}"
    },
    "agent_id": "example_agent"
}

# Create agent
from topaz_agent_kit.agents.base import AgnoBaseAgent
agent = AgnoBaseAgent("example_agent", agent_config=agent_config)
await agent.initialize({})
"""
            elif framework == "langgraph":
                return """
# Example LangGraph agent configuration
agent_config = {
    "name": "Example Agent",
    "prompt": {
        "inline": "You are a helpful AI assistant. {question}"
    },
    "agent_id": "example_agent"
}

# Create agent
from topaz_agent_kit.agents.base import LangGraphBaseAgent
agent = LangGraphBaseAgent("example_agent", agent_config=agent_config)
await agent.initialize({})
"""
            elif framework == "crewai":
                return """
# Example CrewAI agent configuration
agent_config = {
    "name": "Example Agent",
    "role": {"inline": "AI Assistant"},
    "goal": {"inline": "Help users with their questions"},
    "backstory": {"inline": "You are a helpful AI assistant"},
    "task": {
        "description": {"inline": "{question}"},
        "expected_output": {"inline": "A helpful response"}
    },
    "agent_id": "example_agent"
}

# Create agent
from topaz_agent_kit.agents.base import CrewAIBaseAgent
agent = CrewAIBaseAgent("example_agent", agent_config=agent_config)
await agent.initialize({})
"""
            else:
                return f"# Example configuration for {framework} framework"
                
        except Exception as e:
            self.logger.error("Failed to generate example usage: {}", e)
            return "# Example configuration could not be generated"
    
    def validate_framework_dependencies(self, pipeline_config: Dict[str, Any]) -> List[str]:
        """Validate framework dependencies in pipeline"""
        errors = []
        
        try:
            from topaz_agent_kit.frameworks.framework_config_manager import FrameworkConfigManager
            
            framework_manager = FrameworkConfigManager()
            agents = pipeline_config.get("agents", [])
            
            # Check framework compatibility between agents
            for i, agent1 in enumerate(agents):
                for j, agent2 in enumerate(agents):
                    if i >= j:  # Skip self and already checked pairs
                        continue
                    
                    framework1 = agent1.get("type", "agno")
                    framework2 = agent2.get("type", "agno")
                    
                    if framework1 != framework2:
                        # Check compatibility between different frameworks
                        compatibility = framework_manager.check_framework_compatibility(framework1, framework2)
                        
                        if not compatibility.get("compatible", False):
                            errors.append(f"Framework compatibility issue: {framework1} and {framework2} may not work well together: {self.pipeline_file}")
            
            # Check for framework-specific pipeline requirements
            for i, agent in enumerate(agents):
                framework = agent.get("type", "agno")
                
                # Validate framework-specific pipeline requirements
                framework_errors = self._validate_framework_pipeline_requirements(framework, agent, i)
                errors.extend(framework_errors)
            
            return errors
            
        except Exception as e:
            self.logger.error("Failed to validate framework dependencies: {}", e)
            errors.append(f"Failed to validate framework dependencies: {e}: {self.pipeline_file}")
            return errors
    
    def _validate_framework_pipeline_requirements(self, framework: str, agent: Dict[str, Any], agent_index: int) -> List[str]:
        """Validate framework-specific pipeline requirements"""
        errors = []
        agent_id = agent.get("id", f"agent_{agent_index}")
        
        try:
            from topaz_agent_kit.frameworks.framework_config_manager import FrameworkConfigManager
            
            framework_manager = FrameworkConfigManager()
            
            # Get framework capabilities
            try:
                capabilities = framework_manager.get_framework_capabilities(framework)
            except Exception:
                # Framework not available, skip detailed validation
                return errors
            
            # Check if agent configuration matches framework capabilities
            agent_config = agent.get("agent_config", {})
            
            # Check memory requirements
            if capabilities.get("agent", {}).get("supports_memory", False):
                # Framework supports memory, check if agent uses it
                if "memory" in agent_config and not agent_config.get("memory"):
                    errors.append(f"Agent '{agent_id}' uses {framework} framework which supports memory, but memory is disabled: {self.pipeline_file}")
            
            # Check tool requirements
            if capabilities.get("agent", {}).get("supports_tools", False):
                # Framework supports tools, check if agent has tools
                if "mcp_tools" in agent and not agent.get("mcp_tools"):
                    errors.append(f"Agent '{agent_id}' uses {framework} framework which supports tools, but no MCP tools specified: {self.pipeline_file}")
            
            # Check model compatibility
            if "model" in agent_config:
                model_type = agent_config.get("model")
                try:
                    framework_manager.get_model_requirements(framework, model_type)
                    # Model is compatible with framework
                except Exception:
                    errors.append(f"Model '{model_type}' is not supported by {framework} framework: {self.pipeline_file}")
            
            return errors
            
        except Exception as e:
            self.logger.error("Failed to validate framework pipeline requirements for {}: {}", framework, e)
            return errors
    
    def get_framework_awareness_summary(self, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive framework awareness summary for pipeline"""
        try:
            from topaz_agent_kit.frameworks.framework_config_manager import FrameworkConfigManager
            
            framework_manager = FrameworkConfigManager()
            agents = pipeline_config.get("agents", [])
            
            summary = {
                "total_agents": len(agents),
                "framework_distribution": {},
                "compatibility_matrix": {},
                "capability_summary": {},
                "recommendations": []
            }
            
            # Analyze framework distribution
            for agent in agents:
                framework = agent.get("type", "agno")
                summary["framework_distribution"][framework] = summary["framework_distribution"].get(framework, 0) + 1
            
            # Build compatibility matrix
            frameworks = list(summary["framework_distribution"].keys())
            for framework1 in frameworks:
                summary["compatibility_matrix"][framework1] = {}
                for framework2 in frameworks:
                    compatibility = framework_manager.check_framework_compatibility(framework1, framework2)
                    summary["compatibility_matrix"][framework1][framework2] = compatibility
            
            # Analyze capabilities
            for framework in frameworks:
                try:
                    capabilities = framework_manager.get_framework_capabilities(framework)
                    summary["capability_summary"][framework] = {
                        "models": len(capabilities.get("models", {})),
                        "mcp_support": capabilities.get("mcp_integration", {}).get("supported", False),
                        "memory_support": capabilities.get("agent", {}).get("supports_memory", False),
                        "tool_support": capabilities.get("agent", {}).get("supports_tools", False)
                    }
                except Exception:
                    summary["capability_summary"][framework] = {"error": "Capabilities not available"}
            
            # Generate recommendations
            if len(frameworks) > 1:
                # Multiple frameworks in use
                overall_compatibility = 0
                total_checks = 0
                
                for framework1 in frameworks:
                    for framework2 in frameworks:
                        if framework1 != framework2:
                            compatibility = summary["compatibility_matrix"][framework1][framework2]
                            overall_compatibility += compatibility.get("score", 0)
                            total_checks += 1
                
                if total_checks > 0:
                    avg_compatibility = overall_compatibility / total_checks
                    if avg_compatibility < 70:
                        summary["recommendations"].append(f"Low framework compatibility ({avg_compatibility:.1f}/100). Consider using more compatible frameworks.")
                    elif avg_compatibility < 85:
                        summary["recommendations"].append(f"Moderate framework compatibility ({avg_compatibility:.1f}/100). Some optimizations may be needed.")
                    else:
                        summary["recommendations"].append(f"Good framework compatibility ({avg_compatibility:.1f}/100). Frameworks should work well together.")
            
            # Check for framework-specific optimizations
            for framework in frameworks:
                try:
                    capabilities = framework_manager.get_framework_capabilities(framework)
                    if capabilities.get("features", {}).get("batch_processing", False):
                        summary["recommendations"].append(f"Framework {framework} supports batch processing. Consider batching operations for better performance.")
                    if capabilities.get("features", {}).get("multi_agent", False):
                        summary["recommendations"].append(f"Framework {framework} supports multi-agent workflows. Consider using collaborative agents.")
                except Exception:
                    pass
            
            return summary
            
        except Exception as e:
            self.logger.error("Failed to get framework awareness summary: {}", e)
            return {
                "error": str(e),
                "total_agents": 0,
                "framework_distribution": {},
                "compatibility_matrix": {},
                "capability_summary": {},
                "recommendations": ["Failed to analyze framework awareness"]
            }
    
    def _validate_pipelines_section(self, pipelines: List[Dict[str, Any]]) -> None:
        """Validate pipelines section in global pipeline configuration."""
        if not isinstance(pipelines, list):
            self.errors.append(f"Pipelines must be a list: {self.pipeline_file}")
            return
        
        if len(pipelines) == 0:
            self.errors.append(f"At least one pipeline must be defined: {self.pipeline_file}")
            return
        
        pipeline_ids = set()
        for i, pipeline in enumerate(pipelines):
            if not isinstance(pipeline, dict):
                self.errors.append(f"Pipeline {i} must be a YAML object: {self.pipeline_file}")
                continue
            
            # Validate required fields
            if "id" not in pipeline:
                self.errors.append(f"Pipeline {i} must have an 'id' field: {self.pipeline_file}")
            elif not isinstance(pipeline["id"], str) or not pipeline["id"].strip():
                self.errors.append(f"Pipeline {i} ID must be a non-empty string: {self.pipeline_file}")
            else:
                # Check for duplicate IDs
                if pipeline["id"] in pipeline_ids:
                    self.errors.append(f"Duplicate pipeline ID '{pipeline['id']}': {self.pipeline_file}")
                pipeline_ids.add(pipeline["id"])
            
            if "config_file" not in pipeline:
                self.errors.append(f"Pipeline {i} must have a 'config_file' field: {self.pipeline_file}")
            elif not isinstance(pipeline["config_file"], str) or not pipeline["config_file"].strip():
                self.errors.append(f"Pipeline {i} config_file must be a non-empty string: {self.pipeline_file}")
    
    def _validate_context_section(self, context: Dict[str, Any]) -> None:
        """Validate context section in global pipeline configuration."""
        if not isinstance(context, dict):
            self.errors.append(f"Context must be a YAML object: {self.pipeline_file}")
            return
        
        # Validate storage type
        if "storage" not in context:
            self.errors.append(f"Context must specify 'storage' type: {self.pipeline_file}")
        elif context["storage"] not in ["sqlite", "json", "chromadb"]:
            self.errors.append(f"Context storage must be one of: sqlite, json, chromadb: {self.pipeline_file}")
        
        # Validate persistent path
        if "persistent_path" not in context:
            self.errors.append(f"Context must specify 'persistent_path': {self.pipeline_file}")
        elif not isinstance(context["persistent_path"], str) or not context["persistent_path"].strip():
            self.errors.append(f"Context persistent_path must be a non-empty string: {self.pipeline_file}")
    
    def _validate_chatdb_path(self, chatdb_path: str) -> None:
        """Validate chatdb_path configuration."""
        if not isinstance(chatdb_path, str):
            self.errors.append(f"chatdb_path must be a string: {self.pipeline_file}")
            return
        
        if not chatdb_path.strip():
            self.errors.append(f"chatdb_path cannot be empty: {self.pipeline_file}")
            return
        
        # Check if path ends with .db
        if not chatdb_path.endswith('.db'):
            self.warnings.append(f"chatdb_path should end with .db extension: {chatdb_path}")
        
        # Check if path is absolute or relative
        if chatdb_path.startswith('/'):
            # Absolute path - check if parent directory exists
            from pathlib import Path
            db_path = Path(chatdb_path)
            if not db_path.parent.exists():
                self.warnings.append(f"Parent directory for chatdb_path does not exist: {db_path.parent}")
        else:
            # Relative path - check if it's reasonable
            if '..' in chatdb_path:
                self.warnings.append(f"Relative chatdb_path contains '..' which may cause issues: {chatdb_path}")
        
        # Check for common issues
        if ' ' in chatdb_path and not chatdb_path.startswith('"') and not chatdb_path.startswith("'"):
            self.warnings.append(f"chatdb_path contains spaces, consider using quotes: {chatdb_path}")
        
        # Validate path length (SQLite has limits)
        if len(chatdb_path) > 255:
            self.errors.append(f"chatdb_path is too long (max 255 characters): {len(chatdb_path)}")
        
        # Check for invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        for char in invalid_chars:
            if char in chatdb_path:
                self.errors.append(f"chatdb_path contains invalid character '{char}': {chatdb_path}")
                break
    
    def _validate_chromadb_path(self, chromadb_path: str) -> None:
        """Validate chromadb_path configuration."""
        if not isinstance(chromadb_path, str):
            self.errors.append(f"chromadb_path must be a string: {self.pipeline_file}")
            return
        
        if not chromadb_path.strip():
            self.errors.append(f"chromadb_path cannot be empty: {self.pipeline_file}")
            return
        
        # Check if path is absolute or relative
        if chromadb_path.startswith('/'):
            # Absolute path - check if parent directory exists
            from pathlib import Path
            db_path = Path(chromadb_path)
            if not db_path.parent.exists():
                self.warnings.append(f"Parent directory for chromadb_path does not exist: {db_path.parent}")
        else:
            # Relative path - check if it's reasonable
            if '..' in chromadb_path:
                self.warnings.append(f"Relative chromadb_path contains '..' which may cause issues: {chromadb_path}")
        
        # Check for common issues
        if ' ' in chromadb_path and not chromadb_path.startswith('"') and not chromadb_path.startswith("'"):
            self.warnings.append(f"chromadb_path contains spaces, consider using quotes: {chromadb_path}")
        
        # Check for invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        for char in invalid_chars:
            if char in chromadb_path:
                self.errors.append(f"chromadb_path contains invalid character '{char}': {chromadb_path}")
                break
    
    def _validate_embedding_model(self, embedding_model: str) -> None:
        """Validate embedding_model configuration."""
        if not isinstance(embedding_model, str):
            self.errors.append(f"embedding_model must be a string: {self.pipeline_file}")
            return
        
        if not embedding_model.strip():
            self.errors.append(f"embedding_model cannot be empty: {self.pipeline_file}")
            return
        
        # Basic validation - just check it's not empty
        # The actual model validation happens at runtime in ContentIngester
    
    def _validate_vision_model(self, vision_model: str) -> None:
        """Validate vision_model configuration."""
        if not isinstance(vision_model, str):
            self.errors.append(f"vision_model must be a string: {self.pipeline_file}")
            return
        
        if not vision_model.strip():
            self.errors.append(f"vision_model cannot be empty: {self.pipeline_file}")
            return
        
        # Basic validation - just check it's not empty
        # The actual model validation happens at runtime in ContentIngester
    
    def _validate_files_path(self, files_path: str) -> None:
        """Validate files_path configuration."""
        if not isinstance(files_path, str):
            self.errors.append(f"files_path must be a string: {self.pipeline_file}")
            return
        
        if not files_path.strip():
            self.errors.append(f"files_path cannot be empty: {self.pipeline_file}")
            return
        
        # Check if path is absolute or relative (OS-agnostic)
        from pathlib import Path
        path_obj = Path(files_path)
        
        # Detect absolute paths (Unix: starts with /, Windows: has drive letter)
        is_absolute = path_obj.is_absolute() or (
            len(files_path) >= 2 and files_path[1] == ':' and files_path[0].isalpha()
        )
        
        if is_absolute:
            # Absolute path - check if parent directory exists
            if not path_obj.parent.exists():
                self.warnings.append(f"Parent directory for files_path does not exist: {path_obj.parent}")
        else:
            # Relative path - check if it's reasonable
            if '..' in files_path:
                self.warnings.append(f"Relative files_path contains '..' which may cause issues: {files_path}")
        
        # Check for common issues
        if ' ' in files_path and not files_path.startswith('"') and not files_path.startswith("'"):
            self.warnings.append(f"files_path contains spaces, consider using quotes: {files_path}")
        
        # Check for invalid characters (OS-specific)
        import os
        if os.name == 'nt':  # Windows
            invalid_chars = ['<', '>', '"', '|', '?', '*']
        else:  # Unix/Linux/Mac
            invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        
        for char in invalid_chars:
            if char in files_path:
                self.errors.append(f"files_path contains invalid character '{char}': {files_path}")
                break
    
    def _validate_assistant_section(self, assistant: Dict[str, Any]) -> None:
        """Validate assistant section of global pipeline configuration."""
        if not isinstance(assistant, dict):
            self.errors.append(f"Assistant section must be a YAML object: {self.pipeline_file}")
            return
        
        # Validate required fields for assistant
        required_fields = ["id", "type", "model", "prompt"]
        for field in required_fields:
            if field not in assistant:
                self.errors.append(f"Assistant section must include '{field}' field: {self.pipeline_file}")
        
        # Validate model field
        if "model" in assistant:
            if not isinstance(assistant["model"], str) or not assistant["model"].strip():
                self.errors.append(f"Assistant model must be a non-empty string: {self.pipeline_file}")
        
        # Validate prompt field (new structure: prompt.instruction + optional prompt.inputs)
        if "prompt" in assistant:
            prompt = assistant["prompt"]
            if not isinstance(prompt, dict):
                self.errors.append(f"Assistant prompt must be a YAML object: {self.pipeline_file}")
            else:
                # instruction (required): must specify one of inline/file/jinja
                if "instruction" not in prompt:
                    self.errors.append(f"Assistant prompt must include 'instruction' object with one of: inline, file, jinja: {self.pipeline_file}")
                else:
                    instruction = prompt["instruction"]
                    if not isinstance(instruction, dict):
                        self.errors.append(f"Assistant prompt.instruction must be a YAML object: {self.pipeline_file}")
                    else:
                        instruction_methods = ["inline", "file", "jinja"]
                        if not any(method in instruction for method in instruction_methods):
                            self.errors.append(
                                f"Assistant prompt.instruction must specify one of: {', '.join(instruction_methods)}: {self.pipeline_file}"
                            )

                # inputs (optional): must be a dict if present. Accept either template source (inline/file/jinja)
                # or a map of variables {var: value}
                if "inputs" in prompt:
                    inputs = prompt["inputs"]
                    if not isinstance(inputs, dict):
                        self.errors.append(f"Assistant prompt.inputs must be a YAML object: {self.pipeline_file}")

    def _validate_servers_section(self, servers: Dict[str, Any]) -> None:
        """Validate servers section of pipeline configuration."""
        if not isinstance(servers, dict):
            self.errors.append(f"Servers section must be a YAML object: {self.pipeline_file}")
            return
        
        # Validate FastAPI server
        if "fastapi" not in servers:
            self.errors.append(f"Servers section must include 'fastapi' field: {self.pipeline_file}")
        else:
            fastapi = servers["fastapi"]
            if not isinstance(fastapi, dict):
                self.errors.append(f"FastAPI server must be a YAML object: {self.pipeline_file}")
            elif "url" not in fastapi:
                self.errors.append(f"FastAPI server must include 'url' field: {self.pipeline_file}")
            elif not isinstance(fastapi["url"], str) or not fastapi["url"].strip():
                self.errors.append(f"FastAPI server URL must be a non-empty string: {self.pipeline_file}")
            elif not fastapi["url"].startswith(('http://', 'https://')):
                self.errors.append(f"FastAPI server URL must be a valid HTTP/HTTPS URL: {self.pipeline_file}")
        
        # Validate MCP servers
        if "mcp" not in servers:
            self.errors.append(f"Servers section must include 'mcp' field: {self.pipeline_file}")
        else:
            mcp_servers = servers["mcp"]
            if not isinstance(mcp_servers, list):
                self.errors.append(f"MCP servers must be a list: {self.pipeline_file}")
            elif len(mcp_servers) == 0:
                self.errors.append(f"MCP servers list cannot be empty: {self.pipeline_file}")
            else:
                for i, server in enumerate(mcp_servers):
                    if not isinstance(server, dict):
                        self.errors.append(f"MCP server {i} must be a YAML object: {self.pipeline_file}")
                        continue
                    
                    # Validate required fields
                    if "name" not in server:
                        self.errors.append(f"MCP server {i} must include 'name' field: {self.pipeline_file}")
                    elif not isinstance(server["name"], str) or not server["name"].strip():
                        self.errors.append(f"MCP server {i} name must be a non-empty string: {self.pipeline_file}")
                    
                    if "url" not in server:
                        self.errors.append(f"MCP server {i} must include 'url' field: {self.pipeline_file}")
                    elif not isinstance(server["url"], str) or not server["url"].strip():
                        self.errors.append(f"MCP server {i} URL must be a non-empty string: {self.pipeline_file}")
                    elif not server["url"].startswith(('http://', 'https://')):
                        self.errors.append(f"MCP server {i} URL must be a valid HTTP/HTTPS URL: {self.pipeline_file}")
                    
                    if "model" not in server:
                        self.errors.append(f"MCP server {i} must include 'model' field: {self.pipeline_file}")
                    elif not isinstance(server["model"], str) or not server["model"].strip():
                        self.errors.append(f"MCP server {i} model must be a non-empty string: {self.pipeline_file}")
                    
                    if "transport" not in server:
                        self.errors.append(f"MCP server {i} must include 'transport' field: {self.pipeline_file}")
                    elif not isinstance(server["transport"], str) or not server["transport"].strip():
                        self.errors.append(f"MCP server {i} transport must be a non-empty string: {self.pipeline_file}")
    
    def _validate_ui_manifest_config(self, config: Dict[str, Any]) -> None:
        """Validate global UI manifest configuration structure and content."""
        # Validate required fields for new global UI manifest structure
        required_fields = ["title", "subtitle", "brand", "appearance", "chat", "pipelines", "footer"]
        for field in required_fields:
            if field not in config:
                self.errors.append(f"UI manifest must include '{field}' field: {self.ui_manifest_file}")
        
        # Validate title and subtitle
        if "title" in config:
            if not isinstance(config["title"], str) or not config["title"].strip():
                self.errors.append(f"Title must be a non-empty string: {self.ui_manifest_file}")
        
        if "subtitle" in config:
            if not isinstance(config["subtitle"], str) or not config["subtitle"].strip():
                self.errors.append(f"Subtitle must be a non-empty string: {self.ui_manifest_file}")
        
        # Validate brand section
        if "brand" in config:
            brand = config["brand"]
            if not isinstance(brand, dict):
                self.errors.append(f"Brand must be a YAML object: {self.ui_manifest_file}")
            elif "logo" not in brand:
                self.errors.append(f"Brand must include 'logo' field: {self.ui_manifest_file}")
            elif not isinstance(brand["logo"], str) or not brand["logo"].strip():
                self.errors.append(f"Brand logo must be a non-empty string: {self.ui_manifest_file}")
        
        # Validate appearance section
        if "appearance" in config:
            appearance = config["appearance"]
            if not isinstance(appearance, dict):
                self.errors.append(f"Appearance must be a YAML object: {self.ui_manifest_file}")
            else:
                if "default_theme" not in appearance:
                    self.errors.append(f"Appearance must include 'default_theme' field: {self.ui_manifest_file}")
                elif appearance["default_theme"] not in ["system", "light", "dark"]:
                    self.errors.append(f"Appearance default_theme must be one of: system, light, dark: {self.ui_manifest_file}")
                
                if "default_accent" not in appearance:
                    self.errors.append(f"Appearance must include 'default_accent' field: {self.ui_manifest_file}")
                elif not isinstance(appearance["default_accent"], str) or not appearance["default_accent"].strip():
                    self.errors.append(f"Appearance default_accent must be a non-empty string: {self.ui_manifest_file}")
        
        # Validate chat section
        if "chat" in config:
            chat = config["chat"]
            if not isinstance(chat, dict):
                self.errors.append(f"Chat must be a YAML object: {self.ui_manifest_file}")
            elif "placeholder" not in chat:
                self.errors.append(f"Chat must include 'placeholder' field: {self.ui_manifest_file}")
            elif not isinstance(chat["placeholder"], str) or not chat["placeholder"].strip():
                self.errors.append(f"Chat placeholder must be a non-empty string: {self.ui_manifest_file}")
        
        # Validate pipelines section (pipeline hero cards)
        if "pipelines" in config:
            pipelines = config["pipelines"]
            if not isinstance(pipelines, list):
                self.errors.append(f"Pipelines must be a list: {self.ui_manifest_file}")
            elif len(pipelines) == 0:
                self.errors.append(f"At least one pipeline must be defined: {self.ui_manifest_file}")
            else:
                pipeline_ids = set()
                for i, pipeline in enumerate(pipelines):
                    if not isinstance(pipeline, dict):
                        self.errors.append(f"Pipeline {i} must be a YAML object: {self.ui_manifest_file}")
                        continue
                    
                    # Validate required pipeline fields
                    required_pipeline_fields = ["id", "title", "subtitle", "icon", "ui_manifest"]
                    for field in required_pipeline_fields:
                        if field not in pipeline:
                            self.errors.append(f"Pipeline {i} must have '{field}' field: {self.ui_manifest_file}")
                        elif not isinstance(pipeline[field], str) or not pipeline[field].strip():
                            self.errors.append(f"Pipeline {i} {field} must be a non-empty string: {self.ui_manifest_file}")
                    
                    # Check for duplicate pipeline IDs
                    if "id" in pipeline and pipeline["id"] in pipeline_ids:
                        self.errors.append(f"Duplicate pipeline ID '{pipeline['id']}': {self.ui_manifest_file}")
                    pipeline_ids.add(pipeline.get("id", ""))
        
        # Validate footer section
        if "footer" in config:
            footer = config["footer"]
            if not isinstance(footer, dict):
                self.errors.append(f"Footer must be a YAML object: {self.ui_manifest_file}")
            elif "text" not in footer:
                self.errors.append(f"Footer must include 'text' field: {self.ui_manifest_file}")
            elif not isinstance(footer["text"], str) or not footer["text"].strip():
                self.errors.append(f"Footer text must be a non-empty string: {self.ui_manifest_file}")
    
    def _validate_individual_pipelines(self, individual_pipelines: Dict[str, Dict[str, Any]]) -> None:
        """Validate individual pipeline configuration files using schema."""
        try:
            import json
            from jsonschema import Draft202012Validator
            
            # Load individual pipeline schema
            schema_path = Path(__file__).parent / "schemas" / "pipeline_individual.schema.json"
            if schema_path.exists():
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
                
                validator = Draft202012Validator(schema)
                
                for pipeline_id, config in individual_pipelines.items():
                    # Validate using schema (no embedded configs to worry about)
                    errors = list(validator.iter_errors(config))
                    if errors:
                        for error in errors:
                            self.errors.append(f"Individual pipeline '{pipeline_id}' validation error: {error.message} at {'.'.join(str(p) for p in error.absolute_path)}")
                    else:
                        self.logger.debug("Individual pipeline '{}' validation successful", pipeline_id)
                    
                    # Validate pipelines registry if present
                    pipelines_registry = config.get("pipelines", [])
                    if pipelines_registry:
                        self._validate_pipelines_registry(pipeline_id, pipelines_registry, individual_pipelines, self.project_dir)
            else:
                self.warnings.append("Individual pipeline schema not found, skipping schema validation")
                
        except ImportError:
            self.warnings.append("jsonschema not available, skipping individual pipeline schema validation")
        except Exception as e:
            self.errors.append(f"Failed to validate individual pipelines: {e}")
    
    
    def _validate_individual_ui_manifests(self, individual_ui_manifests: Dict[str, Dict[str, Any]]) -> None:
        """Validate individual UI manifest configuration files using schema."""
        try:
            import json
            from jsonschema import Draft202012Validator
            
            # Load individual UI manifest schema
            schema_path = Path(__file__).parent / "schemas" / "ui_manifest_individual.schema.json"
            if schema_path.exists():
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
                
                validator = Draft202012Validator(schema)
                
                for pipeline_id, config in individual_ui_manifests.items():
                    errors = list(validator.iter_errors(config))
                    if errors:
                        for error in errors:
                            self.errors.append(f"Individual UI manifest '{pipeline_id}' validation error: {error.message} at {'.'.join(str(p) for p in error.absolute_path)}")
                    else:
                        self.logger.debug("Individual UI manifest '{}' validation successful", pipeline_id)
            else:
                self.warnings.append("Individual UI manifest schema not found, skipping schema validation")
                
        except ImportError:
            self.warnings.append("jsonschema not available, skipping individual UI manifest schema validation")
        except Exception as e:
            self.errors.append(f"Failed to validate individual UI manifests: {e}")
    
    def _validate_pipelines_registry(
        self, 
        pipeline_id: str, 
        pipelines_registry: List[Dict[str, Any]], 
        individual_pipelines: Dict[str, Dict[str, Any]],
        project_dir: Path
    ) -> None:
        """Validate pipelines registry for a pipeline configuration.
        
        Args:
            pipeline_id: ID of the pipeline being validated
            pipelines_registry: List of pipeline registry entries
            individual_pipelines: Dictionary of all loaded individual pipelines
            project_dir: Project root directory
        """
        if not isinstance(pipelines_registry, list):
            self.errors.append(
                f"Pipeline '{pipeline_id}': 'pipelines' must be a list"
            )
            return
        
        # Track referenced pipeline IDs for circular dependency detection
        referenced_pipeline_ids = set()
        
        for i, pipeline_entry in enumerate(pipelines_registry):
            if not isinstance(pipeline_entry, dict):
                self.errors.append(
                    f"Pipeline '{pipeline_id}': pipelines[{i}] must be a dictionary"
                )
                continue
            
            # Validate required fields
            if "id" not in pipeline_entry:
                self.errors.append(
                    f"Pipeline '{pipeline_id}': pipelines[{i}] missing required 'id' field"
                )
                continue
            
            if "pipeline_file" not in pipeline_entry:
                self.errors.append(
                    f"Pipeline '{pipeline_id}': pipelines[{i}] missing required 'pipeline_file' field"
                )
                continue
            
            sub_pipeline_id = pipeline_entry["id"]
            pipeline_file = pipeline_entry["pipeline_file"]
            
            # Validate pipeline_file path exists
            pipeline_file_path = project_dir / "config" / pipeline_file
            if not pipeline_file_path.exists():
                self.errors.append(
                    f"Pipeline '{pipeline_id}': pipelines[{i}] references non-existent pipeline_file: {pipeline_file}"
                )
                continue
            
            # Validate that the referenced pipeline exists in individual_pipelines
            if sub_pipeline_id not in individual_pipelines:
                self.errors.append(
                    f"Pipeline '{pipeline_id}': pipelines[{i}] references pipeline '{sub_pipeline_id}' that is not defined in pipeline.yml"
                )
                continue
            
            # Track for circular dependency detection
            referenced_pipeline_ids.add(sub_pipeline_id)
        
        # Check for circular dependencies (simple check: if A references B, B shouldn't reference A)
        # More complex cycles would require a full graph traversal, but this catches the common case
        for referenced_id in referenced_pipeline_ids:
            if referenced_id in individual_pipelines:
                referenced_config = individual_pipelines[referenced_id]
                referenced_registry = referenced_config.get("pipelines", [])
                for ref_entry in referenced_registry:
                    if isinstance(ref_entry, dict) and ref_entry.get("id") == pipeline_id:
                        self.errors.append(
                            f"Pipeline '{pipeline_id}': Circular dependency detected - references '{referenced_id}' which references back to '{pipeline_id}'"
                        )
                        break
    
    def _validate_cross_references(self, pipeline_config: Dict[str, Any], ui_config: Dict[str, Any], individual_pipelines: Dict[str, Dict[str, Any]] = None, individual_ui_manifests: Dict[str, Dict[str, Any]] = None) -> None:
        """Validate cross-references between pipeline and UI configurations."""
        # Get agent IDs from pipeline
        pipeline_agents = set()
        if "agents" in pipeline_config:
            for agent in pipeline_config["agents"]:
                if isinstance(agent, dict) and "id" in agent:
                    pipeline_agents.add(agent["id"])
        
        # Get card IDs from UI manifest
        ui_cards = set()
        if "cards" in ui_config:
            for card in ui_config["cards"]:
                if isinstance(card, dict) and "id" in card:
                    ui_cards.add(card["id"])
        
        # Check for mismatched agent/card IDs
        pipeline_only = pipeline_agents - ui_cards
        ui_only = ui_cards - pipeline_agents
        
        if pipeline_only:
            self.warnings.append(
                f"Agents defined in pipeline but not in UI: {', '.join(pipeline_only)}"
            )
        
        if ui_only:
            self.warnings.append(
                f"Cards defined in UI but not in pipeline: {', '.join(ui_only)}"
            )
    
    def _validate_mcp_tools(self, pipeline_config: Dict[str, Any]) -> None:
        """Validate new multi-server, per-agent MCP configuration schema."""
        
        # Check nodes section for MCP configuration (MVP-6.0)
        agents_to_validate = []
        
        if "nodes" in pipeline_config:
            for node in pipeline_config["nodes"]:
                if isinstance(node, dict) and "config" in node:
                    agents_to_validate.append(node["config"])
        
        for i, agent in enumerate(agents_to_validate):
            if not isinstance(agent, dict):
                continue
                
            agent_id = agent.get("id", f"agent[{i}]")
            
            # Check if agent has MCP configuration
            if "mcp" not in agent:
                # NEW: MCP is enabled by presence of config, not enabled flag
                continue
            
            mcp_config = agent["mcp"]
            
            # Validate mcp configuration is a dictionary
            if not isinstance(mcp_config, dict):
                self.errors.append(
                    f"Agent '{agent_id}' mcp configuration must be a dictionary: {self.pipeline_file}"
                )
                continue
            
            # REMOVED: mcp.enabled validation - now enabled by presence of config
            
            # Get servers field (optional when mcp section exists)
            servers = mcp_config.get("servers", [])
            
            # If servers field exists but is not a list, that's an error
            if "servers" in mcp_config and not isinstance(servers, list):
                self.errors.append(
                    f"Agent '{agent_id}' mcp.servers must be a list: {self.pipeline_file}"
                )
                continue
            
            # Empty servers array or missing servers field is valid - means agent doesn't use MCP tools
            if not servers:
                continue
            
            # Validate each server configuration
            for j, server in enumerate(servers):
                if not isinstance(server, dict):
                    self.errors.append(
                        f"Agent '{agent_id}' mcp.servers[{j}] must be a dictionary: {self.pipeline_file}"
                    )
                    continue
                
                # Validate server.url (required, no hardcoded fallbacks)
                if "url" not in server:
                    self.errors.append(
                        f"Agent '{agent_id}' mcp.servers[{j}] missing required 'url' field: {self.pipeline_file}"
                    )
                    continue
                
                server_url = server["url"]
                if not isinstance(server_url, str):
                    self.errors.append(
                        f"Agent '{agent_id}' mcp.servers[{j}].url must be a string, got {type(server_url).__name__}: {self.pipeline_file}"
                    )
                    continue
                
                if not server_url.strip():
                    self.errors.append(
                        f"Agent '{agent_id}' mcp.servers[{j}].url cannot be empty: {self.pipeline_file}"
                    )
                    continue
                
                # Basic URL format validation
                if not (server_url.startswith(("http://", "https://")) or ":" in server_url):
                    self.warnings.append(
                        f"Agent '{agent_id}' mcp.servers[{j}].url '{server_url}' may not be a valid URL format: {self.pipeline_file}"
                    )
                
                # Validate server.toolkits (required)
                if "toolkits" not in server:
                    self.errors.append(
                        f"Agent '{agent_id}' mcp.servers[{j}] missing required 'toolkits' field: {self.pipeline_file}"
                    )
                    continue
                
                toolkits = server["toolkits"]
                if not isinstance(toolkits, list):
                    self.errors.append(
                        f"Agent '{agent_id}' mcp.servers[{j}].toolkits must be a list: {self.pipeline_file}"
                    )
                    continue
                
                if not toolkits:
                    self.errors.append(
                        f"Agent '{agent_id}' mcp.servers[{j}].toolkits cannot be empty: {self.pipeline_file}"
                    )
                    continue
                
                # Validate individual toolkit names
                for k, toolkit in enumerate(toolkits):
                    if not isinstance(toolkit, str):
                        self.errors.append(
                            f"Agent '{agent_id}' mcp.servers[{j}].toolkits[{k}] must be a string, got {type(toolkit).__name__}: {self.pipeline_file}"
                        )
                    elif not toolkit.strip():
                        self.errors.append(
                            f"Agent '{agent_id}' mcp.servers[{j}].toolkits[{k}] cannot be empty: {self.pipeline_file}"
                        )
                    elif toolkit.strip() != toolkit:
                        self.errors.append(
                            f"Agent '{agent_id}' mcp.servers[{j}].toolkits[{k}] '{toolkit}' has leading/trailing whitespace: {self.pipeline_file}"
                        )
                
                # Validate server.tools (required)
                if "tools" not in server:
                    self.errors.append(
                        f"Agent '{agent_id}' mcp.servers[{j}] missing required 'tools' field: {self.pipeline_file}"
                    )
                    continue
                
                tools = server["tools"]
                if not isinstance(tools, list):
                    self.errors.append(
                        f"Agent '{agent_id}' mcp.servers[{j}].tools must be a list: {self.pipeline_file}"
                    )
                    continue
                
                if not tools:
                    self.errors.append(
                        f"Agent '{agent_id}' mcp.servers[{j}].tools cannot be empty: {self.pipeline_file}"
                    )
                    continue
                
                # Validate individual tool patterns (supports wildcards and exact names)
                for k, tool in enumerate(tools):
                    if not isinstance(tool, str):
                        self.errors.append(
                            f"Agent '{agent_id}' mcp.servers[{j}].tools[{k}] must be a string, got {type(tool).__name__}: {self.pipeline_file}"
                        )
                    elif not tool.strip():
                        self.errors.append(
                            f"Agent '{agent_id}' mcp.servers[{j}].tools[{k}] cannot be empty: {self.pipeline_file}"
                        )
                    elif tool.strip() != tool:
                        self.errors.append(
                            f"Agent '{agent_id}' mcp.servers[{j}].tools[{k}] '{tool}' has leading/trailing whitespace: {self.pipeline_file}"
                        )
                    else:
                        # Validate tool pattern format (supports wildcards and exact names)
                        tool_clean = tool.strip()
                        if "." not in tool_clean:
                            self.warnings.append(
                                f"Agent '{agent_id}' mcp.servers[{j}].tools[{k}] '{tool_clean}' may not be a valid tool pattern (missing toolkit prefix): {self.pipeline_file}"
                            )
                
                # Validate no duplicate tools within the same server
                tool_counts = {}
                for tool in tools:
                    if isinstance(tool, str):
                        tool_counts[tool] = tool_counts.get(tool, 0) + 1
                
                duplicates = [tool for tool, count in tool_counts.items() if count > 1]
                if duplicates:
                    self.errors.append(
                        f"Agent '{agent_id}' mcp.servers[{j}] has duplicate tools: {', '.join(duplicates)}: {self.pipeline_file}"
                    )
            
            # Validate no duplicate server URLs for the same agent
            server_urls = []
            for server in servers:
                if isinstance(server, dict) and "url" in server:
                    server_urls.append(server["url"])
            
            duplicate_urls = [url for url in set(server_urls) if server_urls.count(url) > 1]
            if duplicate_urls:
                self.errors.append(
                    f"Agent '{agent_id}' has duplicate MCP server URLs: {', '.join(duplicate_urls)}: {self.pipeline_file}"
                )
    
    def _validate_paths(self, pipeline_config: Dict[str, Any], ui_config: Dict[str, Any]) -> None:
        """Validate file paths referenced in configuration."""
        # Validate prompt file paths in individual pipelines
        if "pipelines" in pipeline_config:
            for pipeline in pipeline_config["pipelines"]:
                if isinstance(pipeline, dict) and "config_file" in pipeline:
                    pipeline_file = pipeline["config_file"]
                    pipeline_path = self.project_dir / "config" / pipeline_file
                    
                    if pipeline_path.exists():
                        # Load individual pipeline config to validate agent paths
                        try:
                            import yaml
                            with open(pipeline_path, 'r', encoding='utf-8') as f:
                                individual_config = yaml.safe_load(f)
                            
                            if "nodes" in individual_config:
                                for node in individual_config["nodes"]:
                                    if isinstance(node, dict) and "config_file" in node:
                                        agent_config_file = node["config_file"]
                                        # Resolve agent config path using flat structure
                                        agent_config_path = self.project_dir / "config" / agent_config_file
                                        
                                        if not agent_config_path.exists():
                                            self.errors.append(f"Agent config file not found: {agent_config_file} (expected at {agent_config_path})")
                                        
                                        # Validate prompt paths within agent config
                                        if agent_config_path.exists():
                                            with open(agent_config_path, 'r', encoding='utf-8') as f:
                                                agent_config = yaml.safe_load(f)
                                                self._validate_agent_prompt_paths(agent_config, agent_config_path)
                        except Exception as e:
                            self.errors.append(f"Failed to validate paths for pipeline {pipeline_file}: {e}")
        
        # Validate UI asset paths using configured assets directory
        if "pipelines" in ui_config:
            for pipeline in ui_config["pipelines"]:
                if isinstance(pipeline, dict) and "icon" in pipeline:
                    icon_path = pipeline["icon"]
                    if isinstance(icon_path, str) and not icon_path.startswith(("http://", "https://")):
                        full_path = self.resolve_ui_asset_path(icon_path)
                        if not full_path.exists():
                            self.warnings.append(f"UI icon not found: {icon_path} (expected at {full_path})")
        
        # Validate logo path
        if "brand" in ui_config and "logo" in ui_config["brand"]:
            logo_path = ui_config["brand"]["logo"]
            if isinstance(logo_path, str) and not logo_path.startswith(("http://", "https://")):
                full_path = self.resolve_ui_asset_path(logo_path)
                if not full_path.exists():
                    self.warnings.append(f"Logo not found: {logo_path} (expected at {full_path})")

    def _validate_agent_prompt_paths(self, agent_config: Dict[str, Any], agent_config_path: Path) -> None:
        """Validate prompt file paths within an agent configuration."""
        if "prompt" in agent_config:
            prompt = agent_config["prompt"]
            if isinstance(prompt, dict):
                # Check file-based prompts
                if "file" in prompt:
                    file_path = prompt["file"]
                    if isinstance(file_path, str):
                        full_path = self.project_dir / file_path
                        if not full_path.exists():
                            self.errors.append(f"Prompt file not found: {file_path} (expected at {full_path}): {agent_config_path}")
                
                # Check Jinja template paths
                if "jinja" in prompt:
                    jinja_path = prompt["jinja"]
                    if isinstance(jinja_path, str):
                        full_path = self.project_dir / jinja_path
                        if not full_path.exists():
                            self.errors.append(f"Jinja template not found: {jinja_path} (expected at {full_path}): {agent_config_path}") 

    def resolve_agent_config_path(self, pipeline_id: str, agent_config_file: str) -> Path:
        """
        Resolve agent config file path relative to pipeline directory.
        
        Args:
            pipeline_id: ID of the pipeline (e.g., 'stock_analysis')
            agent_config_file: Agent config file name (e.g., 'agents/research_analyst.yml')
            
        Returns:
            Full path to agent config file
        """
        pipeline_dir = self.project_dir / "config" / "pipelines" / pipeline_id
        return pipeline_dir / agent_config_file

    def resolve_ui_manifest_path(self, ui_manifest_file: str) -> Path:
        """
        Resolve UI manifest file path using default manifests directory.
        
        Args:
            ui_manifest_file: UI manifest file name (e.g., 'ui_manifests/stock_analysis.yml')
            
        Returns:
            Full path to UI manifest file
        """
        # Use default location for flat structure
        return self.project_dir / "config" / "ui_manifests" / ui_manifest_file

    def resolve_ui_asset_path(self, asset_file: str) -> Path:
        """
        Resolve UI asset file path using default assets directory.
        
        Args:
            asset_file: Asset file name (e.g., 'assets/stock_analysis/research_analyst.svg')
            
        Returns:
            Full path to UI asset file
        """
        # Use default location for flat structure
        return self.project_dir / "ui" / "static" / "assets" / asset_file

    def _validate_agent_config(self, agent: Dict[str, Any], agent_index: int) -> List[str]:
        """Validate individual agent configuration."""
        errors = []
        
        # Check agent type
        agent_type = agent.get("type")
        if not agent_type:
            errors.append(f"Agent type is required: {self.pipeline_file}")
            return errors
        
        if agent_type not in ["agno", "langgraph", "crewai", "adk", "sk", "oak"]:
            errors.append(f"Unsupported agent type: {agent_type} for agent: {self.pipeline_file}")
            return errors
        
        # Validate based on agent type
        if agent_type == "agno":
            errors.extend(self._validate_agno_agent_config(agent, agent_index))
        elif agent_type == "langgraph":
            errors.extend(self._validate_langgraph_agent_config(agent, agent_index))
        elif agent_type == "crewai":
            errors.extend(self._validate_crewai_agent_config(agent, agent_index))
        
        return errors 
    
    # Context storage configuration methods
    def get_context_storage_config(self) -> Dict[str, Any]:
        """Get context storage configuration from validated config."""
        if not self.validated_config:
            return {}
        
        return {
            "chatdb_path": self.validated_config.chatdb_path,
            "project_dir": str(self.validated_config.project_dir),
            "is_configured": bool(self.validated_config.chatdb_path)
        }
    
    def validate_context_storage_connection(self) -> Dict[str, Any]:
        """Validate that context storage can be initialized."""
        validation_result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "chatdb_path": "",
            "can_create": False
        }
        
        if not self.validated_config or not self.validated_config.chatdb_path:
            validation_result["errors"].append("No chatdb_path configured")
            return validation_result
        
        chatdb_path = self.validated_config.chatdb_path
        validation_result["chatdb_path"] = chatdb_path
        
        try:
            from pathlib import Path
            
            # Check if it's an absolute path
            if chatdb_path.startswith('/'):
                db_path = Path(chatdb_path)
            else:
                # Relative path - resolve against base directory
                db_path = self.validated_config.project_dir / chatdb_path
            
            # Check if parent directory exists
            if db_path.parent.exists():
                validation_result["can_create"] = True
            else:
                validation_result["warnings"].append(f"Parent directory does not exist: {db_path.parent}")
                # Check if we can create the parent directory
                try:
                    db_path.parent.mkdir(parents=True, exist_ok=True)
                    validation_result["can_create"] = True
                    validation_result["warnings"].append(f"Created parent directory: {db_path.parent}")
                except Exception as e:
                    validation_result["errors"].append(f"Cannot create parent directory: {e}")
            
            # Check if database file exists and is accessible
            if db_path.exists():
                if db_path.is_file():
                    validation_result["warnings"].append("Database file already exists")
                else:
                    validation_result["errors"].append("Database path exists but is not a file")
            else:
                validation_result["warnings"].append("Database file does not exist (will be created)")
            
            # Test SQLite connection
            try:
                import sqlite3
                test_conn = sqlite3.connect(str(db_path))
                test_conn.close()
                validation_result["valid"] = True
            except Exception as e:
                validation_result["errors"].append(f"Cannot connect to SQLite database: {e}")
            
        except Exception as e:
            validation_result["errors"].append(f"Validation error: {e}")
        
        return validation_result
    
    def get_context_storage_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for context storage configuration."""
        recommendations = {
            "path_recommendations": [],
            "performance_recommendations": [],
            "security_recommendations": [],
            "backup_recommendations": []
        }
        
        if not self.validated_config or not self.validated_config.chatdb_path:
            recommendations["path_recommendations"].append("Configure chatdb_path in pipeline.yml")
            return recommendations
        
        chatdb_path = self.validated_config.chatdb_path
        
        # Path recommendations
        if not chatdb_path.endswith('.db'):
            recommendations["path_recommendations"].append("Use .db extension for SQLite database files")
        
        if chatdb_path.startswith('/'):
            recommendations["path_recommendations"].append("Consider using relative paths for portability")
        else:
            if '..' in chatdb_path:
                recommendations["path_recommendations"].append("Avoid '..' in relative paths for security")
        
        # Performance recommendations
        recommendations["performance_recommendations"].extend([
            "Place database on fast storage (SSD recommended)",
            "Consider using WAL mode for better concurrency",
            "Regular VACUUM operations for optimal performance",
            "Monitor database size and implement cleanup policies"
        ])
        
        # Security recommendations
        recommendations["security_recommendations"].extend([
            "Ensure database file has appropriate permissions",
            "Consider encrypting sensitive context data",
            "Implement regular backup procedures",
            "Use environment variables for sensitive paths"
        ])
        
        # Backup recommendations
        recommendations["backup_recommendations"].extend([
            "Implement automated database backups",
            "Test backup restoration procedures",
            "Consider point-in-time recovery options",
            "Monitor backup integrity"
        ])
        
        return recommendations