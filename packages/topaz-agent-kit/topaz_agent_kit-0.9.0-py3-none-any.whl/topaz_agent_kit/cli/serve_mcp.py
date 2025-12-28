"""
MCP Service Module

This module provides the MCP service functionality.
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

import warnings

# Suppress deprecation warnings from external libraries EARLY - before any imports
# This must be done before importing any third-party libraries that might trigger warnings
# Suppress litellm asyncio event loop deprecation warnings (Python 3.12+)
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*There is no current event loop.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="litellm.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*asyncio.get_event_loop.*")

import signal
import threading
import time
from pathlib import Path

from topaz_agent_kit.mcp.mcp_server import main as mcp_main
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.core.exceptions import ConfigurationError
from dotenv import load_dotenv


def main(project_dir: str, name: str | None = None, log_level: str | None = None) -> None:
    """Start MCP service."""
    logger = Logger("ServeMCP")
    logger.info("Starting MCP service")
    
    # Apply log level if specified
    if log_level:
        try:
            Logger.set_global_level_from_string(log_level)
            logger.info("Log level set to: {}", log_level)
        except Exception as e:
            logger.warning("Failed to set log level to {}: {}", log_level, e)
    
    logger.info("Using provided projects's directory: {}", project_dir)
    
    # Load environment variables once at the top level
    load_dotenv(Path(project_dir) / ".env")
    logger.debug("Loaded environment variables from: {}", Path(project_dir) / ".env")

    # Load pipeline.yml to get MCP servers
    try:
        import yaml
        from urllib.parse import urlparse
        pipeline_file = Path(project_dir) / "config" / "pipeline.yml"
        with open(pipeline_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        mcp_servers = config["servers"]["mcp"]
        
        # Filter by --name if provided
        if name:
            mcp_servers = [s for s in mcp_servers if s["name"] == name]
            if not mcp_servers:
                available_names = [s["name"] for s in config["servers"]["mcp"]]
                raise ConfigurationError(f"MCP server '{name}' not found. Available servers: {available_names}")
            logger.info("Starting specific MCP server: {}", name)
        
        # Start all servers in parallel threads
        server_threads = []
        
        for server in mcp_servers:
            # Parse URL from configuration
            parsed_url = urlparse(server["url"])
            server_host = parsed_url.hostname
            server_port = parsed_url.port
            
            # Validate configuration
            if not server_host or not server_port:
                raise ConfigurationError(f"MCP server '{server['name']}' missing host/port: host={server_host}, port={server_port}")
            
            logger.info("Starting MCP server '{}' on {}:{}", server["name"], server_host, server_port)
            
            # Start server in a separate thread
            def start_server(server_config):
                # Ensure UTF-8 encoding in thread (Windows compatibility)
                if sys.platform == "win32":
                    os.environ["PYTHONIOENCODING"] = "utf-8"
                    if hasattr(sys.stdout, "reconfigure"):
                        try:
                            sys.stdout.reconfigure(encoding="utf-8")
                        except Exception:
                            pass  # Ignore if already configured
                    if hasattr(sys.stderr, "reconfigure"):
                        try:
                            sys.stderr.reconfigure(encoding="utf-8")
                        except Exception:
                            pass  # Ignore if already configured
                try:
                    mcp_main(host=server_config["host"], port=server_config["port"], model=server_config["model"], transport=server_config["transport"], embedding_model=server_config.get("embedding_model"), db_path=server_config.get("db_path"), server_name=server_config["name"])
                except Exception as e:
                    logger.error("MCP server '{}' failed: {}", server_config["name"], e)
            
            # Capture server configuration to avoid closure issues
            server_config = {
                "name": server["name"],
                "host": server_host,
                "port": server_port,
                "model": server["model"],
                "transport": server["transport"],
                "embedding_model": server.get("embedding_model"),
                "db_path": server.get("db_path")
            }
            
            thread = threading.Thread(target=start_server, args=(server_config,), name=f"MCP-{server['name']}")
            thread.daemon = True
            thread.start()
            server_threads.append(thread)
        
        # Set up signal handler for graceful shutdown
        shutdown_requested = threading.Event()
        
        def signal_handler(signum, frame):
            logger.info("Received signal {}, shutting down MCP servers...", signum)
            shutdown_requested.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Wait for all servers to start
        logger.info("All MCP servers started. Press Ctrl+C to stop all servers.")
        try:
            # Keep main thread alive and monitor server threads
            while not shutdown_requested.is_set():
                # Check if any server threads have died
                alive_threads = [t for t in server_threads if t.is_alive()]
                if len(alive_threads) == 0:
                    logger.warning("All MCP server threads have died")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down MCP servers...")
            shutdown_requested.set()
        
        # Graceful shutdown - wait for threads to finish
        if shutdown_requested.is_set():
            logger.info("Shutting down MCP servers...")
            # HTTP servers don't have graceful shutdown, so we just wait briefly
            time.sleep(0.5)
            logger.info("All MCP servers shut down")
        
    except Exception as e:
        logger.error("Failed to load MCP configuration: {}", e)
        raise ConfigurationError(f"Failed to load MCP configuration: {e}")


if __name__ == "__main__":  # pragma: no cover
    main()

