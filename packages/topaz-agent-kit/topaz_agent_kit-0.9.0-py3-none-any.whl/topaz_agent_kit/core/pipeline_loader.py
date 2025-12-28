import json
from pathlib import Path
from typing import Any, Dict, Tuple, List
import importlib.resources as pkg_resources
from jsonschema import Draft202012Validator

from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.env_substitution import env_substitution
from topaz_agent_kit.frameworks import FrameworkConfigManager
from topaz_agent_kit.core.exceptions import (
    ConfigurationError,
    PipelineError
)

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


class PipelineLoader:
    """Load and lightly validate pipeline.yml and ui_manifest.json from a project root.
    """

    def __init__(self, root_dir: str | Path) -> None:
        self.root = Path(root_dir)
        self.logger = Logger("PipelineLoader")
        self.logger.info("Initialized with root directory: {}", self.root)

    def __str__(self) -> str:
        """String representation of PipelineLoader."""
        return f"PipelineLoader(root={self.root})"

    def load_yaml(self, file_path: Path) -> Dict[str, Any]:
        self.logger.debug("Loading YAML file: {}", file_path)
        
        # Environment variables are already loaded by Orchestrator
        if yaml is None:
            self.logger.error("PyYAML is required to load pipeline.yml")
            raise ConfigurationError("PyYAML is required to load pipeline.yml")
        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            if not isinstance(data, dict):
                self.logger.error("YAML root must be a mapping: {}", file_path)
                raise ConfigurationError(f"Invalid YAML format in {file_path}: Root must be a mapping/dictionary")
            
            # Apply environment variable substitution
            data = env_substitution.substitute_in_yaml_data(data)
            
            self.logger.debug("Successfully loaded YAML with {} keys", len(data))
            return data
        except Exception as e:
            self.logger.error("Failed to load YAML file {}: {}", file_path, e)
            raise ConfigurationError(f"Failed to load YAML file {file_path}: {e}")

    def load_json(self, file_path: Path) -> Dict[str, Any]:
        self.logger.debug("Loading JSON file: {}", file_path)
        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f) or {}
            if not isinstance(data, dict):
                self.logger.error("JSON root must be an object: {}", file_path)
                raise ConfigurationError(f"Invalid JSON format in {file_path}: Root must be an object/dictionary")
            
            # Apply environment variable substitution
            data = env_substitution.substitute_in_yaml_data(data)
            
            self.logger.debug("Successfully loaded JSON with {} keys", len(data))
            return data
        except Exception as e:
            self.logger.error("Failed to load JSON file {}: {}", file_path, e)
            raise ConfigurationError(f"Failed to load JSON file {file_path}: {e}")

    def load(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        self.logger.info("Loading pipeline configuration from: {}", self.root)
        pipeline_file = self.root / "config" / "pipeline.yml"
        ui_yml = self.root / "config" / "ui_manifest.yml"
        ui_yaml = self.root / "config" / "ui_manifest.yaml"
        
        self.logger.debug("Loading pipeline from: {}", pipeline_file)
        pipeline = self.load_yaml(pipeline_file)
        
        # Note: Agent configurations are loaded separately by AgentFactory when needed
        # Pipeline structure should only contain references (id, config_file)
        
        # YAML-only manifest (preferred): ui_manifest.yml|yaml
        if ui_yml.exists():
            self.logger.debug("Loading UI manifest from: {}", ui_yml)
            ui = self.load_yaml(ui_yml)
        elif ui_yaml.exists():
            self.logger.debug("Loading UI manifest from: {}", ui_yaml)
            ui = self.load_yaml(ui_yaml)
        else:
            self.logger.debug("No UI manifest found, using empty defaults")
            ui = {}
        
        # Validate UI manifest (warn-only for MVP)
        try:
            schema_path = pkg_resources.files("topaz_agent_kit.core.schemas") / "ui_manifest.schema.json"
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            validator = Draft202012Validator(schema)
            errors = sorted(validator.iter_errors(ui), key=lambda e: e.path)
            for err in errors:
                self.logger.warning("ui_manifest validation: {}", err.message)
        except Exception as e:
            # Non-fatal: schema missing or invalid should not block loading
            self.logger.warning("ui_manifest validation skipped: {}", e)

        # Minimal normalization for forward-compat
        try:
            meta = ui.setdefault("meta", {})
            meta.setdefault("ui_schema_version", "1.0")
            if not ui.get("cards") and not ((ui.get("hero") or {}).get("cards")):
                ui["cards"] = []
        except Exception:
            pass

        # Do not touch defaults here; services inject settings.json into cfg["defaults"].
        # Only ensure meta exists for forward-compat keys.
        self.logger.debug("Normalizing configuration keys (meta only); defaults come from settings.json")
        pipeline.setdefault("meta", {})
        
        # UI toggles moved to ui_manifest.yml; no defaults here
        self.logger.debug("Validating pipeline configuration")
        validation_errors = self._validate(pipeline)
        
        if validation_errors:
            error_message = "Pipeline validation failed:\n" + "\n".join(f"- {error}" for error in validation_errors)
            self.logger.error("Pipeline validation failed: {}", error_message)
            raise PipelineError(error_message)
        
        # Count agents from pattern-only format (nodes) or pipelines format (multi-pipeline)
        agent_count = 0
        if "nodes" in pipeline and isinstance(pipeline["nodes"], list):
            # Single-pipeline structure (pattern-only)
            agent_count = len(pipeline["nodes"])
        elif "pipelines" in pipeline:
            # Multi-pipeline structure - count agents from individual pipeline files
            for pipeline_ref in pipeline["pipelines"]:
                if isinstance(pipeline_ref, dict) and "config_file" in pipeline_ref:
                    pipeline_file = self.root / "config" / pipeline_ref["config_file"]
                    if pipeline_file.exists():
                        try:
                            pipeline_config = self.load_yaml(pipeline_file)
                            if "nodes" in pipeline_config and isinstance(pipeline_config["nodes"], list):
                                agent_count += len(pipeline_config["nodes"])
                        except Exception as e:
                            self.logger.warning("Failed to load pipeline file {} for agent counting: {}", pipeline_file, e)
        
        self.logger.success("Successfully loaded pipeline with {} agents and {} UI config keys", 
                        agent_count, len(ui))
        return pipeline, ui

    def _validate(self, config: Dict[str, Any]) -> List[str]:
        """Validate pipeline configuration"""
        errors = []
        
        # Basic structure validation
        if not isinstance(config, dict):
            errors.append("Pipeline configuration must be a dictionary")
            return errors
        
        # Check if this is a multi-pipeline configuration
        if "pipelines" in config:
            # Multi-pipeline structure: validate pipelines section
            pipeline_errors = self._validate_pipelines_section(config["pipelines"])
            errors.extend(pipeline_errors)
            
            # Validate required fields for multi-pipeline
            required_fields = ["name", "description", "servers", "chatdb_path", "assistant"]
            for field in required_fields:
                if field not in config:
                    errors.append(f"Missing required field: '{field}'")
            
        else:
            errors.append("Configuration must use multi-pipeline structure with 'pipelines' section")
        
        return errors
    
    def _validate_pipelines_section(self, pipelines: List[Dict[str, Any]]) -> List[str]:
        """Validate pipelines section of multi-pipeline configuration"""
        errors = []
        
        if not isinstance(pipelines, list):
            errors.append("Pipelines section must be a list")
            return errors
        
        if not pipelines:
            errors.append("Pipelines list cannot be empty")
            return errors
        
        # Validate each pipeline reference
        for i, pipeline in enumerate(pipelines):
            if not isinstance(pipeline, dict):
                errors.append(f"Pipeline at index {i} must be a dictionary")
                continue
            
            # Check required fields
            if "id" not in pipeline:
                errors.append(f"Pipeline at index {i} missing required field: id")
            elif not isinstance(pipeline["id"], str):
                errors.append(f"Pipeline at index {i} id must be a string")
            
            if "config_file" not in pipeline:
                errors.append(f"Pipeline at index {i} missing required field: config_file")
            elif not isinstance(pipeline["config_file"], str):
                errors.append(f"Pipeline at index {i} config_file must be a string")
        
        return errors
    
    def _validate_pipeline_section(self, pipeline: Dict[str, Any]) -> List[str]:
        """Validate pipeline section of pipeline configuration"""
        errors = []
        
        if not isinstance(pipeline, dict):
            errors.append("Pipeline section must be a dictionary")
            return errors
        
        # Pipeline section is optional, so no required fields
        # Only validate if steps are present
        if "steps" in pipeline and not isinstance(pipeline["steps"], list):
            errors.append("Pipeline steps must be a list")
        
        return errors
    
    def _validate_agent_types(self, pipeline_config: Dict[str, Any]) -> List[str]:
        """Validate that all agent types are supported frameworks"""
        errors = []
        
        # Get supported frameworks dynamically - fail fast if not available
        supported_frameworks = FrameworkConfigManager().get_available_frameworks()
        
        # Handle both list and dictionary agent formats
        agents = pipeline_config.get("agents", {})
        if isinstance(agents, list):
            # Convert list format to dictionary for validation
            agents_dict = {}
            for i, agent_config in enumerate(agents):
                if isinstance(agent_config, dict) and "id" in agent_config:
                    agents_dict[agent_config["id"]] = agent_config
                else:
                    agents_dict[f"agent_{i}"] = agent_config
            agents = agents_dict
        elif not isinstance(agents, dict):
            # Invalid format
            errors.append("Agents section must be a list or dictionary")
            return errors
        
        for agent_id, agent_config in agents.items():
            if not isinstance(agent_config, dict):
                errors.append(f"Agent '{agent_id}' configuration must be a dictionary")
                continue
                
            agent_type = agent_config.get("type")
            if not agent_type:
                errors.append(f"Agent '{agent_id}' missing 'type' field")
            elif agent_type not in supported_frameworks:
                errors.append(f"Agent '{agent_id}' has unsupported type '{agent_type}'. Supported: {supported_frameworks}")
        
        return errors

    def load_framework_configs(self) -> Dict[str, Any]:
        """Load framework-specific configurations for new architecture"""
        try:
            # Import here to make it more mockable in tests
            from topaz_agent_kit.frameworks import FrameworkConfigManager
            
            config_manager = FrameworkConfigManager()
            frameworks = config_manager.get_available_frameworks()
            
            self.logger.info("Loaded {} framework configurations: {}", len(frameworks), frameworks)
            
            # Load configurations for each available framework
            framework_configs = {}
            for framework in frameworks:
                try:
                    config = config_manager.get_framework_config(framework)
                    # Only add framework if config is valid (not None and has content)
                    if config is not None:
                        framework_configs[framework] = config
                        self.logger.debug("Loaded config for framework {}: {} keys", framework, len(config))
                    else:
                        self.logger.warning("Framework {} returned None config, skipping", framework)
                except Exception as e:
                    self.logger.warning("Failed to load config for framework {}: {}", framework, e)
                    continue
            
            self.logger.success("Successfully loaded {} framework configurations", len(framework_configs))
            return framework_configs
            
        except ImportError as e:
            self.logger.warning("Framework configs not available: {}", e)
            self.logger.warning("PipelineLoader will operate without framework awareness")
            return {}
        except Exception as e:
            self.logger.error("Failed to load framework configs: {}", e)
            self.logger.warning("PipelineLoader will operate without framework awareness")
            return {}

