"""Framework-aware model factory that creates appropriate models for each framework"""

from typing import Any, Dict
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.frameworks.framework_config_manager import FrameworkConfigManager
from topaz_agent_kit.core.exceptions import (
    ConfigurationError, 
    FrameworkError,
    ModelError
)


class FrameworkModelFactory:
    """Framework-aware model factory that creates appropriate models for each framework"""
    
    _logger = Logger("FrameworkModelFactory")
    
    @classmethod
    def get_model(cls, model_type: str, framework: str = None, **config) -> Any:
        """Get a model, optionally framework-specific"""
        try:
            # Default to langgraph if no framework specified
            if framework is None:
                framework = "langgraph"
                cls._logger.info("No framework specified, defaulting to {}", framework)
            
            # Validate framework parameter
            if not framework or not isinstance(framework, str):
                raise ConfigurationError("Framework parameter must be a non-empty string")
            
            cls._logger.info("Creating {} model for {} framework", model_type, framework)
            
            # Get framework-specific model requirements
            framework_config = FrameworkConfigManager()
            try:
                model_requirements = framework_config.get_model_requirements(framework, model_type)
            except ValueError as e:
                raise ConfigurationError(f"Failed to get model requirements for {framework}/{model_type}: {str(e)}")
            
            # Get model configuration from FrameworkConfigManager
            try:
                model_config = framework_config.get_model_config(model_type, framework=framework)
            except Exception as e:
                raise ConfigurationError(f"Failed to get model configuration for {model_type}: {str(e)}")
            
            # Merge configs (model_config has priority, then passed config)
            merged_config = {**model_config, **config}
            
            # Create model using the same logic for ALL frameworks
            model_class = model_requirements["class"]
            if not model_class:
                raise ConfigurationError(f"Missing 'class' in model requirements for {model_type}")
            
            # Import the required class
            try:
                module_path, class_name = model_class.rsplit(".", 1)
                module = __import__(module_path, fromlist=[class_name])
                model_class_obj = getattr(module, class_name)
            except (ImportError, AttributeError) as e:
                raise ConfigurationError(f"Failed to import model class {model_class}: {str(e)}")
            
            # Create model with config (no validation - user provides what they need)
            try:
                model = model_class_obj(**merged_config)
            except Exception as e:
                raise ModelError(f"Failed to instantiate {framework} model {model_class}: {str(e)}")
            
            cls._logger.success("Created {} {} model: {}", framework, model_type, type(model).__name__)
            return model
            
        except (ConfigurationError, ModelError, FrameworkError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Convert unexpected exceptions to our standardized types
            cls._logger.error("Unexpected error creating {} model: {}", model_type, e, exc_info=True)
            raise FrameworkError(f"Unexpected error creating {model_type} model: {str(e)}")
    

    
    @classmethod
    def validate_framework_support(cls, framework: str, model_type: str) -> bool:
        """Validate if a framework supports a specific model type"""
        try:
            framework_config = FrameworkConfigManager()
            model_requirements = framework_config.get_model_requirements(framework, model_type)
            return bool(model_requirements and "class" in model_requirements)
        except Exception:
            return False
    
    @classmethod
    def get_supported_frameworks(cls) -> list:
        """Get list of supported frameworks"""
        try:
            framework_config = FrameworkConfigManager()
            return framework_config.get_available_frameworks()
        except Exception:
            return []
    
    @classmethod
    def get_supported_models_for_framework(cls, framework: str) -> list:
        """Get list of supported models for a specific framework"""
        try:
            framework_config = FrameworkConfigManager()
            framework_config_data = framework_config.get_framework_config(framework)
            return list(framework_config_data.get("models", {}).keys())
        except Exception:
            return [] 