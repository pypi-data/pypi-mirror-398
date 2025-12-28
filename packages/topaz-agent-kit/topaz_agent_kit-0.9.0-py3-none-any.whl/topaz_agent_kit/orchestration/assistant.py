import os
import base64
import json
import asyncio
from typing import Any, Dict, List, Optional
from pathlib import Path

from agent_framework import ChatAgent, ChatMessage, Role
from agent_framework.observability import setup_observability

from topaz_agent_kit.frameworks.framework_config_manager import FrameworkConfigManager
from topaz_agent_kit.frameworks.framework_model_factory import FrameworkModelFactory
from topaz_agent_kit.utils.logger import Logger, remove_opentelemetry_console_handlers
from topaz_agent_kit.orchestration.orchestrator import Orchestrator
from topaz_agent_kit.core.ag_ui_event_emitter import AGUIEventEmitter
from topaz_agent_kit.core.exceptions import AgentError
from topaz_agent_kit.utils.prompt_loader import PromptLoader
from topaz_agent_kit.utils.json_utils import JSONUtils

from pydantic import BaseModel, Field, Json
from langfuse import get_client
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# Module-level logger for Langfuse initialization
_langfuse_logger = Logger("Langfuse")

# Initialize Langfuse client (optional - will gracefully handle if not available)
try:
    langfuse = get_client()
    # Verify connection (optional - don't fail if Langfuse is not running)
    try:
        if langfuse.auth_check():
            _langfuse_logger.success("Langfuse client is authenticated and ready!")
        else:
            _langfuse_logger.error("Langfuse client is not authenticated. Please check your credentials.")
    except Exception as e:
        # Langfuse server may not be running - this is okay, observability will still work
        _langfuse_logger.warning(f"Langfuse connection check skipped (server may not be running)")
except Exception as e:
    # Langfuse initialization failed - set to None and continue without it
    langfuse = None
    _langfuse_logger.warning(f"Langfuse client initialization skipped: {type(e).__name__}")

# Configure OTLP exporter for Langfuse
# Langfuse OTLP endpoint: http://localhost:3000/api/public/otel
# 
# Required environment variables:
# - LANGFUSE_PUBLIC_KEY: Your Langfuse public key (pk-lf-...)
# - LANGFUSE_SECRET_KEY: Your Langfuse secret key (sk-lf-...)
# - LANGFUSE_HOST: Langfuse host URL (default: http://localhost:3000)
#   For cloud: https://cloud.langfuse.com or https://us.cloud.langfuse.com
langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
langfuse_host = os.getenv("LANGFUSE_HOST", "http://localhost:4000")

# Create OTLP exporters with Langfuse authentication
# Langfuse supports Basic auth with Base64 encoded credentials
otlp_endpoint = f"{langfuse_host}/api/public/otel"

# Encode credentials for Basic authentication
if langfuse_public_key and langfuse_secret_key:
    credentials = base64.b64encode(
        f"{langfuse_public_key}:{langfuse_secret_key}".encode()
    ).decode()
    auth_header = f"Basic {credentials}"
else:
    _langfuse_logger.warning("LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY not set. OTLP export may fail.")
    auth_header = None

# Trace exporter - this is all we need for Langfuse
# Traces contain: execution flow, timing, span attributes, and events
# Configure exporter to fail silently if Langfuse is not available
trace_exporter = OTLPSpanExporter(
    endpoint=f"{otlp_endpoint}/v1/traces",
    headers={"Authorization": auth_header} if auth_header else {}
)

# Suppress OpenTelemetry console output via environment variables
os.environ.setdefault('OTEL_SDK_DISABLED', 'false')
os.environ.setdefault('OTEL_LOG_LEVEL', 'ERROR')
os.environ.setdefault('OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED', 'false')

# Only export traces - Langfuse focuses on trace-based observability
setup_observability(
    enable_sensitive_data=True,
    exporters=[trace_exporter]
)

# Remove OpenTelemetry console handlers that output unwanted JSON logs
remove_opentelemetry_console_handlers()

class ToolParams(BaseModel):
    pipeline_id: Optional[str] = None
    agent_id: Optional[str] = None
    user_text: Optional[str] = None
    model_config = {"extra": "forbid"}


class AssistantResponse(BaseModel):
    assistant_response: str
    tool_planned: Optional[str] = None
    tool_executed: Optional[str] = None
    tool_params: Optional[ToolParams] = None
    raw_tool_output: Optional[Json[Any]] = Field(
        default=None, description="Serialized JSON tool output"
    )
    reasoning: Optional[str] = None
    success: bool = False
    error: Optional[str] = None
    session_title: Optional[str] = Field(
        default=None,
        description="Optional session title update (50-80 characters, concise and descriptive)",
    )
    model_config = {"extra": "forbid"}


class Assistant:
    """Assistant class"""

    def __init__(
        self,
        config: Dict[str, Any],
        project_dir: str,
        emitter: AGUIEventEmitter,
        agui_service: Optional[Any] = None,
        session_id: Optional[str] = None,
    ):
        self._logger = Logger("Assistant")

        self._emitter = emitter
        self._project_dir = project_dir

        self._assistant_config = config.get("assistant")
        if not self._assistant_config:
            self._send_error_message("Assistant section missing in pipeline.yml")

        self._agent_id = self._assistant_config.get("id")
        self._framework_type = self._assistant_config.get("type")
        self._model_type = self._assistant_config.get("model")
        self._llm = None
        self._agent = None

        # load assistant instruction
        self._prompt_loader = PromptLoader(self._project_dir)
        self._prompt_spec = self._assistant_config.get("prompt")
        self._prompt_spec_instruction = self._prompt_spec.get("instruction")
        self._assistant_instruction = self._prompt_loader.load_prompt(
            self._prompt_spec_instruction
        )

        if not self._assistant_instruction:
            self._send_error_message(
                f"Failed to load assistant instruction: {self._prompt_spec_instruction}"
            )

        self._orch = Orchestrator(config, project_dir)
        self._agui_service = agui_service  # Store AGUIService for pipeline execution

        # Use provided session_id or create new session
        if session_id:
            self._session_id = session_id
            self._logger.info("Using provided session ID: {}", session_id)
        else:
            self._session_id = self._orch.create_session("assistant")
            self._logger.info("Created new session ID: {}", self._session_id)
        self._thread = None

        # Store last execution results for final return
        self._last_result = None
        self._last_pipeline_id = None
        self._last_agent_id = None
        self._last_user_input = None

        self._pending_turn_options: Optional[Dict[str, Any]] = None

        # NEW: File context storage for unified file handling
        self._pending_file_paths: List[str] = []
        self._pending_original_filenames: List[str] = []
        self._pending_upload_intent: str = "session"
        self._pending_mode: str = "cli"

        # Streaming state management
        self._active_message_id: Optional[str] = None

        self._logger.success(
            "Assistant initialized with session ID: {}", self._session_id
        )

    async def _send_message_streaming(
        self,
        message: str,
        role: str = "assistant",
        chunk_size: int = 50,
        delay_ms: float = 10.0,
    ) -> None:
        """
        Send message to the user with chunked streaming for better UX.

        Args:
            message: The message to send
            role: The role of the message (default: "assistant")
            chunk_size: Number of characters per chunk (default: 50)
            delay_ms: Delay in milliseconds between chunks (default: 10.0ms)
        """
        _ = self._start_message_stream(role)

        # Stream in chunks with delay for realistic effect
        for i in range(0, len(message), chunk_size):
            chunk = message[i : i + chunk_size]
            self._append_to_stream(chunk)

            # Add small delay between chunks to simulate real streaming
            if i + chunk_size < len(message):  # Don't delay after the last chunk
                await asyncio.sleep(delay_ms / 1000.0)  # Convert ms to seconds

        self._end_message_stream()

    async def _send_message(self, message: str, streaming: bool = True) -> None:
        """
        Send message to the user.
        Uses streaming by default for better UX, but can be disabled.
        """
        if streaming:
            await self._send_message_streaming(message, "assistant")
        else:
            message_id = self._emitter.text_message_start("assistant")
            self._emitter.text_message_content(message_id, message)
            self._emitter.text_message_end(message_id)

    # === STREAMING MESSAGE METHODS ===

    def _start_message_stream(self, role: str = "assistant") -> str:
        """
        Start a streaming message. Returns the message_id.
        Raises error if a message is already active (must end previous first).
        """
        if self._active_message_id:
            self._logger.error(
                "Message stream already active: {}", self._active_message_id
            )
            raise RuntimeError("Cannot start new stream while one is active")

        self._active_message_id = self._emitter.text_message_start(role)
        self._logger.debug("Started message stream: {}", self._active_message_id)
        return self._active_message_id

    def _append_to_stream(self, content: str) -> None:
        """
        Append content to the active message stream.
        Safe to call if no stream is active (creates one).
        """
        if not self._active_message_id:
            # Auto-start if not started
            self._active_message_id = self._emitter.text_message_start("assistant")
            self._logger.debug(
                "Auto-started message stream: {}", self._active_message_id
            )

        self._emitter.text_message_content(self._active_message_id, content)

    def _end_message_stream(self) -> None:
        """
        End the active message stream and clear the state.
        Safe to call if no stream is active.
        """
        if self._active_message_id:
            self._emitter.text_message_end(self._active_message_id)
            self._logger.debug("Ended message stream: {}", self._active_message_id)
            self._active_message_id = None
        else:
            self._logger.debug("No active message stream to end")

    def _reset_message_stream(self) -> None:
        """
        Force reset if needed (cleanup)
        """
        if self._active_message_id:
            self._logger.warning(
                "Force resetting message stream: {}", self._active_message_id
            )
            self._active_message_id = None

    async def _send_error_message(self, message: str) -> None:
        """
        Send error message to the user.
        """
        self._logger.error(message)
        await self._send_message(f"I'm sorry, but I encountered an error: {message}")
        self._emitter.run_error(self._session_id, message)
        raise AgentError(f"Assistant error: {message}")

    async def _create_execution_error_response(
        self,
        error_message: str,
        run_id: str,
        user_message: str = None,
        tool_planned: str = None,
        tool_executed: str = None,
        tool_params: dict = None,
        reasoning: str = None,
    ) -> AssistantResponse:
        """
        Create a structured error response for any execution issue.

        Args:
            error_message: The technical error message for logging
            run_id: The run ID for emitting run_error event
            user_message: User-friendly message (defaults to generic error message)
            tool_planned: Tool that was planned to be executed
            tool_executed: Tool that was actually executed
            tool_params: Parameters passed to the tool (dict or ToolParams)
            reasoning: Human-readable reason for the error
        """
        self._logger.error(error_message)

        # Send user-friendly message
        if user_message:
            await self._send_message(user_message)
        else:
            await self._send_message(
                f"I'm sorry, but I encountered an error: {error_message}"
            )

        # Emit run error event
        if run_id:
            self._emitter.run_error(run_id, error_message)

        # Convert tool_params to ToolParams model if it's a dict
        tool_params_model = None
        if tool_params:
            if isinstance(tool_params, dict):
                tool_params_model = ToolParams(**tool_params)
            elif isinstance(tool_params, ToolParams):
                tool_params_model = tool_params
        elif self._last_pipeline_id or self._last_agent_id or self._last_user_input:
            tool_params_model = ToolParams(
                pipeline_id=self._last_pipeline_id,
                agent_id=self._last_agent_id,
                user_text=self._last_user_input,
            )

        # Build response with defaults
        response = AssistantResponse(
            success=False,
            assistant_response=user_message
            or "I apologize, but I encountered an error processing your request. Please try again.",
            tool_planned=tool_planned,
            tool_executed=tool_executed,
            tool_params=tool_params_model,
            raw_tool_output=None,
            reasoning=reasoning or "Error occurred during execution",
            error=error_message,
        )

        return response

    def _extract_formatted_output(self, result: Dict[str, Any]) -> str:
        """
        Extract formatted output from execution result.
        Prioritizes formatted_output (contains citations) over summary.

        Args:
            result: Execution result dictionary

        Returns:
            Formatted output string or fallback to summary
        """
        # Use formatted_output if available (contains citations), otherwise fall back to summary
        if result.get("success") and "result" in result:
            agent_result = result["result"]
            if isinstance(agent_result, dict) and "formatted_output" in agent_result:
                return agent_result["formatted_output"]

        return result.get("summary", str(result))

    async def execute_pipeline(self, pipeline_id: str, user_text: str) -> str:
        """
        Tool: Execute a pipeline

        Args:
            pipeline_id: The ID of the pipeline to execute
            user_text: The user text to execute the pipeline with

        Returns:
            A JSON string containing the result of the pipeline execution
        """
        try:
            # Emit run metadata with pipeline information
            if hasattr(self, "_current_run_id") and self._current_run_id:
                self._emitter.run_metadata(
                    run_id=self._current_run_id, pipeline_name=pipeline_id
                )
            
            # Load agent titles for this pipeline if project_dir is available
            if hasattr(self._orch, "_project_dir") and self._orch._project_dir:
                project_dir = Path(self._orch._project_dir)
                # Load titles into emitter (will be used in step_output and state_delta)
                if hasattr(self._emitter, "_load_agent_titles"):
                    self._emitter._load_agent_titles(pipeline_id, project_dir)

            result = await self._orch.execute_pipeline(
                pipeline_id=pipeline_id,
                user_text=user_text,
                emitter=self._emitter,
                session_id=self._session_id,
                options=self._pending_turn_options or {},
                user_files=self._pending_file_paths
                if self._pending_upload_intent == "session"
                else [],
                agui_service=self._agui_service,  # Pass AGUIService for HITL gate registration
            )

            # Handle user-initiated stops as success
            if result.get("stopped_by_user"):
                return {
                    "assistant_response": f"Pipeline stopped as requested at gate '{result['gate_id']}'. {result['reason']}",
                    "tool_planned": "execute_pipeline",
                    "tool_executed": "execute_pipeline",
                    "tool_params": {"pipeline_id": pipeline_id, "user_text": user_text},
                    "raw_tool_output": JSONUtils.normalize_for_ui(result),
                    "reasoning": "User requested to stop the pipeline",
                }

            # Store raw result for final return
            self._last_result = result
            self._last_pipeline_id = pipeline_id
            self._last_agent_id = None
            # Return raw result as JSON string for structured response
            return JSONUtils.normalize_for_ui(result)
        except Exception as e:
            # Return error as tool response instead of raising to prevent session state corruption
            error_result = {
                "success": False,
                "error": str(e),
                "pipeline_id": pipeline_id,
                "user_text": user_text,
            }
            self._last_result = error_result
            self._last_pipeline_id = pipeline_id
            self._last_agent_id = None
            self._logger.error("Pipeline execution failed: {}", e)
            return JSONUtils.normalize_for_ui(error_result)

    async def execute_agent(self, agent_id: str, user_text: str) -> str:
        """
        Tool: Execute an independent agent

        Args:
            agent_id: The ID of the agent to execute
            user_text: The user text to execute the agent with

        Returns:
            A JSON string containing the result of the agent execution
        """
        try:
            # Emit run metadata with agent information
            if hasattr(self, "_current_run_id") and self._current_run_id:
                self._emitter.run_metadata(
                    run_id=self._current_run_id,
                    agent_id=agent_id,
                    pipeline_name=agent_id,  # Use agent_id as display name
                )

            result = await self._orch.execute_agent(
                agent_id=agent_id,
                user_text=user_text,
                emitter=self._emitter,
                session_id=self._session_id,
                options=self._pending_turn_options or {},
                user_files=self._pending_file_paths
                if self._pending_upload_intent == "session"
                else [],
            )
            # Store raw result for final return
            self._last_result = result
            self._last_pipeline_id = None
            self._last_agent_id = agent_id
            # Return raw result as JSON string for structured response
            return JSONUtils.normalize_for_ui(result)
        except Exception as e:
            # Return error as tool response instead of raising to prevent session state corruption
            error_result = {
                "success": False,
                "error": str(e),
                "agent_id": agent_id,
                "user_text": user_text,
            }
            self._last_result = error_result
            self._last_pipeline_id = None
            self._last_agent_id = agent_id
            self._logger.error("Agent execution failed: {}", e)
            return JSONUtils.normalize_for_ui(error_result)

    async def initialize(self) -> None:
        """
        Initialize the assistant.
        """
        await self._initialize_llm()
        await self._create_assistant_agent()

    async def cleanup(self) -> None:
        """
        Clean up resources on shutdown.

        Args:
            None

        Returns:
            None
        """
        try:
            await self._serialize_session_thread()
            await self._orch.cleanup()
        except Exception as e:
            self._logger.error("Failed to cleanup: {}", e)
            # Note: cleanup is a tool method, but it returns None, so we don't need to return error response
            # The exception will be handled by the assistant's main error handling

    async def run_process_file_turn(self, user_text: str) -> dict:
        """
        Tool: Handle file uploads and processing for RAG ingestion.

        Args:
            user_text: The user message to execute

        Returns:
            Dict containing the processing results
        """

        try:
            # Validate upload intent
            if self._pending_upload_intent != "rag":
                return {
                    "success": False,
                    "error": f"run_process_file_turn only supports rag uploads, got: {self._pending_upload_intent}",
                }

            return await self._orch.run_process_file_turn(
                self._session_id,
                self._pending_file_paths,
                self._emitter,
                user_text,
                self._pending_original_filenames,
                self._pending_mode,
            )
        except Exception as e:
            # Return error as tool response instead of raising to prevent session state corruption
            error_result = {
                "success": False,
                "error": str(e),
                "file_paths": self._pending_file_paths,
                "user_text": user_text,
                "original_filenames": self._pending_original_filenames,
                "upload_intent": self._pending_upload_intent,
            }
            self._logger.error("File processing failed: {}", e)
            return error_result

    async def _initialize_llm(self) -> None:
        """
        Initialize LLM using unified framework-aware factory.
        Reads model configuration from pipeline.yml via agent_config.
        """
        try:
            # Get configuration from unified config manager
            config_manager = FrameworkConfigManager()
            model_config = config_manager.get_model_config(
                model_type=self._model_type,
                framework=self._framework_type,  # agno, langgraph, crewai, adk, sk, oak, maf
            )

            # Create model using framework-aware factory
            self._llm = FrameworkModelFactory.get_model(
                model_type=self._model_type,
                framework=self._framework_type,
                **model_config,
            )

            self._logger.success(
                "Initialized Assistant with {} {} model using unified factory",
                self._framework_type.title(),
                self._model_type,
            )

        except Exception as e:
            await self._send_error_message(f"Failed to initialize LLM: {e}")

    async def _create_assistant_agent(self) -> None:
        """
        Create assistant agent.
        """
        try:
            self._agent = ChatAgent(
                chat_client=self._llm,
                name=self._agent_id,
                description="Primary AI assistant - routes requests to pipelines and agents",
                instructions=self._assistant_instruction,
                tools=[
                    self.execute_pipeline,
                    self.execute_agent,
                    self.run_process_file_turn,
                ],
            )

            await self._deserialize_session_thread()
            self._logger.success("Assistant agent created successfully")

        except Exception as e:
            await self._send_error_message(f"Failed to create assistant agent: {e}")

    def _emit_assistant_response_card(
        self, structured_response: AssistantResponse, user_message: str
    ) -> None:
        """
        Emit assistant_response custom event.
        Called before streaming the assistant message to user.
        Display is controlled by frontend execution settings.
        """
        # Extract pipeline_name and agent_name from tool_params
        pipeline_name = None
        agent_name = None
        if structured_response.tool_params:
            pipeline_name = structured_response.tool_params.pipeline_id
            agent_name = structured_response.tool_params.agent_id

        # Prepare event payload with full structured response + metadata
        event_payload = {
            "assistant_response": structured_response.assistant_response,
            "tool_planned": structured_response.tool_planned,
            "tool_executed": structured_response.tool_executed,
            "tool_params": structured_response.tool_params.model_dump()
            if structured_response.tool_params
            else None,
            "raw_tool_output": structured_response.raw_tool_output,
            "reasoning": structured_response.reasoning,
            "success": structured_response.success,
            "error": structured_response.error,
            "session_title": structured_response.session_title,
            "framework": self._framework_type,
            "model": self._model_type,
            "pipeline_name": pipeline_name,
            "agent_name": agent_name,
            "user_input": user_message,  # Final message sent to assistant (with context)
            "prompt_template": self._assistant_instruction,  # Static instruction prompt
        }

        # Emit assistant_response custom event
        self._emitter.assistant_response(event_payload)
        self._logger.info("Emitted assistant_response event")

    @staticmethod
    def _sanitize_raw_tool_output(raw_output: Any) -> Optional[str]:
        """
        Sanitize raw_tool_output to ensure it's a valid JSON string.

        Pydantic's Json[Any] expects a JSON-encoded string, not a dict.
        This method ensures the string is valid JSON with properly escaped control characters.
        """
        if raw_output is None:
            return None

        # If it's already a string, validate and sanitize it
        if isinstance(raw_output, str):
            try:
                # Try to parse it - if it parses, it's valid JSON
                parsed = json.loads(raw_output)
                # Re-serialize to ensure proper escaping
                return json.dumps(parsed, ensure_ascii=False)
            except (json.JSONDecodeError, ValueError):
                # If it's not valid JSON, try to fix it
                try:
                    # Use JSONUtils to parse and fix
                    fixed = JSONUtils.parse_json_from_text(raw_output)
                    # Re-serialize as JSON string
                    return json.dumps(fixed, ensure_ascii=False)
                except Exception:
                    # Last resort: escape the string as a JSON string value
                    return json.dumps(raw_output, ensure_ascii=False)

        # If it's a dict or other object, serialize it
        try:
            return json.dumps(raw_output, ensure_ascii=False)
        except (TypeError, ValueError):
            # Fallback: convert to string and escape
            return json.dumps(str(raw_output), ensure_ascii=False)

    async def execute_assistant_agent(
        self,
        user_input: str,
        turn_options: Optional[Dict[str, Any]] = None,
        file_paths: Optional[List[str]] = None,
        original_filenames: Optional[List[str]] = None,
        upload_intent: str = "session",
        mode: str = "cli",
    ) -> AssistantResponse:
        """Execute assistant with full event control"""

        self._logger.input("Executing assistant agent with:")
        self._logger.input(f"    User input: {user_input}")
        self._logger.input(f"    File paths: {file_paths}")
        self._logger.input(f"    Upload intent: {upload_intent}")

        # Store user input for error reporting
        self._last_user_input = user_input

        run_id = None
        turn_id = None
        try:
            # 1. START RUN
            run_id = self._emitter.run_started(session_id=self._session_id)
            self._current_run_id = run_id  # Store for use in execute methods

            # 1.5. START TURN IN DATABASE (use the same run_id from emitter)
            try:
                # Determine pipeline_id if tool is planned (we'll update later if needed)
                pipeline_id = None
                # Start turn via orchestrator, passing the run_id from emitter to ensure consistency
                db_turn_id, turn_id, turn_run_id = self._orch.start_turn(
                    self._session_id,
                    user_input,
                    pipeline_id,
                    run_id,  # Pass the run_id from emitter so database uses the same ID
                )
                # Verify run_id matches
                if turn_run_id != run_id:
                    self._logger.warning(
                        "Run ID mismatch: emitter={}, database={}", run_id, turn_run_id
                    )
                self._logger.info(
                    "Turn started in database: {} (run_id: {})", turn_id, turn_run_id
                )
            except Exception as e:
                self._logger.warning("Failed to start turn in database: {}", e)
                turn_id = None

            # 2. RESET and store file context for this turn
            self._pending_turn_options = turn_options
            self._pending_file_paths = file_paths or []
            self._pending_original_filenames = original_filenames or []
            self._pending_upload_intent = upload_intent
            self._pending_mode = mode

            # 3. Prepare available content for context
            available_content = []
            try:
                available_content = self._orch.get_available_content()
            except Exception:
                pass

            # 4. Run assistant agent (LLM decides which tool)
            # Create user message with available content context and file context
            user_message = user_input

            if available_content:
                content_summary = "\n\nAvailable documents:\n" + "\n".join(
                    [
                        f"- {doc.get('summary', 'No summary')}"
                        for doc in available_content
                    ]
                )
                user_message = user_message + content_summary

            # Add file context if provided
            if self._pending_file_paths:
                files_context = (
                    f"\n\nUpload intent: {self._pending_upload_intent}\nUploaded files:\n"
                    + "\n".join(
                        [
                            f"- {Path(file_path).name}"
                            for file_path in self._pending_file_paths
                        ]
                    )
                )
                user_message = user_message + files_context

            self._logger.input("Final user message: {}", user_message)

            message = ChatMessage(role=Role.USER, text=user_message)

            # Run the agent and get complete response
            response = await self._agent.run(
                message,
                tool_choice="required",
                thread=self._thread,
                response_format=AssistantResponse,
            )

            if response.value:
                final_output = response.value
            elif response.text:
                final_output = response.text
            else:
                await self._send_error_message(
                    f"Assistant returned no value: {response}"
                )
                error_response = await self._create_execution_error_response(
                    "Assistant returned no value",
                    run_id,
                    user_message="I apologize, but I encountered an error processing your request. Please try again.",
                    reasoning="No response from assistant",
                )
                # Emit assistant response card (if enabled)
                self._emit_assistant_response_card(error_response, user_input)
                # Emit run_finished so footers can be created
                self._emitter.run_finished(run_id, result=error_response)
                # Complete turn in database
                if turn_id:
                    await self._complete_turn_in_database(
                        turn_id,
                        error_response,
                        user_input,
                        file_paths,
                        original_filenames,
                    )
                # Update session title if provided
                await self._update_session_title(
                    error_response.session_title, user_input
                )
                # Clear file context for next turn
                self._pending_file_paths = []
                self._pending_original_filenames = []
                return error_response

            # Handle Pydantic model response or fall back to JSON parsing
            if isinstance(final_output, AssistantResponse):
                # Already a Pydantic model, use directly
                structured_response = final_output
            else:
                # Fallback: Try JSON parsing (backward compatibility)
                try:
                    parsed = JSONUtils.parse_json_from_text(
                        final_output, expect_json=True
                    )

                    # Sanitize raw_tool_output before Pydantic validation
                    # Json[Any] expects a JSON string, not a dict
                    if (
                        "raw_tool_output" in parsed
                        and parsed["raw_tool_output"] is not None
                    ):
                        parsed["raw_tool_output"] = self._sanitize_raw_tool_output(
                            parsed["raw_tool_output"]
                        )

                    # Convert dict to Pydantic model
                    structured_response = AssistantResponse(**parsed)
                except (ValueError, TypeError) as e:
                    json_error = f"Assistant returned non-JSON response. Expected only JSON object, got: {final_output[:200]}... Error: {e}"
                    error_response = await self._create_execution_error_response(
                        json_error,
                        run_id,
                        user_message="I apologize, but I encountered an error processing your request. Please try again.",
                        reasoning="JSON parsing failed - response was not valid JSON",
                    )
                    # Emit assistant response card (if enabled)
                    self._emit_assistant_response_card(error_response, user_input)
                    # Emit run_finished so footers can be created
                    self._emitter.run_finished(run_id, result=error_response)
                    # Complete turn in database
                    if turn_id:
                        await self._complete_turn_in_database(
                            turn_id,
                            error_response,
                            user_input,
                            file_paths,
                            original_filenames,
                        )
                    # Update session title if provided
                    await self._update_session_title(
                        error_response.session_title, user_input
                    )
                    # Clear file context for next turn
                    self._pending_file_paths = []
                    self._pending_original_filenames = []
                    return error_response

            self._logger.output(f"Assistant Structured Response: {structured_response}")

            # Validate tool execution consistency immediately
            tool_planned = structured_response.tool_planned
            tool_executed = structured_response.tool_executed

            if tool_planned and not tool_executed:
                tool_error = f"Tool '{tool_planned}' was planned but not executed"
                error_response = await self._create_execution_error_response(
                    tool_error,
                    run_id,
                    user_message=structured_response.assistant_response,
                    reasoning="Tool execution failed",
                    tool_planned=tool_planned,
                    tool_executed=tool_executed,
                    tool_params=structured_response.tool_params.model_dump()
                    if structured_response.tool_params
                    else {},
                )
                # Emit assistant response card (if enabled)
                self._emit_assistant_response_card(error_response, user_message)
                # Emit run_finished so footers can be created
                self._emitter.run_finished(run_id, result=error_response)
                # Complete turn in database
                if turn_id:
                    await self._complete_turn_in_database(
                        turn_id,
                        error_response,
                        user_input,
                        file_paths,
                        original_filenames,
                    )
                # Update session title if provided
                await self._update_session_title(
                    error_response.session_title, user_input
                )
                # Clear file context for next turn
                self._pending_file_paths = []
                self._pending_original_filenames = []
                return error_response
            elif tool_planned and tool_executed and tool_planned != tool_executed:
                tool_error = f"Tool execution mismatch: planned '{tool_planned}' but executed '{tool_executed}'"
                error_response = await self._create_execution_error_response(
                    tool_error,
                    run_id,
                    user_message=structured_response.assistant_response,
                    reasoning="Tool execution mismatch",
                    tool_planned=tool_planned,
                    tool_executed=tool_executed,
                    tool_params=structured_response.tool_params.model_dump()
                    if structured_response.tool_params
                    else {},
                )
                # Emit assistant response card (if enabled)
                self._emit_assistant_response_card(error_response, user_message)
                # Emit run_finished so footers can be created
                self._emitter.run_finished(run_id, result=error_response)
                # Complete turn in database
                if turn_id:
                    await self._complete_turn_in_database(
                        turn_id,
                        error_response,
                        user_input,
                        file_paths,
                        original_filenames,
                    )
                # Update session title if provided
                await self._update_session_title(
                    error_response.session_title, user_input
                )
                # Clear file context for next turn
                self._pending_file_paths = []
                self._pending_original_filenames = []
                return error_response

            assistant_response_text = structured_response.assistant_response or str(
                final_output
            )

            # 5.5. EMIT ASSISTANT RESPONSE CARD (if enabled, BEFORE streaming message)
            self._emit_assistant_response_card(structured_response, user_message)

            # 6. EMIT FINAL MESSAGE (stream the assistant_response to user)
            await self._send_message(assistant_response_text)

            # 7. FINISH RUN
            # Set success flag before emitting
            structured_response.success = True
            self._emitter.run_finished(run_id, result=structured_response)

            # 8. SAVE THREAD STATE TO DATABASE
            await self._serialize_session_thread()

            # 9. UPDATE SESSION TITLE IF PROVIDED
            await self._update_session_title(
                structured_response.session_title, user_input
            )

            # 10. COMPLETE TURN IN DATABASE WITH EVENTS AND RESPONSE
            if turn_id:
                await self._complete_turn_in_database(
                    turn_id,
                    structured_response,
                    user_input,
                    file_paths,
                    original_filenames,
                )

            # 11. CLEAR FILE CONTEXT FOR NEXT TURN (files are turn-specific)
            self._pending_file_paths = []
            self._pending_original_filenames = []

            # Return the full structured response
            return structured_response

        except Exception as e:
            # Error handling with proper events
            error_str = str(e)
            if "HITL rejected" in error_str or "HITL timeout" in error_str:
                message = "Pipeline stopped as requested."
                is_controlled = True
            else:
                message = f"I'm sorry, but I encountered an error: {error_str}"
                is_controlled = False

            # Convert tool_params dict to ToolParams model if needed
            tool_params_model = None
            if self._last_pipeline_id or self._last_agent_id or user_input:
                tool_params_model = ToolParams(
                    pipeline_id=self._last_pipeline_id,
                    agent_id=self._last_agent_id,
                    user_text=user_input,
                )

            if is_controlled:
                response = AssistantResponse(
                    assistant_response=message,
                    tool_planned=None,
                    tool_executed=None,
                    tool_params=tool_params_model,
                    raw_tool_output=None,
                    reasoning="Pipeline stopped as requested",
                    success=False,
                    error=error_str,
                )
                # Emit assistant_response card before sending message (if enabled)
                self._emit_assistant_response_card(response, user_message)
                await self._send_message(message)
                self._emitter.run_finished(run_id, result=response)

                # Update session title even on error (first turn should still set title)
                await self._update_session_title(None, user_input)

                # Complete turn in database with error status
                if turn_id:
                    await self._complete_turn_in_database_with_error(
                        turn_id, response, user_input, error_str, is_controlled
                    )

                # Clear file context for next turn (files are turn-specific)
                self._pending_file_paths = []
                self._pending_original_filenames = []

                return response
            else:
                error_response = await self._create_execution_error_response(
                    error_str,
                    run_id,
                    user_message=message,
                    reasoning="Error occurred during execution",
                )
                # Emit assistant_response card (if enabled)
                # Note: Message already sent by _create_execution_error_response
                self._emit_assistant_response_card(error_response, user_message)
                # Emit run_finished so footers can be created
                self._emitter.run_finished(run_id, result=error_response)

                # Update session title even on error (first turn should still set title)
                await self._update_session_title(None, user_input)

                # Complete turn in database with error status
                if turn_id:
                    await self._complete_turn_in_database_with_error(
                        turn_id, error_response, user_input, error_str, False
                    )

                # Clear file context for next turn (files are turn-specific)
                self._pending_file_paths = []
                self._pending_original_filenames = []

                return error_response

    async def _serialize_session_thread(self) -> None:
        """
        Serialize the session thread to database.
        """
        if not self._thread:
            self._logger.warning("No thread to serialize")
            return

        try:
            self._logger.info(
                "Serializing session thread to database for session: {}",
                self._session_id,
            )
            serialized_thread = await self._thread.serialize()
            serialized_json = json.dumps(serialized_thread)

            # Store thread state via orchestrator
            success = self._orch.update_session_thread_state(
                self._session_id, serialized_json
            )

            if success:
                self._logger.success(
                    "Thread state saved to database for session: {}", self._session_id
                )
            else:
                self._logger.error(
                    "Failed to save thread state to database for session: {}",
                    self._session_id,
                )
        except Exception as e:
            self._logger.error("Error serializing thread to database: {}", e)

    async def _deserialize_session_thread(self) -> None:
        """
        Deserialize the session thread from database.
        """
        try:
            # Get thread state via orchestrator
            thread_state_json = self._orch.get_session_thread_state(self._session_id)

            if thread_state_json:
                self._logger.info(
                    "Deserializing session thread from database for session: {}",
                    self._session_id,
                )
                serialized_thread = json.loads(thread_state_json)
                self._thread = await self._agent.deserialize_thread(serialized_thread)
                self._logger.success(
                    "Thread state loaded from database for session: {}",
                    self._session_id,
                )
            else:
                self._logger.info(
                    "No thread state found in database for session: {}, creating new thread",
                    self._session_id,
                )
                self._thread = self._agent.get_new_thread()
        except json.JSONDecodeError as e:
            self._logger.error("Failed to parse thread state JSON from database: {}", e)
            self._thread = self._agent.get_new_thread()
        except Exception as e:
            self._logger.error("Error deserializing thread from database: {}", e)
            self._thread = self._agent.get_new_thread()

    async def _update_session_title(
        self, new_title: Optional[str], user_input: str
    ) -> None:
        """
        Update session title if provided and different from current title.
        On first turn, always set a title (from assistant or fallback to user message).
        """
        try:
            # Get current title via orchestrator
            current_title = self._orch.get_session_title(self._session_id) or "New chat"
            is_first_turn = current_title == "New chat"

            # Determine what title to use
            title_to_use = None

            if new_title:
                # Assistant provided a title
                # Validate length (trim if too long)
                title_to_use = new_title.strip()[:100]  # Max 100 chars for database
                if len(title_to_use) != len(new_title.strip()):
                    self._logger.warning(
                        "Title truncated from {} to {} characters",
                        len(new_title.strip()),
                        len(title_to_use),
                    )

                # Only update if different from current (or if first turn)
                if is_first_turn or title_to_use != current_title:
                    success = self._orch.update_session_title(
                        self._session_id, title_to_use
                    )
                    if success:
                        self._logger.success(
                            "Session title updated: '{}' -> '{}'",
                            current_title,
                            title_to_use,
                        )
                        # Emit custom event to notify frontend of title update
                        self._emitter.session_title_updated(
                            self._session_id, title_to_use
                        )
                    else:
                        self._logger.error("Failed to update session title")
            elif is_first_turn:
                # First turn but no title from assistant - use truncated user message as fallback
                fallback_title = user_input.strip()[:60]  # Max 60 chars for readability
                if not fallback_title:
                    fallback_title = "New chat"
                else:
                    # Ensure it ends at word boundary if possible
                    if len(user_input.strip()) > 60:
                        # Try to truncate at word boundary
                        last_space = fallback_title.rfind(" ")
                        if last_space > 40:  # Only if we keep enough content
                            fallback_title = fallback_title[:last_space]
                    fallback_title = fallback_title.strip()

                if fallback_title and fallback_title != "New chat":
                    success = self._orch.update_session_title(
                        self._session_id, fallback_title
                    )
                    if success:
                        self._logger.success(
                            "Session title set from user message: '{}'", fallback_title
                        )
                        # Emit custom event to notify frontend of title update
                        self._emitter.session_title_updated(
                            self._session_id, fallback_title
                        )
                    else:
                        self._logger.error(
                            "Failed to set session title from user message"
                        )
        except Exception as e:
            self._logger.error("Error updating session title: {}", e)

    async def _complete_turn_in_database(
        self,
        turn_id: str,
        structured_response: AssistantResponse,
        user_input: str,
        file_paths: Optional[List[str]] = None,
        original_filenames: Optional[List[str]] = None,
    ) -> None:
        """
        Complete turn in database.
        """
        try:
            # Complete the turn via orchestrator
            success = self._orch.complete_turn(turn_id=turn_id)

            if success:
                self._logger.success("Turn completed in database: {}", turn_id)
            else:
                self._logger.error("Failed to complete turn in database: {}", turn_id)

        except Exception as e:
            self._logger.error("Error completing turn in database: {}", e)

    async def _complete_turn_in_database_with_error(
        self,
        turn_id: str,
        response: AssistantResponse,
        user_input: str,
        error_str: str,
        is_controlled: bool,
    ) -> None:
        """
        Complete turn in database with error status.
        """
        try:
            # Update turn with error status via orchestrator
            status = "failed" if not is_controlled else "stopped"
            updates = {"error_message": error_str}

            success = self._orch.update_turn_status(turn_id, status, updates)

            if success:
                self._logger.success(
                    "Turn marked as {} in database: {} ({})",
                    status,
                    turn_id,
                    error_str[:50],
                )
            else:
                self._logger.error(
                    "Failed to update turn with error status: {}", turn_id
                )

        except Exception as e:
            self._logger.error("Error updating turn with error status: {}", e)
