"""
AG-UI Event Emitter
Direct AG-UI protocol event emitter - replaces EventEmitter
"""

import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from ag_ui.core import (
    EventType,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    ToolCallStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallResultEvent,
    StateSnapshotEvent,
    StateDeltaEvent,
    MessagesSnapshotEvent,
    RawEvent,
    CustomEvent,
    RunStartedEvent,
    RunFinishedEvent,
    RunErrorEvent,
    StepStartedEvent,
    StepFinishedEvent,
)
from topaz_agent_kit.utils.logger import Logger
import yaml


class AGUIEventEmitter:
    """Direct AG-UI event emitter - replaces EventEmitter"""

    def __init__(
        self,
        emit_fn: Optional[Callable[[Dict[str, Any]], None]] = None,
        run_counter: Optional[Callable[[], int]] = None,
    ) -> None:
        self.logger = Logger("AGUIEventEmitter")
        self._emit = emit_fn or (lambda _evt: None)
        self.message_id_counter = 0
        self.run_id_counter = 0
        self.step_id_counter = 0
        self.tool_call_id_counter = 0
        self._run_counter_fn = run_counter  # External counter function

        # Step management state
        self._step_agent_names: Dict[str, str] = {}  # step_id -> agent_name
        self._agent_step_counts: Dict[str, int] = {}  # agent_name -> count

        # Agent title mapping (loaded from UI manifests)
        self._agent_title_map: Dict[str, str] = {}  # agent_id -> title
        self._project_dir: Optional[Path] = None

        self.logger.debug(
            "AGUIEventEmitter initialized with emit function: {}", bool(emit_fn)
        )

    def _load_agent_titles(self, pipeline_id: str, project_dir: Path) -> None:
        """Load agent titles from UI manifest for the given pipeline.
        
        Args:
            pipeline_id: The pipeline ID to load UI manifest for
            project_dir: Path to project root directory
        """
        try:
            ui_manifest_path = project_dir / "config" / "ui_manifests" / f"{pipeline_id}.yml"
            if not ui_manifest_path.exists():
                self.logger.debug(
                    "UI manifest not found for pipeline {}: {}",
                    pipeline_id,
                    ui_manifest_path,
                )
                return

            with open(ui_manifest_path, "r", encoding="utf-8") as f:
                ui_manifest = yaml.safe_load(f)
                agents = ui_manifest.get("agents", [])
                for agent in agents:
                    agent_id = agent.get("id")
                    agent_title = agent.get("title")
                    if agent_id and agent_title:
                        self._agent_title_map[agent_id] = agent_title

            self.logger.debug(
                "Loaded {} agent titles from UI manifest for pipeline {}",
                len(self._agent_title_map),
                pipeline_id,
            )
        except Exception as e:
            self.logger.debug(
                "Could not load UI manifest for pipeline {}: {}",
                pipeline_id,
                e,
            )

    def _emit_event(self, event: Dict[str, Any]) -> None:
        """Internal method to emit events with error handling"""
        try:
            if isinstance(event, dict):
                event_type = event.get("type")
                # Add more context for specific event types
                if event_type == "CUSTOM":
                    custom_name = event.get("name", "unknown")
                    self.logger.event(
                        "Emitting AG-UI event: type={}, custom_name={}",
                        event_type,
                        custom_name,
                    )
                elif event_type == "STATE_SNAPSHOT":
                    snapshot = event.get("snapshot", {})
                    agents = snapshot.get("agents", {})
                    agent_names = list(agents.keys()) if agents else []
                    self.logger.event(
                        "Emitting AG-UI event: type={}, agents={}",
                        event_type,
                        agent_names,
                    )
                elif event_type == "STEP_STARTED":
                    step_name = event.get("step_name", "unknown")
                    self.logger.event(
                        "Emitting AG-UI event: type={}, step_name={}",
                        event_type,
                        step_name,
                    )
                elif event_type == "STEP_FINISHED":
                    step_name = event.get("step_name", "unknown")
                    self.logger.event(
                        "Emitting AG-UI event: type={}, step_name={}",
                        event_type,
                        step_name,
                    )
                else:
                    self.logger.event("Emitting AG-UI event: type={}", event_type)
                self._emit(event)
            else:
                self.logger.error("Event is not a dict: {}", type(event))
                raise ValueError(f"Event must be a dict, got {type(event)}")
        except Exception as e:
            self.logger.error("Failed to emit AG-UI event: {}", e)
            raise

    def emit(self, event: Dict[str, Any]) -> None:
        """Generic emit method - converts custom events to AG-UI CUSTOM events"""
        try:
            event_type = event.get("type", "")

            # Check if it's already an AG-UI event type using official enum
            if event_type in EventType.__members__.values():
                # Already an AG-UI event, emit directly
                self._emit_event(event)
            else:
                # Convert custom event to AG-UI CUSTOM event
                custom_event = CustomEvent(
                    name=event_type, value=event, timestamp=int(time.time() * 1000)
                )
                self._emit_event(custom_event.model_dump())

        except Exception as e:
            self.logger.error("Failed to emit event: {}", e)
            raise

    # === TEXT MESSAGE EVENTS ===
    def text_message_start(self, role: str = "assistant") -> str:
        """Start a text message"""
        message_id = f"msg_{self.message_id_counter}"
        self.message_id_counter += 1
        event = TextMessageStartEvent(
            message_id=message_id, role=role, timestamp=int(time.time() * 1000)
        )
        self._emit_event(event.model_dump())
        return message_id

    def text_message_content(self, message_id: str, delta: str) -> None:
        """Stream text content"""
        event = TextMessageContentEvent(
            message_id=message_id, delta=delta, timestamp=int(time.time() * 1000)
        )
        self._emit_event(event.model_dump())

    def text_message_end(self, message_id: str) -> None:
        """Complete text message"""
        event = TextMessageEndEvent(
            message_id=message_id, timestamp=int(time.time() * 1000)
        )
        self._emit_event(event.model_dump())

    # === TOOL CALL EVENTS ===
    def tool_call_start(self, tool_name: str, agent_name: Optional[str] = None) -> str:
        """Start tool call"""
        tool_call_id = f"tool_{self.tool_call_id_counter}"
        self.tool_call_id_counter += 1
        event = ToolCallStartEvent(
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            agent_name=agent_name,
            timestamp=int(time.time() * 1000),
        )
        self._emit_event(event.model_dump())
        return tool_call_id

    def tool_call_args(self, tool_call_id: str, args: Dict[str, Any]) -> None:
        """Send tool call arguments"""
        event = ToolCallArgsEvent(
            tool_call_id=tool_call_id, args=args, timestamp=int(time.time() * 1000)
        )
        self._emit_event(event.model_dump())

    def tool_call_end(self, tool_call_id: str) -> None:
        """Complete tool call"""
        event = ToolCallEndEvent(
            tool_call_id=tool_call_id, timestamp=int(time.time() * 1000)
        )
        self._emit_event(event.model_dump())

    def tool_call_result(
        self, tool_call_id: str, result: Any, error: Optional[str] = None
    ) -> None:
        """Send tool call result"""
        event = ToolCallResultEvent(
            tool_call_id=tool_call_id,
            result=result,
            error=error,
            timestamp=int(time.time() * 1000),
        )
        self._emit_event(event.model_dump())

    # === STATE EVENTS ===

    def step_output(
        self,
        node_id: str,
        result: Optional[Any] = None,
        status: str = "completed",
        error_message: Optional[str] = None,
        ended_at: Optional[str] = None,
        elapsed_ms: Optional[int] = None,
    ) -> None:
        """Emit step output/result data only (header comes from step_started, inputs from step_input)"""
        # Format step name (handles instance IDs by extracting base name and instance number)
        # This must match the formatting used in step_started and step_finished
        # For instance IDs, use _format_step_name_for_instance
        # For non-instance agents, use case-insensitive lookup from UI manifest
        if self._is_instance_id(node_id):
            agent_title = self._format_step_name_for_instance(node_id)
        else:
            # Non-instance agent: use case-insensitive lookup from UI manifest
            agent_title = None
            node_id_lower = node_id.lower()
            for key, value in self._agent_title_map.items():
                if key.lower() == node_id_lower:
                    agent_title = value
                    break
            
            if not agent_title:
                agent_title = self._convert_agent_id_to_title(node_id)
        
        agent_data = {
            "node_id": node_id,
            "agent_id": node_id,  # Add agent_id field for frontend compatibility
            "title": agent_title,  # Include formatted title (handles instances)
            "status": status,
            "snapshot": result
            if result is not None
            else ("Completed" if not error_message else None),
        }

        # Only include error info if failed
        if error_message:
            agent_data["error_message"] = error_message
            # Include error in snapshot for failed agents
            if result is None:
                agent_data["snapshot"] = {"error": error_message}

        # Timing info (only end time since started_at is in step_started)
        if ended_at:
            agent_data["ended_at"] = ended_at
        if elapsed_ms:
            agent_data["elapsed_ms"] = elapsed_ms

        # Create state snapshot with agents structure
        snapshot = {"agents": {node_id: agent_data}}

        event = StateSnapshotEvent(snapshot=snapshot, timestamp=int(time.time() * 1000))
        self._emit_event(event.model_dump())

    def state_delta(self, delta: List[Dict[str, Any]]) -> None:
        """Send state changes"""
        event = StateDeltaEvent(delta=delta, timestamp=int(time.time() * 1000))
        self._emit_event(event.model_dump())

    def messages_snapshot(self, messages: List[Dict[str, Any]]) -> None:
        """Send full message history"""
        event = MessagesSnapshotEvent(
            messages=messages, timestamp=int(time.time() * 1000)
        )
        self._emit_event(event.model_dump())

    # === RUN EVENTS ===

    def run_started(
        self,
        run_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        session_id: Optional[str] = None,
        pipeline_name: Optional[str] = None,
        project_dir: Optional[Path] = None,
    ) -> str:
        """Start agent run/pipeline
        
        Args:
            run_id: Optional run ID (will be generated if not provided)
            thread_id: Optional thread ID (will be generated if not provided)
            session_id: Optional session ID
            pipeline_name: Optional pipeline name/ID
            project_dir: Optional project directory path for loading UI manifests
        """
        if not run_id:
            # Use external counter if available, otherwise use internal counter
            if self._run_counter_fn:
                counter = self._run_counter_fn()
            else:
                counter = self.run_id_counter
                self.run_id_counter += 1

            # Include session_id in run_id for uniqueness across sessions
            if session_id:
                run_id = f"{session_id}_run_{counter}"
            else:
                run_id = f"run_{counter}"
        if not thread_id:
            thread_id = f"thread_{run_id}"

        # Load agent titles from UI manifest if pipeline_name and project_dir are provided
        if pipeline_name and project_dir:
            self._project_dir = project_dir
            self._agent_title_map.clear()  # Clear previous mapping
            self._load_agent_titles(pipeline_name, project_dir)

        # Create event with session_id and pipeline_name in rawEvent field (AG-UI compliant)
        event_data = {
            "run_id": run_id,
            "thread_id": thread_id,
            "timestamp": int(time.time() * 1000),
        }
        if session_id or pipeline_name:
            raw_event = {}
            if session_id:
                raw_event["session_id"] = session_id
            if pipeline_name:
                raw_event["pipeline_name"] = pipeline_name
            event_data["rawEvent"] = raw_event

        event = RunStartedEvent(**event_data)
        self._emit_event(event.model_dump())
        # Reset per-run step counts so step numbering applies only within this run
        self._agent_step_counts = {}
        return run_id

    def run_finished(
        self, run_id: str, result: Optional[Any] = None, thread_id: Optional[str] = None
    ) -> None:
        """Complete agent run/pipeline"""
        if not thread_id:
            thread_id = f"thread_{run_id}"
        event = RunFinishedEvent(
            run_id=run_id,
            result=result,
            thread_id=thread_id,
            timestamp=int(time.time() * 1000),
        )
        self._emit_event(event.model_dump())

    def run_error(
        self,
        run_id: str,
        error: str,
        details: Optional[Dict[str, Any]] = None,
        thread_id: Optional[str] = None,
    ) -> None:
        """Handle run error (AG-UI expects only message and optional code)"""
        # RunErrorEvent schema: message (str), code (Optional[str])
        event = RunErrorEvent(
            message=error,
            code=(details or {}).get("code") if isinstance(details, dict) else None,
            timestamp=int(time.time() * 1000),
        )
        self._emit_event(event.model_dump())

    def run_metadata(
        self,
        run_id: str,
        pipeline_name: Optional[str] = None,
        agent_id: Optional[str] = None,
        framework: Optional[str] = None,
        model: Optional[str] = None,
        run_mode: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit run metadata with pipeline/agent information"""
        value = {"run_id": run_id}

        if pipeline_name:
            value["pipeline_name"] = pipeline_name
        if agent_id:
            value["agent_id"] = agent_id
        if framework:
            value["framework"] = framework
        if model:
            value["model"] = model
        if run_mode:
            value["run_mode"] = run_mode
        if extra:
            value.update(extra)

        self.custom_event("run_metadata", value)

    # === STEP EVENTS ===

    def _convert_agent_id_to_title(self, agent_id: str) -> str:
        """Convert agent ID to human-readable title.
        
        Removes common prefixes and converts underscores to spaces with title case.
        Case-insensitive matching for agent ID lookup.
        """
        # Normalize agent_id to lowercase for lookup
        agent_id_lower = agent_id.lower()
        
        # Try case-insensitive lookup in title map first
        for key, value in self._agent_title_map.items():
            if key.lower() == agent_id_lower:
                return value
        
        title = agent_id
        
        # Remove common prefixes (case-insensitive)
        prefixes = ["rfp_rsp_eval_", "math_", "enhanced_math_repeater_", "file_", "agent_"]
        for prefix in prefixes:
            if title.lower().startswith(prefix):
                title = title[len(prefix):]
                break
        
        # Convert underscores to spaces and title case
        title = title.replace('_', ' ').title()
        
        return title
    
    def _is_instance_id(self, agent_name: str) -> bool:
        """Detect if an agent_name looks like an instance-specific ID."""
        import re
        # Generic rule: any trailing "_<number>" indicates an instance
        return bool(re.search(r'_\d+$', agent_name))
    
    def _format_step_name_for_instance(self, agent_name: str) -> str:
        """Extract base agent name and instance number from instance_id and format as 'Agent Title (Instance N)'.
        
        Args:
            agent_name: Instance ID (e.g., 'rfp_rsp_eval_response_extractor_supplier_0') or regular agent name
            
        Returns:
            Formatted step name (e.g., 'Response Extractor (Instance 1)') or original agent name if not an instance
        """
        import re
        # Check if this looks like an instance_id (trailing "_<number>")
        if not self._is_instance_id(agent_name):
            return agent_name
        
        # Extract base agent name and instance numbers from trailing "_<number>_<number>" pattern
        # Handle nested instance IDs (e.g., problem_solver_0_0) where:
        # - First number is nested index (e.g., problem 0 within file)
        # - Second number is parent index (e.g., file 0)
        # Pattern: {base_agent_id}_{nested_index}_{parent_index}
        base_name = agent_name
        instance_num = None
        parent_instance_num = None
        
        # Match nested instance IDs: pattern is {base}_{parent_index}_{nested_index} (e.g., problem_solver_0_0)
        # The ID structure now matches the display format: parent_index comes first, then nested_index
        nested_match = re.search(r'^(.*?)_(\d+)_(\d+)$', agent_name)
        if nested_match:
            # Nested instance ID (e.g., problem_solver_0_0 = file 0, problem 0)
            base_name = nested_match.group(1)
            parent_index = int(nested_match.group(2))  # 0-based parent index (file index) - comes first in ID
            nested_index = int(nested_match.group(3))  # 0-based nested index (problem index) - comes second in ID
            # Display as "Agent (Instance Parent.Nested)" e.g., "Problem Solver (Instance 1.1)" = File 1, Problem 1
            instance_num = f"{parent_index + 1}.{nested_index + 1}"  # Parent comes first in both ID and display
        else:
            # Single instance ID (e.g., file_reader_0)
            match = re.search(r'^(.*?)_(\d+)$', agent_name)
            if match:
                base_name = match.group(1)
                instance_num = int(match.group(2)) + 1  # Convert 0-based to 1-based for display
        
        # Get title from mapping if available (case-insensitive), otherwise convert agent ID to title
        base_title = None
        base_name_lower = base_name.lower()
        for key, value in self._agent_title_map.items():
            if key.lower() == base_name_lower:
                base_title = value
                break
        
        if not base_title:
            base_title = self._convert_agent_id_to_title(base_name)
        
        # Format as "Agent Title (Instance N)"
        if instance_num is not None:
            return f"{base_title} (Instance {instance_num})"
        else:
            return base_title

    def step_started(
        self,
        step_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        framework: Optional[str] = None,
        model: Optional[str] = None,
        run_mode: Optional[str] = None,
        started_at: Optional[str] = None,
        parent_pattern_id: Optional[str] = None,
    ) -> str:
        """Start agent step with optional header metadata"""
        if not step_id:
            step_id = f"step_{self.step_id_counter}"
            self.step_id_counter += 1

        # Store agent name for this step_id for use in step_finished
        agent_name = agent_name or "unknown_agent"
        self._step_agent_names[step_id] = agent_name

        # Always get human-readable title first (from manifest or ID conversion)
        # This ensures we never show raw IDs, even on first execution
        # Try case-insensitive lookup first
        base_title = None
        agent_name_lower = agent_name.lower()
        for key, value in self._agent_title_map.items():
            if key.lower() == agent_name_lower:
                base_title = value
                break
        
        if not base_title:
            base_title = self._convert_agent_id_to_title(agent_name)
        
        # Format step name (handles instance IDs by extracting base name and instance number)
        if self._is_instance_id(agent_name):
            # For instance IDs (from repeat patterns), use the existing formatting logic
            # These already have instance numbers encoded in the ID (e.g., "agent_0", "agent_1")
            step_name = self._format_step_name_for_instance(agent_name)
        else:
            # For non-instance agents (regular sequential/parallel patterns):
            # - Count steps per agent for multiple executions (e.g., in loops)
            # - Only add "(Instance N)" suffix when agent runs multiple times (step_count > 1)
            # - Single-run agents show clean title without "(Instance 1)" suffix
            # This ensures backward compatibility: existing patterns work the same,
            # but single-run agents have cleaner display names
            self._agent_step_counts[agent_name] = (
                self._agent_step_counts.get(agent_name, 0) + 1
            )
            step_count = self._agent_step_counts[agent_name]

            if step_count > 1:
                # Multiple executions: show instance number (e.g., "Agent Title (Instance 2)")
                step_name = f"{base_title} (Instance {step_count})"
            else:
                # Single execution: show clean title (e.g., "Agent Title")
                step_name = base_title

        # Build event with optional rawEvent for header metadata (similar to RunStartedEvent)
        event_data = {
            "stepName": step_name,  # ui expects stepName
            "timestamp": int(time.time() * 1000),
        }

        # Get title from mapping if available (case-insensitive lookup from UI manifest)
        # For instance IDs, extract base agent ID first
        base_agent_name = agent_name
        if self._is_instance_id(agent_name):
            # Extract base agent name by removing trailing "_<number>"
            import re
            match = re.search(r'^(.*)_(\d+)$', agent_name)
            if match:
                base_agent_name = match.group(1)
        
        agent_title = None
        base_agent_name_lower = base_agent_name.lower()
        for key, value in self._agent_title_map.items():
            if key.lower() == base_agent_name_lower:
                agent_title = value
                break
        
        if not agent_title:
            # For instance IDs, use the formatted step name; for non-instance, convert ID to title
            if self._is_instance_id(agent_name):
                agent_title = step_name  # Use the formatted step name (e.g., "File Reader (Instance 1)")
            else:
                agent_title = self._convert_agent_id_to_title(base_agent_name)
        
        # Add header metadata via rawEvent if provided
        # Always create rawEvent if we have any metadata OR if we have a title from UI manifest
        # Also always include node_id for UI matching with step_output events
        has_title = agent_title != agent_name  # True if title was found in UI manifest
        if framework or model or run_mode or started_at or has_title or parent_pattern_id is not None or True:  # Always create rawEvent to include node_id
            raw_event = {}
            # Always include node_id (raw agent_name) for UI matching with step_output
            raw_event["node_id"] = agent_name
            if framework:
                raw_event["framework"] = framework
            if model:
                raw_event["model"] = model
            if run_mode:
                raw_event["run_mode"] = run_mode
            if started_at:
                raw_event["started_at"] = started_at
            # Include parent_pattern_id if provided (None for independent agents, pattern_id for pipeline agents)
            if parent_pattern_id is not None:
                raw_event["parent_pattern_id"] = parent_pattern_id
            # Always include agent title in rawEvent if it was found in UI manifest
            # This allows frontend to use the title immediately when creating cards
            if has_title:
                raw_event["agent_title"] = agent_title
            event_data["rawEvent"] = raw_event

        event = StepStartedEvent(**event_data)
        self._emit_event(event.model_dump())
        return step_id

    def get_step_name(self, step_id: str) -> Optional[str]:
        """Get step_name for a given step_id"""
        agent_name = self._step_agent_names.get(step_id)
        if not agent_name:
            return None

        # Format step name (handles instance IDs by extracting base name and instance number)
        # This must match the formatting used in step_started
        if self._is_instance_id(agent_name):
            # Instance IDs keep their own formatting (e.g., Response Extractor (Instance 1))
            step_name = self._format_step_name_for_instance(agent_name)
        else:
            # Regular agents: use human-readable title and instance count
            step_count = self._agent_step_counts.get(agent_name, 1)
            # Try case-insensitive lookup first
            base_title = None
            agent_name_lower = agent_name.lower()
            for key, value in self._agent_title_map.items():
                if key.lower() == agent_name_lower:
                    base_title = value
                    break
            
            if not base_title:
                base_title = self._convert_agent_id_to_title(agent_name)
            # Only add "(Instance N)" if agent runs multiple times (step_count > 1)
            if step_count > 1:
                step_name = f"{base_title} (Instance {step_count})"
            else:
                step_name = base_title
        
        return step_name

    def step_input(
        self,
        step_name: str,
        node_id: str,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit step input data (inputs only - header comes from step_started)"""
        value = {
            "step_name": step_name,  # Links to step_started/step_finished
            "node_id": node_id,
        }
        if inputs:
            value["inputs"] = inputs

        self.custom_event("step_input", value)

    def step_finished(
        self,
        step_id: str,
        result: Optional[Any] = None,
        status: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """Complete agent step with optional status and error"""
        # Get the agent name that was stored during step_started
        agent_name = self._step_agent_names.get(step_id, step_id)

        # Format step name (handles instance IDs by extracting base name and instance number)
        # This must match the formatting used in step_started
        if self._is_instance_id(agent_name):
            step_name = self._format_step_name_for_instance(agent_name)
        else:
            # For regular agents, get step count to match step_started naming
            step_count = self._agent_step_counts.get(agent_name, 1)
            base_title = self._agent_title_map.get(
                agent_name, self._convert_agent_id_to_title(agent_name)
            )
            # Only add "(Instance N)" if agent runs multiple times (step_count > 1)
            if step_count > 1:
                step_name = f"{base_title} (Instance {step_count})"
            else:
                step_name = base_title

        # Build event with optional rawEvent for status/error (similar to RunStartedEvent)
        event_data = {
            "stepName": step_name,  # ui expects stepName
            "timestamp": int(time.time() * 1000),
        }

        # Add status/error via rawEvent (similar to RunStartedEvent)
        if status or error:
            raw_event = {}
            if status:
                raw_event["status"] = status  # "completed" or "failed"
            if error:
                raw_event["error"] = error
            event_data["rawEvent"] = raw_event

        event = StepFinishedEvent(**event_data)
        self._emit_event(event.model_dump())

        # Clean up stored agent name
        if step_id in self._step_agent_names:
            del self._step_agent_names[step_id]

    # === SPECIAL EVENTS ===

    def custom_event(self, name: str, value: Dict[str, Any]) -> None:
        """Send custom event"""
        event = CustomEvent(name=name, value=value, timestamp=int(time.time() * 1000))
        self._emit_event(event.model_dump())

    def raw_event(self, data: Dict[str, Any]) -> None:
        """Send raw event"""
        event = RawEvent(data=data, timestamp=int(time.time() * 1000))
        self._emit_event(event.model_dump())

    # === CONVENIENCE METHODS FOR COMMON CUSTOM EVENTS ===

    def hitl_request(
        self,
        gate_id: str,
        gate_type: str,  # "approval" | "input" | "selection"
        title: str = "",
        description: str = "",
        fields: List[Dict[str, Any]] = None,
        options: List[Dict[str, Any]] = None,
        buttons: Dict[str, Any] = None,
        timeout_ms: int = 300000,
        on_timeout: str = "reject",
        context_key: str = None,
        default: str = None,
        retry_target: str = None,
        max_retries: int = None,
        parent_pattern_id: Optional[str] = None,
    ) -> None:
        """Emit HITL request event"""
        event_data = {
            "gate_id": gate_id,
            "gate_type": gate_type,
            "title": title,
            "description": description,
            "fields": fields or [],
            "options": options or [],
            "buttons": buttons or {},
            "timeout_ms": timeout_ms,
            "on_timeout": on_timeout,
            "context_key": context_key or gate_id,
            "requested_at_ms": int(time.time() * 1000),
            "deadline_at_ms": int(time.time() * 1000) + timeout_ms,
            "retry_target": retry_target,
            "max_retries": max_retries,
        }
        # Add default value for selection gates
        if default is not None:
            event_data["default"] = default
        # Add parent_pattern_id if provided
        if parent_pattern_id is not None:
            event_data["parent_pattern_id"] = parent_pattern_id
        self.custom_event("hitl_request", event_data)

    def hitl_result(
        self, gate_id: str, decision: str, actor: str = "user", data: Any = None
    ) -> None:
        """Emit HITL result event"""
        self.custom_event(
            "hitl_result",
            {"gate_id": gate_id, "decision": decision, "actor": actor, "data": data},
        )

    def edge_protocol(
        self, from_agent: str, to_agent: str, protocol: str, label: Optional[str] = None, parent_pattern_id: Optional[str] = None
    ) -> None:
        """Emit edge protocol event for agent connections"""
        if not label:
            label = f"protocol: {protocol}"

        event_data = {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "protocol": protocol,
            "label": label,
        }
        
        if parent_pattern_id is not None:
            event_data["parent_pattern_id"] = parent_pattern_id

        self.custom_event("edge_protocol", event_data)

    def session_title_updated(self, session_id: str, title: str) -> None:
        """Emit session title updated event"""
        self.custom_event(
            "session_title_updated", {"session_id": session_id, "title": title}
        )

    def assistant_response(self, data: Dict[str, Any]) -> None:
        """Emit assistant response card event"""
        self.custom_event("assistant_response", data)

    def pattern_started(
        self,
        pattern_id: str,
        pattern_type: str,
        parent_pattern_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        instance_info: Optional[Dict[str, Any]] = None,
        started_at: Optional[str] = None,
    ) -> None:
        """Emit pattern started event
        
        Args:
            pattern_id: Unique identifier for the pattern
            pattern_type: Type of pattern (sequential, parallel, repeat, switch, loop)
            parent_pattern_id: ID of parent pattern if nested, None if top-level
            name: Optional pattern name from YAML
            description: Optional pattern description from YAML
            instance_info: Optional dict with instance count and IDs for repeat patterns
            started_at: Optional ISO timestamp when pattern started
        """
        if not started_at:
            started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        event_data = {
            "pattern_id": pattern_id,
            "pattern_type": pattern_type,
            "started_at": started_at,
        }
        
        if parent_pattern_id is not None:
            event_data["parent_pattern_id"] = parent_pattern_id
        
        if name:
            event_data["name"] = name
        
        if description:
            event_data["description"] = description
        
        if instance_info:
            event_data["instance_info"] = instance_info
        
        self.custom_event("pattern_started", event_data)

    def pattern_finished(
        self,
        pattern_id: str,
        ended_at: Optional[str] = None,
        elapsed_ms: Optional[int] = None,
        error: Optional[str] = None,
    ) -> None:
        """Emit pattern finished event
        
        Args:
            pattern_id: Unique identifier for the pattern
            ended_at: Optional ISO timestamp when pattern ended
            elapsed_ms: Optional elapsed time in milliseconds
            error: Optional error message if pattern failed
        """
        if not ended_at:
            ended_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        event_data = {
            "pattern_id": pattern_id,
            "ended_at": ended_at,
        }
        
        if elapsed_ms is not None:
            event_data["elapsed_ms"] = elapsed_ms
        
        if error:
            event_data["error"] = error
        
        self.custom_event("pattern_finished", event_data)

