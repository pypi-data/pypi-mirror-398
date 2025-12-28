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

from topaz_agent_kit.mcp.framework import McpServerApp

from topaz_agent_kit.mcp.toolkits.browser import BrowserMCPTools
from topaz_agent_kit.mcp.toolkits.doc_rag import DocRAGMCPTools
from topaz_agent_kit.mcp.toolkits.image_rag import ImageRAGMCPTools
from topaz_agent_kit.mcp.toolkits.doc_extract import DocExtractMCPTools
from topaz_agent_kit.mcp.toolkits.common import CommonMCPTools
# from topaz_agent_kit.mcp.toolkits.insurance import InsuranceMCPTools
from topaz_agent_kit.mcp.toolkits.math import MathMCPTools
from topaz_agent_kit.mcp.toolkits.serper_api import SerperApiMCPTools
from topaz_agent_kit.mcp.toolkits.sec_api import SecApiMCPTools
from topaz_agent_kit.mcp.toolkits.email import EmailMCPTools
from topaz_agent_kit.mcp.toolkits.flights import FlightsMCPTools
from topaz_agent_kit.mcp.toolkits.hotels import HotelsMCPTools
from topaz_agent_kit.mcp.toolkits.activities import ActivitiesMCPTools
from topaz_agent_kit.mcp.toolkits.sqlite import SQLiteMCPTools
from topaz_agent_kit.mcp.toolkits.python import PythonMCPTools
from topaz_agent_kit.mcp.toolkits.filesystem import FilesystemMCPTools

from topaz_agent_kit.models.model_factory import ModelFactory
from topaz_agent_kit.core.exceptions import ConfigurationError
from topaz_agent_kit.utils.logger import Logger

logger = Logger("MCPServer")

def main(host: str | None = None, port: int | None = None, model: str | None = None, transport: str | None = None, embedding_model: str | None = None, db_path: str | None = None, server_name: str | None = None) -> None:

    server_display_name = f"'{server_name}'" if server_name else "unnamed"
    logger.info("Starting MCP server {}", server_display_name)
    
    # Validate required parameters - fail fast
    missing_params = []
    if not host:
        missing_params.append("host")
    if not port:
        missing_params.append("port")
    if not model:
        missing_params.append("model")
    if not transport:
        missing_params.append("transport")
    
    if missing_params:
        raise ConfigurationError(f"MCP server missing required parameters: {', '.join(missing_params)}")
    
    logger.info("MCP server {} configuration: host={}, port={}, model={}, transport={}, db_path={}", server_display_name, host, port, model, transport, db_path)
    
    app = McpServerApp(name="topaz-agent-kit-mcp", host=host, port=port)
    # Initialize model for toolkits using framework-agnostic approach
    try:
        logger.info("Creating framework-agnostic model for MCP toolkits: {}", model)
        llm = ModelFactory.get_model(model)  # Use generic ModelFactory
        logger.success("Framework-agnostic model creation successful: {}", model)
    except Exception as e:
        logger.error("Framework-agnostic model creation failed: {}", e)
        raise ConfigurationError(f"Failed to create framework-agnostic model '{model}' for MCP toolkits: {e}")

    register_toolkits(app, llm, db_path, server_display_name, embedding_model)

    logger.success("Starting MCP server {} with transport={}...", server_display_name, transport)
    
    # Disable uvicorn HTTP access logs for cleaner output
    import logging
    from contextlib import redirect_stderr, redirect_stdout
    
    # Redirect uvicorn's output to /dev/null to completely silence HTTP logs
    # Use UTF-8 encoding for devnull on Windows
    devnull_mode = 'w'
    if sys.platform == "win32":
        devnull_mode = 'w'
    try:
        with open(os.devnull, devnull_mode, encoding='utf-8') as devnull:
            with redirect_stderr(devnull), redirect_stdout(devnull):
                app.run(transport=transport)
    except Exception as e:
        # If redirect fails, try without encoding (for older Python versions)
        with open(os.devnull, 'w') as devnull:
            with redirect_stderr(devnull), redirect_stdout(devnull):
                app.run(transport=transport)

def register_toolkits(app: McpServerApp, llm, db_path=None, server_name=None, embedding_model=None) -> None:
    logger.info("Registering BrowserMCPTools toolkit for {}", server_name)
    app.register_toolkit(BrowserMCPTools())

    # Register DocRAG and ImageRAG if db_path is provided
    if db_path:
        logger.info("Registering DocRAGMCPTools toolkit for {}", server_name)
        app.register_toolkit(DocRAGMCPTools(db_path=db_path, embedding_model=embedding_model))
        logger.info("Registering ImageRAGMCPTools toolkit for {}", server_name)
        app.register_toolkit(ImageRAGMCPTools(db_path=db_path, embedding_model=embedding_model))
    else:
        logger.warning("Skipping DocRAGMCPTools toolkit for {} - not a doc_rag server", server_name)
        logger.warning("Skipping ImageRAGMCPTools toolkit for {} - not an image_rag server", server_name)

    logger.info("Registering CommonMCPTools toolkit for {}", server_name)
    app.register_toolkit(CommonMCPTools())

    # logger.info("Registering InsuranceMCPTools toolkit for {}", server_name)
    # app.register_toolkit(InsuranceMCPTools())

    # Math toolkit needs llm
    logger.info("Registering MathMCPTools toolkit for {}", server_name)
    app.register_toolkit(MathMCPTools(llm=llm))

    logger.info("Registering SerperApiMCPTools toolkit for {}", server_name)
    app.register_toolkit(SerperApiMCPTools())
    
    logger.info("Registering SecApiMCPTools toolkit for {}", server_name)
    app.register_toolkit(SecApiMCPTools())

    logger.info("Registering EmailMCPTools toolkit for {}", server_name)
    app.register_toolkit(EmailMCPTools())

    # # NEW: Register DocExtract toolkit (no db_path needed - transient extraction)
    logger.info("Registering DocExtractMCPTools toolkit for {}", server_name)
    app.register_toolkit(DocExtractMCPTools(llm=llm))

    # Travel toolkits
    logger.info("Registering FlightsMCPTools toolkit for {}", server_name)
    app.register_toolkit(FlightsMCPTools())
    logger.info("Registering HotelsMCPTools toolkit for {}", server_name)
    app.register_toolkit(HotelsMCPTools())
    logger.info("Registering ActivitiesMCPTools toolkit for {}", server_name)
    app.register_toolkit(ActivitiesMCPTools())

    logger.info("Registering SQLiteMCPTools toolkit for {}", server_name)
    app.register_toolkit(SQLiteMCPTools())

    logger.info("Registering PythonMCPTools toolkit for {}", server_name)
    app.register_toolkit(PythonMCPTools())

    logger.info("Registering FilesystemMCPTools toolkit for {}", server_name)
    app.register_toolkit(FilesystemMCPTools())

if __name__ == "__main__":  # pragma: no cover
    main()

