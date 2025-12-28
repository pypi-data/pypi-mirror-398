# CRITICAL: Suppress deprecation warnings BEFORE any imports
# This must be the very first thing in the file to catch warnings emitted during importlib bootstrap
import warnings

# Set default action for DeprecationWarnings to ignore BEFORE any imports
# This catches warnings emitted during importlib bootstrap (e.g., SWIG warnings)
warnings.simplefilter("ignore", DeprecationWarning)

# Additional specific suppressions (redundant but explicit for clarity)
# Suppress SWIG-related deprecation warnings (from MCP/C extensions like PyMuPDF)
# These must be suppressed first as they occur during importlib bootstrap
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*SwigPy.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*swigvarlink.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*builtin type.*has no __module__ attribute.*")

# Suppress websockets.legacy deprecation warnings (from uvicorn)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="websockets.legacy")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="uvicorn.protocols.websockets.websockets_impl")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*websockets.legacy.*deprecated.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*websockets.server.WebSocketServerProtocol.*deprecated.*")

# Suppress sqlite3 datetime adapter deprecation warnings (Python 3.12+)
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*datetime adapter.*deprecated.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlite3")

# Suppress litellm asyncio event loop deprecation warnings (Python 3.12+)
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*There is no current event loop.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="litellm.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*asyncio.get_event_loop.*")

# Suppress other library warnings
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic.*")
warnings.filterwarnings("ignore", message="Support for class-based.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*EXPERIMENTAL.*BaseAuthenticatedTool.*", category=UserWarning)

import logging
logging.getLogger("httpx").setLevel(logging.WARNING)

# Silence uvicorn and only let critical errors through
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.WARNING)

# Suppress agent_framework verbose logs (function execution details)
logging.getLogger("agent_framework").setLevel(logging.WARNING)

# Suppress OpenTelemetry and only let critical errors through
logging.getLogger("opentelemetry").setLevel(logging.ERROR)
logging.getLogger("opentelemetry.trace").setLevel(logging.ERROR)

# Suppress ADK authentication warnings (expected when auth is not configured)
logging.getLogger("google_adk.google.adk.tools.base_authenticated_tool").setLevel(logging.ERROR)

# Suppress semantic_kernel verbose logs (function execution details, usage info, etc.)
logging.getLogger("semantic_kernel").setLevel(logging.WARNING)
logging.getLogger("semantic_kernel.functions").setLevel(logging.WARNING)
logging.getLogger("semantic_kernel.connectors").setLevel(logging.WARNING)
logging.getLogger("semantic_kernel.kernel").setLevel(logging.WARNING)

from .core.ag_ui_event_emitter import AGUIEventEmitter
from .core.pipeline_loader import PipelineLoader
from .core.pipeline_runner import PipelineRunner
from .core.configuration_engine import ConfigurationEngine, ConfigurationResult
from .core.prompt_intelligence_engine import PromptIntelligenceEngine
from .agents.base import BaseAgent
from .agents.agent_factory import AgentFactory
from .orchestration.orchestrator import Orchestrator
from .utils.file_upload import FileUploadHandler, FileUploadError, FileValidator, FileMetadata

__version__ = "0.3.0"

__all__ = [
    "AGUIEventEmitter",
    "PipelineLoader",
    "PipelineRunner",
    "ConfigurationEngine",
    "ConfigurationResult",
    "PromptIntelligenceEngine",
    "BaseAgent",
    "AgentFactory",
    "Orchestrator",
    "FileUploadHandler",
    "FileUploadError",
    "FileValidator",
    "FileMetadata",
    "__version__",
]


