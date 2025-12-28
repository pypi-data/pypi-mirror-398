"""
Centralized class naming utilities for agent and service generation.
Provides consistent naming conventions across all generators.
"""

from typing import Tuple


class AgentClassNaming:
    """
    Centralized class naming utilities for agents and services.
    Ensures consistent naming conventions across all generators.
    """
    
    # Framework mappings for class name generation
    # Format: (type_prefix, framework_display_name)
    FRAMEWORK_MAPPINGS = {
        "agno": ("Agno", "Agno"),
        "langgraph": ("LangGraph", "Lang Graph"),
        "crewai": ("CrewAI", "CrewAI"),
        "adk": ("ADK", "ADK"),
        "oak": ("OAK", "OAK"),
        "sk": ("SK", "SK"),
        "maf": ("MAF", "MAF")
    }
    
    @classmethod
    def get_type_prefix(cls, agent_type: str) -> str:
        """
        Get the type prefix for class name generation.
        
        Args:
            agent_type: Agent type (agno, langgraph, crewai, adk, oak, sk, maf)
            
        Returns:
            Type prefix for class naming
            
        Raises:
            ValueError: If agent_type is not supported
        """
        if agent_type not in cls.FRAMEWORK_MAPPINGS:
            raise ValueError(f"Unsupported agent type: '{agent_type}'. Supported types: {list(cls.FRAMEWORK_MAPPINGS.keys())}")
        
        type_prefix, _ = cls.FRAMEWORK_MAPPINGS[agent_type]
        return type_prefix
    
    @classmethod
    def get_framework_info(cls, agent_type: str) -> Tuple[str, str]:
        """
        Get full framework information for agent generation.
        
        Args:
            agent_type: Agent type
            
        Returns:
            Tuple of (type_prefix, framework_display_name)
            
        Raises:
            ValueError: If agent_type is not supported
        """
        if agent_type not in cls.FRAMEWORK_MAPPINGS:
            raise ValueError(f"Unsupported agent type: '{agent_type}'. Supported types: {list(cls.FRAMEWORK_MAPPINGS.keys())}")
        
        return cls.FRAMEWORK_MAPPINGS[agent_type]
    
    @classmethod
    def generate_class_name(cls, agent_id: str) -> str:
        """
        Generate class name for agent (without framework prefix).
        
        Args:
            agent_id: Agent ID from configuration
            
        Returns:
            Generated class name (e.g., "ReplyContextWizardAgent")
            
        Examples:
            >>> AgentClassNaming.generate_class_name("reply_context_wizard")
            "ReplyContextWizardAgent"
            >>> AgentClassNaming.generate_class_name("reply_draft_wizard") 
            "ReplyDraftWizardAgent"
            >>> AgentClassNaming.generate_class_name("research_analyst")
            "ResearchAnalystAgent"
        """
        # Convert agent_id to suitable format
        # Examples: "reply_context_wizard" -> "ReplyContextWizard", "research_analyst" -> "ResearchAnalyst"
        formatted_agent_id = agent_id.title().replace('_', '')
        
        return f"{formatted_agent_id}Agent"
    
    @classmethod
    def generate_module_name(cls, agent_id: str) -> str:
        """
        Generate module name for agent file (without framework prefix).
        
        Args:
            agent_id: Agent ID from configuration
            
        Returns:
            Generated module name (e.g., "reply_context_wizard_agent")
            
        Examples:
            >>> AgentClassNaming.generate_module_name("reply_context_wizard")
            "reply_context_wizard_agent"
            >>> AgentClassNaming.generate_module_name("reply_draft_wizard")
            "reply_draft_wizard_agent"
        """
        return f"{agent_id}_agent"
    
    @classmethod
    def get_import_statement(cls, agent_id: str) -> str:
        """
        Generate import statement for agent (without framework prefix).
        
        Args:
            agent_id: Agent ID from configuration
            
        Returns:
            Import statement (e.g., "from agents.reply_context_wizard_agent import ReplyContextWizardAgent")
            
        Examples:
            >>> AgentClassNaming.get_import_statement("reply_context_wizard")
            "from agents.reply_context_wizard_agent import ReplyContextWizardAgent"
        """
        module_name = cls.generate_module_name(agent_id)
        class_name = cls.generate_class_name(agent_id)
        return f"from agents.{module_name} import {class_name}"
    
    @classmethod
    def get_supported_types(cls) -> list[str]:
        """
        Get list of supported agent types.
        
        Returns:
            List of supported agent type strings
        """
        return list(cls.FRAMEWORK_MAPPINGS.keys())
    
    @classmethod
    def validate_agent_type(cls, agent_type: str) -> None:
        """
        Validate that agent_type is supported.
        
        Args:
            agent_type: Agent type to validate
            
        Raises:
            ValueError: If agent_type is not supported
        """
        if agent_type not in cls.FRAMEWORK_MAPPINGS:
            supported = cls.get_supported_types()
            raise ValueError(f"Unsupported agent type: '{agent_type}'. Supported types: {supported}")


# Convenience functions for backward compatibility
def get_type_prefix(agent_type: str) -> str:
    """Convenience function for AgentClassNaming.get_type_prefix()"""
    return AgentClassNaming.get_type_prefix(agent_type)


def generate_class_name(agent_id: str) -> str:
    """Convenience function for AgentClassNaming.generate_class_name()"""
    return AgentClassNaming.generate_class_name(agent_id)


def generate_module_name(agent_id: str) -> str:
    """Convenience function for AgentClassNaming.generate_module_name()"""
    return AgentClassNaming.generate_module_name(agent_id)


def get_import_statement(agent_id: str) -> str:
    """Convenience function for AgentClassNaming.get_import_statement()"""
    return AgentClassNaming.get_import_statement(agent_id)