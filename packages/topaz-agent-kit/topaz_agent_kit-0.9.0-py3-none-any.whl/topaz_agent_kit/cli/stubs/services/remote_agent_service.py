# Single Protocol Service Template
SINGLE_PROTOCOL_SERVICE_TEMPLATE = """
from pathlib import Path
import sys
from topaz_agent_kit.services.base_agent_service import BaseAgentService

# Add agents directory to Python path for imports
sys.path.append(str(Path(__file__).resolve().parents[1] / "agents"))
from {agent_module_path} import {class_name}

# Create service instance
service = BaseAgentService(
    agent_id="{agent_id}",
    agent_class={class_name},
    project_path=Path(__file__).resolve().parents[1]
)

if __name__ == "__main__":
    # Start A2A service
    import asyncio
    async def start_service():
        await service.start_a2a_server(port={port}, path='/{agent_id}')
    
    asyncio.run(start_service())
"""

# Multi Protocol Service Template
MULTI_PROTOCOL_SERVICE_TEMPLATE = '''
from pathlib import Path
import sys
import asyncio
from topaz_agent_kit.services.base_agent_service import BaseAgentService

# Add agents directory to Python path for imports
sys.path.append(str(Path(__file__).resolve().parents[1] / "agents"))
from {agent_module_path} import {class_name}

# Create service instance
service = BaseAgentService(
    agent_id="{agent_id}",
    agent_class={class_name},
    project_path=Path(__file__).resolve().parents[1]
)

if __name__ == "__main__":
    async def start_all_protocols():
        """Start all supported protocols concurrently"""
        await asyncio.gather(
{protocol_startup_code}
        )
    
    # Start all protocols
    asyncio.run(start_all_protocols())
'''

# Pipeline Service Template (for running all agents in a pipeline)
# Individual Service Template (for single agent services)
INDIVIDUAL_SERVICE_TEMPLATE = '''
from pathlib import Path
import sys
import asyncio
from topaz_agent_kit.services.base_agent_service import BaseAgentService

# Add agents directory to Python path for imports
sys.path.append(str(Path(__file__).resolve().parents[1] / "agents"))

{agent_import}

# Create service instance
{service_instance}

async def start_{agent_id}_service():
    """Start {agent_id} agent service"""
    await asyncio.gather(
{agent_startup_code}
    )

if __name__ == "__main__":
    # Start agent
    asyncio.run(start_{agent_id}_service())
'''

PIPELINE_SERVICE_TEMPLATE = '''
from pathlib import Path
import sys
import asyncio
from topaz_agent_kit.services.base_agent_service import BaseAgentService

# Add agents directory to Python path for imports
sys.path.append(str(Path(__file__).resolve().parents[1] / "agents"))
# Add services directory to Python path for imports (works for both direct execution and module execution)
sys.path.insert(0, str(Path(__file__).resolve().parent))

{agent_imports}

async def start_{pipeline_id}_services():
    """Start all {pipeline_id} agent services concurrently"""
    await asyncio.gather(
{agent_startup_code}
    )

if __name__ == "__main__":
    # Start all agents
    asyncio.run(start_{pipeline_id}_services())
'''

# Unified Service Template (for running all agents together)
UNIFIED_SERVICE_TEMPLATE = '''
from pathlib import Path
import sys
import asyncio
from topaz_agent_kit.services.base_agent_service import BaseAgentService

# Add agents directory to Python path for imports
sys.path.append(str(Path(__file__).resolve().parents[1] / "agents"))
# Add services directory to Python path for imports (works for both direct execution and module execution)
sys.path.insert(0, str(Path(__file__).resolve().parent))

{agent_imports}

# Create service instances
{service_instances}

async def start_all_agents():
    """Start all agent services concurrently"""
    await asyncio.gather(
{agent_startup_code}
    )

if __name__ == "__main__":
    # Start all agents
    asyncio.run(start_all_agents())
'''

# Unified A2A Server Template (for multiple agents sharing the same A2A port)
UNIFIED_A2A_SERVER_TEMPLATE = '''
from pathlib import Path
import sys
import asyncio
import uvicorn
import logging
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse

# Add agents directory to Python path for imports
sys.path.append(str(Path(__file__).resolve().parents[1] / "agents"))
# Add services directory to Python path for imports (works for both direct execution and module execution)
sys.path.insert(0, str(Path(__file__).resolve().parent))

{service_imports}

async def start_unified_a2a_server():
    """Start unified A2A server on port {a2a_port} with all agents mounted at their paths"""
    from topaz_agent_kit.utils.logger import Logger
    logger = Logger("UnifiedA2AServer")
    
    agent_count = len({agent_list})
    logger.info("Starting unified A2A server on 127.0.0.1:{a2a_port} with {agent_count} agents")
    
    # Build A2A apps for each agent
{app_build_code}
    
    # Create health check endpoint
    async def health_check(request):
        return JSONResponse({{
            "status": "ok",
            "service": "{pipeline_id}_unified",
            "agents": {agent_list}
        }})
    
    # Create unified Starlette app with all agents mounted at their paths
    unified_app = Starlette(routes=[
{mount_routes}
        Route("/", health_check, methods=["GET"]),
    ])
    
    # Disable uvicorn logging
    logging.getLogger("uvicorn").setLevel(logging.CRITICAL)
    logging.getLogger("uvicorn.error").setLevel(logging.CRITICAL)
    logging.getLogger("uvicorn.access").setLevel(logging.CRITICAL)
    logging.getLogger("uvicorn.asgi").setLevel(logging.CRITICAL)
    
    # Get host from first service
    host, _ = {first_service_name}.a2a_service.get_host_port()
    
    logger.info("Unified A2A server ready on {}:{}", host, {a2a_port})
    
    config = uvicorn.Config(
        unified_app,
        host=host,
        port={a2a_port},
        log_level="critical",
        log_config=None,
        access_log=False
    )
    server = uvicorn.Server(config)
    logger.info("Unified A2A server listening on {}:{}", host, {a2a_port})
    await server.serve()
'''
