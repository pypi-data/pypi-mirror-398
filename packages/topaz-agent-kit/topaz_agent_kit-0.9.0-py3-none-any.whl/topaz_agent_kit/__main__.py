"""
Topaz Agent Kit Main Entry Point

This module is executed when the package is run as a module:
    python -m topaz_agent_kit
    uv run topaz-agent-kit
"""

# Suppress deprecation warnings from external libraries BEFORE any imports
# This must be the very first thing to run, before importing anything
import warnings
import sys

# Set default action for DeprecationWarnings to ignore BEFORE any imports
# This catches warnings emitted during importlib bootstrap
warnings.simplefilter("ignore", DeprecationWarning)

# Suppress SWIG-related deprecation warnings (from MCP/C extensions like PyMuPDF)
# These occur during importlib bootstrap, so they must be suppressed immediately
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

# Now import and run the main CLI
from topaz_agent_kit.cli.main import main

if __name__ == "__main__":
    main()
