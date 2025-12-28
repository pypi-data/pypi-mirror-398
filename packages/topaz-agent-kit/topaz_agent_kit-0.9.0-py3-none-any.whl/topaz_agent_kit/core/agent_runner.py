import time
from typing import Any, Dict, List, Optional
from pathlib import Path

from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.agents.agent_factory import AgentFactory
from topaz_agent_kit.core.configuration_engine import ConfigurationResult
from topaz_agent_kit.core.exceptions import AgentError, ConfigurationError
from topaz_agent_kit.utils.json_utils import JSONUtils
from topaz_agent_kit.transport.agent_bus import AgentBus
from topaz_agent_kit.core.ag_ui_event_emitter import AGUIEventEmitter
from topaz_agent_kit.core.output_manager import OutputManager


class AgentRunner:
    """Reusable agent execution for both standalone and pipeline contexts.

    This class encapsulates the core agent execution logic extracted from PipelineRunner,
    making it available for both independent agent execution (via Orchestrator) and
    pipeline agent execution (via PipelineRunner).
    """

    def __init__(
        self,
        config_result: Optional[ConfigurationResult] = None,
        agent_bus: Optional[AgentBus] = None,
        pipeline_structure_getter: Optional[callable] = None,
    ) -> None:
        """Initialize AgentRunner with optional configuration result, agent bus, and pipeline structure getter."""
        self.config_result = config_result

        # Initialize logger
        self.logger = Logger("AgentRunner")

        # Store configuration for agent creation
        if config_result:
            self.pipeline_config = config_result.pipeline_config
            self.project_dir = getattr(config_result, "project_dir", None)
        else:
            self.pipeline_config = {}
            self.project_dir = None

        # Initialize agent storage
        self.agents = {}

        # Store pipeline structure getter
        self.pipeline_structure_getter = pipeline_structure_getter

        # Use provided agent bus or create new one
        if agent_bus:
            self.agent_bus = agent_bus
        else:
            # Initialize agent bus for unified transport
            # Use the full configuration that includes independent_agents
            agent_bus_config = {}
            if config_result and hasattr(config_result, "pipeline_config"):
                agent_bus_config = config_result.pipeline_config.copy()
            if config_result and hasattr(config_result, "project_dir"):
                agent_bus_config["project_dir"] = config_result.project_dir

            self.agent_bus = AgentBus(
                agents_by_id={},  # Will be populated with built agents
                config=agent_bus_config,
                emitter=None,  # Will be set when emitter is available
            )

    def _extract_base_agent_id(self, instance_id: str, instance_id_template: str = None) -> str:
        """Extract base agent ID from instance ID using the template pattern.
        
        Uses the instance_id_template from pipeline config to reverse-engineer
        the base agent ID. If template is not provided, falls back to pattern matching.
        
        Args:
            instance_id: Instance ID to extract base from (e.g., math_repeater_solver_0)
            instance_id_template: Template pattern from YAML (e.g., "{{node_id}}_{{index}}")
            
        Returns:
            Base agent ID, or original instance_id if extraction fails
        """
        if not instance_id_template:
            # Fallback: try to extract using common patterns
            import re
            # Pattern: _{number} at the end (e.g., math_repeater_solver_0)
            match = re.search(r'^(.+?)_(\d+)$', instance_id)
            if match:
                potential_base = match.group(1)
                # Only treat as instance if base has underscore (multi-part agent ID)
                if '_' in potential_base:
                    return potential_base
            return instance_id
        
        # Use template to reverse-engineer base agent ID
        # Template examples:
        # - "{{node_id}}_{{index}}" -> instance_id "math_repeater_solver_0" -> base "math_repeater_solver"
        # - "{{node_id}}_instance_{{index}}" -> instance_id "math_repeater_solver_instance_0" -> base "math_repeater_solver"
        # - "{{node_id}}_supplier_{{index}}" -> instance_id "math_repeater_solver_supplier_0" -> base "math_repeater_solver"
        
        import re
        
        # Extract the pattern between {{node_id}} and {{index}}
        # Template format: {{node_id}}<separator>{{index}}
        template_pattern = r'\{\{node_id\}\}(.*?)\{\{index\}\}'
        match = re.search(template_pattern, instance_id_template)
        
        if match:
            separator = match.group(1)
            # Build regex to match: <base><separator><number>
            # Escape special regex characters in separator
            escaped_separator = re.escape(separator)
            instance_pattern = rf'^(.+?){escaped_separator}(\d+)$'
            
            instance_match = re.match(instance_pattern, instance_id)
            if instance_match:
                return instance_match.group(1)
        
        # Fallback: try simple pattern matching
        match = re.search(r'^(.+?)_(\d+)$', instance_id)
        if match:
            potential_base = match.group(1)
            if '_' in potential_base:
                return potential_base
        
        return instance_id

    def get_agent_info(self, node_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get agent information from the agent factory"""
        try:
            agent_factory = context.get("agent_factory")
            if not agent_factory:
                return {}

            # Try direct lookup first
            info = agent_factory.get_agent_info(node_id)
            
            # If no info found, try extracting base_agent_id (might be an instance ID)
            if not info:
                # Get instance_id_template from context (set by RepeatPatternRunner)
                instance_id_template = context.get("_instance_id_template")
                base_agent_id_from_context = context.get("_base_agent_id")
                
                # Use base_agent_id from context if available (most reliable)
                if base_agent_id_from_context:
                    info = agent_factory.get_agent_info(base_agent_id_from_context) or {}
                elif instance_id_template:
                    # Extract base using template pattern from YAML
                    base_agent_id = self._extract_base_agent_id(node_id, instance_id_template)
                    if base_agent_id != node_id:
                        info = agent_factory.get_agent_info(base_agent_id) or {}
                else:
                    # Fallback: try pattern matching without template
                    base_agent_id = self._extract_base_agent_id(node_id)
                    if base_agent_id != node_id:
                        info = agent_factory.get_agent_info(base_agent_id) or {}
            
            return info or {}

        except Exception as e:
            self.logger.error("Failed to get agent info for {}: {}", node_id, e)
            return {}

    def get_filtered_tools_for_agent(
        self, agent_info: Dict[str, Any], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get filtered MCP tools for a specific agent"""
        try:
            mcp_tools_cache = context.get("mcp_tools_cache", {})
            self.logger.debug(
                "MCP tools cache type: {}, content: {}",
                type(mcp_tools_cache),
                mcp_tools_cache,
            )

            if not mcp_tools_cache:
                self.logger.debug("No MCP tools cache available")
                return []

            # Get agent roles from agent info
            agent_roles = agent_info.get("roles", [])
            if not agent_roles:
                self.logger.debug("No roles defined for agent, returning all tools")
                return list(mcp_tools_cache.values())

            # Filter tools based on agent roles
            filtered_tools = []
            for tool_name, tool_info in mcp_tools_cache.items():
                tool_roles = tool_info.get("roles", [])
                if not tool_roles or any(role in tool_roles for role in agent_roles):
                    filtered_tools.append(tool_info)

            self.logger.debug(
                "Filtered {} tools for agent with roles: {}",
                len(filtered_tools),
                agent_roles,
            )
            return filtered_tools

        except Exception as e:
            self.logger.error("Failed to filter MCP tools for agent: {}", e)
            return []

    async def build_agent(self, base_agent_id: str, instance_id_or_context: str | Dict[str, Any] | None = None, context: Dict[str, Any] | None = None) -> Any:
        """Build agent on-demand when it's about to execute (extracted from PipelineRunner._build_agent_if_needed)
        
        Args:
            base_agent_id: Base agent ID for config lookup (e.g., "math_solver")
            instance_id_or_context: Either instance_id (str) for new signature, or context (dict) for old signature
            context: Execution context (required for new signature, optional for old)
        """
        # Handle backward compatibility: old signature was build_agent(node_id, context)
        # New signature: build_agent(base_agent_id, instance_id, context)
        # Old signature: build_agent(node_id, context)
        
        if isinstance(instance_id_or_context, dict):
            # Old signature: build_agent(node_id, context)
            context = instance_id_or_context
            instance_id = None
        elif isinstance(instance_id_or_context, str):
            # New signature: build_agent(base_agent_id, instance_id, context)
            instance_id = instance_id_or_context
        else:
            # instance_id_or_context is None
            instance_id = None
        
        if context is None:
            raise ValueError("build_agent requires context")
        
        # If instance_id not provided, use base_agent_id (backward compatibility)
        if instance_id is None:
            instance_id = base_agent_id
        
        # Use instance_id for caching and registration (so each instance is unique)
        if instance_id not in self.agents:
            self.logger.info("Building agent on-demand: {} (instance: {})", base_agent_id, instance_id)

            # Create agent factory if not available
            agent_factory = context.get("agent_factory")
            if not agent_factory:
                if not self.config_result:
                    raise ConfigurationError(
                        "Configuration result not available for agent creation"
                    )

                # Create agent factory with configuration result
                agent_factory = AgentFactory(self.config_result)
                context["agent_factory"] = agent_factory
                self.logger.info("Created new AgentFactory for agent creation")

                # Create agent using base_agent_id for config lookup
            try:
                agent = agent_factory.create_agent(
                    base_agent_id, emitter=context.get("emitter")
                )

                # Update agent_id and name to instance_id to keep them in sync with node_id
                # This ensures agent.agent_id matches the instance ID used in context (node_id)
                # Framework SDKs use these as identifiers, so instance IDs are fine
                setattr(agent, "agent_id", instance_id)
                setattr(agent, "name", instance_id)

                # Get filtered MCP tools for this agent (use base_agent_id for config lookup)
                # Note: Agent initialization with tools will be handled by LocalClient when needed
                agent_info = self.get_agent_info(base_agent_id, context)
                _filtered_tools = self.get_filtered_tools_for_agent(agent_info, context)

                # Cache the built agent with instance_id (so each instance is cached separately)
                self.agents[instance_id] = agent

                # Add to agent_bus with instance_id (so each instance is registered separately)
                self.agent_bus._agents_by_id[instance_id] = agent

                self.logger.info("Agent {} (instance: {}) built and cached", base_agent_id, instance_id)

            except Exception as e:
                self.logger.error("Failed to build agent {} (instance: {}): {}", base_agent_id, instance_id, e)
                raise AgentError(f"Agent {base_agent_id} (instance: {instance_id}) build failed: {e}")

        return self.agents[instance_id]

    def get_agent_inputs_data(
        self, agent_id: str, context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract agent inputs data from context for UI display.

        Args:
            agent_id: The agent ID to get inputs for
            context: The execution context containing agent_inputs

        Returns:
            The agent inputs data if found, None otherwise
        """
        inputs_data = (
            context.get("agent_inputs", {}).get(agent_id)
            if isinstance(context.get("agent_inputs"), dict)
            else None
        )

        if inputs_data is not None:
            self.logger.debug(
                "Found agent_inputs in context for {}: {}", agent_id, inputs_data
            )
        else:
            self.logger.debug("No agent inputs found in context for {}", agent_id)

        return inputs_data

    async def execute_agent(
        self,
        node_id: str,
        agent: Any,
        context: Dict[str, Any],
        previous_agent: Optional[str] = None,
    ) -> Any:
        """Execute agent via agent bus (extracted from PipelineRunner._execute_agent)"""
        original_node_id = node_id
        
        # For repeat patterns with nested sequential flows, create per-instance node_ids
        # so AG-UI can distinguish instances (e.g., File Report Generator (Instance 1..N)).
        # We only adjust node_id if it doesn't already look like an instance ID.
        try:
            import re
            # Detect if node_id already encodes an instance (trailing _<number>)
            is_instance_like = bool(re.search(r"_\d+$", node_id))
            if not is_instance_like:
                instance_context_key = context.get("_instance_context_key")
                if instance_context_key:
                    instance_ctx = context.get(instance_context_key, {})
                    if isinstance(instance_ctx, dict):
                        idx = instance_ctx.get("index")
                        if isinstance(idx, int):
                            node_id = f"{node_id}_{idx}"
                            self.logger.debug(
                                "Adjusted node_id '{}' -> '{}' using instance context key '{}' (index={})",
                                original_node_id,
                                node_id,
                                instance_context_key,
                                idx,
                            )
        except Exception as e:
            # Non-fatal: fall back to original node_id on any error
            self.logger.debug(
                "Failed to adjust node_id '{}' for instance context: {}",
                original_node_id,
                e,
            )
            node_id = original_node_id
        
        self.logger.info(
            "Executing agent (unified): {} with agent type: {}",
            node_id,
            type(agent).__name__,
        )

        # Record start time for timing calculation
        import time

        start_time = time.time()
        start_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start_time))
        context["started_at"] = start_timestamp

        # Populate framework/model/run_mode from AgentFactory BEFORE step_started
        # This allows us to include header info in step_started event
        framework = None
        model = None
        run_mode = None
        
        try:
            # Get agent factory from context (created by PipelineRunner)
            agent_factory = context.get("agent_factory")
            if agent_factory:
                # Try to get agent info with node_id first
                info = agent_factory.get_agent_info(node_id)
                
                # If no info found, node_id might be an instance ID - extract base_agent_id
                if not info:
                    # Get instance_id_template from context (set by RepeatPatternRunner)
                    instance_id_template = context.get("_instance_id_template")
                    base_agent_id_from_context = context.get("_base_agent_id")
                    
                    # Use base_agent_id from context if available (most reliable)
                    if base_agent_id_from_context:
                        base_agent_id_for_config = base_agent_id_from_context
                        info = agent_factory.get_agent_info(base_agent_id_for_config) or {}
                        self.logger.debug(
                            "Using base_agent_id '{}' from context for instance_id '{}'",
                            base_agent_id_for_config,
                            node_id
                        )
                    elif instance_id_template:
                        # Extract base using template pattern from YAML
                        base_agent_id_for_config = self._extract_base_agent_id(node_id, instance_id_template)
                        if base_agent_id_for_config != node_id:
                            info = agent_factory.get_agent_info(base_agent_id_for_config) or {}
                            self.logger.debug(
                                "Extracted base_agent_id '{}' from instance_id '{}' using template '{}'",
                                base_agent_id_for_config,
                                node_id,
                                instance_id_template
                            )
                        else:
                            base_agent_id_for_config = node_id
                    else:
                        # Fallback: try pattern matching without template
                        base_agent_id_for_config = self._extract_base_agent_id(node_id)
                        if base_agent_id_for_config != node_id:
                            info = agent_factory.get_agent_info(base_agent_id_for_config) or {}
                            self.logger.debug(
                                "Extracted base_agent_id '{}' from instance_id '{}' using pattern matching",
                                base_agent_id_for_config,
                                node_id
                            )
                        else:
                            base_agent_id_for_config = node_id
                else:
                    # Found config with node_id, use it as-is
                    base_agent_id_for_config = node_id
                    info = info or {}

                framework = info.get("type")
                model = info.get("model")
                run_mode = info.get("run_mode")

                # Make agent info available in context (mirrors pipeline path)
                context["agent_config"] = info
                context["framework"] = framework
                context["model"] = model
                context["run_mode"] = run_mode

                self.logger.info(
                    "Agent info for {}: framework={}, model={}, run_mode={}",
                    node_id,
                    framework,
                    model,
                    run_mode,
                )
            else:
                self.logger.warning("No agent_factory in context for {}", node_id)
        except Exception as e:
            self.logger.warning("Failed to resolve agent info for {}: {}", node_id, e)

        # CRITICAL: Ensure node_id is adjusted BEFORE step_started is called
        # This ensures that step_started receives the instance ID (e.g., enhanced_math_repeater_file_reader_0)
        # instead of the base agent ID (e.g., enhanced_math_repeater_file_reader)
        # StepRunner should have already constructed instance_id and passed it here, but if it didn't,
        # we need to adjust it here to ensure step_started gets the correct instance ID
        import re
        final_node_id = node_id
        is_already_instance = bool(re.search(r"_\d+$", node_id))
        
        if not is_already_instance:
            # node_id doesn't look like an instance ID - try to adjust it
            instance_context_key = context.get("_instance_context_key")
            if instance_context_key:
                instance_ctx = context.get(instance_context_key, {})
                if isinstance(instance_ctx, dict):
                    idx = instance_ctx.get("index")
                    if isinstance(idx, int):
                        final_node_id = f"{node_id}_{idx}"
                        self.logger.debug(
                            "Adjusted node_id '{}' -> '{}' before step_started (instance_context_key='{}', index={})",
                            node_id,
                            final_node_id,
                            instance_context_key,
                            idx,
                        )
                    else:
                        self.logger.warning(
                            "Instance context key '{}' found but 'index' is not an integer: {} (type: {})",
                            instance_context_key, idx, type(idx)
                        )
                else:
                    self.logger.warning(
                        "Instance context key '{}' found but value is not a dict: {} (type: {})",
                        instance_context_key, instance_ctx, type(instance_ctx)
                    )
            else:
                # Log available context keys for debugging
                context_keys = [k for k in context.keys() if k.startswith("_instance") or k.startswith("file_instance")]
                self.logger.debug(
                    "No instance context key found. Available instance-related keys: {}",
                    context_keys
                )
        else:
            self.logger.debug(
                "node_id '{}' already looks like an instance ID, no adjustment needed",
                node_id
            )
        
        # Use final_node_id for step_started to ensure it always gets the instance ID
        node_id = final_node_id
        
        # Store node_id in context BEFORE step_started so it's available everywhere
        # This ensures consistency - LocalClient will also set context["node_id"] = recipient,
        # but we set it here first so step_started can use it if needed
        context["node_id"] = node_id
        
        # Emit step started event with header info
        emitter = context.get("emitter")
        step_id = None
        # Extract parent_pattern_id from context (set by pattern runners)
        # This MUST match the pattern_id emitted in pattern_started event
        # so that UI can correctly match cards to their parent patterns
        parent_pattern_id = context.get("parent_pattern_id")
        
        step_name = None
        if emitter and hasattr(emitter, "step_started"):
            step_id = emitter.step_started(
                agent_name=node_id,
                framework=framework,
                model=model,
                run_mode=run_mode,
                started_at=start_timestamp,
                parent_pattern_id=parent_pattern_id,
            )
            # Get step_name from emitter for step_input emission
            if hasattr(emitter, "get_step_name"):
                step_name = emitter.get_step_name(step_id)
        
        # Store step_name in context for base_agent to use in step_input
        if step_name:
            context["current_step_name"] = step_name

        # Initialize result to None - will be set if agent execution succeeds
        result = None

        try:
            # Prepare input for the agent
            input_text = context.get("user_text", "")
            upstream_for_node = context.get("upstream", {}).get(node_id, {})
            
            # Handle accumulated loop results (list of results from multiple iterations)
            # When accumulate_results is true, upstream context contains lists instead of single dicts
            # If the agent's own upstream data is a list, it means it's accumulated results from previous iterations
            # The agent shouldn't use its own previous results as input, so skip "primary" input logic
            if isinstance(upstream_for_node, list):
                # This is the agent's own accumulated results - don't use as input
                upstream_for_node = {}
            
            primary_input = upstream_for_node.get("primary") if isinstance(upstream_for_node, dict) else None

            # If there's upstream input, use it as the text
            if primary_input and isinstance(primary_input, dict):
                if "result" in primary_input:
                    input_text = primary_input["result"]
                elif "summary" in primary_input:
                    input_text = primary_input["summary"]

            # Unified path via agent bus for both local and remote agents
            self.logger.debug(
                "Agent {}: Using UNIFIED execution via agent bus", node_id
            )

            # Always add agent to agent bus - let agent_bus handle local vs remote routing
            self.agent_bus._agents_by_id[node_id] = agent

            # Add agent_config to main context for agent snapshot emission (same as working version)
            # Use base_agent_id_for_config for config lookup (instance IDs don't have configs)
            agent_info = self.get_agent_info(base_agent_id_for_config, context)
            if agent_info:
                context["agent_config"] = agent_info
                self.logger.debug(
                    "Added agent_config to execution context for agent: {} (base: {})", 
                    node_id, 
                    base_agent_id_for_config
                )

            # Get pipeline structure if available
            pipeline_structure = {}
            if self.pipeline_structure_getter:
                try:
                    pipeline_structure = self.pipeline_structure_getter()
                except Exception as e:
                    self.logger.warning("Failed to get pipeline structure: {}", e)

            # Pass the full context to the agent
            # Add agent_config to context for agent snapshot emission
            # Use base_agent_id_for_config for config lookup (instance IDs don't have configs)
            context["agent_config"] = self.get_agent_info(base_agent_id_for_config, context)
            context["pipeline_structure"] = pipeline_structure

            # Inject HITL results for targeted agents
            hitl_variables = self._inject_hitl_variables(node_id, context)
            if hitl_variables:
                context["hitl_results"] = hitl_variables
                self.logger.debug(
                    "Injected HITL results for agent {}: {}",
                    node_id,
                    list(hitl_variables.keys()),
                )

            # Pre-process user_files if not already done (for pipeline execution)
            if "user_files_data" not in context:
                user_files = context.get("user_files", [])
                user_text = context.get("user_text", "")
                if user_files:
                    context["user_files_data"] = self._preprocess_user_files(user_files, user_text)

            # Determine correct sender
            sender = previous_agent if previous_agent else "orchestrator"
            self.logger.debug(
                "Executing node: {}, Previous Agent: {}, Sender: {}",
                node_id,
                previous_agent,
                sender,
            )

            # Prepare content structure for agent execution
            content = {
                "text": input_text,
                "input": input_text,
                "node_id": node_id,
                "context": context,  # Nested context structure expected by LocalClient
            }

            result = await self.agent_bus.route_agent_call(
                sender=sender,
                recipient=node_id,
                content=content,
                context=context,  # Full context for protocol determination
            )

            # Extract and emit step_input for remote agents (inputs come back in result)
            # Local agents emit step_input directly in base_agent.execute() before execution
            # IMPORTANT: Extract agent_inputs BEFORE checking for errors, so instructions tab shows even on failure
            if run_mode == "remote":
                self._extract_and_emit_step_input(emitter, step_name, node_id, result)

            # Check for errors in agent results (both local and remote agents can return errors as JSON)
            # Only treat as error if the error field exists AND has a non-empty value
            if isinstance(result, dict) and "error" in result:
                error_msg = result.get("error", "")
                # Only raise error if error message is non-empty (successful runs may have empty error field)
                if error_msg:
                    # Use appropriate error message based on actual run_mode
                    agent_type = "Remote agent" if run_mode == "remote" else "Agent"
                    self.logger.error("{} {} returned error: {}", agent_type, node_id, error_msg)
                    # Raise exception to trigger error handling path
                    raise AgentError(f"{agent_type} {node_id} execution failed: {error_msg}")

            # Calculate timing for UI
            end_time = time.time()
            end_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(end_time))
            elapsed_ms = int((end_time - start_time) * 1000)

            # Update context with timing
            context["ended_at"] = end_timestamp
            context["elapsed_ms"] = elapsed_ms

            # Emit state delta for UI (header/metadata only, no inputs)
            self._emit_state_delta(emitter, node_id, result, context)

            # Emit agent snapshot for UI (simplified - no inputs/header, just result/status/timing)
            self._emit_step_output(emitter, node_id, result, context)

            if emitter and hasattr(emitter, "step_finished") and step_id:
                emitter.step_finished(step_id, status="completed")

            return result

        except Exception as e:
            self.logger.error("Failed to execute agent {}: {}", node_id, e)
            
            # Calculate timing for failure case (same as success path)
            end_time = time.time()
            end_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(end_time))
            elapsed_ms = int((end_time - start_time) * 1000)
            
            # Update context with timing for failure snapshot
            context["ended_at"] = end_timestamp
            context["elapsed_ms"] = elapsed_ms
            
            # Emit step_output for failure scenario
            # If result exists (agent executed but post-processing failed), include it
            # Otherwise, result will be None and error_message will be used
            self._emit_step_output(
                emitter=emitter,
                node_id=node_id,
                result=result,  # May be None if agent execution failed, or have value if post-processing failed
                context=context,
                error_message=str(e),  # Pass exception as error_message
                status="failed",
            )
            
            if emitter and hasattr(emitter, "step_finished") and step_id:
                emitter.step_finished(step_id, status="failed", error=str(e))
            raise AgentError(f"Agent {node_id} execution failed: {e}")

    def _preprocess_user_files(self, user_files: List[str], user_text: str) -> Dict[str, Any]:
        """Pre-process user files into structured multimodal data"""
        from topaz_agent_kit.utils.file_utils import FileUtils
        
        result = {
            "images": [],
            "documents": [],
            "urls": []
        }
        
        # Process file paths
        for file_path in user_files:
            try:
                file_type = FileUtils.detect_file_type(file_path)
                if file_type == "image":
                    image_data = FileUtils.read_image_file(file_path)
                    result["images"].append(image_data)
                elif file_type == "document":
                    doc_data = FileUtils.read_document_file(file_path)
                    result["documents"].append(doc_data)
            except Exception as e:
                self.logger.error("Failed to pre-process file {}: {}", file_path, e)
                raise  # Fail agent execution on error
        
        # Detect URLs in user_text
        if user_text:
            urls = FileUtils.detect_urls(user_text)
            for url in urls:
                url_type = FileUtils.detect_url_type(url)
                if url_type in ["image", "document"]:
                    media_type = FileUtils.get_url_media_type(url, url_type)
                    result["urls"].append({
                        "url": url,
                        "type": url_type,
                        "media_type": media_type
                    })
        
        return result

    def _initialize_upstream_context(self, context: Dict[str, Any]) -> None:
        """
        Initialize upstream context with user input as a pseudo-agent.
        This makes user input available to all agents through the standard upstream mechanism.
        Same logic as PipelineRunner._initialize_upstream_context.
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
                },
            }

            self.logger.debug(
                "Initialized user_input in upstream context: {} chars", len(user_text)
            )

        except Exception as e:
            self.logger.error(
                "Failed to initialize user_input in upstream context: {}", e
            )
            # Don't fail the agent for user input initialization issues

    async def execute_standalone_agent(
        self,
        agent_id: str,
        user_text: str,
        emitter: AGUIEventEmitter,
        session_id: str,
        agent_factory: AgentFactory,
        mcp_tools_cache: Dict[str, Any],
        mcp_clients: Dict[str, Any],
        project_dir: Path,
        additional_context: Optional[Dict[str, Any]] = None,
        suppress_step_events: bool = False,
        user_files: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Execute independent agent (new method for orchestrator use)

        This method provides a simplified interface for executing standalone agents
        without pipeline context or upstream dependencies.
        """
        self.logger.info("Executing standalone agent: {}", agent_id)
        if user_files:
            self.logger.info("User files provided: {}", user_files)

        # Set emitter in agent bus
        self.agent_bus.emitter = emitter

        # Create execution context with timing and metadata
        start_time = time.time()
        start_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start_time))

        context = {
            "user_text": user_text,
            "emitter": emitter,
            "agent_factory": agent_factory,
            "mcp_tools_cache": mcp_tools_cache,
            "mcp_clients": mcp_clients,
            "project_dir": project_dir,
            "session_id": session_id,
            "upstream": {},  # Will be initialized below
            "pipeline_structure": {},  # No pipeline structure for standalone agents
            "pipeline_data": {},  # No pipeline data for standalone agents
            "user_files": user_files or [],  # Add user files to context
            # Add timing fields for UI
            "started_at": start_timestamp,
            "start_time": start_time,
            # Add metadata fields for UI (will be populated from agent config)
            "run_mode": None,  # Will be populated from agent config
            "protocol": None,  # Will be populated from agent config
            "framework": None,  # Will be populated from agent config
            "model": None,  # Will be populated from agent config
        }

        # Pre-process user_files if not already done
        if "user_files_data" not in context:
            context["user_files_data"] = self._preprocess_user_files(user_files or [], user_text)

        # Merge additional context if provided
        if additional_context:
            context.update(additional_context)

        # Initialize upstream context for standalone agents (same as pipeline agents)
        self._initialize_upstream_context(context)

        # Inject HITL results for targeted agents
        hitl_variables = self._inject_hitl_variables(agent_id, context)
        if hitl_variables:
            context["hitl_results"] = hitl_variables
            self.logger.debug(
                "Injected HITL results for agent {}: {}",
                agent_id,
                list(hitl_variables.keys()),
            )

        # Populate framework/model/run_mode/protocol from AgentFactory
        try:
            # High-level info (id, type, model, run_mode, etc.)
            info = agent_factory.get_agent_info(agent_id) or {}
            # Raw config (for nested sections like remote.protocol)
            cfg = agent_factory.get_agent_config(agent_id) or {}

            context["framework"] = info.get("type")
            context["model"] = info.get("model")
            context["run_mode"] = info.get("run_mode")

            # Make agent info available in context (mirrors pipeline path)
            context["agent_config"] = info

            self.logger.debug(
                "Agent info for {}: framework={}, model={}, run_mode={}",
                agent_id,
                context["framework"],
                context["model"],
                context["run_mode"],
            )
        except Exception as e:
            self.logger.warning("Failed to resolve agent info for {}: {}", agent_id, e)

        try:
            # Build agent
            agent = await self.build_agent(agent_id, context)

            # Execute agent
            result = await self.execute_agent(agent_id, agent, context)

            # Extract the content from wrapped response for UI display
            content = result
            if isinstance(result, dict) and "content" in result:
                content = result["content"]
                self.logger.debug(
                    "Extracted content from wrapped response for standalone agent {}: {} chars",
                    agent_id,
                    len(str(content)),
                )

            # Calculate timing for UI
            end_time = time.time()
            end_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(end_time))
            elapsed_ms = int((end_time - context["start_time"]) * 1000)

            # Update context with timing
            context["ended_at"] = end_timestamp
            context["elapsed_ms"] = elapsed_ms

            # Normalize result for UI
            normalized_result = JSONUtils.normalize_for_ui(result)

            # Process output using Output Manager if agent has output configuration
            formatted_output = None
            try:
                agent_config = agent_factory.get_agent_config(agent_id)
                self.logger.debug("Agent config for {}: {}", agent_id, agent_config)
                if agent_config and "outputs" in agent_config:
                    # Create a minimal pipeline config for Output Manager
                    # For standalone agents, we need to add the node field to the final config
                    outputs_config = agent_config["outputs"].copy()
                    if "final" in outputs_config:
                        outputs_config["final"] = outputs_config["final"].copy()
                        outputs_config["final"]["node"] = agent_id

                    pipeline_config = {"outputs": outputs_config}
                    output_manager = OutputManager(pipeline_config)

                    # Process final output
                    if output_manager.has_final_output():
                        # Create a mock results dict with the agent result
                        # The normalized_result contains the actual agent output under 'result' key
                        mock_results = {agent_id: normalized_result}
                        self.logger.debug(
                            "Mock results for Output Manager: {}", mock_results
                        )
                        formatted_output = output_manager.process_final_output(
                            mock_results, emitter
                        )
                        self.logger.debug("Formatted output: {}", formatted_output)
                else:
                    self.logger.debug(
                        "No outputs configuration found for agent: {}", agent_id
                    )
            except Exception as e:
                self.logger.debug("Failed to process output with Output Manager: {}", e)

            self.logger.info("Standalone agent {} executed successfully", agent_id)

            return {
                "agent": agent_id,
                "result": normalized_result,
                "formatted_output": formatted_output,
                "session_id": session_id,
            }

        except Exception as e:
            self.logger.error("Failed to execute standalone agent {}: {}", agent_id, e)
            raise AgentError(f"Standalone agent {agent_id} execution failed: {e}")

    async def execute_virtual_agent(
        self, agent_id: str, inline_config: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a virtual agent with inline configuration (no config file lookup).

        Used for handoff pattern orchestrators that are created dynamically.
        Calls LLM directly with the orchestrator prompt without creating a full agent.

        Args:
            agent_id: Virtual agent identifier (e.g., "__orchestrator__")
            inline_config: Dict with keys: instruction, framework, model
            context: Execution context

        Returns:
            Agent execution result in standard format
        """
        # Extract config
        instruction = inline_config.get("instruction", "")
        model = inline_config.get("model", "azure_openai")

        self.logger.info(
            "Executing virtual agent: {} (model: {})",
            agent_id,
            model,
        )

        # NOTE: Virtual agents don't emit step events - they're transparent routing mechanisms
        # Users should only see the actual specialist agents in the UI

        # Get user input from context
        user_text = context.get("user_text", "")

        # Use ModelFactory for framework-agnostic model creation
        from topaz_agent_kit.models.model_factory import ModelFactory

        try:
            # Get model using generic ModelFactory (no framework dependency)
            llm = ModelFactory.get_model(model)

            # Combine system prompt (instruction) with user message
            full_prompt = f"{instruction}\n\nUser request: {user_text}"

            # Call LLM using standard OpenAI API format (synchronous)
            # ModelFactory returns OpenAI-compatible models (openai.AzureOpenAI, etc.)
            response = llm.chat.completions.create(
                model=model, messages=[{"role": "user", "content": full_prompt}]
            )

            # Extract content from OpenAI response
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
            else:
                content = str(response)

        except Exception as e:
            self.logger.error("Model call failed: {}", e)
            raise AgentError(f"Virtual agent LLM call failed: {e}")

        # Return in standard format
        return {"content": content, "agent_id": agent_id, "success": True}

    def _extract_and_emit_step_input(
        self,
        emitter: Optional[AGUIEventEmitter],
        step_name: Optional[str],
        node_id: str,
        result: Any,
    ) -> None:
        """Extract agent_inputs from remote agent result and emit step_input event"""
        if not emitter or not hasattr(emitter, "step_input") or not step_name:
            return
        
        try:
            agent_inputs = None
            
            # Extract agent_inputs from result (may be nested in "content" for remote responses)
            # A2A service now sends full result as JSON, so agent_inputs may be at top level or in content
            if isinstance(result, dict):
                # First check top level (A2A client preserves it)
                agent_inputs = result.pop("agent_inputs", None)
                
                # If not at top level, check in content
                if not agent_inputs and "content" in result and isinstance(result["content"], dict):
                    # Remote response format: {"content": {...}}
                    agent_inputs = result["content"].pop("agent_inputs", None)
            
            if agent_inputs:
                self.logger.info("Extracted agent_inputs for remote agent {}: keys={}", node_id, list(agent_inputs.keys()) if isinstance(agent_inputs, dict) else "not a dict")
                if isinstance(agent_inputs, dict) and "prompt_template" in agent_inputs:
                    self.logger.info("Remote agent {} has prompt_template: {} chars", node_id, len(agent_inputs["prompt_template"]) if isinstance(agent_inputs["prompt_template"], str) else "not a string")
                emitter.step_input(
                    step_name=step_name,
                    node_id=node_id,
                    inputs=agent_inputs,
                )
                self.logger.info("Emitted step_input for remote agent {} from result", node_id)
            else:
                self.logger.warning("No agent_inputs found in result for remote agent {} (result keys: {})", node_id, list(result.keys()) if isinstance(result, dict) else "not a dict")
        except Exception as e:
            self.logger.debug("Failed to extract and emit step_input for remote agent {}: {}", node_id, e)

    def _emit_state_delta(
        self,
        emitter: AGUIEventEmitter,
        node_id: str,
        result: Any,
        context: Dict[str, Any],
    ) -> None:
        """Emit state_delta event for UI"""
        if (
            not emitter
            or not hasattr(emitter, "state_delta")
            or not isinstance(result, dict)
        ):
            return

        try:
            # Extract the actual content from wrapped response for snapshot
            content = result
            if isinstance(result, dict) and "content" in result:
                content = result["content"]

            # Get title from emitter's mapping, fallback to node_id
            agent_title = node_id
            if emitter and hasattr(emitter, "_agent_title_map"):
                agent_title = emitter._agent_title_map.get(node_id, node_id)
            
            # Create state delta with agent data (use actual content for snapshot)
            state_delta = [
                {
                    "op": "add",
                    "path": f"/agents/{node_id}",
                    "value": {
                        "node_id": node_id,
                        "title": agent_title,  # Use title from UI manifest
                        "content": "",
                        "snapshot": content,  # Use actual content, not wrapped response
                        "status": "completed",
                        "started_at": context.get("started_at"),
                        "ended_at": context.get("ended_at"),
                        "elapsed_ms": context.get("elapsed_ms"),
                        "run_mode": context.get("run_mode"),
                        "protocol": context.get("protocol"),
                        "framework": context.get("framework"),
                        "model": context.get("model"),
                        # No inputs field - handled by agent_snapshot
                    },
                }
            ]
            emitter.state_delta(delta=state_delta)
            self.logger.debug("Emitted state_delta for agent: {}", node_id)
        except Exception as e:
            self.logger.debug("state_delta emission failed for {}: {}", node_id, e)

    def _emit_step_output(
        self,
        emitter: AGUIEventEmitter,
        node_id: str,
        result: Any,
        context: Dict[str, Any],
        error_message: Optional[str] = None,
        status: Optional[str] = None,
    ) -> None:
        """Emit step_output event for UI (simplified - header comes from step_started, inputs from step_input)
        
        Args:
            emitter: Event emitter instance
            node_id: Agent node ID
            result: Agent execution result (may be None for failures)
            context: Execution context with timing info
            error_message: Optional error message (for explicit failures)
            status: Optional status override (for explicit failures)
        """
        if not emitter or not hasattr(emitter, "step_output"):
            return

        try:
            # Extract the content from wrapped response (LocalClient wraps in {"content": result})
            content = result
            if isinstance(result, dict) and "content" in result:
                content = result["content"]
                self.logger.debug(
                    "Extracted content from wrapped response for {}: {} chars",
                    node_id,
                    len(str(content)),
                )

            # Normalize content for UI (removed agent_inputs extraction - now handled via step_input)
            normalized_for_output = JSONUtils.normalize_for_ui(content) if content is not None else None
            
            # Override agent_id in output to use instance_id (node_id) for repeat pattern instances
            # This ensures the UI shows the correct instance ID (e.g., math_repeater_solver_0) instead of base ID
            if isinstance(normalized_for_output, dict):
                if "agent_id" in normalized_for_output:
                    # Only override if node_id is different from the agent_id in output (indicates an instance)
                    original_agent_id = normalized_for_output["agent_id"]
                    if original_agent_id != node_id:
                        normalized_for_output["agent_id"] = node_id
                        self.logger.debug(
                            "Overrode agent_id in output from '{}' to '{}' for instance",
                            original_agent_id,
                            node_id,
                        )
                else:
                    # Add agent_id if missing (use node_id which may be an instance ID)
                    normalized_for_output["agent_id"] = node_id
                    self.logger.debug("Added agent_id '{}' to output", node_id)
            
            # If status and error_message are explicitly provided (from exception handler), use them
            # Otherwise, determine from result content
            if status is None:
                status = "completed"
                # Check if there's an actual error (non-empty error string or success=False)
                if isinstance(normalized_for_output, dict):
                    error_value = normalized_for_output.get("error")
                    success_value = normalized_for_output.get("success")
                    
                    # Mark as failed if:
                    # 1. error field exists and is non-empty string, OR
                    # 2. success field exists and is False
                    if (error_value and str(error_value).strip()) or (success_value is False):
                        status = "failed"
            
            if error_message is None:
                # Extract error_message from result if available
                if isinstance(normalized_for_output, dict):
                    error_value = normalized_for_output.get("error")
                    if error_value and str(error_value).strip():
                        error_message = str(error_value)
                    elif normalized_for_output.get("success") is False:
                        error_message = "Operation failed"
            
            # Use normalized result for emission
            result_for_emission = normalized_for_output
            
            emitter.step_output(
                node_id=node_id,
                result=result_for_emission,
                status=status or "completed",
                error_message=error_message,
                ended_at=context.get("ended_at"),
                elapsed_ms=context.get("elapsed_ms"),
            )
            self.logger.debug("Emitted step_output for agent: {} (status: {})", node_id, status or "completed")
        except Exception as e:
            self.logger.debug("step_output emission failed for {}: {}", node_id, e)

    def get_pipeline_structure(self) -> Dict[str, Any]:
        """Get pipeline structure for context (used by execute_agent)"""
        # This method will be implemented when we integrate with PipelineRunner
        # For now, return empty structure for standalone agents
        return {}

    def _inject_hitl_variables(
        self, agent_id: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Inject HITL results for this agent - flows naturally through pipeline"""

        # Skip HITL injection for independent agents
        if (
            not context.get("pipeline_data")
            and not context.get("pipeline_id")
            and not context.get("pipeline")
        ):
            self.logger.debug(
                "Skipping HITL injection for independent agent: {}", agent_id
            )
            return {}

        hitl_data = {}

        self.logger.info(
            "Injecting HITL variables for agent {}: context.hitl = {}",
            agent_id,
            context.get("hitl", {}),
        )

        for gate_id, gate_result in context.get("hitl", {}).items():
            # Ensure gate_result is a dictionary
            if not isinstance(gate_result, dict):
                self.logger.warning(
                    "Gate result is not a dictionary for gate {}: {} (type: {})",
                    gate_id,
                    gate_result,
                    type(gate_result),
                )
                continue

            # HITL data flows naturally to all subsequent agents in the pipeline
            context_key = gate_result.get("context_key", gate_id)
            data = gate_result.get("data", {})
            gate_type = gate_result.get("gate_type", "approval")
            context_strategy = gate_result.get("context_strategy")

            self.logger.info(
                "Processing gate {}: context_key='{}', data={}",
                gate_id,
                context_key,
                data,
            )

            # Ensure data is a dictionary
            if isinstance(data, dict):
                # For input gates, flatten the data to make it more accessible
                if gate_type == "input" and len(data) == 1:
                    field_name, field_value = next(iter(data.items()))
                    # Apply append strategy if requested
                    if context_strategy == "append":
                        previous = context.get(context_key)
                        if previous:
                            combined = f"{previous}\n{field_value}"
                        else:
                            combined = field_value
                        hitl_data[context_key] = combined
                    else:
                        hitl_data[context_key] = field_value
                    self.logger.info(
                        "Flattened input gate data: {} -> {}", field_name, hitl_data.get(context_key)
                    )
                else:
                    # For other gates or multi-field input gates, keep the full data structure
                    hitl_data[context_key] = data
            else:
                self.logger.warning(
                    "HITL data is not a dictionary for gate {}: {} (type: {})",
                    gate_id,
                    data,
                    type(data),
                )
                hitl_data[context_key] = {}

        self.logger.info("Final HITL data for agent {}: {}", agent_id, hitl_data)

        # No aliases – rely strictly on declared context_key in YAML

        # Debug: Log each HITL variable individually
        for key, value in hitl_data.items():
            self.logger.info(
                "HITL variable '{}' = '{}' (type: {})", key, value, type(value)
            )

        return hitl_data
