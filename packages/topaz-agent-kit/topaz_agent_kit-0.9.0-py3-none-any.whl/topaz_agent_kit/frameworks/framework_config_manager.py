"""Framework-specific configuration manager using YAML configs"""

import os
from typing import Dict, Any, List
from pathlib import Path
import yaml

from topaz_agent_kit.core.exceptions import FrameworkError, ConfigurationError
from topaz_agent_kit.utils.logger import Logger


class FrameworkConfigManager:
    """Framework-specific configuration manager using YAML configs"""
    
    def __init__(self):
        self.logger = Logger("FrameworkConfigManager")
        self._configs = {}
        self._capabilities_cache = {}
        self._compatibility_matrix = {}
        self._load_framework_configs()
        self._build_capabilities_registry()
        self._build_compatibility_matrix()
    
    def _load_framework_configs(self):
        """Load framework configurations using a mandatory id→file registry.

        _frameworks.yml is the single source of truth (id → filename mapping).
        If missing or malformed, we fail fast with a ConfigurationError.
        """
        try:
            # Environment variables are already loaded by Orchestrator
            config_dir = Path(__file__).parent / "config"
            
            if not config_dir.exists():
                self.logger.error("Framework config directory does not exist: {}", config_dir)
                raise ConfigurationError(f"Framework config directory not found: {config_dir}")
            
            registry_file = config_dir / "_frameworks.yml"
            if not registry_file.exists():
                self.logger.error("Missing required framework registry: {}", registry_file)
                raise ConfigurationError(f"Required registry file not found: {registry_file}")
            
            with open(registry_file, "r", encoding='utf-8') as f:
                registry = yaml.safe_load(f) or {}
            
            mapping = registry.get("frameworks", {})
            if not isinstance(mapping, dict):
                self.logger.error("Invalid _frameworks.yml: 'frameworks' must be a mapping")
                raise ConfigurationError("Invalid _frameworks.yml: 'frameworks' must be a mapping")
            
            self._configs = {}
            for framework_id, filename in mapping.items():
                if not isinstance(framework_id, str) or not isinstance(filename, str):
                    self.logger.error("Invalid _frameworks.yml: keys and values must be strings")
                    raise ConfigurationError("Invalid _frameworks.yml: keys and values must be strings")
                
                config_file = config_dir / filename
                if not config_file.exists():
                    self.logger.error("Framework '{}' file not found: {}", framework_id, config_file)
                    raise ConfigurationError(f"Framework '{framework_id}' file not found: {config_file}")
                
                with open(config_file, "r", encoding='utf-8') as f:
                    self._configs[framework_id] = yaml.safe_load(f) or {}
                    
            self.logger.info("Loaded {} framework configurations from _frameworks.yml", len(self._configs))
            
        except Exception as e:
            self.logger.error("Failed to load framework configs: {}", e)
            self._configs = {}
            raise
    
    def _build_capabilities_registry(self):
        """Build comprehensive capabilities registry for all frameworks"""
        try:
            for framework, config in self._configs.items():
                capabilities = self._extract_framework_capabilities(framework, config)
                self._capabilities_cache[framework] = capabilities
                
            self.logger.info("Built capabilities registry for {} frameworks", len(self._capabilities_cache))
            
        except Exception as e:
            self.logger.error("Failed to build capabilities registry: {}", e)
            self._capabilities_cache = {}
    
    def _extract_framework_capabilities(self, framework: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract comprehensive capabilities from framework configuration"""
        try:
            # Get framework metadata
            framework_info = config.get("framework", {})
            
            # Extract model capabilities
            model_capabilities = {}
            for model_type, model_config in config.get("models", {}).items():
                model_capabilities[model_type] = {
                    "class": model_config.get("class", ""),
                    "parameter_count": len(model_config.get("parameters", {}))
                }
            
            # Extract MCP capabilities
            mcp_capabilities = config.get("mcp_integration", {})
            
            # Build comprehensive capabilities
            capabilities = {
                "framework": {
                    "name": framework_info.get("name", framework),
                    "version": framework_info.get("version", "unknown"),
                    "description": framework_info.get("description", ""),
                    "type": framework
                },
                "models": model_capabilities,
                "mcp_integration": {
                    "supported": bool(mcp_capabilities),
                    "transport": mcp_capabilities.get("transport", "unknown"),
                    "auto_discovery": mcp_capabilities.get("tool_discovery", {}).get("auto_discover", False),
                    "connection_timeout": mcp_capabilities.get("connection", {}).get("timeout", 30)
                }
            }
            
            return capabilities
            
        except Exception as e:
            self.logger.error("Failed to extract capabilities for framework {}: {}", framework, e)
            return {}
    
    def _build_compatibility_matrix(self):
        """Build framework compatibility matrix"""
        try:
            frameworks = list(self._configs.keys())
            
            for framework1 in frameworks:
                self._compatibility_matrix[framework1] = {}
                for framework2 in frameworks:
                    compatibility = self._calculate_framework_compatibility(framework1, framework2)
                    self._compatibility_matrix[framework1][framework2] = compatibility
            
            self.logger.info("Built compatibility matrix for {} frameworks", len(frameworks))
            
        except Exception as e:
            self.logger.error("Failed to build compatibility matrix: {}", e)
            self._compatibility_matrix = {}
    
    def _calculate_framework_compatibility(self, framework1: str, framework2: str) -> Dict[str, Any]:
        """Calculate compatibility between two frameworks"""
        try:
            if framework1 == framework2:
                return {
                    "compatible": True,
                    "score": 100,
                    "data_formats": ["identical"],
                    "tool_protocols": ["identical"],
                    "notes": "Same framework"
                }
            
            # Get capabilities for both frameworks
            cap1 = self._capabilities_cache.get(framework1, {})
            cap2 = self._capabilities_cache.get(framework2, {})
            
            # Calculate compatibility score
            compatibility_score = 0
            data_format_compatibility = []
            tool_protocol_compatibility = []
            
            # Check MCP integration compatibility
            if cap1.get("mcp_integration", {}).get("supported") and cap2.get("mcp_integration", {}).get("supported"):
                compatibility_score += 30
                tool_protocol_compatibility.append("mcp")
            
            # Check model compatibility
            if cap1.get("models") and cap2.get("models"):
                common_models = set(cap1["models"].keys()) & set(cap2["models"].keys())
                if common_models:
                    compatibility_score += 20
                    data_format_compatibility.append("common_models")
            
            # Check agent capability compatibility
            agent_cap1 = cap1.get("agent", {})
            agent_cap2 = cap2.get("agent", {})
            
            if agent_cap1.get("supports_tools") and agent_cap2.get("supports_tools"):
                compatibility_score += 25
                tool_protocol_compatibility.append("tool_support")
            
            if agent_cap1.get("supports_memory") and agent_cap2.get("supports_memory"):
                compatibility_score += 15
                data_format_compatibility.append("memory_support")
            
            # Determine overall compatibility
            compatible = compatibility_score >= 50
            
            return {
                "compatible": compatible,
                "score": compatibility_score,
                "data_formats": data_format_compatibility,
                "tool_protocols": tool_protocol_compatibility,
                "notes": f"Compatibility score: {compatibility_score}/100"
            }
            
        except Exception as e:
            self.logger.error("Failed to calculate compatibility between {} and {}: {}", framework1, framework2, e)
            return {
                "compatible": False,
                "score": 0,
                "data_formats": [],
                "tool_protocols": [],
                "notes": f"Error calculating compatibility: {e}"
            }
    
    def detect_framework_from_config(self, agent_config: Dict[str, Any]) -> str:
        """Detect framework from agent configuration using mandatory type field"""
        try:
            # Check mandatory framework type
            if "type" not in agent_config:
                raise FrameworkError("Agent configuration must specify 'type' field")
            
            framework_type = agent_config["type"]
            if framework_type not in self._configs:
                raise FrameworkError(f"Unsupported framework type: {framework_type}")
            
            self.logger.debug("Framework specified: {}", framework_type)
            return framework_type
            
        except Exception as e:
            self.logger.error("Failed to detect framework from config: {}", e)
            raise
    
    def get_framework_capabilities(self, framework: str) -> Dict[str, Any]:
        """Get detailed capabilities for a framework"""
        if framework not in self._capabilities_cache:
            raise FrameworkError(f"Framework capabilities not available: {framework}")
        return self._capabilities_cache[framework].copy()
    
    def check_framework_compatibility(self, framework1: str, framework2: str) -> Dict[str, Any]:
        """Check if two frameworks can work together in pipeline"""
        if framework1 not in self._compatibility_matrix or framework2 not in self._compatibility_matrix[framework1]:
            return {
                "compatible": False,
                "score": 0,
                "data_formats": [],
                "tool_protocols": [],
                "notes": "Compatibility information not available"
            }
        
        return self._compatibility_matrix[framework1][framework2].copy()
    
    def get_framework_config(self, framework: str) -> Dict[str, Any]:
        """Get configuration for a specific framework"""
        if framework not in self._configs:
            raise FrameworkError(f"Unsupported framework: {framework}")
        return self._configs[framework]
    
    def get_model_requirements(self, framework: str, model_type: str) -> Dict[str, Any]:
        """Get model requirements for a specific framework + model type"""
        framework_config = self.get_framework_config(framework)
        
        if "models" not in framework_config or model_type not in framework_config["models"]:
            raise FrameworkError(f"Model type {model_type} not supported by {framework}")
        
        return framework_config["models"][model_type]
    
    def get_mcp_integration(self, framework: str) -> Dict[str, Any]:
        """Get MCP integration details for a framework"""
        framework_config = self.get_framework_config(framework)
        return framework_config.get("mcp_integration", {})
    
    def get_agent_config(self, framework: str) -> Dict[str, Any]:
        """Get agent creation configuration for a framework"""
        framework_config = self.get_framework_config(framework)
        return framework_config.get("agent", {})
    
    def get_framework_features(self, framework: str) -> Dict[str, Any]:
        """Get framework-specific features"""
        framework_config = self.get_framework_config(framework)
        return framework_config.get("features", {})
    
    def get_error_handling(self, framework: str) -> Dict[str, Any]:
        """Get error handling configuration for a framework"""
        framework_config = self.get_framework_config(framework)
        return framework_config.get("error_handling", {})
    
    def get_model_config(self, model_type: str, framework: str = None) -> Dict[str, str]:
        """Get model configuration with optional framework overrides"""
        
        if framework is None:
            raise ConfigurationError(f"Framework must be specified for model type: {model_type}")
        
        try:
            model_requirements = self.get_model_requirements(framework, model_type)
        except ValueError as e:
            raise ConfigurationError(f"Failed to get model requirements for {framework}/{model_type}: {e}")
        
        # Environment variables are already loaded by Orchestrator
        # Extract parameters and resolve environment variables
        config = {}
        parameters = model_requirements.get("parameters", {})
        
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # Resolve environment variable
                env_var = value[2:-1]  # Remove ${}
                config[key] = os.getenv(env_var)
            else:
                config[key] = value
        
        return config
    
    def get_available_frameworks(self) -> List[str]:
        """Get list of available frameworks"""
        return list(self._configs.keys())
    
    def get_framework_info(self, framework: str) -> Dict[str, Any]:
        """Get detailed information about a framework"""
        if framework not in self._configs:
            return {}
        
        config = self._configs[framework]
        return {
            "name": config.get("framework", {}).get("name", framework),
            "version": config.get("framework", {}).get("version", "unknown"),
            "description": config.get("framework", {}).get("description", ""),
            "supported_models": list(config.get("models", {}).keys()),
            "features": config.get("features", {}),
            "mcp_support": "mcp_integration" in config
        }
    
    def validate_framework_config(self, framework: str) -> Dict[str, Any]:
        """Enhanced validation with detailed feedback"""
        try:
            config = self.get_framework_config(framework)
            
            validation_result = {
                "valid": True,
                "framework": framework,
                "missing_sections": [],
                "warnings": [],
                "suggestions": [],
                "capabilities": {}
            }
            
            # Check required sections
            required_sections = ["name", "description", "models", "mcp_integration"]
            for section in required_sections:
                if section not in config:
                    validation_result["missing_sections"].append(section)
                    validation_result["valid"] = False
            
            # Check required MCP integration subsections
            mcp_config = config.get("mcp_integration", {})
            required_mcp_sections = ["transport", "tool_class", "params_class", "timeout"]
            for section in required_mcp_sections:
                if section not in mcp_config:
                    validation_result["missing_sections"].append(f"mcp_integration.{section}")
                    validation_result["valid"] = False
            
            # Check that at least one model is defined
            if not config.get("models", {}):
                validation_result["warnings"].append("No models defined")
                validation_result["suggestions"].append("Add at least one model configuration")
            
            # Check MCP integration completeness
            mcp_config = config.get("mcp_integration", {})
            if not mcp_config.get("transport"):
                validation_result["warnings"].append("MCP transport not specified")
                validation_result["suggestions"].append("Specify transport protocol (e.g., 'streamable-http')")
            
            # Check timeout parameter value (if present)
            if "timeout" in mcp_config and (not isinstance(mcp_config.get("timeout"), int) or mcp_config.get("timeout", 0) < 1):
                validation_result["warnings"].append("Invalid timeout value")
                validation_result["suggestions"].append("Timeout must be a positive integer (seconds)")
            
            # Check agent configuration
            agent_config = config.get("agent", {})
            if not agent_config.get("class"):
                validation_result["warnings"].append("Agent class not specified")
                validation_result["suggestions"].append("Specify agent class for framework")
            
            # Add capabilities information
            if framework in self._capabilities_cache:
                validation_result["capabilities"] = self._capabilities_cache[framework]
            
            # Add suggestions for improvement
            if validation_result["valid"]:
                validation_result["suggestions"].append("Configuration is valid and complete")
            
            return validation_result
            
        except Exception as e:
            self.logger.error("Failed to validate framework {}: {}", framework, e)
            return {
                "valid": False,
                "framework": framework,
                "error": str(e),
                "missing_sections": [],
                "warnings": [],
                "suggestions": ["Fix configuration errors before validation"]
            }
    
 