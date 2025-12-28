"""
Base A2A service class for remote agent services
Supports official A2A SDK server implementation
"""

import json
from typing import Any, Dict, Type
from pathlib import Path
from urllib.parse import urlparse
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.utils import new_agent_text_message
from a2a.types import AgentCard, AgentCapabilities, AgentSkill

from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.json_utils import JSONUtils
from topaz_agent_kit.core.exceptions import ConfigurationError


class TopazAgentExecutor(AgentExecutor):
    """AgentExecutor wrapper for Topaz agents"""
    
    def __init__(self, agent_id: str, agent_class: Type, project_path: Path, agent_config: Dict, logger: Logger):
        self.agent_id = agent_id
        self.agent_class = agent_class
        self.project_path = project_path
        self.agent_config = agent_config
        self.logger = logger
        self.model = agent_config["model"]
        self.agent_instance = None
    
    async def execute(self, context: RequestContext, event_queue: EventQueue):
        """Execute the agent with proper A2A context handling"""
        try:
            # Initialize agent if not already done
            if self.agent_instance is None:
                self.agent_instance = self.agent_class(self.agent_id, agent_config=self.agent_config)
            
            # Extract content from A2A context
            content = {}
            if hasattr(context, 'message') and context.message:
                self.logger.debug("A2A message has {} parts", len(context.message.parts) if hasattr(context.message, 'parts') and context.message.parts else 0)
                if hasattr(context.message, 'parts') and context.message.parts:
                    # Extract text from message parts and try to parse as JSON
                    text_parts = []
                    for part in context.message.parts:
                        if hasattr(part, 'root') and hasattr(part.root, 'text'):
                            text_parts.append(part.root.text)
                    
                    combined_text = " ".join(text_parts)
                    self.logger.debug("A2A combined text: {}...", combined_text[:100])
                    
                    # Use JSONUtils for robust JSON parsing with automatic fixes
                    parsed_content = JSONUtils.parse_json_from_text(combined_text, expect_json=False)
                    self.logger.debug("A2A parsed content using JSONUtils: {}", parsed_content)
                    
                    # JSONUtils returns {"content": text} for plain text, or actual dict for JSON
                    if isinstance(parsed_content, dict):
                        if 'content' in parsed_content and len(parsed_content) == 1:
                            # Plain text wrapped in content structure - use original text
                            content = {"text": combined_text}
                        else:
                            # Actual JSON content - use parsed content
                            content = parsed_content
                    else:
                        # Fallback for unexpected types
                        content = {"text": str(parsed_content)}
                elif hasattr(context.message, 'content'):
                    content = context.message.content
                    self.logger.info("A2A direct content: {}", content)
            
            self.logger.debug("A2A final extracted content: {}", content)
            
            # Create execution context
            exec_context = {
                "model": self.model,
                "agent_config": self.agent_config,
                "project_dir": str(self.project_path),
                **content  # Include content in context
            }
            
            # Add upstream context if present in content
            if isinstance(content, dict) and "context" in content:
                context_data = content["context"]
                if isinstance(context_data, dict):
                    exec_context.update(context_data)
                    self.logger.debug("Added context data to execution context: {} keys", len(context_data))
            
            # Initialize the agent
            await self.agent_instance.initialize(exec_context)
            
            # Execute agent
            if hasattr(self.agent_instance, "execute"):
                result = await self.agent_instance.execute(exec_context)
            else:
                result = {"error": "Agent has no execute method"}
            
            # Preserve full result structure (including agent_inputs) by serializing as JSON
            # The A2A client will parse this back to extract agent_inputs
            if isinstance(result, dict):
                # Serialize the full result dict as JSON to preserve agent_inputs
                result_json = json.dumps(result)
                await event_queue.enqueue_event(new_agent_text_message(result_json))
            else:
                # For non-dict results, convert to string
                await event_queue.enqueue_event(new_agent_text_message(str(result)))
            
        except Exception as e:
            self.logger.error("Agent execution failed: {}", e)
            # Check if result contains agent_inputs (from base_agent error handling)
            # If so, include it in the error result so instructions tab can still show
            error_result = {"error": str(e), "agent_id": self.agent_id}
            # Try to get agent_inputs from the exception if it was set
            if hasattr(e, "agent_inputs"):
                error_result["agent_inputs"] = e.agent_inputs
            # Send error as structured JSON so client can detect it
            error_json = json.dumps(error_result)
            await event_queue.enqueue_event(new_agent_text_message(error_json))
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        """Cancel agent execution"""
        self.logger.warning("Agent cancellation not supported")
        raise Exception("Cancel not supported")


class BaseA2AService:
    """Base class for A2A protocol remote agent services"""
    
    def __init__(self, agent_id: str, agent_class: Type, project_path: str | Path, agent_config: Dict, logger: Logger):
        """
        Initialize the A2A service
        
        Args:
            agent_id: ID of the agent this service represents
            agent_class: The agent class to instantiate
            project_path: Path to the project directory
            agent_config: Pre-loaded agent configuration
            logger: Shared logger instance
        """
        self.agent_id = agent_id
        self.agent_class = agent_class
        self.project_path = Path(project_path)
        self.logger = logger
        self.agent_config = agent_config
        
        # Validate model configuration
        if "model" not in agent_config:
            raise ConfigurationError(f"Agent '{agent_id}' has no model configured")
        self.model = agent_config["model"]
        
        # Get the A2A URL from remote configuration
        remote_config = agent_config.get("remote", {})
        if not remote_config:
            raise ConfigurationError(f"Agent '{agent_id}' has no remote configuration")
        if "url" not in remote_config:
            raise ConfigurationError(f"Agent '{agent_id}' has no URL configured in remote.url")
        self.remote_url = remote_config["url"]
        
        # Create A2A server components
        self.agent_card = self._create_agent_card()
        self.agent_executor = TopazAgentExecutor(agent_id, agent_class, self.project_path, agent_config, logger)
        self.task_store = InMemoryTaskStore()
        self.request_handler = DefaultRequestHandler(
            agent_executor=self.agent_executor,
            task_store=self.task_store
        )
        self.a2a_app = A2AStarletteApplication(
            http_handler=self.request_handler,
            agent_card=self.agent_card
        )
    
    
    def _create_agent_card(self) -> AgentCard:
        """Create AgentCard for A2A service"""
        # Create a skill for this agent
        skill = AgentSkill(
            id=f"{self.agent_id}_skill",
            name=f"{self.agent_id.title()} Agent",
            description=f"Agent service for {self.agent_id}",
            tags=[self.agent_id, "agent", "topaz"],
            examples=[f"Execute {self.agent_id}", f"Run {self.agent_id}"]
        )
        
        return AgentCard(
            name=self.agent_id,
            description=f"Agent service for {self.agent_id}",
            url=self.remote_url,
            version="1.0.0",
            capabilities=AgentCapabilities(
                streaming=False,
                pushNotifications=False,
                stateTransitionHistory=False
            ),
            skills=[skill],
            defaultInputModes=["text"],
            defaultOutputModes=["text"]
        )
    
    
    
    def get_host_port(self) -> tuple[str, int]:
        """Extract host and port from remote URL"""
        parsed_url = urlparse(self.remote_url)
        if parsed_url.hostname is None:
            raise ConfigurationError(f"Agent '{self.agent_id}' URL '{self.remote_url}' missing hostname")
        if parsed_url.port is None:
            raise ConfigurationError(f"Agent '{self.agent_id}' URL '{self.remote_url}' missing port number")
        return parsed_url.hostname, parsed_url.port
    
    async def start_a2a_server(self, port: int = None, path: str = None) -> None:
        """Start A2A server on specified port with optional path"""
        if port is None:
            _, port = self.get_host_port()
        
        host, _ = self.get_host_port()
        if path:
            self.logger.info("Starting A2A server on {}:{}{}", host, port, path)
        else:
            self.logger.info("Starting A2A server on {}:{}", host, port)
        
        # Build the A2A application
        app = self.a2a_app.build()
        
        # If path is specified, mount the app at that path
        if path:
            from starlette.applications import Starlette
            from starlette.routing import Mount, Route
            from starlette.responses import JSONResponse
            
            # Create a health check endpoint
            async def health_check(request):
                return JSONResponse({"status": "ok", "service": self.agent_id})
            
            # Create a new Starlette app that mounts the A2A app at the specified path
            # Use path with trailing slash to avoid redirects
            mount_path = path if path.endswith('/') else path + '/'
            root_app = Starlette(routes=[
                Mount(mount_path, app=app),
                # Add a health check endpoint at the root
                Route("/", health_check, methods=["GET"])
            ])
            app = root_app
        
        # Completely disable uvicorn logging
        import uvicorn
        import logging
        logging.getLogger("uvicorn").setLevel(logging.CRITICAL)
        logging.getLogger("uvicorn.error").setLevel(logging.CRITICAL)
        logging.getLogger("uvicorn.access").setLevel(logging.CRITICAL)
        logging.getLogger("uvicorn.asgi").setLevel(logging.CRITICAL)
        
        config = uvicorn.Config(
            app, 
            host=host, 
            port=port, 
            log_level="critical",  # Only show critical errors
            log_config=None,  # Disable uvicorn's default logging completely
            access_log=False  # Disable access logs to reduce noise
        )
        server = uvicorn.Server(config)
        await server.serve()

        
    
    def _to_json_safe(self, obj: Any) -> Any:
        """Recursively convert obj to a JSON-serializable structure."""
        import json
        # Primitives
        if obj is None or isinstance(obj, (bool, int, float, str)):
            return obj
        # Mapping
        if isinstance(obj, dict):
            return {str(self._to_json_safe(k)): self._to_json_safe(v) for k, v in obj.items()}
        # Iterable
        if isinstance(obj, (list, tuple, set)):
            return [self._to_json_safe(x) for x in obj]
        # Pydantic-like
        if hasattr(obj, "model_dump") and callable(getattr(obj, "model_dump")):
            return self._to_json_safe(obj.model_dump())
        # Dataclass-like or generic objects
        if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
            return self._to_json_safe(obj.dict())
        if hasattr(obj, "__dict__"):
            return self._to_json_safe(vars(obj))
        # Fallback string conversion
        try:
            json.dumps(obj)  # will raise if not serializable
            return obj
        except Exception:
            return str(obj)