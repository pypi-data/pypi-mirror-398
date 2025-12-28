"""
FastAPI Service Module

This module provides the FastAPI service functionality.
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

# Now we can safely import other modules
import signal
import asyncio
import logging
from pathlib import Path
import uvicorn

from topaz_agent_kit.services.fastapi_app import create_app
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.core.exceptions import ConfigurationError


def main(project_dir: str, log_level: str | None = None, ui_dist: str | None = None, reload: bool = False) -> None:
    """Start FastAPI service."""
    logger = Logger("ServeFastAPI")
    logger.info("Starting FastAPI service")
    
    # Apply log level if specified
    if log_level:
        try:
            Logger.set_global_level_from_string(log_level)
            logger.info("Log level set to: {}", log_level)
        except Exception as e:
            logger.warning("Failed to set log level to {}: {}", log_level, e)
    
    logger.info("Using provided project directory: {}", project_dir)
    
    # Optional UI dist override via argument or env TOPAZ_UI_DIST_DIR
    ui_dist_dir = ui_dist or os.environ.get("TOPAZ_UI_DIST_DIR")
    app = create_app(project_dir, ui_dist_dir)
    logger.debug("FastAPI app created successfully")
    
    # Load pipeline.yml to get FastAPI URL
    try:
        import yaml
        from urllib.parse import urlparse
        pipeline_file = Path(project_dir) / "config" / "pipeline.yml"
        with open(pipeline_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        fastapi_url = config["servers"]["fastapi"]["url"]
        parsed_url = urlparse(fastapi_url)
        
        # Use configuration values
        server_host = parsed_url.hostname
        server_port = parsed_url.port
        
        # Validate required parameters
        if not server_host:
            raise ConfigurationError("FastAPI host must be specified in pipeline.yml")
        if not server_port:
            raise ConfigurationError("FastAPI port must be specified in pipeline.yml")
        
        # Warn if using localhost (won't be accessible from outside)
        if server_host in ("localhost", "127.0.0.1"):
            logger.warning("Host is set to '{}' - server will only be accessible locally. Use '0.0.0.0' for external access.", server_host)
        
        logger.info("Starting server on {}:{}", server_host, server_port)
        if server_host == "0.0.0.0":
            logger.info("Server bound to 0.0.0.0 - accessible from all network interfaces")
            logger.info("External access: Use http://<server-ip>:{} to access from other machines", server_port)
            logger.info("Local access: Use http://localhost:{} or http://127.0.0.1:{}", server_port, server_port)
        
    except Exception as e:
        logger.error("Failed to load FastAPI configuration: {}", e)
        raise ConfigurationError(f"Failed to load FastAPI configuration: {e}")
    
    # Suppress noisy shutdown errors and warnings
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    # Suppress asyncio cancellation errors during shutdown
    asyncio_logger = logging.getLogger("asyncio")
    asyncio_logger.setLevel(logging.CRITICAL)
    
    # Add a logging filter to suppress shutdown-related errors
    class ShutdownErrorFilter(logging.Filter):
        """Filter out shutdown-related error messages"""
        def filter(self, record):
            msg = record.getMessage() if hasattr(record, 'getMessage') else str(record.msg)
            # Suppress cancellation and shutdown errors
            suppress_keywords = [
                "CancelledError",
                "KeyboardInterrupt", 
                "WouldBlock",
                "lifespan",
                "Exception in ASGI application"
            ]
            return not any(keyword in msg for keyword in suppress_keywords)
    
    # Apply filter to uvicorn and starlette loggers
    shutdown_filter = ShutdownErrorFilter()
    logging.getLogger("uvicorn.error").addFilter(shutdown_filter)
    logging.getLogger("uvicorn").addFilter(shutdown_filter)
    logging.getLogger("starlette").addFilter(shutdown_filter)
    
    # Suppress "Invalid HTTP request received" warnings (usually from bots/proxies)
    class InvalidRequestFilter(logging.Filter):
        """Filter out invalid HTTP request warnings"""
        def filter(self, record):
            msg = record.getMessage() if hasattr(record, 'getMessage') else str(record.msg)
            # Suppress invalid HTTP request warnings
            if "Invalid HTTP request received" in msg:
                return False
            return True
    
    invalid_request_filter = InvalidRequestFilter()
    logging.getLogger("uvicorn.error").addFilter(invalid_request_filter)
    
    # Suppress tracebacks for shutdown-related exceptions
    original_excepthook = sys.excepthook
    
    def graceful_excepthook(exc_type, exc_value, exc_traceback):
        """Suppress tracebacks for shutdown-related exceptions"""
        # Suppress KeyboardInterrupt and CancelledError tracebacks
        if exc_type in (KeyboardInterrupt, SystemExit):
            return
        # Check if it's a CancelledError (from asyncio)
        if exc_type.__name__ == "CancelledError":
            return
        # For other exceptions, use the original handler
        original_excepthook(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = graceful_excepthook
    
    try:
        if reload:
            # For reload to work, we need to use import string instead of app object
            logger.info("Starting with hot reload enabled")
            uvicorn.run(
                "topaz_agent_kit.services.fastapi_app:create_app",
                host=server_host, 
                port=server_port, 
                reload=True,
                log_level="info",
                access_log=True  # Enable access logs to debug external access issues
            )
        else:
            config = uvicorn.Config(
                app,
                host=server_host,
                port=server_port,
                log_level="info",
                access_log=True  # Enable access logs to debug external access issues
            )
            server = uvicorn.Server(config)
            
            try:
                server.run()
            except (KeyboardInterrupt, SystemExit):
                logger.info("Shutdown requested, exiting gracefully...")
            except Exception as e:
                # Suppress cancellation errors during shutdown
                error_name = type(e).__name__
                if error_name not in ("CancelledError", "KeyboardInterrupt", "SystemExit"):
                    logger.error("Unexpected error: {}", e)
                    raise
                # For cancellation errors, just exit silently
                pass
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown requested, exiting gracefully...")
    except Exception as e:
        # Suppress shutdown-related errors
        error_name = type(e).__name__
        if error_name not in ("CancelledError", "KeyboardInterrupt", "SystemExit"):
            logger.error("Failed to start server: {}", e)
            raise


if __name__ == "__main__":  # pragma: no cover
    main()

