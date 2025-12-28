"""
Simple Exception Module for Topaz Agent Kit

Just 7 basic exception types that cover all our needs without over-engineering.
"""


class TopazAgentKitError(Exception):
    """Base exception class for Topaz Agent Kit."""
    pass


class ConfigurationError(TopazAgentKitError):
    """Any errors related to YAML, config files, settings, etc."""
    def __init__(self, message: str = "Configuration error"):
        self.message = message
        super().__init__(self.message)


class PipelineError(TopazAgentKitError):
    """Any errors related to pipeline execution, validation, etc."""
    def __init__(self, message: str = "Pipeline error"):
        self.message = message
        super().__init__(self.message)


class PipelineStoppedByUser(TopazAgentKitError):
    """Pipeline was stopped by user decision (not an error)"""
    def __init__(self, gate_id: str, reason: str):
        self.gate_id = gate_id
        self.reason = reason
        super().__init__(f"Pipeline stopped by user at gate {gate_id}: {reason}")


class AgentError(TopazAgentKitError):
    """Any errors related to agent creation, execution, etc."""
    def __init__(self, message: str = "Agent error"):
        self.message = message
        super().__init__(self.message)


class MCPError(TopazAgentKitError):
    """Any errors related to MCP (Model Context Protocol) integration."""
    def __init__(self, message: str = "MCP error"):
        self.message = message
        super().__init__(self.message)


class FrameworkError(TopazAgentKitError):
    """Any errors related to frameworks (ADK, Agno, LangGraph, CrewAI, OAK, SK)."""
    def __init__(self, message: str = "Framework error"):
        self.message = message
        super().__init__(self.message)


class ModelError(TopazAgentKitError):
    """Any errors related to model creation, configuration, requirements."""
    def __init__(self, message: str = "Model error"):
        self.message = message
        super().__init__(self.message)

class DatabaseError(TopazAgentKitError):
    """Any errors related to database creation, configuration, requirements."""
    def __init__(self, message: str = "Database error"):
        self.message = message
        super().__init__(self.message)

class FileError(TopazAgentKitError):
    """Any errors related to file creation, configuration, requirements."""
    def __init__(self, message: str = "File error"):
        self.message = message
        super().__init__(self.message)

class CommunicationError(TopazAgentKitError):
    """Any errors related to communication creation, configuration, requirements."""
    def __init__(self, message: str = "Communication error"):
        self.message = message
        super().__init__(self.message)

# Simple utility function for creating error context
def create_error_context(component: str, operation: str, **kwargs):
    """Create a simple error context dictionary."""
    context = {
        "component": component,
        "operation": operation
    }
    context.update(kwargs)
    return context 