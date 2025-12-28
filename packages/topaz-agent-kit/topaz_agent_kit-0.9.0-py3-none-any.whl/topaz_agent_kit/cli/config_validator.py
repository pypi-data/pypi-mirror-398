import argparse
import json
import yaml  # type: ignore
import jsonschema  # type: ignore
import importlib.resources as pkg_resources
from pathlib import Path
from typing import Any, Dict
import sys

from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.env_substitution import env_substitution


class ConfigValidator:
    """
    Validates Topaz Agent Kit configuration files.
    Provides extensible framework for configuration validation.
    """
    
    def __init__(self):
        self.logger = Logger("ConfigValidator")
    
    def _validate_pipeline_yaml(self, project_dir: Path) -> tuple[bool, list[str]]:
        """Validate main pipeline.yml structure"""
        errs: list[str] = []
        yml = project_dir / "config" / "pipeline.yml"
        if not yml.exists():
            return False, [f"Missing file: {yml}"]
        
        try:
            data = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
            # Apply environment variable substitution
            data = env_substitution.substitute_env_vars(data)
            if not isinstance(data, dict):
                errs.append("pipeline.yml root must be a mapping")
                return False, errs
            
            # Required top-level keys for main pipeline.yml
            for key in ("name", "description", "servers", "pipelines", "chatdb_path", "router", "independent_agents"):
                if key not in data:
                    errs.append(f"Missing required key: {key}")
            
            # Validate pipelines array
            pipelines = data.get("pipelines") or []
            if not isinstance(pipelines, list) or not pipelines:
                errs.append("pipelines must be a non-empty list")
            else:
                for i, pipeline in enumerate(pipelines):
                    if not isinstance(pipeline, dict):
                        errs.append(f"pipelines[{i}] must be a mapping")
                        continue
                    if not pipeline.get("id"):
                        errs.append(f"pipelines[{i}].id is required")
                    if not pipeline.get("config_file"):
                        errs.append(f"pipelines[{i}].config_file is required")
            
            # Validate independent_agents array
            independent_agents = data.get("independent_agents") or []
            if not isinstance(independent_agents, list):
                errs.append("independent_agents must be a list")
            else:
                for i, agent in enumerate(independent_agents):
                    if not isinstance(agent, dict):
                        errs.append(f"independent_agents[{i}] must be a mapping")
                        continue
                    if not agent.get("id"):
                        errs.append(f"independent_agents[{i}].id is required")
                    if not agent.get("config_file"):
                        errs.append(f"independent_agents[{i}].config_file is required")
            
            return (len(errs) == 0), errs
        except Exception as e:
            return False, [f"Failed to parse pipeline.yml: {e}"]

    def _validate_ui_manifest_yaml(self, project_dir: Path) -> tuple[bool, list[str]]:
        """Validate ui_manifest.yml structure"""
        errs: list[str] = []
        yml = project_dir / "config" / "ui_manifest.yml"
        if not yml.exists():
            # Optional; pass if absent
            return True, []
        
        try:
            data = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
            # Apply environment variable substitution
            data = env_substitution.substitute_env_vars(data)
            if not isinstance(data, dict):
                errs.append("ui_manifest.yml root must be a mapping")
                return False, errs
            
            if not isinstance(data.get("title"), (str, type(None))):
                errs.append("title must be a string if present")
            
            cards = data.get("cards")
            if cards is not None and not isinstance(cards, list):
                errs.append("cards must be a list if present")
            
            return (len(errs) == 0), errs
        except Exception as e:
            return False, [f"Failed to parse ui_manifest.yml: {e}"]

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML file from path"""
        self.logger.debug("Loading YAML from: {}", path)
        
        try:
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                # Apply environment variable substitution
                return env_substitution.substitute_env_vars(data)
        except Exception as e:
            self.logger.error("Failed to load YAML from {}: {}", path, e)
            raise SystemExit(f"Failed to load YAML: {e}")

    def _validate_jsonschema(self, cfg: Dict[str, Any], schema_path: Path) -> None:
        """Validate configuration against JSON schema"""
        self.logger.debug("Validating against JSON schema: {}", schema_path)
        
        try:
            with schema_path.open("r", encoding='utf-8') as f:
                schema = json.load(f)
            self.logger.debug("Schema loaded successfully")
            jsonschema.validate(cfg, schema)
            self.logger.debug("JSON schema validation passed")
        except Exception as e:
            self.logger.error("JSON schema validation failed: {}", e)
            raise

    def validate_project(self, project_dir: str | Path) -> int:
        """
        Validate pipeline.yml and ui_manifest.yml
        
        Args:
            project_dir: Path to project root
            
        Returns:
            0 on success, 1 on error
        """
        self.logger.info("Starting configuration validation")
        
        root = Path(project_dir)
        self.logger.info("Validating project: {}", root)
        
        ok1, e1 = self._validate_pipeline_yaml(root)
        ok2, e2 = self._validate_ui_manifest_yaml(root)
        ok = ok1 and ok2
        
        if not ok:
            for e in [*e1, *e2]:
                self.logger.error("- {}", e)
            return 1
        
        self.logger.info("OK: validation passed")
        return 0

    def validate_with_schema(self, config_path: Path, schema_path: Path | None = None) -> int:
        """
        Validate configuration file against JSON schema
        
        Args:
            config_path: Path to configuration file
            schema_path: Optional path to JSON schema file
            
        Returns:
            0 on success, 1 on error
        """
        self.logger.info("Starting schema validation")
        
        if not config_path.exists():
            self.logger.error("Configuration file not found: {}", config_path)
            return 1
        
        cfg = self._load_yaml(config_path)
        self.logger.success("Configuration loaded successfully")

        if schema_path is None:
            # Use default packaged schema location
            self.logger.debug("Looking for default packaged schema")
            try:
                schema_res = pkg_resources.files("topaz_agent_kit.core.schemas") / "pipeline.schema.json"
                schema_path = Path(str(schema_res))
                self.logger.debug("Default schema path: {}", schema_path)
            except Exception as e:
                self.logger.warning("Failed to locate default schema: {}", e)
                schema_path = None

        if schema_path and schema_path.exists():
            self.logger.info("Validating against schema: {}", schema_path)
            self._validate_jsonschema(cfg, schema_path)
            self.logger.success("Validation successful: YAML matches schema")
        else:
            self.logger.warning("Schema not found, skipping schema validation")
        
        self.logger.success("Schema validation completed")
        return 0


def main() -> None:
    """CLI entry point for configuration validation"""
    parser = argparse.ArgumentParser(description="Validate a topaz-agent-kit YAML config")
    parser.add_argument("project", help="Path to project directory containing config/pipeline.yml")
    parser.add_argument("--schema", dest="schema", default=None, help="Optional path to pipeline JSON schema")
    args = parser.parse_args()

    validator = ConfigValidator()
    
    if args.schema:
        # Validate specific file against schema
        config_path = Path(args.project) / "config" / "pipeline.yml"
        schema_path = Path(args.schema)
        exit_code = validator.validate_with_schema(config_path, schema_path)
    else:
        # Validate project structure
        exit_code = validator.validate_project(args.project)
    
    sys.exit(exit_code)


if __name__ == "__main__":  # pragma: no cover
    main()

