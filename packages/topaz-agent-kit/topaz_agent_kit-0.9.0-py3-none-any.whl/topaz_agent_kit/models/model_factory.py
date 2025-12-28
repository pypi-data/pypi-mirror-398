"""Framework-agnostic model factory for generic model creation"""

import os
import yaml
from typing import Any, Dict
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.core.exceptions import ConfigurationError, ModelError


class ModelFactory:
    """Framework-agnostic model factory for generic model creation"""
    
    _logger = Logger("ModelFactory")
    _config_cache = None
    _model_cache = {}  # Cache for model instances to avoid redundant creation
    
    @classmethod
    def _load_config(cls, config_type: str = "models") -> Dict[str, Any]:
        """Load the generic models or embedding models configuration"""
        cache_key = f"{config_type}_config"
        if not hasattr(cls, '_config_cache') or cls._config_cache is None:
            cls._config_cache = {}
        
        if cache_key not in cls._config_cache:
            config_path = os.path.join(os.path.dirname(__file__), "config", f"{config_type}.yml")
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    cls._config_cache[cache_key] = yaml.safe_load(f)
                cls._logger.info("Loaded generic {} configuration from: {}", config_type, config_path)
            except Exception as e:
                cls._logger.error("Failed to load generic {} configuration: {}", config_type, e)
                raise ConfigurationError(f"Failed to load generic {config_type} configuration: {e}")
        
        return cls._config_cache[cache_key]
    
    @classmethod
    def _resolve_env_variables(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve environment variables in configuration"""
        # Environment variables are already loaded by Orchestrator
        resolved_config = {}
        for key, value in config.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # Resolve environment variable
                env_var = value[2:-1]  # Remove ${}
                resolved_value = os.getenv(env_var)
                if resolved_value is None:
                    cls._logger.warning("Environment variable '{}' not found", env_var)
                resolved_config[key] = resolved_value
            else:
                resolved_config[key] = value
        
        return resolved_config
    
    @classmethod
    def get_model(cls, model_type: str) -> Any:
        """Create a generic model (chat/completion models)"""
        # Check cache first
        cache_key = f"generic_{model_type}"
        if cache_key in cls._model_cache:
            cls._logger.info("Reusing cached generic model: {}", model_type)
            return cls._model_cache[cache_key]
        
        try:
            cls._logger.info("Creating generic model: {}", model_type)
            
            config = cls._load_config("models")
            models_config = config.get("models", {})
            
            if model_type not in models_config:
                available_models = list(models_config.keys())
                raise ConfigurationError(f"Model '{model_type}' not found. Available models: {available_models}")
            
            model_config = models_config[model_type]
            model_class = model_config.get("class")
            
            if not model_class:
                raise ConfigurationError(f"Missing 'class' in model configuration for '{model_type}'")
            
            # Resolve environment variables in parameters
            parameters = model_config.get("parameters", {})
            resolved_parameters = cls._resolve_env_variables(parameters)
            
            # Import and create model
            try:
                module_path, class_name = model_class.rsplit(".", 1)
                module = __import__(module_path, fromlist=[class_name])
                model_class_obj = getattr(module, class_name)
            except (ImportError, AttributeError) as e:
                raise ConfigurationError(f"Failed to import model class {model_class}: {str(e)}")
            
            # Create model instance
            try:
                model = model_class_obj(**resolved_parameters)
            except Exception as e:
                raise ModelError(f"Failed to instantiate model {model_class}: {str(e)}")
            
            # Cache the model instance
            cls._model_cache[cache_key] = model
            cls._logger.success("Created and cached generic model: {} ({})", model_type, type(model).__name__)
            return model
            
        except (ConfigurationError, ModelError):
            raise
        except Exception as e:
            cls._logger.error("Unexpected error creating generic model '{}': {}", model_type, e, exc_info=True)
            raise ModelError(f"Unexpected error creating generic model '{model_type}': {str(e)}")
    
    @classmethod
    def get_vision_model(cls, model_type: str) -> tuple[Any, str]:
        """Create a vision model for image analysis"""
        # Check cache first
        if model_type in cls._model_cache:
            cls._logger.info("Reusing cached vision model: {}", model_type)
            return cls._model_cache[model_type]
        
        try:
            cls._logger.info("Creating vision model: {}", model_type)
            
            config = cls._load_config("vision_models")
            vision_models_config = config.get("vision_models", {})
            
            # Use dedicated vision model configuration
            if model_type not in vision_models_config:
                available_models = list(vision_models_config.keys())
                raise ConfigurationError(f"Vision model '{model_type}' not found. Available vision models: {available_models}")
            
            model_config = vision_models_config[model_type]
            model_class = model_config.get("class")
            
            if not model_class:
                raise ConfigurationError(f"Missing 'class' in vision model configuration for '{model_type}'")
            
            # Resolve environment variables in parameters
            parameters = model_config.get("parameters", {})
            resolved_parameters = cls._resolve_env_variables(parameters)
            
            # Import and create model
            try:
                module_path, class_name = model_class.rsplit(".", 1)
                module = __import__(module_path, fromlist=[class_name])
                model_class_obj = getattr(module, class_name)
            except (ImportError, AttributeError) as e:
                raise ConfigurationError(f"Failed to import vision model class {model_class}: {str(e)}")
            
            # Create model instance
            try:
                model = model_class_obj(**resolved_parameters)
            except Exception as e:
                raise ModelError(f"Failed to instantiate vision model {model_class}: {str(e)}")
            
            # Get the actual model name for vision (usually same as deployment)
            model_name = resolved_parameters.get("azure_deployment", model_type)
            
            # Cache the model instance
            cls._model_cache[model_type] = (model, model_name)
            cls._logger.success("Created and cached vision model: {} ({})", model_type, type(model).__name__)
            return model, model_name
            
        except (ConfigurationError, ModelError):
            raise
        except Exception as e:
            cls._logger.error("Unexpected error creating vision model '{}': {}", model_type, e, exc_info=True)
            raise ModelError(f"Unexpected error creating vision model '{model_type}': {str(e)}")
    
    @classmethod
    def get_embedding_model(cls, model_type: str) -> tuple[Any, str]:
        """Create a generic embedding model and return (model, model_name)"""
        # Check cache first
        cache_key = f"embedding_{model_type}"
        if cache_key in cls._model_cache:
            cls._logger.info("Reusing cached embedding model: {}", model_type)
            return cls._model_cache[cache_key]
        
        try:
            cls._logger.info("Creating generic embedding model: {}", model_type)
            
            config = cls._load_config("embedding_models")
            embedding_models_config = config.get("embedding_models", {})
            
            if model_type not in embedding_models_config:
                available_models = list(embedding_models_config.keys())
                raise ConfigurationError(f"Embedding model '{model_type}' not found. Available embedding models: {available_models}")
            
            model_config = embedding_models_config[model_type]
            model_class = model_config.get("class")
            
            if not model_class:
                raise ConfigurationError(f"Missing 'class' in embedding model configuration for '{model_type}'")
            
            # Resolve environment variables in parameters
            parameters = model_config.get("parameters", {})
            resolved_parameters = cls._resolve_env_variables(parameters)
            
            # Extract model name from azure_deployment parameter
            model_name = resolved_parameters.get("azure_deployment")
            if not model_name:
                raise ConfigurationError(f"Missing 'azure_deployment' parameter in embedding model configuration for '{model_type}'")
            
            # Import and create model
            try:
                module_path, class_name = model_class.rsplit(".", 1)
                module = __import__(module_path, fromlist=[class_name])
                model_class_obj = getattr(module, class_name)
            except (ImportError, AttributeError) as e:
                raise ConfigurationError(f"Failed to import embedding model class {model_class}: {str(e)}")
            
            # Create model instance
            try:
                model = model_class_obj(**resolved_parameters)
            except Exception as e:
                raise ModelError(f"Failed to instantiate embedding model {model_class}: {str(e)}")
            
            # Cache the model instance
            cls._model_cache[cache_key] = (model, model_name)
            cls._logger.success("Created and cached generic embedding model: {} ({}) with model name: {}", model_type, type(model).__name__, model_name)
            return model, model_name
            
        except (ConfigurationError, ModelError):
            raise
        except Exception as e:
            cls._logger.error("Unexpected error creating generic embedding model '{}': {}", model_type, e, exc_info=True)
            raise ModelError(f"Unexpected error creating generic embedding model '{model_type}': {str(e)}")
    
    @classmethod
    def get_available_models(cls) -> Dict[str, list]:
        """Get list of available models, embedding models, and vision models"""
        try:
            models_config = cls._load_config("models")
            embedding_config = cls._load_config("embedding_models")
            vision_config = cls._load_config("vision_models")
            return {
                "models": list(models_config.get("models", {}).keys()),
                "embedding_models": list(embedding_config.get("embedding_models", {}).keys()),
                "vision_models": list(vision_config.get("vision_models", {}).keys())
            }
        except Exception as e:
            cls._logger.error("Failed to get available models: {}", e)
            return {"models": [], "embedding_models": [], "vision_models": []}