import asyncio
import json
import time
from typing import Any, Dict, List, Optional

from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.frameworks.framework_config_manager import FrameworkConfigManager
from topaz_agent_kit.core.configuration_engine import ConfigurationResult
from topaz_agent_kit.core.exceptions import PipelineError, PipelineStoppedByUser
from topaz_agent_kit.transport.agent_bus import AgentBus
from topaz_agent_kit.core.output_manager import OutputManager
from topaz_agent_kit.core.agent_runner import AgentRunner
from topaz_agent_kit.core.runner_compiler import RunnerCompiler
from topaz_agent_kit.utils.json_utils import JSONUtils


class PipelineRunner:
    """Config-driven DAG executor supporting sequential, parallel, optional nodes, and joins."""

    def __init__(
        self,
        pattern_config: Dict[str, Any],
        config_result: Optional[ConfigurationResult] = None,
    ) -> None:
        """Initialize PipelineRunner with pattern configuration and optional configuration result."""
        self.pattern_config = pattern_config
        self.config_result = config_result

        # Initialize logger
        self.logger = Logger("PipelineRunner")

        # Store pipeline and UI configuration for test access
        if config_result:
            self.pipeline_config = config_result.pipeline_config
            self.ui_config = config_result.ui_config
        else:
            self.pipeline_config = {}
            self.ui_config = {}

        # Initialize agent storage
        self.agents = {}

        # Initialize framework configuration manager
        self.framework_config_manager = FrameworkConfigManager()

        # Initialize output manager for intermediate and final outputs
        self.output_manager = OutputManager(self.pipeline_config)

        # Initialize agent bus for unified transport
        # Add project_dir and pipeline_dir to config for agent config file loading
        agent_bus_config = self.pipeline_config.copy()
        if config_result and hasattr(config_result, "project_dir"):
            agent_bus_config["project_dir"] = config_result.project_dir

        self.agent_bus = AgentBus(
            agents_by_id={},  # Will be populated with built agents
            config=agent_bus_config,
            emitter=None,  # Will be set in run() method when emitter is available
        )

        # Initialize agent runner for agent execution (share agent_bus and pipeline structure)
        self.agent_runner = AgentRunner(
            config_result, self.agent_bus, self._get_pipeline_structure
        )

        # Initialize runner compiler after agent_runner is created
        self.runner_compiler = RunnerCompiler(
            agent_runner=self.agent_runner,
            logger=self.logger,
            populate_upstream_context_func=None,  # Will be set by caller
            output_manager=self.output_manager,
            config_result=config_result,
        )
        # Inject pipeline_config into runner_compiler for global settings
        self.runner_compiler.pipeline_config = self.pipeline_config

        # Debug: Log orchestrator config if present
        if self.pipeline_config and "orchestrator" in self.pipeline_config:
            self.logger.info(
                "Found orchestrator config: {}", self.pipeline_config["orchestrator"]
            )
        else:
            self.logger.warning("No orchestrator config found in pipeline_config")
            self.logger.info(
                "Pipeline config keys: {}", list(self.pipeline_config.keys())
            )

        # Debug: Log what we're passing to agent bus
        self.logger.debug(
            "Agent bus config keys: {}",
            list(self.pipeline_config.keys()) if self.pipeline_config else "None",
        )
        self.logger.debug("Pattern structure: {}", self.pattern_config)
        self.logger.debug(
            "Agent bus config agents count: {}",
            len(self.pipeline_config.get("agents", [])) if self.pipeline_config else 0,
        )
        self.logger.debug(
            "Agent bus pipeline_dir: {}", agent_bus_config.get("pipeline_dir")
        )
        self.logger.debug(
            "Agent bus project_dir: {}", agent_bus_config.get("project_dir")
        )

    def _get_agent_info_from_config(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get agent information from configuration"""
        try:
            self.logger.debug("🔍 Getting agent info for: {}", node_id)

            # Try to get agent info from agent factory if available
            if hasattr(self, "agent_runner") and self.agent_runner:
                # Create context with agent_factory if available
                context = {}
                if (
                    hasattr(self.agent_runner, "config_result")
                    and self.agent_runner.config_result
                ):
                    # Get agent factory from config_result
                    from topaz_agent_kit.agents.agent_factory import AgentFactory

                    agent_factory = AgentFactory(self.agent_runner.config_result)
                    context["agent_factory"] = agent_factory

                agent_info = self.agent_runner.get_agent_info(node_id, context)
                self.logger.debug("🔍 Agent info from agent_runner: {}", agent_info)
                if agent_info:
                    return agent_info

            # Fallback: try to get from config_result directly
            if hasattr(self, "config_result") and self.config_result:
                # Look for agent config in the pipeline config
                agents = self.config_result.pipeline_config.get("agents", [])
                self.logger.debug(
                    "🔍 Available agents in config: {}",
                    [a.get("id") if isinstance(a, dict) else str(a) for a in agents],
                )
                for agent in agents:
                    if isinstance(agent, dict) and agent.get("id") == node_id:
                        agent_info = {
                            "id": node_id,
                            "run_mode": agent.get("run_mode", "local"),
                            "type": agent.get("type"),
                            "name": agent.get("name"),
                        }
                        self.logger.debug(
                            "🔍 Agent info from config_result: {}", agent_info
                        )
                        return agent_info

            self.logger.warning("🔍 No agent info found for: {}", node_id)
            return None

        except Exception as e:
            self.logger.warning("Failed to get agent info for {}: {}", node_id, e)
            return None

    def _get_pipeline_structure(self) -> Dict[str, Any]:
        """Extract pipeline structure from pattern-only configuration"""
        # Get agent IDs from the pipeline config (not from pattern)
        nodes = self.pipeline_config.get("nodes", [])

        # Extract node IDs from the nodes structure
        node_ids = []
        for node in nodes:
            if isinstance(node, dict) and "id" in node:
                node_ids.append(node["id"])
            elif isinstance(node, str):
                node_ids.append(node)

        return {"agents": node_ids, "pattern": self.pattern_config}

    def _initialize_upstream_context(self, context: Dict[str, Any]) -> None:
        """
        Initialize upstream context with user input as a pseudo-agent.
        This makes user input available to all agents through the standard upstream mechanism.
        """
        try:
            # Get user input from context
            user_text = context.get("user_text", "")

            if not user_text:
                self.logger.warning(
                    "No user_text found in context - skipping user_input initialization"
                )
                return

            # Initialize upstream context if it doesn't exist
            if "upstream" not in context:
                context["upstream"] = {}

            # Add user_input as a pseudo-agent in upstream context
            context["upstream"]["user_input"] = {
                "result": user_text,
                "parsed": {
                    "user_text": user_text,
                    # "question": user_text,
                    # "user_message": user_text,
                    # "input": user_text,
                    # "input_text": user_text,
                    # "input_message": user_text,
                    # "query": user_text,
                    # "query_text": user_text,
                    # "message": user_text,
                    # "text": user_text,
                    # "user_input": user_text
                },
            }

            self.logger.debug(
                "Initialized user_input in upstream context: {} chars", len(user_text)
            )

        except Exception as e:
            self.logger.error(
                "Failed to initialize user_input in upstream context: {}", e
            )
            # Don't fail the pipeline for user input initialization issues

    def _populate_upstream_context(
        self, node_id: str, result: Any, context: Dict[str, Any]
    ) -> None:
        """
        Populate the upstream context so downstream agents can access upstream agent results.

        This method stores agent results in the context structure that generated agents
        expect for their _get_upstream_variable methods to work properly.

        Args:
            node_id: ID of the agent that just executed
            result: Result from the agent execution
            context: Pipeline execution context
        """
        try:
            # Initialize upstream context if it doesn't exist
            if "upstream" not in context:
                context["upstream"] = {}

            # Extract the actual result content (handle different result types)
            # NOTE: AgentOutputParser.parse_agent_output() already parses outputs, so result should be a dict
            # However, if JSON parsing failed, it may have returned {"content": "<json string>"}
            if result is None:
                self.logger.warning("Agent {} returned None result", node_id)
                result_content = {}
                parsed_content = {}
            elif hasattr(result, "content"):
                # Handle objects with .content attribute (like LLM responses)
                result_content = result.content
                # Parse if it's a string
                if isinstance(result_content, str):
                    parsed_content = JSONUtils.parse_json_from_text(result_content, expect_json=False)
                else:
                    parsed_content = result_content
            elif isinstance(result, dict):
                # Check if this is a fallback from failed JSON parsing: {"content": "<json string>"}
                # If so, parse the content string
                if "content" in result and isinstance(result.get("content"), str) and len(result) == 1:
                    # This is likely a JSON parse failure fallback - try parsing the content
                    content_str = result["content"]
                    parsed_content = JSONUtils.parse_json_from_text(content_str, expect_json=False)
                    # If parsing succeeded, use the parsed dict; otherwise use original
                    # Check if we got a proper dict (not the {"content": ...} fallback)
                    if isinstance(parsed_content, dict) and (len(parsed_content) > 1 or "content" not in parsed_content):
                        # Parsing succeeded - use the parsed dict
                        result_content = parsed_content
                    else:
                        # Parsing failed again - keep original structure
                        result_content = result["content"]
                        parsed_content = result
                elif "content" in result and result.get("content"):
                    # SDK-style 'content' field (already parsed or dict)
                    result_content = result["content"]
                    parsed_content = result_content
                # Handle execute_agent structured responses (MVP-6.0 format)
                elif "result" in result and "agent" in result:
                    result_content = result["result"]
                    if isinstance(result_content, str):
                        parsed_content = JSONUtils.parse_json_from_text(result_content, expect_json=False)
                    else:
                        parsed_content = result_content
                    self.logger.debug(
                        "Extracted agent result content from structured response: {} chars",
                        len(str(result_content)),
                    )
                else:
                    # Regular dictionary result (already parsed by AgentOutputParser)
                    result_content = result
                    parsed_content = result
            else:
                # Handle string or other types
                result_content = str(result)
                # Parse string as JSON if possible
                parsed_content = JSONUtils.parse_json_from_text(result_content, expect_json=False)

            self.logger.info(
                "Using normalized agent output: {} (keys: {})",
                node_id,
                list(parsed_content.keys())
                if isinstance(parsed_content, dict)
                else "n/a",
            )
            # Log what we're about to store for observability
            self.logger.info(
                "Upstream store [{}]: type(result)={}, parsed_keys={}",
                node_id,
                type(result_content).__name__,
                list(parsed_content.keys())
                if isinstance(parsed_content, dict)
                else "n/a",
            )
            if node_id == "planner" and isinstance(parsed_content, dict):
                missing = [
                    k for k in ("expression", "steps") if k not in parsed_content
                ]
                if missing:
                    self.logger.info("Planner parsed output missing keys: {}", missing)

            # Remove content wrapping just before storing in context
            # This ensures we don't store nested {"content": {...}} structures
            def unwrap_content(data: Any) -> Any:
                """Recursively unwrap content wrapping like {"content": {...}}."""
                if isinstance(data, dict):
                    # Check if this is a content wrapper (only has "content" key)
                    if len(data) == 1 and "content" in data:
                        content_value = data["content"]
                        # Recursively unwrap nested content wrappers
                        if isinstance(content_value, dict) and len(content_value) == 1 and "content" in content_value:
                            return unwrap_content(content_value)
                        # Return the unwrapped content
                        return content_value
                    # Not a content wrapper, return as-is
                    return data
                # Not a dict, return as-is
                return data
            
            # Unwrap content from both result_content and parsed_content
            unwrapped_result = unwrap_content(result_content)
            unwrapped_parsed = unwrap_content(parsed_content)
            
            # Store the result in upstream context for pattern-based execution
            # In MVP-6.0, pattern execution handles the flow, so we just store the result
            context["upstream"][node_id] = {
                "result": unwrapped_result,
                "parsed": unwrapped_parsed,
            }

            # 🔎 Debug: Log raw agent output for troubleshooting expression evaluation
            try:
                raw_str = result_content if isinstance(result_content, str) else str(result_content)
                self.logger.output("Raw output [{}]: {} chars", node_id, len(raw_str))
                # For long outputs, log a small head
                self.logger.output("Raw output head [{}]: {}", node_id, raw_str[:500])
            except Exception:
                pass

            self.logger.debug(
                "Updated upstream context for {}: {} chars",
                node_id,
                len(str(result_content)),
            )

        except Exception as e:
            self.logger.error(
                "Failed to populate upstream context for {}: {}", node_id, e
            )
            # Don't fail the pipeline for context population issues

    # NOTE: Agent execution methods moved to AgentRunner class

    async def run(self, context: Dict[str, Any]) -> Any:
        """
        Execute the pipeline using pattern-only runners (sequential, parallel, loop).

        Args:
            context: Execution context containing user_text, intent, session, etc.

        Returns:
            Pipeline execution result or error response
        """

        # Attach emitter to agent bus if provided
        emitter = context.get("emitter")
        if emitter:
            self.agent_bus._emitter = emitter

            # Initialize upstream context for user input once
            self._initialize_upstream_context(context)

        # Compile and run the pattern
        # Use the already initialized runner_compiler (with pipeline_config)
        self.runner_compiler.populate_upstream_context_func = (
            self._populate_upstream_context
        )
        self.runner_compiler.gate_lookup_func = self._get_gate_config
        self.runner_compiler.pipeline_runner_gate_handler_func = (
            self._handle_gate_execution
        )

        composed = self.runner_compiler.compile(self.pattern_config, is_top_level=True)
        
        pattern_results = await composed.run(context)

        # Process final outputs if configured
        final_output = None
        try:
            if emitter and self.output_manager.has_final_output():
                final_output = self.output_manager.process_final_output(
                    pattern_results, emitter
                )
                if final_output:
                    self.logger.info(
                        "Processed final output: {} chars", len(final_output)
                    )
        except Exception as e:
            self.logger.warning("Failed to process final output: {}", e)

        # Include final_output in pattern_results if available
        if final_output:
            if not isinstance(pattern_results, dict):
                pattern_results = {}
            pattern_results["final_output"] = final_output

        return pattern_results

    def _get_gates(self) -> List[Dict[str, Any]]:
        """Get gates configuration from pipeline config"""
        try:
            gates = self.pipeline_config.get("gates", [])
            self.logger.info(
                "Loaded {} gates: {}", len(gates), [g.get("id") for g in gates]
            )
            return gates
        except Exception:
            return []

    def _get_gate_config(self, gate_id: str) -> Optional[Dict[str, Any]]:
        """Look up gate configuration by ID"""
        gates = self.pipeline_config.get("gates", [])
        for gate in gates:
            if gate.get("id") == gate_id:
                return gate
        return None

    async def _handle_gate_execution(
        self,
        context: Dict[str, Any],
        gate_id: str,
        gate_config: Dict[str, Any],
        flow_control_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute HITL gate and handle flow control decisions.

        Returns:
            result: {"decision": "approve/continue", "data": {...}, "flow_action": "continue/retry/skip/stop"}
        """
        # Get effective gate configuration with defaults
        effective_config = self._get_effective_gate_config(gate_config)

        gate_type = effective_config.get("type", "approval")
        title = effective_config.get("title", "Approval Required")
        description = effective_config.get("description", "")
        fields = effective_config.get("fields", [])
        options = effective_config.get("options", [])
        options_source = effective_config.get("options_source")  # e.g., "agent_id.key.path"
        buttons = effective_config.get("buttons", {})
        timeout_ms = int(effective_config.get("timeout_ms", 300000))
        on_timeout = effective_config.get("on_timeout", "reject")
        context_key = effective_config.get("context_key", gate_id)
        context_strategy = effective_config.get("context_strategy")  # e.g., 'append'
        preserve_feedback = effective_config.get("preserve_feedback", True)  # Default: preserve feedback for retry
        default_value = effective_config.get("default")  # For selection gates

        emitter = context.get("emitter")

        # Filter and render field-level conditions/defaults before emitting to UI
        filtered_fields = self._filter_gate_fields(fields, context)
        
        # Populate selection gate options only via explicit options_source (no heuristics)
        populated_options = self._populate_selection_options(
            options,
            context,
            gate_type,
            gate_id,
            options_source=options_source,
        )
        
        # Render default value for selection gates if it's a Jinja2 template
        if gate_type == "selection" and default_value and isinstance(default_value, str):
            try:
                from jinja2 import Environment, Undefined
                
                class SafeUndefined(Undefined):
                    """Custom Undefined class that returns empty string instead of raising errors."""
                    def __getattr__(self, name: str) -> Any:
                        return SafeUndefined()
                    
                    def __getitem__(self, key: Any) -> Any:
                        return SafeUndefined()
                    
                    def __str__(self) -> str:
                        return ""
                    
                    def __repr__(self) -> str:
                        return ""
                
                def get_nested_value(data: Any, path: str, default: Any = None) -> Any:
                    """Safely get nested value from dict using dot notation path."""
                    if not path or not isinstance(data, dict):
                        return default
                    parts = path.split(".")
                    value = data
                    for field in parts:
                        if isinstance(value, dict) and field in value:
                            value = value[field]
                        else:
                            return default
                    return value
                
                from topaz_agent_kit.utils.jinja2_filters import register_jinja2_filters
                
                env = Environment(undefined=SafeUndefined, autoescape=False)
                # Add custom filter for safe nested dict access
                env.filters['nested_get'] = get_nested_value
                register_jinja2_filters(env)
                # Check if it looks like a template (contains {{ or {%)
                if "{{" in default_value or "{%" in default_value:
                    tmpl = env.from_string(default_value)
                    # Build render context similar to description rendering
                    render_context = dict(context)
                    upstream = context.get("upstream", {}) if isinstance(context, dict) else {}
                    flat: Dict[str, Any] = {}
                    if isinstance(upstream, dict):
                        for agent_id, node in upstream.items():
                            # Handle accumulated loop results (list of results from multiple iterations)
                            if isinstance(node, list):
                                if not node:
                                    self.logger.debug("Upstream agent '{}' has empty list result", agent_id)
                                    continue
                                # Use the last element (most recent iteration's result)
                                node = node[-1]
                                if not isinstance(node, dict):
                                    self.logger.warning("Upstream agent '{}' list element is not a dict: {}", agent_id, type(node))
                                    continue
                            
                            if not isinstance(node, dict):
                                self.logger.warning("Upstream agent '{}' result is not a dict: {}", agent_id, type(node))
                                continue
                            
                            parsed = node.get("parsed")
                            if parsed is None:
                                # Check if there's an error or if parsing failed
                                if "error" in node:
                                    self.logger.warning("Upstream agent '{}' has error in result: {}", agent_id, node.get("error"))
                                elif "result" in node:
                                    # Try to use raw result if parsed is missing
                                    raw_result = node.get("result")
                                    self.logger.debug("Upstream agent '{}' missing 'parsed', using 'result' field (type: {})", agent_id, type(raw_result))
                                    if isinstance(raw_result, dict):
                                        parsed = raw_result
                                    else:
                                        self.logger.warning("Upstream agent '{}' 'result' field is not a dict: {}", agent_id, type(raw_result))
                                else:
                                    self.logger.warning("Upstream agent '{}' missing both 'parsed' and 'result' fields. Available keys: {}", agent_id, list(node.keys()))
                            
                            if isinstance(parsed, dict):
                                render_context.setdefault(agent_id, parsed)
                                # Log structure for debugging missing nested paths
                                if agent_id == "tci_document_extractor" and "extracted_data" not in parsed:
                                    self.logger.warning(
                                        "Upstream agent '{}' parsed output missing 'extracted_data' key. Available keys: {}. "
                                        "This may indicate agent execution failure or parsing error.",
                                        agent_id,
                                        list(parsed.keys())
                                    )
                                for k, v in parsed.items():
                                    flat.setdefault(k, v)
                    render_context.update({k: v for k, v in flat.items() if k not in render_context})
                    rendered_default = tmpl.render(**render_context)
                    # Strip whitespace from rendered default
                    rendered_default = rendered_default.strip() if isinstance(rendered_default, str) else rendered_default
                    # Update effective_config with rendered default
                    effective_config["default"] = rendered_default
                    default_value = rendered_default
                    self.logger.debug("Rendered default value for gate {}: '{}'", gate_id, default_value)
            except Exception as e:
                self.logger.warning("Failed to render default value for gate {}: {}, using as-is", gate_id, e)
        
        # After populating options, verify default value matches an option (for selection gates)
        if gate_type == "selection" and default_value and populated_options:
            # Check if default value matches any option
            default_matches = any(
                isinstance(opt, dict) and (opt.get("value") == default_value or opt.get("id") == default_value)
                for opt in populated_options
            )
            if not default_matches and default_value:
                self.logger.warning("Default value '{}' for gate {} does not match any option. Available option values: {}", 
                                  default_value, gate_id, [opt.get("value") if isinstance(opt, dict) else str(opt) for opt in populated_options[:5]])
                # Try to find a match by stripping whitespace
                for opt in populated_options:
                    if isinstance(opt, dict):
                        opt_value = str(opt.get("value", "")).strip()
                        if opt_value == str(default_value).strip():
                            effective_config["default"] = opt_value
                            default_value = opt_value
                            self.logger.debug("Fixed default value match by stripping whitespace: '{}'", default_value)
                            break

        # Ensure validation sees dynamically populated options for selection gates
        try:
            if gate_type == "selection":
                effective_config["options"] = populated_options or []
        except Exception:
            pass

        # Emit type-specific HITL request
        if emitter and hasattr(emitter, "hitl_request"):
            # Load description from file if it's a dict with jinja key, otherwise use as-is
            description_template = description
            if isinstance(description, dict) and "jinja" in description:
                # Load template from file using PromptLoader
                try:
                    from pathlib import Path
                    from topaz_agent_kit.utils.prompt_loader import PromptLoader
                    project_dir = context.get("project_dir")
                    if project_dir:
                        project_dir = Path(project_dir)
                        prompt_loader = PromptLoader(project_dir)
                        description_template = prompt_loader.load_prompt(description)
                        if not description_template:
                            self.logger.warning("Failed to load HITL description from file: {}, using empty string", description.get("jinja"))
                            description_template = ""
                        # Ensure description_template is a string
                        if not isinstance(description_template, str):
                            description_template = str(description_template) if description_template else ""
                    else:
                        self.logger.warning("No project_dir in context, cannot load HITL description from file")
                        description_template = ""
                except Exception as e:
                    self.logger.warning("Failed to load HITL description from file: {}, using empty string", e)
                    description_template = ""
            elif not isinstance(description, str):
                description_template = str(description) if description else ""
            
            # Ensure description_template is always a string at this point
            if not isinstance(description_template, str):
                description_template = str(description_template) if description_template else ""
            
            # Render description via Jinja if it contains templates
            try:
                from jinja2 import Environment, Undefined
                
                class SafeUndefined(Undefined):
                    """Custom Undefined class that returns empty string instead of raising errors."""
                    def __getattr__(self, name: str) -> Any:
                        return SafeUndefined()
                    
                    def __getitem__(self, key: Any) -> Any:
                        return SafeUndefined()
                    
                    def __str__(self) -> str:
                        return ""
                    
                    def __repr__(self) -> str:
                        return ""
                
                def get_nested_value(data: Any, path: str, default: Any = None) -> Any:
                    """Safely get nested value from dict using dot notation path."""
                    if not path or not isinstance(data, dict):
                        return default
                    parts = path.split(".")
                    value = data
                    for field in parts:
                        if isinstance(value, dict) and field in value:
                            value = value[field]
                        else:
                            return default
                    return value
                
                from topaz_agent_kit.utils.jinja2_filters import register_jinja2_filters
                
                env = Environment(undefined=SafeUndefined, autoescape=False)
                # Add custom filters
                env.filters['nested_get'] = get_nested_value
                register_jinja2_filters(env)
                tmpl = env.from_string(description_template if isinstance(description_template, str) else str(description_template))
                # Build render context similar to defaults rendering
                render_context = dict(context)
                upstream = context.get("upstream", {}) if isinstance(context, dict) else {}
                flat: Dict[str, Any] = {}
                if isinstance(upstream, dict):
                    for agent_id, node in upstream.items():
                        # Handle accumulated loop results (list of results from multiple iterations)
                        if isinstance(node, list):
                            if not node:
                                self.logger.debug("Upstream agent '{}' has empty list result", agent_id)
                                continue
                            # Use the last element (most recent iteration's result)
                            node = node[-1]
                            # Handle nested lists (list of lists) - keep extracting until we get a dict
                            # This can happen with nested loops where outer loop accumulates results
                            while isinstance(node, list):
                                if not node:
                                    self.logger.debug("Upstream agent '{}' has empty nested list", agent_id)
                                    break
                                node = node[-1]
                            if not isinstance(node, dict):
                                self.logger.warning("Upstream agent '{}' list element is not a dict: {}", agent_id, type(node))
                                continue
                        
                        if not isinstance(node, dict):
                            self.logger.warning("Upstream agent '{}' result is not a dict: {}", agent_id, type(node))
                            continue
                        
                        parsed = node.get("parsed")
                        if parsed is None:
                            # Check if there's an error or if parsing failed
                            if "error" in node:
                                self.logger.warning("Upstream agent '{}' has error in result: {}", agent_id, node.get("error"))
                            elif "result" in node:
                                # Try to use raw result if parsed is missing
                                raw_result = node.get("result")
                                self.logger.debug("Upstream agent '{}' missing 'parsed', using 'result' field (type: {})", agent_id, type(raw_result))
                                if isinstance(raw_result, dict):
                                    parsed = raw_result
                                else:
                                    self.logger.warning("Upstream agent '{}' 'result' field is not a dict: {}", agent_id, type(raw_result))
                            else:
                                self.logger.warning("Upstream agent '{}' missing both 'parsed' and 'result' fields. Available keys: {}", agent_id, list(node.keys()))
                        
                        # If parsed is a string, try to parse it as JSON
                        if isinstance(parsed, str):
                            try:
                                parsed = JSONUtils.parse_json_from_text(parsed, expect_json=False)
                            except Exception as e:
                                self.logger.debug("Failed to parse JSON string from agent '{}': {}", agent_id, e)
                                parsed = None
                        
                        if isinstance(parsed, dict):
                            render_context.setdefault(agent_id, parsed)
                            # Log structure for debugging missing nested paths
                            if agent_id == "tci_document_extractor" and "extracted_data" not in parsed:
                                self.logger.warning(
                                    "Upstream agent '{}' parsed output missing 'extracted_data' key. Available keys: {}. "
                                    "This may indicate agent execution failure or parsing error.",
                                    agent_id,
                                    list(parsed.keys())
                                )
                            for k, v in parsed.items():
                                flat.setdefault(k, v)
                render_context.update({k: v for k, v in flat.items() if k not in render_context})
                
                # Add loop item variables if available (e.g., current_claim, current_application)
                for key in ["current_claim", "current_application", "current_item"]:
                    if key in context:
                        render_context[key] = context[key]
                
                # Add gate options to context for label lookup in description templates
                if gate_type == "selection" and populated_options:
                    render_context["gate_options"] = populated_options
                description = tmpl.render(**render_context)
                # Ensure description is a string
                if not isinstance(description, str):
                    description = str(description) if description else ""
            except Exception as e:
                # Log the actual error for debugging instead of silently failing
                self.logger.error("Failed to render HITL gate description template for gate {}: {}", gate_id, e)
                # Fall back to empty string or original description string on render failure
                # description_template is guaranteed to be a string at this point (set above)
                if isinstance(description_template, str) and description_template:
                    description = description_template
                else:
                    description = ""
            # Get parent_pattern_id from context (set by pattern runners)
            parent_pattern_id = context.get("parent_pattern_id")
            emitter.hitl_request(
                gate_id=gate_id,
                gate_type=gate_type,
                title=title,
                description=description,
                fields=filtered_fields,
                options=populated_options,
                buttons=buttons,
                timeout_ms=timeout_ms,
                on_timeout=on_timeout,
                context_key=context_key,
                default=default_value if gate_type == "selection" else None,
                retry_target=flow_control_config.get("retry_target"),
                max_retries=flow_control_config.get("max_retries"),
                parent_pattern_id=parent_pattern_id,
            )

            # Register gate with AGUIService for backend lookup
            agui_service = context.get("agui_service")
            if agui_service and hasattr(agui_service, "create_hitl_gate"):
                # Create options list from buttons for AGUIService
                gate_options = (
                    list(buttons.keys()) if buttons else ["approve", "reject"]
                )
                agui_service.create_hitl_gate(gate_id, title, description, gate_options)

        # Await user response
        waiter = context.get("options", {}).get("hitl", {}).get("wait_for_approval")
        if not callable(waiter):
            # No waiter - auto-approve for CLI mode
            result = {"decision": "approve", "data": {}}

            # Emit hitl_result event for CLI auto-approve
            if emitter and hasattr(emitter, "hitl_result"):
                emitter.hitl_result(
                    gate_id=gate_id, decision="approve", actor="system", data={}
                )
        else:
            try:
                result = await waiter(gate_id, timeout_ms)
            except asyncio.TimeoutError:
                result = self._handle_gate_timeout(
                    gate_type, on_timeout, filtered_fields, populated_options, effective_config
                )
                if result is None:
                    raise PipelineError(f"HITL timeout for gate {gate_id}")

                # Emit hitl_result event for auto-decision due to timeout
                if emitter and hasattr(emitter, "hitl_result"):
                    emitter.hitl_result(
                        gate_id=gate_id,
                        decision=result.get("decision", "approve"),
                        actor="system",
                        data=result.get("data", {}),
                    )

        # Normalize checkbox input payloads to arrays (coerce "", null -> [], CSV -> list)
        try:
            if gate_type == "input" and isinstance(result, dict) and isinstance(result.get("data"), dict):
                field_types = {f.get("name"): f.get("type") for f in filtered_fields if isinstance(f, dict)}
                for fname, ftype in (field_types or {}).items():
                    if ftype == "checkbox" and fname in result["data"]:
                        v = result["data"].get(fname)
                        if v is None or v == "":
                            result["data"][fname] = []
                        elif isinstance(v, str):
                            coerced = None
                            try:
                                parsed = json.loads(v)
                                if isinstance(parsed, list):
                                    coerced = [str(x) for x in parsed]
                            except Exception:
                                pass
                            if coerced is None:
                                coerced = [s.strip() for s in v.split(",") if str(s).strip()]
                            result["data"][fname] = coerced
                        elif isinstance(v, (int, float)):
                            result["data"][fname] = [str(v)]
                        elif isinstance(v, dict):
                            result["data"][fname] = [
                                str(v.get("value") or v.get("id") or "")
                            ]
                        elif isinstance(v, list):
                            result["data"][fname] = [str(x) for x in v]
        except Exception:
            # Best-effort normalization only
            pass

        # For selection gates, do matching BEFORE validation
        # This ensures we can match the option even if validation would fail
        # CRITICAL: Selection matching must happen before validation because:
        # 1. Validation checks if "selection" is in data
        # 2. Matching replaces {"selection": "OPT-2"} with the complete option object
        # 3. If validation runs first and fails, matching never happens
        if gate_type == "selection":
            try:
                data = result.get("data", {})
                # CRITICAL: Extract selection value correctly - UI sends {"selection": "OPT-2"}
                # Handle both dict format {"selection": value} and direct value format
                if isinstance(data, dict):
                    selection_value = data.get("selection")
                else:
                    # If data is not a dict, it might be the selection value directly (legacy format)
                    selection_value = data
                
                # CRITICAL: Use populated_options if available (from options_source), otherwise fall back to effective_config options
                options_to_search = populated_options if populated_options else (effective_config.get("options", []) if effective_config else [])
                
                if selection_value and options_to_search:
                    # Log all available options for debugging
                    self.logger.info("Selection gate {}: user selected value='{}' (type: {}), available options: {}", 
                                    gate_id, selection_value, type(selection_value),
                                    [(opt.get("value") if isinstance(opt, dict) else str(opt), 
                                      opt.get("label") if isinstance(opt, dict) else "N/A") 
                                     for opt in options_to_search[:10]])
                    
                    # Find the selected option - use DIRECT comparison like the old working code
                    # OLD WORKING CODE: if isinstance(opt, dict) and (opt.get("value") == selection_value or opt.get("id") == selection_value)
                    selected_option = None
                    for opt in options_to_search:
                        if isinstance(opt, dict):
                            opt_value = opt.get("value")
                            opt_id = opt.get("id")
                            # Match by value or id (case-insensitive string comparison for safety)
                            if (opt_value and str(opt_value).strip() == str(selection_value).strip()) or \
                               (opt_id and str(opt_id).strip() == str(selection_value).strip()):
                                selected_option = opt
                                self.logger.info("Matched option: value='{}', id='{}', label='{}'", 
                                               opt_value, opt_id, opt.get("label", "N/A"))
                                break
                    
                    # Store the complete selected option object instead of just the selection value
                    if selected_option and isinstance(selected_option, dict):
                        # Replace data with the complete selected option object
                        result["data"] = selected_option
                        option_id = selected_option.get("value") or selected_option.get("id") or "unknown"
                        option_label = selected_option.get("label") or "N/A"
                        # CRITICAL: Verify the matched option's value matches what user selected
                        if str(option_id).strip() != str(selection_value).strip() and str(selected_option.get("id", "")).strip() != str(selection_value).strip():
                            self.logger.error("MATCHING ERROR in gate {}: User selected '{}' but matched option has value '{}'! This is a bug!", 
                                            gate_id, selection_value, option_id)
                        self.logger.info("Stored complete selected option object for gate {}: option_id={}, option_label={}, keys={}", 
                                       gate_id, option_id, option_label, list(selected_option.keys()))
                    else:
                        self.logger.error("Option lookup FAILED for gate {}: selection_value='{}' (type: {}), options_count={}, available_values={}", 
                                          gate_id, selection_value, type(selection_value), 
                                          len(options_to_search) if options_to_search else 0,
                                          [opt.get("value") if isinstance(opt, dict) else str(opt) for opt in options_to_search[:10]])
                elif not selection_value:
                    self.logger.warning("Selection gate {}: No selection value found in data: {}", gate_id, data)
                elif not options_to_search:
                    self.logger.error("Selection gate {}: No options available for matching! options_source={}, populated_options_count={}, effective_config_options_count={}", 
                                      gate_id, options_source, 
                                      len(populated_options) if populated_options else 0,
                                      len(effective_config.get("options", [])) if effective_config else 0)
            except Exception as e:
                self.logger.error("Failed to extract selected option for gate {}: {}", gate_id, e, exc_info=True)

        # Validate result based on gate type (use effective_config with dynamic options)
        # CRITICAL: For selection gates, validation happens AFTER matching so it can validate
        # the complete option object instead of just {"selection": "OPT-2"}
        self._validate_gate_result(result, gate_type, effective_config)

        self.logger.info("Gate result: {}", result)

        # Store result in context for downstream agents
        # Only store gate data in hitl if preserve_feedback is True (default) OR decision is not retry
        # This allows retried agents to access feedback when preserve_feedback=True (e.g., article_smith)
        # but skips storage when preserve_feedback=False (e.g., rate_case simple retry)
        # NOTE: context_key data (e.g., selected_options) is ALWAYS stored below for downstream agents
        # CRITICAL: Read data AFTER selection matching (line 905 may have replaced result["data"] with selected_option)
        decision = result.get("decision")
        should_preserve = preserve_feedback or decision not in ["retry", "skip"]
        
        if should_preserve:
            # CRITICAL: Use result.get("data") AFTER selection matching has completed
            # For selection gates, result["data"] should now be the complete selected_option object (not {"selection": "OPT-2"})
            hitl_data = result.get("data", {})
            context.setdefault("hitl", {})[gate_id] = {
                "decision": decision,
                "data": hitl_data,
                "gate_type": gate_type,
                "context_key": context_key,
                "context_strategy": context_strategy,
            }
            # Log what we're storing in HITL for selection gates
            if gate_type == "selection" and gate_id == "option_selection_gate":
                if isinstance(hitl_data, dict):
                    option_id = hitl_data.get("value") or hitl_data.get("id") or "unknown"
                    self.logger.info("Stored HITL data for {}: option_id={}, data_keys={}", gate_id, option_id, list(hitl_data.keys()))
                else:
                    self.logger.warning("HITL data for {} is not a dict: {}", gate_id, hitl_data)
            self.logger.info("Stored HITL data in context: {}", context.get("hitl", {}))
        else:
            self.logger.debug("Skipping HITL data storage for gate {} (preserve_feedback=False, decision={})", gate_id, decision)
        
        # CRITICAL: For retry decisions with preserve_feedback=false, clear context_key data
        # because we're generating new options and old selections are no longer valid
        if decision == "retry" and not preserve_feedback and context_key:
            gate_context_key = f"{gate_id}.{context_key}"
            if gate_context_key in context:
                self.logger.debug("Clearing context_key '{}' on retry (preserve_feedback=False)", gate_context_key)
                del context[gate_context_key]

        # Apply context_strategy (generic): overwrite by default; append if specified
        # CRITICAL: Store context_key data with gate prefix (e.g., option_validation_gate.selected_options)
        # for downstream agents (repeat pattern, recommender) to avoid naming conflicts with agent outputs.
        # BUT: For retry decisions with preserve_feedback=false, DON'T store old data (it's invalid for new options)
        # The new data will be stored when user submits the gate again after new options are generated
        try:
            # CRITICAL: Read data AFTER selection matching (line 901 may have replaced result["data"] with selected_option)
            data = result.get("data", {})
            
            # For selection gates, verify data is the complete option object (not just {"selection": "OPT-2"})
            if gate_type == "selection" and isinstance(data, dict):
                # If data still has "selection" key, it means matching failed or didn't run
                if "selection" in data and options_source:
                    selection_value = data.get("selection")
                    self.logger.error("CRITICAL: Selection gate {} data still contains 'selection' key after matching! selection='{}', data={}. This means option matching failed or was skipped!", 
                                     gate_id, selection_value, data)
                    # Try to match again as fallback
                    if selection_value and populated_options:
                        for opt in populated_options:
                            if isinstance(opt, dict):
                                opt_value = str(opt.get("value", "")).strip()
                                if opt_value == str(selection_value).strip():
                                    data = opt  # Replace with complete option object
                                    result["data"] = opt
                                    self.logger.warning("Fallback matching succeeded: matched '{}' to option with value '{}'", 
                                                       selection_value, opt_value)
                                    break
            
            # For retry with preserve_feedback=false, skip storing context_key (old data is invalid)
            if decision == "retry" and not preserve_feedback:
                self.logger.debug("Skipping context_key storage for retry (preserve_feedback=False, will store new data on next submission)")
            else:
                # Flatten single-field input for convenience (matches AgentRunner behavior)
                flattened_value = None
                if gate_type == "input" and isinstance(data, dict) and len(data) == 1:
                    _, flattened_value = next(iter(data.items()))
                
                # Store context_key data with gate prefix to avoid conflicts with agent outputs
                if context_key:
                    # Store at gate_id.context_key (e.g., option_validation_gate.selected_options)
                    gate_context_key = f"{gate_id}.{context_key}"
                    
                    if context_strategy == "append" and decision not in ["retry", "skip"]:
                        # Only build Q/A pairs for non-retry decisions (feedback for retried agent)
                        previous = context.get(gate_context_key)
                        if gate_type == "input" and flattened_value is not None:
                            # Use description variable (already rendered if it was a template)
                            qa_block = f"Q: {description}\nA: {flattened_value}"
                            # Dedupe: if previous ends with the same A: value, do not append again
                            if isinstance(previous, str):
                                prev_lines = [ln for ln in previous.split("\n") if ln and ln.strip()]
                                last_a = None
                                for ln in reversed(prev_lines):
                                    if ln and isinstance(ln, str) and ln.startswith("A: "):
                                        last_a = ln[3:].strip()
                                        break
                                if last_a is not None and last_a == str(flattened_value).strip():
                                    combined = previous  # skip duplicate append
                                else:
                                    combined = f"{previous}\n{qa_block}"
                            else:
                                combined = qa_block
                            context[gate_context_key] = combined
                        else:
                            appended = flattened_value if flattened_value is not None else str(data)
                            combined = f"{previous}\n{appended}" if previous else appended
                            context[gate_context_key] = combined
                    else:
                        # Overwrite (default) - Store for downstream agents with gate prefix
                        # For approval gates, store decision as boolean at gate_context_key for easier condition evaluation
                        if gate_type == "approval" and decision:
                            context[gate_context_key] = (decision.lower() == "approve")
                        else:
                            stored_value = flattened_value if flattened_value is not None else data
                            context[gate_context_key] = stored_value
                            # Log the stored value for selection gates to track what was selected
                            if gate_type == "selection" and gate_id == "option_selection_gate":
                                if isinstance(stored_value, dict):
                                    option_id = stored_value.get("value") or stored_value.get("id") or "unknown"
                                    option_label = stored_value.get("label") or "N/A"
                                    # CRITICAL: Verify stored option_id matches what was selected
                                    if "selection" in stored_value:
                                        self.logger.error("CRITICAL BUG: Stored value still contains 'selection' key! This should be the complete option object. stored_value={}", 
                                                         stored_value)
                                    self.logger.info("USER SELECTED OPTION in {}: option_id={}, option_label={}, stored at context_key={}, full_object={}", 
                                                   gate_id, option_id, option_label, gate_context_key, stored_value)
                                else:
                                    self.logger.warning("USER SELECTED OPTION in {}: value={} (NOT A DICT!), stored at context_key={}", 
                                                   gate_id, stored_value, gate_context_key)
                    self.logger.debug("Stored context_key '{}' at '{}' for downstream agents", context_key, gate_context_key)
        except Exception as e:
            self.logger.warning("Failed to apply context_strategy for gate {}: {}", gate_id, e)

        # Determine flow action based on gate type and user decision
        flow_action = self._determine_flow_action(
            result, gate_type, flow_control_config
        )
        result["flow_action"] = flow_action

        # Handle flow action
        if flow_action == "stop":
            raise PipelineStoppedByUser(gate_id, "User rejected approval")
        elif flow_action == "retry_node":
            # Trigger retry logic (handled by SequentialRunner)
            result["retry_target"] = flow_control_config.get("retry_target")
            result["max_retries"] = flow_control_config.get("max_retries", 3)
        elif flow_action == "skip_to_node":
            # Trigger skip logic (handled by SequentialRunner)
            result["skip_to"] = flow_control_config.get("skip_to")

        return result

    def _filter_gate_fields(self, fields: list, context: Dict[str, Any]) -> list:
        """Filter HITL fields based on optional 'condition' (expression) and render defaults.

        - Keeps fields with no condition
        - For fields with 'condition', evaluates using ExpressionEvaluator (same as node conditions); keeps only truthy
        - Renders 'default' when it's a Jinja2 string template
        """
        try:
            from jinja2 import Environment, Undefined
        except Exception:
            Environment = None  # type: ignore

        from topaz_agent_kit.utils.expression_evaluator import evaluate_expression
        filtered: list = []

        for field in fields or []:
            try:
                cond_expr = field.get("condition")
                keep = True
                if cond_expr:
                    # Use ExpressionEvaluator for conditions (same as node conditions)
                    try:
                        keep = evaluate_expression(cond_expr, context)
                    except Exception as e:
                        self.logger.warning("Condition evaluation failed for field {}: {}, defaulting to False", field.get("name", "unknown"), e)
                        keep = False
                if not keep:
                    continue

                # Copy field and drop condition before sending to UI
                f2 = dict(field)
                if "condition" in f2:
                    f2.pop("condition", None)

                # Render default if it's a string template
                default_val = f2.get("default")
                if isinstance(default_val, str) and Environment is not None:
                    try:
                        env = Environment(undefined=Undefined, autoescape=False)
                        tmpl = env.from_string(default_val)
                        # Build a rich render context:
                        # - root context
                        # - agent namespaces: render_context[agent_id] = upstream[agent_id].parsed
                        # - shallow merge of all parsed dicts for convenience (no overwrite)
                        render_context = dict(context)
                        upstream = context.get("upstream", {}) if isinstance(context, dict) else {}
                        flat: Dict[str, Any] = {}
                        if isinstance(upstream, dict):
                            for agent_id, node in upstream.items():
                                parsed = node.get("parsed") if isinstance(node, dict) else None
                                if isinstance(parsed, dict):
                                    # agent namespace
                                    render_context.setdefault(agent_id, parsed)
                                    # shallow flatten
                                    for k, v in parsed.items():
                                        flat.setdefault(k, v)
                        # merge flattened keys last so direct refs like {{ flights_input.* }} may resolve
                        render_context.update({k: v for k, v in flat.items() if k not in render_context})
                        rendered_default = tmpl.render(**render_context)
                        # Parse JSON string defaults for checkbox fields (multi-select)
                        if f2.get("type") == "checkbox" and isinstance(rendered_default, str):
                            try:
                                import json
                                parsed = json.loads(rendered_default)
                                if isinstance(parsed, list):
                                    f2["default"] = parsed
                                else:
                                    f2["default"] = rendered_default
                            except (json.JSONDecodeError, ValueError):
                                # Not JSON, use as-is
                                f2["default"] = rendered_default
                        else:
                            f2["default"] = rendered_default
                    except Exception:
                        # Leave default as-is on render failure
                        pass

                # Populate field options dynamically for select/checkbox/radio fields
                if f2.get("type") in ["select", "checkbox", "radio"]:
                    field_options = f2.get("options", [])
                    options_source = f2.get("options_source")
                    # Populate only via explicit options_source; no heuristics
                    populated_field_options = self._populate_field_options(
                        field_options, context, f2.get("name", ""), options_source=options_source
                    )
                    if populated_field_options:
                        f2["options"] = populated_field_options

                filtered.append(f2)
            except Exception as e:
                # On any failure, conservatively include the field as-is
                self.logger.warning("Error filtering field {}: {}, including as-is", field.get("name", "unknown"), e)
                f2 = dict(field)
                f2.pop("condition", None)
                filtered.append(f2)

        return filtered

    def _populate_selection_options(self, options: list, context: Dict[str, Any], gate_type: str, gate_id: str = None, options_source: str = None) -> list:
        """Populate selection gate options from explicit options_source only.
        
        Also filters options based on optional 'condition' expressions (similar to field filtering).
        """
        if gate_type != "selection":
            return options or []

        from topaz_agent_kit.utils.expression_evaluator import evaluate_expression

        # Prefer explicit options_source if provided
        try:
            if options_source and isinstance(options_source, str) and "." in options_source:
                parts = options_source.split(".")
                agent_id = parts[0]
                field_path = parts[1:]
                upstream = context.get("upstream", {})
                if agent_id in upstream:
                    node_data = upstream[agent_id]
                    # Handle accumulated loop results (list of results from multiple iterations)
                    if isinstance(node_data, list):
                        if not node_data:
                            self.logger.debug("Upstream agent '{}' has empty list result", agent_id)
                            node_data = None
                        else:
                            # Use the last element (most recent iteration's result)
                            node_data = node_data[-1]
                            if not isinstance(node_data, dict):
                                self.logger.warning("Upstream agent '{}' list element is not a dict: {}", agent_id, type(node_data))
                                node_data = None
                    
                    if node_data is None:
                        value = None
                    elif isinstance(node_data, dict):
                        value = node_data.get("parsed") if "parsed" in node_data else node_data
                    else:
                        value = node_data
                    
                    if value is not None:
                        for field in field_path:
                            if isinstance(value, dict) and field in value:
                                value = value[field]
                            else:
                                value = None
                                break
                    
                    if isinstance(value, list):
                        # Filter dynamic options from options_source if they have conditions
                        filtered = []
                        for opt in value:
                            if isinstance(opt, dict):
                                cond_expr = opt.get("condition")
                                if cond_expr:
                                    try:
                                        if not evaluate_expression(cond_expr, context):
                                            continue
                                    except Exception as e:
                                        self.logger.warning("Condition evaluation failed for option {}: {}, skipping", opt.get("value", "unknown"), e)
                                        continue
                                # Remove condition before sending to UI
                                opt_copy = dict(opt)
                                opt_copy.pop("condition", None)
                                filtered.append(opt_copy)
                            else:
                                filtered.append(opt)
                        return filtered
        except Exception:
            pass

        # If options are already provided, use them (static options)
        # Filter static options based on their conditions
        if options and len(options) > 0:
            filtered = []
            for opt in options:
                if not isinstance(opt, dict):
                    filtered.append(opt)
                    continue
                    
                cond_expr = opt.get("condition")
                keep = True
                if cond_expr:
                    try:
                        keep = evaluate_expression(cond_expr, context)
                    except Exception as e:
                        self.logger.warning("Condition evaluation failed for option {}: {}, skipping", opt.get("value", "unknown"), e)
                        keep = False
                
                if not keep:
                    continue
                
                # Copy option and remove condition before sending to UI
                opt_copy = dict(opt)
                opt_copy.pop("condition", None)
                
                # Render description if it contains Jinja2 templates
                if "description" in opt_copy and isinstance(opt_copy["description"], str):
                    try:
                        from jinja2 import Environment, Undefined
                        env = Environment(undefined=Undefined, autoescape=False)
                        if "{{" in opt_copy["description"] or "{%" in opt_copy["description"]:
                            # Build render context similar to gate description rendering
                            render_context = dict(context)
                            upstream = context.get("upstream", {}) if isinstance(context, dict) else {}
                            flat: Dict[str, Any] = {}
                            if isinstance(upstream, dict):
                                for agent_id, node in upstream.items():
                                    parsed = node.get("parsed") if isinstance(node, dict) else None
                                    if isinstance(parsed, dict):
                                        render_context.setdefault(agent_id, parsed)
                                        for k, v in parsed.items():
                                            flat.setdefault(k, v)
                            render_context.update(flat)
                            tmpl = env.from_string(opt_copy["description"])
                            opt_copy["description"] = tmpl.render(**render_context)
                    except Exception as e:
                        self.logger.warning("Failed to render option description template: {}, using original", e)
                        # Keep original description on render failure
                        pass
                
                filtered.append(opt_copy)
            
            return filtered

        # No options_source and no static options -> do not populate
        return []

    def _populate_field_options(self, field_options: list, context: Dict[str, Any], field_name: str, options_source: str = None) -> list:
        """Populate field options from explicit options_source only."""
        # Prefer explicit options_source if provided
        try:
            if options_source and isinstance(options_source, str) and "." in options_source:
                parts = options_source.split(".")
                agent_id = parts[0]
                field_path = parts[1:]
                upstream = context.get("upstream", {})
                if agent_id in upstream:
                    node_data = upstream[agent_id]
                    value = node_data.get("parsed") if isinstance(node_data, dict) else node_data
                    for field in field_path:
                        if isinstance(value, dict) and field in value:
                            value = value[field]
                        else:
                            value = None
                            break
                    if isinstance(value, list):
                        return value
        except Exception:
            pass

        # No options_source -> do not populate; use whatever field_options already has
        return field_options

    def _handle_gate_timeout(
        self,
        gate_type: str,
        on_timeout: str,
        fields: List[Dict],
        options: List[Dict],
        gate_config: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Handle gate timeout based on gate type and timeout policy"""
        if on_timeout == "approve":
            if gate_type == "approval":
                return {"decision": "approve", "data": {}}
            elif gate_type == "input":
                # Use field defaults or provide empty defaults for required fields
                data = {}
                for field in fields:
                    if "default" in field:
                        data[field["name"]] = field["default"]
                    elif field.get("required", False):
                        # Provide empty default for required fields without explicit defaults
                        if field.get("type") == "textarea":
                            data[field["name"]] = ""
                        elif field.get("type") == "select":
                            # Use first option as default
                            options = field.get("options", [])
                            data[field["name"]] = options[0]["value"] if options else ""
                        else:
                            data[field["name"]] = ""
                return {"decision": "continue", "data": data}
            elif gate_type == "selection":
                # Use default option
                default_option = next(
                    (
                        opt
                        for opt in options
                        if opt.get("value") == options[0].get("default")
                    ),
                    options[0] if options else None,
                )
                if default_option:
                    return {
                        "decision": "continue",
                        "data": {"selection": default_option["value"]},
                    }
                return {"decision": "continue", "data": {}}
        elif on_timeout == "reject":
            return None  # Will raise PipelineError
        elif on_timeout == "skip":
            return {"decision": "continue", "data": {}}
        elif on_timeout == "default":
            if gate_type == "selection":
                # Use the gate's default field, not the first option's default
                default_value = gate_config.get("default")
                if default_value:
                    default_option = next(
                        (opt for opt in options if opt.get("value") == default_value),
                        None,
                    )
                    if default_option:
                        return {
                            "decision": "continue",
                            "data": {"selection": default_option["value"]},
                        }
                # Fallback to first option if no default specified
                if options:
                    return {
                        "decision": "continue",
                        "data": {"selection": options[0]["value"]},
                    }
            return {"decision": "continue", "data": {}}

        return None

    def _get_default_buttons_for_gate_type(self, gate_type: str) -> Dict[str, Any]:
        """Get default button configuration for gate types"""
        defaults = {
            "approval": {
                "approve": {"label": "Approve", "description": "Approve and continue"},
                "reject": {"label": "Reject", "description": "Reject and stop"},
            },
            "input": {
                "continue": {
                    "label": "Continue",
                    "description": "Continue without input",
                },
                "retry": {
                    "label": "Retry with Input",
                    "description": "Retry with provided input",
                },
            },
            "selection": {
                "submit": {
                    "label": "Submit",
                    "description": "Submit selection and continue",
                }
            },
        }
        return defaults.get(gate_type, {})

    def _get_default_actions_for_gate_type(self, gate_type: str) -> Dict[str, str]:
        """Get default action configuration for gate types"""
        defaults = {
            "approval": {"on_approve": "continue", "on_reject": "stop"},
            "input": {"on_continue": "continue", "on_retry": "retry_node"},
            "selection": {"on_submit": "continue"},
        }
        return defaults.get(gate_type, {})

    def _get_effective_gate_config(self, gate_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get effective gate configuration with defaults applied"""
        gate_type = gate_config.get("type", "approval")

        # Start with the original config
        effective_config = gate_config.copy()

        # Apply default buttons if not specified
        if "buttons" not in effective_config:
            self.logger.debug(
                f"No custom buttons found for gate, applying defaults for type: {gate_type}"
            )
            effective_config["buttons"] = self._get_default_buttons_for_gate_type(
                gate_type
            )
        else:
            self.logger.info(
                f"Using custom buttons for gate: {effective_config.get('buttons')}"
            )

        return effective_config

    def _validate_gate_result(
        self, result: Dict[str, Any], gate_type: str, gate_config: Dict[str, Any]
    ) -> None:
        """Validate gate result based on gate type"""
        if not isinstance(result, dict):
            raise ValueError(f"Gate result must be a dict, got {type(result)}")

        decision = result.get("decision", "").lower()
        data = result.get("data", {})

        # Validate required fields for input gates (except retry/continue decisions)
        if gate_type == "input" and decision not in ["retry", "continue"]:
            for field in gate_config.get("fields", []):
                if field.get("required") and field["name"] not in data:
                    raise ValueError(
                        f"Required field '{field['name']}' missing from input gate result"
                    )

        # Validate selection data for selection gates
        elif gate_type == "selection":
            # NOTE: Validation for selection gates is minimal because matching logic (which runs BEFORE validation)
            # already handles all the heavy lifting:
            # 1. Matching finds the option from available options
            # 2. Matching replaces {"selection": "OPT-2"} with the complete option object
            # 3. Matching logs errors if it can't find the option
            # 
            # Validation here is just a sanity check that matching succeeded (data should be the complete option object)
            # If matching failed, it would have already logged an error, so we just verify the structure is correct
            if "selection" in data:
                # Matching didn't run or failed - this is unexpected since matching runs before validation
                # Log a warning but don't fail (matching already logged the error)
                selection_value = data.get("selection")
                self.logger.warning(
                    "Selection gate validation: data still contains 'selection' key after matching. "
                    "This indicates matching failed or didn't run. selection_value='{}', data={}",
                    selection_value, data
                )
                # Don't raise exception - matching already logged the error, and we want to continue
                # so downstream agents can handle the error gracefully
            elif "value" in data or "id" in data:
                # Matching succeeded - data is the complete option object
                # This is the expected state after matching
                self.logger.debug("Selection gate validation: option object structure is valid (has value='{}' or id='{}')", 
                                 data.get("value"), data.get("id"))
            else:
                # Neither selection key nor option object structure - this is unexpected
                # But don't fail hard - just log a warning
                self.logger.warning(
                    "Selection gate validation: data has unexpected structure. "
                    "Expected either 'selection' (before matching) or 'value'/'id' (after matching), "
                    "but got: data={}",
                    data
                )
                # Don't raise exception - let downstream agents handle gracefully

    def _determine_flow_action(
        self,
        result: Dict[str, Any],
        gate_type: str,
        flow_control_config: Dict[str, Any],
    ) -> str:
        """Determine flow action based on gate result and config"""
        decision = result.get("decision", "").lower()

        self.logger.info(
            "Determining flow action: decision='{}', flow_control_config={}",
            decision,
            flow_control_config,
        )

        # Generic button action handling: on_<button_name>
        action_key = f"on_{decision}"
        if action_key in flow_control_config:
            action = flow_control_config[action_key]
            self.logger.info("Found action key '{}' -> '{}'", action_key, action)
            return action

        # Default action if no specific button action is defined
        self.logger.info(
            "No action key '{}' found, using default 'continue'", action_key
        )
        return "continue"
