"""
Services Module

This module provides the services functionality for running unified_service.py.
"""

import os
import sys

# Set UTF-8 encoding for Windows compatibility (fixes charmap codec errors)
# This must be done before any other imports that might output Unicode characters
if sys.platform == "win32":
    # Set environment variable for subprocesses
    os.environ["PYTHONIOENCODING"] = "utf-8"
    # Reconfigure stdout/stderr to use UTF-8
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# CRITICAL: Suppress deprecation warnings BEFORE any imports
# This must be the very first thing in the file to catch warnings emitted during importlib bootstrap
import warnings

# Set default action for DeprecationWarnings to ignore BEFORE any imports
# This catches warnings emitted during importlib bootstrap (e.g., SWIG warnings)
warnings.simplefilter("ignore", DeprecationWarning)

# Additional specific suppressions (redundant but explicit for clarity)
# Suppress SWIG-related deprecation warnings (from MCP/C extensions like PyMuPDF)
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*SwigPy.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*swigvarlink.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*builtin type.*has no __module__ attribute.*")
# Suppress websockets.legacy deprecation warnings (from uvicorn)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="websockets.legacy")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="uvicorn.protocols.websockets.websockets_impl")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*websockets.legacy.*deprecated.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*websockets.server.WebSocketServerProtocol.*deprecated.*")

import signal
import asyncio
from pathlib import Path

from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.core.exceptions import ConfigurationError
from dotenv import load_dotenv


def main(project_dir: str, log_level: str | None = None) -> None:
    """Start unified service."""
    logger = Logger("ServeServices")
    logger.info("Starting services")
    
    # Apply log level if specified
    if log_level:
        try:
            Logger.set_global_level_from_string(log_level)
            logger.info("Log level set to: {}", log_level)
        except Exception as e:
            logger.warning("Failed to set log level to {}: {}", log_level, e)
    
    logger.info("Using provided project directory: {}", project_dir)
    
    # Validate that unified_service.py exists
    unified_service_file = Path(project_dir) / "services" / "unified_service.py"
    if not unified_service_file.exists():
        raise ConfigurationError(
            f"unified_service.py not found at {unified_service_file}. "
            f"Please generate services using: topaz-agent-kit generate {project_dir} --services"
        )
    
    # Load environment variables
    load_dotenv(Path(project_dir) / ".env")
    logger.debug("Loaded environment variables from: {}", Path(project_dir) / ".env")
    
    # Change to project directory
    original_cwd = Path.cwd()
    try:
        os.chdir(project_dir)
        logger.debug("Changed working directory to: {}", project_dir)
        
        # Add services directory to Python path for imports
        services_dir = Path(project_dir) / "services"
        if str(services_dir) not in sys.path:
            sys.path.insert(0, str(services_dir))
        
        # Add agents directory to Python path (unified_service expects this)
        agents_dir = Path(project_dir) / "agents"
        if str(agents_dir) not in sys.path:
            sys.path.append(str(agents_dir))
        
        # Import unified_service module
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "unified_service",
                unified_service_file
            )
            if spec is None or spec.loader is None:
                raise ConfigurationError(f"Failed to create module spec for {unified_service_file}")
            
            unified_service = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(unified_service)
            logger.debug("Successfully imported unified_service module")
        except Exception as e:
            logger.error("Failed to import unified_service: {}", e)
            raise ConfigurationError(f"Failed to import unified_service: {e}")
        
        # Verify start_all_agents function exists
        if not hasattr(unified_service, 'start_all_agents'):
            raise ConfigurationError(
                f"unified_service.py does not expose 'start_all_agents' function. "
                f"Please regenerate services using: topaz-agent-kit generate {project_dir} --services"
            )
        
        start_all_agents = unified_service.start_all_agents
        
        # Set up signal handler for graceful shutdown
        shutdown_requested = False
        
        def signal_handler(signum, frame):
            nonlocal shutdown_requested
            logger.info("Received signal {}, shutting down services...", signum)
            shutdown_requested = True
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("All services starting. Press Ctrl+C to stop all services.")
        
        try:
            # Run the async function
            asyncio.run(start_all_agents())
        except KeyboardInterrupt:
            logger.info("Shutting down services...")
            shutdown_requested = True
        except Exception as e:
            logger.error("Service execution failed: {}", e)
            raise
        
    finally:
        # Restore original working directory
        os.chdir(original_cwd)
        logger.debug("Restored working directory to: {}", original_cwd)
        
        # Clean up sys.path modifications
        if str(services_dir) in sys.path:
            sys.path.remove(str(services_dir))
        if str(agents_dir) in sys.path:
            sys.path.remove(str(agents_dir))


if __name__ == "__main__":  # pragma: no cover
    main()

