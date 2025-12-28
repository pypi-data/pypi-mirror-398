"""
Environment variable substitution utilities for YAML configuration files.
Provides generic ${VAR_NAME} substitution across all configuration files.
"""

import os
from typing import Any, Dict, Union
from topaz_agent_kit.utils.logger import Logger


class EnvSubstitution:
    """Utility class for environment variable substitution in configuration data"""
    
    def __init__(self):
        self.logger = Logger("EnvSubstitution")
    
    def substitute_env_vars(self, data: Any) -> Any:
        """
        Recursively substitute environment variables in configuration data.
        
        Args:
            data: Configuration data (dict, list, str, or other types)
            
        Returns:
            Data with environment variables substituted
        """
        if isinstance(data, dict):
            return {key: self.substitute_env_vars(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.substitute_env_vars(item) for item in data]
        elif isinstance(data, str):
            return self._substitute_string(data)
        else:
            return data
    
    def _substitute_string(self, text: str) -> str:
        """
        Substitute environment variables in a string.
        
        Pattern: ${VAR_NAME} -> os.getenv('VAR_NAME')
        Skips Jinja2 template syntax ({{ and {% patterns) to avoid false warnings.
        
        Args:
            text: String that may contain ${VAR_NAME} patterns
            
        Returns:
            String with environment variables substituted
        """
        if not isinstance(text, str) or '${' not in text:
            return text
        
        # Skip entire string if it contains Jinja2 template syntax
        # This is more efficient and avoids false positives
        if '{{' in text or '{%' in text:
            # This string likely contains Jinja2 templates, skip environment variable substitution
            return text
        
        # Environment variables are already loaded by Orchestrator
        result = text
        start = 0
        
        while True:
            # Find next ${ pattern
            start_idx = result.find('${', start)
            if start_idx == -1:
                break
            
            # Find matching }
            end_idx = result.find('}', start_idx)
            if end_idx == -1:
                # Malformed pattern, leave as-is
                self.logger.warning("Malformed environment variable pattern in: {}", text)
                break
            
            # Extract variable name
            var_name = result[start_idx + 2:end_idx]
            
            # Get environment variable value
            env_value = os.getenv(var_name)
            
            if env_value is None:
                self.logger.warning("Environment variable '{}' not found, leaving as-is", var_name)
                # Leave the original pattern if env var not found
                start = end_idx + 1
                continue
            
            # Replace the pattern with the environment variable value
            result = result[:start_idx] + env_value + result[end_idx + 1:]
            
            # Continue from after the replacement
            start = start_idx + len(env_value)
        
        return result
    
    def substitute_in_yaml_data(self, yaml_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convenience method to substitute environment variables in YAML data.
        
        Args:
            yaml_data: Parsed YAML data as dictionary
            
        Returns:
            YAML data with environment variables substituted
        """
        self.logger.debug("Substituting environment variables in YAML data")
        return self.substitute_env_vars(yaml_data)


# Global instance for easy access
env_substitution = EnvSubstitution()