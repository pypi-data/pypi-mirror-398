from __future__ import annotations
from typing import Any, Dict

from topaz_agent_kit.core.execution_patterns import (
    BaseRunner,
    StepRunner,
    GateRunner,
    ConditionalStepRunner,
    SequentialRunner,
    ParallelRunner,
    LoopRunner,
    SwitchRunner,
    HandoffRunner,
    GroupChatRunner,
    RepeatPatternRunner,
)
from topaz_agent_kit.core.exceptions import ConfigurationError


class RunnerCompiler:
    def __init__(
        self,
        agent_runner,
        logger,
        populate_upstream_context_func=None,
        output_manager=None,
        gate_lookup_func=None,
        pipeline_runner_gate_handler_func=None,
        config_result=None,
    ) -> None:
        self.agent_runner = agent_runner
        self.logger = logger
        self.populate_upstream_context_func = populate_upstream_context_func
        self.output_manager = output_manager
        self.gate_lookup_func = gate_lookup_func
        self.pipeline_runner_gate_handler_func = pipeline_runner_gate_handler_func
        self.config_result = config_result
    
    def compile(self, pattern: Dict[str, Any], is_top_level: bool = False):
        pattern_type = pattern.get("type")
        if not pattern_type:
            self.logger.error("Pattern missing 'type' field: {}", pattern)
            raise ValueError("Pattern must include 'type'")

        self.logger.info("Compiling pattern of type: {}", pattern_type)

        if pattern_type == "sequential":
            steps = [self._compile_step(s) for s in pattern["steps"]]
            self.logger.debug("Compiled sequential pattern with {} steps", len(steps))
            
            # Set pattern_index on each step runner that is a pattern (for unique ID generation)
            # This ensures nested patterns get unique IDs based on their position in the steps list
            for step_index, step_runner in enumerate(steps):
                # Handle ConditionalStepRunner wrapper (it wraps the actual runner)
                actual_runner = step_runner
                if hasattr(step_runner, "runner"):
                    actual_runner = step_runner.runner
                
                # Set pattern_index on pattern runners (ParallelRunner, LoopRunner, SwitchRunner, RepeatPatternRunner)
                if hasattr(actual_runner, "pattern_index"):
                    actual_runner.pattern_index = step_index
                    self.logger.debug(
                        "Set pattern_index=%d on step %d (type: %s)",
                        step_index, step_index, type(actual_runner).__name__
                    )
            
            runner = SequentialRunner(steps)
            # Set pattern metadata
            runner.pattern_name = pattern.get("name")
            runner.pattern_description = pattern.get("description")
            # Set pattern_index for unique ID generation (0 for top-level, will be set by parent for nested)
            runner.pattern_index = 0
            self.logger.info(
                "RunnerCompiler: SequentialRunner compiled with name=%s, description=%s (first 50 chars)",
                runner.pattern_name,
                runner.pattern_description[:50] if runner.pattern_description else None
            )
            # Branch-level condition support
            if "condition" in pattern:
                cond = pattern["condition"]
                on_false_config = pattern.get("on_false")
                on_false_runner = self._compile_on_false_branch(on_false_config, "sequential_pattern")
                self.logger.debug("Wrapping sequential branch with condition: {}, on_false: {}", cond, 
                    "compiled_runner" if isinstance(on_false_runner, BaseRunner) else on_false_runner)
                return ConditionalStepRunner(runner, cond, on_false=on_false_runner)
            return runner

        if pattern_type == "parallel":
            # Check if this is a repeat pattern
            if "repeat" in pattern:
                return self._compile_repeat_pattern(pattern)
            
            # Standard parallel pattern with explicit steps
            steps = [self._compile_step(s) for s in pattern["steps"]]
            self.logger.debug("Compiled parallel pattern with {} steps", len(steps))
            runner = ParallelRunner(steps)
            # Set pattern metadata
            runner.pattern_name = pattern.get("name")
            runner.pattern_description = pattern.get("description")
            # Set pattern_index for unique ID generation (will be set by parent SequentialRunner)
            runner.pattern_index = 0
            # Branch-level condition support
            if "condition" in pattern:
                cond = pattern["condition"]
                on_false_config = pattern.get("on_false")
                on_false_runner = self._compile_on_false_branch(on_false_config, "parallel_pattern")
                self.logger.debug("Wrapping parallel branch with condition: {}, on_false: {}", cond,
                    "compiled_runner" if isinstance(on_false_runner, BaseRunner) else on_false_runner)
                return ConditionalStepRunner(runner, cond, on_false=on_false_runner)
            return runner

        if pattern_type == "loop":
            body = self._compile_step(pattern["body"])
            
            # Check for iterate_over mode (new list iteration pattern)
            iterate_over = pattern.get("iterate_over")
            loop_item_key = pattern.get("loop_item_key", "loop_item")
            skip_condition = pattern.get("skip_condition")
            
            # Handle new termination structure or backward-compatible max_iterations
            termination = pattern.get("termination", {})
            max_iter = termination.get("max_iterations") or pattern.get("max_iterations")
            termination_condition = termination.get("condition")
            
            # Validate: either max_iter or iterate_over must be provided
            # When iterate_over is used, max_iter is optional (safety limit only)
            if not max_iter and not iterate_over:
                raise ConfigurationError(
                    "Loop pattern requires either 'max_iterations'/'termination.max_iterations' or 'iterate_over'"
                )
            # When iterate_over is present, max_iter is allowed as an optional safety limit
            # The loop will terminate when list is exhausted OR termination condition is met OR max_iter is reached
            
            # Get configurable loop context key (default: "loop_iteration")
            loop_context_key = pattern.get("loop_context_key", "loop_iteration")
            # Get accumulate_results option (default: True for backward compatibility)
            accumulate_results = pattern.get("accumulate_results", True)
            
            if iterate_over:
                self.logger.debug(
                    "Compiled loop pattern with iterate_over: {}, loop_item_key: {}, skip_condition: {}, termination_condition: {}, loop_context_key: {}, accumulate_results: {}",
                    iterate_over, loop_item_key, skip_condition, termination_condition, loop_context_key, accumulate_results
                )
            else:
                self.logger.debug(
                    "Compiled loop pattern with max_iterations: {}, termination_condition: {}, loop_context_key: {}, accumulate_results: {}",
                    max_iter, termination_condition, loop_context_key, accumulate_results
                )
            
            runner = LoopRunner(
                body, 
                max_iterations=max_iter,
                termination_condition=termination_condition,
                loop_context_key=loop_context_key,
                accumulate_results=accumulate_results,
                iterate_over=iterate_over,
                loop_item_key=loop_item_key,
                skip_condition=skip_condition
            )
            # Set pattern metadata
            runner.pattern_name = pattern.get("name")
            runner.pattern_description = pattern.get("description")
            # Set pattern_index for unique ID generation (will be set by parent SequentialRunner)
            runner.pattern_index = 0
            if "condition" in pattern:
                cond = pattern["condition"]
                on_false_config = pattern.get("on_false")
                on_false_runner = self._compile_on_false_branch(on_false_config, "loop_pattern")
                self.logger.debug("Wrapping loop branch with condition: {}, on_false: {}", cond,
                    "compiled_runner" if isinstance(on_false_runner, BaseRunner) else on_false_runner)
                return ConditionalStepRunner(runner, cond, on_false=on_false_runner)
            return runner

        # Handle switch pattern
        if pattern_type.startswith("switch"):
            # Support shorthand: type: "switch(field_name)"
            if "(" in pattern_type and pattern_type.endswith(")"):
                # Extract field/expression from type: switch(field_or_expression)
                # Remove "switch(" prefix and ")" suffix
                field_or_expression = pattern_type[
                    7:-1
                ]  # "switch(" is 7 chars, remove last )
                self.logger.debug(
                    "Extracted switch expression: '{}'", field_or_expression
                )
            else:
                # Verbose syntax: type: switch, field: "field_name"
                field_or_expression = pattern.get("field")
                if not field_or_expression:
                    raise ValueError(
                        "Switch pattern must include field (use 'switch(field)' or 'field: ...')"
                    )

            # Compile cases
            cases_config = pattern.get("cases", {})
            compiled_cases = {}
            for case_value, case_steps in cases_config.items():
                # Each case is a list of steps - compile them
                if isinstance(case_steps, list):
                    compiled_steps = [self._compile_step(s) for s in case_steps]
                    if len(compiled_steps) == 1:
                        compiled_cases[case_value] = compiled_steps[0]
                    else:
                        compiled_cases[case_value] = SequentialRunner(compiled_steps)
                else:
                    raise ValueError(
                        f"Switch case '{case_value}' must be a list of steps"
                    )

            # Compile default if present
            default_runner = None
            if "default" in pattern:
                default_steps = pattern["default"]
                if isinstance(default_steps, list):
                    compiled_steps = [self._compile_step(s) for s in default_steps]
                    if len(compiled_steps) == 1:
                        default_runner = compiled_steps[0]
                    else:
                        default_runner = SequentialRunner(compiled_steps)

            self.logger.debug(
                "Compiled switch pattern: '{}' with {} cases, default={}",
                field_or_expression,
                len(compiled_cases),
                default_runner is not None,
            )

            runner = SwitchRunner(field_or_expression, compiled_cases, default_runner)
            # Set pattern metadata
            runner.pattern_name = pattern.get("name")
            runner.pattern_description = pattern.get("description")
            # Set pattern_index for unique ID generation (will be set by parent SequentialRunner)
            runner.pattern_index = 0
            if "condition" in pattern:
                cond = pattern["condition"]
                on_false_config = pattern.get("on_false")
                on_false_runner = self._compile_on_false_branch(on_false_config, "switch_pattern")
                self.logger.debug("Wrapping switch branch with condition: {}, on_false: {}", cond,
                    "compiled_runner" if isinstance(on_false_runner, BaseRunner) else on_false_runner)
                return ConditionalStepRunner(runner, cond, on_false=on_false_runner)
            return runner

        # Handle handoff pattern
        if pattern_type == "handoff":
            self.logger.info("Compiling handoff pattern")

            # Parse optional custom orchestrator
            orchestrator_ref = pattern.get("orchestrator")

            # Parse orchestrator model (REQUIRED - no defaults)
            # Priority: 1) Individual pipeline pattern.model 2) Global pipeline.orchestrator.model
            # If neither exists, raise exception - model is REQUIRED
            orchestrator_model = pattern.get("model")

            if not orchestrator_model:
                # Try to get from global config
                if hasattr(self, "pipeline_config") and isinstance(
                    self.pipeline_config, dict
                ):
                    global_orchestrator = self.pipeline_config.get("orchestrator", {})
                    orchestrator_model = global_orchestrator.get("model")

                if not orchestrator_model:
                    self.logger.error(
                        "Orchestrator model not configured. "
                        "Please configure 'orchestrator.model' in global pipeline.yml"
                    )
                    raise ValueError(
                        "Orchestrator model not configured. "
                        "Either specify 'model' in handoff pattern or configure "
                        "'orchestrator.model' in global pipeline.yml"
                    )

            # Parse handoffs (list of specialist agents or pipelines)
            handoffs_config = pattern.get("handoffs", [])
            compiled_handoffs = {}

            for handoff_item in handoffs_config:
                if not isinstance(handoff_item, dict):
                    raise ValueError("Handoff item must be an object with 'node' or 'pipeline' field")
                
                if "pipeline" in handoff_item:
                    # Pipeline handoff
                    pipeline_id = handoff_item["pipeline"]
                    # Compile pipeline step
                    specialist_runner = self._compile_pipeline_step(handoff_item)
                    compiled_handoffs[pipeline_id] = specialist_runner
                elif "node" in handoff_item:
                    # Agent handoff
                    agent_ref = handoff_item["node"]
                    agent_id = agent_ref.split(":")[0]
                    # Compile specialist agent
                    specialist_runner = self._compile_step({"node": agent_ref})
                    compiled_handoffs[agent_id] = specialist_runner
                else:
                    raise ValueError("Handoff item must have either 'node' or 'pipeline' field")

            self.logger.debug(
                "Compiled handoff pattern with {} specialists", len(compiled_handoffs)
            )

            runner = HandoffRunner(
                orchestrator_ref=orchestrator_ref,
                orchestrator_model=orchestrator_model,
                handoffs=compiled_handoffs,
                agent_runner=self.agent_runner,
                populate_upstream_context_func=self.populate_upstream_context_func,
                output_manager=self.output_manager,
            )
            # Set pattern metadata
            runner.pattern_name = pattern.get("name")
            runner.pattern_description = pattern.get("description")
            # Set pattern_index for unique ID generation (will be set by parent SequentialRunner)
            runner.pattern_index = 0
            if "condition" in pattern:
                cond = pattern["condition"]
                on_false_config = pattern.get("on_false")
                on_false_runner = self._compile_on_false_branch(on_false_config, "handoff_pattern")
                self.logger.debug("Wrapping handoff branch with condition: {}, on_false: {}", cond,
                    "compiled_runner" if isinstance(on_false_runner, BaseRunner) else on_false_runner)
                return ConditionalStepRunner(runner, cond, on_false=on_false_runner)
            return runner

        # Handle group_chat pattern
        if pattern_type == "group_chat":
            self.logger.info("Compiling group_chat pattern")

            # Parse participants (required, min 2)
            participants_config = pattern.get("participants", [])
            if len(participants_config) < 2:
                raise ValueError("Group chat requires at least 2 participants")

            # Compile participants as {participant_id: participant_ref}
            # Support both agents (node) and pipelines (pipeline)
            participants: Dict[str, str] = {}
            participant_runners: Dict[str, BaseRunner] = {}
            for p_item in participants_config:
                if not isinstance(p_item, dict):
                    raise ValueError(
                        "Participant item must be an object with 'node' or 'pipeline' field"
                    )
                
                if "pipeline" in p_item:
                    # Pipeline participant
                    pipeline_id = p_item["pipeline"]
                    participants[pipeline_id] = f"pipeline:{pipeline_id}"
                    # Compile pipeline step
                    participant_runner = self._compile_pipeline_step(p_item)
                    participant_runners[pipeline_id] = participant_runner
                elif "node" in p_item:
                    # Agent participant
                    node_ref = p_item["node"]
                    agent_id = node_ref.split(":")[0]
                    participants[agent_id] = node_ref
                    # Compile agent step for reference (GroupChatRunner will build agent)
                    participant_runner = self._compile_step({"node": node_ref})
                    participant_runners[agent_id] = participant_runner
                else:
                    raise ValueError(
                        "Participant item must have either 'node' or 'pipeline' field"
                    )

            # Selection strategy (required): llm | round_robin
            selection_strategy = pattern.get("selection_strategy")
            if selection_strategy not in ["llm", "round_robin"]:
                raise ValueError(
                    "Group chat requires 'selection_strategy' to be 'llm' or 'round_robin'"
                )

            # Orchestrator (optional for llm)
            orchestrator_ref = pattern.get("orchestrator")
            orchestrator_model = pattern.get("orchestrator_model")

            # If LLM strategy and no orchestrator_model, try global config
            if selection_strategy == "llm" and not orchestrator_model:
                if hasattr(self, "pipeline_config") and isinstance(
                    self.pipeline_config, dict
                ):
                    global_orchestrator = self.pipeline_config.get("orchestrator", {})
                    orchestrator_model = global_orchestrator.get("model")
                if not orchestrator_model:
                    self.logger.error(
                        "Orchestrator model not configured for group_chat LLM selection"
                    )
                    raise ValueError(
                        "Orchestrator model not configured. Either specify 'orchestrator_model' in group_chat pattern or configure 'orchestrator.model' in global pipeline.yml"
                    )

            # Termination (required)
            termination = pattern.get("termination", {})
            if not isinstance(termination, dict) or not termination.get("max_rounds"):
                raise ValueError("Group chat requires 'termination.max_rounds'")

            self.logger.debug(
                "Compiled group_chat with {} participants, strategy: {}",
                len(participants),
                selection_strategy,
            )

            runner = GroupChatRunner(
                participants=participants,
                participant_runners=participant_runners,
                selection_strategy=selection_strategy,
                agent_runner=self.agent_runner,
                termination=termination,
                orchestrator_ref=orchestrator_ref,
                orchestrator_model=orchestrator_model,
                populate_upstream_context_func=self.populate_upstream_context_func,
                output_manager=self.output_manager,
            )
            # Set pattern metadata
            runner.pattern_name = pattern.get("name")
            runner.pattern_description = pattern.get("description")
            # Set pattern_index for unique ID generation (will be set by parent SequentialRunner)
            runner.pattern_index = 0
            if "condition" in pattern:
                cond = pattern["condition"]
                on_false_config = pattern.get("on_false")
                on_false_runner = self._compile_on_false_branch(on_false_config, "group_chat_pattern")
                self.logger.debug("Wrapping group_chat branch with condition: {}, on_false: {}", cond,
                    "compiled_runner" if isinstance(on_false_runner, BaseRunner) else on_false_runner)
                return ConditionalStepRunner(runner, cond, on_false=on_false_runner)
            return runner

        self.logger.error("Unknown pattern type: {}", pattern_type)
        raise ValueError(f"Unknown pattern type: {pattern_type}")
    
    def _compile_repeat_pattern(self, pattern: Dict[str, Any]):
        """Compile a repeat pattern that creates multiple instances.
        
        Supports two modes:
        1. Single agent repeat: Uses 'node' field
        2. Enhanced repeat (nested sequential): Uses 'type: sequential' with 'steps' field
        
        Args:
            pattern: Pattern dict with 'repeat' key containing:
                - For single agent:
                  - node: Agent node ID to repeat
                - For enhanced repeat:
                  - type: sequential (required)
                  - steps: Array of agents/steps to run in sequence
                - Common fields:
                  - instances: Integer or expression string for instance count
                  - input_mapping: Optional dict mapping input names to templates with {{index}}
                  - instance_id_template: Optional template for instance IDs
                  - instance_context_key: Optional context key for instance metadata
        
        Returns:
            RepeatPatternRunner (wrapped in ConditionalStepRunner if condition exists)
        """
        repeat_config = pattern["repeat"]
        instances_spec = repeat_config["instances"]
        # Default instance_id_template based on repeat type
        default_template = "{{node_id}}_instance_{{index}}"
        if "pipeline" in repeat_config:
            default_template = "{{pipeline_id}}_instance_{{index}}"
        instance_id_template = repeat_config.get("instance_id_template", default_template)
        instance_context_key = repeat_config.get("instance_context_key", "repeat_instance")
        max_concurrency = repeat_config.get("max_concurrency")
        
        # NEW: Support "node" (single agent), "pipeline" (single pipeline), and "type: sequential" (nested pattern)
        if "type" in repeat_config and repeat_config["type"] == "sequential":
            # Enhanced repeat pattern: nested sequential
            # IMPORTANT: Copy name and description from the nested sequential pattern config
            # (not from the repeat pattern itself) so the nested sequential pattern
            # can have its own name/description separate from the repeat pattern
            nested_pattern_config = {
                "type": "sequential",
                "steps": repeat_config.get("steps", [])
            }
            # Copy name and description from nested pattern (if present in repeat_config)
            # These are the name/description for the nested sequential pattern, not the repeat pattern
            if "name" in repeat_config:
                nested_pattern_config["name"] = repeat_config["name"]
            if "description" in repeat_config:
                nested_pattern_config["description"] = repeat_config["description"]
            self.logger.info(
                "RunnerCompiler: Creating nested sequential pattern config. name=%s, description=%s (first 50 chars)",
                nested_pattern_config.get("name"),
                nested_pattern_config.get("description")[:50] if nested_pattern_config.get("description") else None
            )
            # Ensure it has steps
            if not nested_pattern_config["steps"]:
                raise ValueError("repeat pattern with type: sequential must have 'steps' array")
            
            # Determine input_mapping:
            # 1. Prefer explicit input_mapping on repeat block
            # 2. Fallback: lift input_mapping from the first step that defines it
            input_mapping = repeat_config.get("input_mapping")
            if input_mapping is None:
                for step in nested_pattern_config["steps"]:
                    if isinstance(step, dict) and "input_mapping" in step:
                        step_mapping = step.get("input_mapping") or {}
                        if isinstance(step_mapping, dict) and step_mapping:
                            input_mapping = step_mapping
                            break
            if input_mapping is None:
                input_mapping = {}
            
            # For nested patterns, we don't have a single base_agent_id
            # Use the instance_id_template to derive a base (e.g., "file_{{index}}" -> "file")
            base_agent_id = None
            node_ref = None
            pipeline_id = None
        elif "pipeline" in repeat_config:
            # NEW: Single pipeline repeat
            pipeline_id = repeat_config["pipeline"]
            input_mapping = repeat_config.get("input_mapping", {})
            if not input_mapping:
                raise ValueError(
                    f"Pipeline repeat pattern for '{pipeline_id}' requires 'input_mapping' to map parent context to sub-pipeline inputs"
                )
            base_agent_id = None
            node_ref = None
            nested_pattern_config = None
        elif "node" in repeat_config:
            # EXISTING: Single agent repeat
            node_ref = repeat_config["node"]
            # Extract base agent_id from node_ref (format: "agent_id" or "agent_id:config_file")
            base_agent_id = node_ref.split(":")[0]
            input_mapping = repeat_config.get("input_mapping", {})
            nested_pattern_config = None
            pipeline_id = None
        else:
            raise ValueError("repeat pattern must have 'node', 'pipeline', or 'type: sequential' with 'steps'")
        
        # Create a RepeatPatternRunner that will evaluate instances at runtime
        runner = RepeatPatternRunner(
            base_agent_id=base_agent_id,
            node_ref=node_ref,
            pipeline_id=pipeline_id,  # NEW: For pipeline repeat
            nested_pattern_config=nested_pattern_config,  # NEW
            instances_spec=instances_spec,
            input_mapping=input_mapping,
            max_concurrency=max_concurrency,
            instance_id_template=instance_id_template,
            instance_context_key=instance_context_key,
            agent_runner=self.agent_runner,
            compile_step_func=self._compile_step,  # This will compile the sequential pattern or pipeline step
            populate_upstream_context_func=self.populate_upstream_context_func,
            config_result=self.config_result,  # NEW: Needed for pipeline compilation
        )
        
        # Set pattern_index for unique ID generation (will be set by parent SequentialRunner)
        runner.pattern_index = 0
        
        # Set pattern metadata for the repeat pattern itself
        # IMPORTANT: For nested sequential patterns, the name/description in repeat_config
        # belong to the nested sequential pattern, NOT the repeat pattern.
        # The repeat pattern should use name/description from the parent pattern (e.g., parallel pattern).
        # The parent pattern's name/description are passed via the 'pattern' parameter.
        if nested_pattern_config is None:
            # For single agent or pipeline repeats, use name/description from the parent pattern
            # (e.g., the parallel pattern that contains this repeat)
            # If not found in parent pattern, fall back to repeat_config
            runner.pattern_name = pattern.get("name") or repeat_config.get("name")
            runner.pattern_description = pattern.get("description") or repeat_config.get("description")
            self.logger.debug(
                "Repeat pattern metadata (single agent/pipeline): name=%s, description=%s (from parent pattern or repeat_config)",
                runner.pattern_name,
                runner.pattern_description[:50] if runner.pattern_description else None
            )
        else:
            # For nested sequential repeats, use name/description from the parent pattern
            # (e.g., the parallel pattern that contains this repeat)
            # The nested sequential pattern will have its own name/description from repeat_config
            runner.pattern_name = pattern.get("name")
            runner.pattern_description = pattern.get("description")
            self.logger.debug(
                "Repeat pattern metadata: name=%s, description=%s (from parent pattern)",
                runner.pattern_name,
                runner.pattern_description[:50] if runner.pattern_description else None
            )
        
        # Branch-level condition support
            if "condition" in pattern:
                cond = pattern["condition"]
                on_false_config = pattern.get("on_false")
                on_false_runner = self._compile_on_false_branch(on_false_config, "repeat_pattern")
                self.logger.debug("Wrapping repeat pattern with condition: {}, on_false: {}", cond,
                    "compiled_runner" if isinstance(on_false_runner, BaseRunner) else on_false_runner)
                return ConditionalStepRunner(runner, cond, on_false=on_false_runner)
        return runner

    def _compile_step(self, node_or_pattern: Dict[str, Any]):
        # Check if it's a pipeline step
        if "pipeline" in node_or_pattern:
            return self._compile_pipeline_step(node_or_pattern)
        
        # Check if it's a gate step
        if "gate" in node_or_pattern:
            gate_ref = node_or_pattern["gate"]
            self.logger.debug("Compiling gate step: {}", gate_ref)

            # Extract flow control config - include all on_* actions
            flow_control_config = {
                "retry_target": node_or_pattern.get("retry_target"),
                "max_retries": node_or_pattern.get("max_retries", 3),
                "skip_to": node_or_pattern.get("skip_to"),
            }

            # Add all on_* actions dynamically
            for key, value in node_or_pattern.items():
                if key.startswith("on_") and key not in [
                    "on_condition"
                ]:  # Skip legacy on_condition
                    flow_control_config[key] = value

            # Get gate config from pipeline_runner
            if not self.gate_lookup_func:
                raise ValueError("gate_lookup_func is required for gate steps")
            gate_config = self.gate_lookup_func(gate_ref)
            if not gate_config:
                raise ValueError(f"Gate configuration not found for gate: {gate_ref}")

            if not self.pipeline_runner_gate_handler_func:
                raise ValueError(
                    "pipeline_runner_gate_handler_func is required for gate steps"
                )

            gate_runner = GateRunner(
                gate_ref,
                gate_config,
                self.pipeline_runner_gate_handler_func,
                flow_control_config,
            )

            # Check if gate has condition - wrap in ConditionalStepRunner
            if "condition" in node_or_pattern:
                condition = node_or_pattern["condition"]
                on_false_config = node_or_pattern.get("on_false")
                on_false_runner = self._compile_on_false_branch(on_false_config, gate_ref)
                self.logger.debug(
                    "Wrapping gate {} with condition: {}, on_false: {}", gate_ref, condition, 
                    "compiled_runner" if isinstance(on_false_runner, BaseRunner) else on_false_runner
                )
                return ConditionalStepRunner(gate_runner, condition, on_false=on_false_runner)

            return gate_runner

        # Existing node/pattern compilation logic
        if isinstance(node_or_pattern, dict) and "type" in node_or_pattern:
            self.logger.debug("Compiling nested pattern within step")
            return self.compile(node_or_pattern, is_top_level=False)

        # Compile the step (node)
        node_ref = node_or_pattern["node"]
        self.logger.debug("Compiling step for node: {}", node_ref)
        step_runner = StepRunner(
            node_ref,
            self.agent_runner,
            populate_upstream_context_func=self.populate_upstream_context_func,
            output_manager=self.output_manager,
        )

        # Check if step has condition - wrap in ConditionalStepRunner
        if "condition" in node_or_pattern:
            condition = node_or_pattern["condition"]
            on_false_config = node_or_pattern.get("on_false")
            on_false_runner = self._compile_on_false_branch(on_false_config, node_ref)
            self.logger.debug(
                "Wrapping step {} with condition: {}, on_false: {}", node_ref, condition, 
                "compiled_runner" if isinstance(on_false_runner, BaseRunner) else on_false_runner
            )
            return ConditionalStepRunner(step_runner, condition, on_false=on_false_runner)

        return step_runner
    
    def _compile_on_false_branch(self, on_false_config: Any, step_ref: str) -> Any:
        """
        Compile on_false configuration into a runner or return string/None.
        
        Args:
            on_false_config: Can be:
                - "stop": stop pipeline
                - "continue" or None: skip and continue
                - dict: single step definition
                - list: array of step definitions
            step_ref: Reference to the step (for logging)
            
        Returns:
            BaseRunner if on_false_config is a step definition, otherwise returns the original value
        """
        if on_false_config is None or on_false_config == "stop" or on_false_config == "continue":
            # String action or None - return as-is
            return on_false_config
        
        if isinstance(on_false_config, dict):
            # Single step definition - compile directly
            return self._compile_step(on_false_config)
        
        if isinstance(on_false_config, list):
            if len(on_false_config) == 0:
                # Empty list - return None (skip)
                return None
            elif len(on_false_config) == 1:
                # Single step in array - compile directly
                return self._compile_step(on_false_config[0])
            else:
                # Multiple steps - compile as sequential
                compiled_steps = [self._compile_step(step) for step in on_false_config]
                return SequentialRunner(compiled_steps)
        
        # Unknown type - return as-is (might be an error, but let it fail at runtime)
        self.logger.warning("Unknown on_false type for step {}: {}", step_ref, type(on_false_config))
        return on_false_config
    
    def _compile_pipeline_step(self, step_config: Dict[str, Any]):
        """Compile a pipeline step that executes a sub-pipeline as a node.
        
        Args:
            step_config: Step configuration with 'pipeline' field and optional 'input_mapping'
            
        Returns:
            PipelineStepRunner (wrapped in ConditionalStepRunner if condition exists)
        """
        pipeline_id = step_config["pipeline"]
        input_mapping = step_config.get("input_mapping", {})
        
        if not input_mapping:
            raise ValueError(
                f"Pipeline step '{pipeline_id}' requires 'input_mapping' to map parent context to sub-pipeline inputs"
            )
        
        self.logger.debug("Compiling pipeline step: {}", pipeline_id)
        
        # Get pipeline config from current pipeline_config
        if not hasattr(self, "pipeline_config") or not self.pipeline_config:
            raise ValueError("pipeline_config not available in RunnerCompiler")
        
        # Get pipelines registry
        pipelines_registry = self.pipeline_config.get("pipelines", [])
        pipeline_ref = None
        for p in pipelines_registry:
            if isinstance(p, dict) and p.get("id") == pipeline_id:
                pipeline_ref = p
                break
        
        if not pipeline_ref:
            raise ValueError(
                f"Pipeline '{pipeline_id}' not found in pipelines registry. "
                f"Available pipelines: {[p.get('id') for p in pipelines_registry if isinstance(p, dict)]}"
            )
        
        pipeline_file = pipeline_ref.get("pipeline_file")
        if not pipeline_file:
            raise ValueError(f"Pipeline '{pipeline_id}' missing 'pipeline_file' in registry")
        
        # Load sub-pipeline configuration
        if not self.config_result:
            raise ValueError("config_result not available in RunnerCompiler for loading sub-pipelines")
        
        # Get project directory
        project_dir = self.config_result.project_dir
        if not project_dir:
            raise ValueError("project_dir not available in config_result")
        
        # Resolve pipeline file path
        from pathlib import Path
        import yaml
        from topaz_agent_kit.utils.env_substitution import env_substitution
        
        pipeline_path = project_dir / "config" / pipeline_file
        if not pipeline_path.exists():
            raise ValueError(
                f"Pipeline file not found: {pipeline_path}. "
                f"Pipeline '{pipeline_id}' references '{pipeline_file}'"
            )
        
        # Load sub-pipeline config
        try:
            with open(pipeline_path, 'r', encoding='utf-8') as f:
                sub_pipeline_config = yaml.safe_load(f)
                sub_pipeline_config = env_substitution.substitute_env_vars(sub_pipeline_config)
        except Exception as e:
            raise ValueError(f"Failed to load pipeline config from {pipeline_path}: {e}")
        
        # Extract pattern from sub-pipeline
        sub_pattern = sub_pipeline_config.get("pattern")
        if not sub_pattern:
            raise ValueError(f"Sub-pipeline '{pipeline_id}' has no 'pattern' configuration")
        
        # Create a new config_result for the sub-pipeline
        # Merge current pipeline_config with sub-pipeline config
        sub_pipeline_dir = pipeline_path.relative_to(project_dir / "config").parent
        sub_pipeline_config["pipeline_dir"] = str(sub_pipeline_dir)
        
        # Create merged config for sub-pipeline
        merged_config = self.pipeline_config.copy()
        merged_config.update(sub_pipeline_config)
        
        # Create sub-pipeline config_result
        from topaz_agent_kit.core.configuration_engine import ConfigurationResult
        sub_config_result = ConfigurationResult(
            is_valid=True,
            project_dir=project_dir,
            pipeline_config=merged_config,
            ui_config=self.config_result.ui_config if hasattr(self.config_result, 'ui_config') else {},
            individual_pipelines={},
            individual_ui_manifests={},
            chatdb_path="",
            chromadb_path="",
            rag_files_path="",
            user_files_path="",
            embedding_model="",
            vision_model=None,
            errors=[],
            warnings=[],
        )
        
        # Recursively compile sub-pipeline pattern
        # Create a new AgentRunner for the sub-pipeline with sub_config_result
        # This ensures AgentFactory can find agents from the sub-pipeline
        from topaz_agent_kit.core.agent_runner import AgentRunner
        from topaz_agent_kit.transport.agent_bus import AgentBus
        
        # Create agent bus config for sub-pipeline
        # CRITICAL: Must create new AgentBus with merged_config so it can find sub-pipeline's agents
        # Cannot reuse parent's AgentBus because it only has parent's nodes in its config
        sub_agent_bus_config = merged_config.copy()
        sub_agent_bus_config["project_dir"] = project_dir
        
        # Always create new AgentBus for sub-pipeline with merged config
        # This ensures AgentBus._get_agent_cfg() can find agents from sub-pipeline's nodes section
        sub_agent_bus = AgentBus(
            agents_by_id={},
            config=sub_agent_bus_config,
            emitter=None,  # Will be set when emitter is available
        )
        
        # Create new AgentRunner with sub_config_result
        # Reuse pipeline_structure_getter from parent if available
        parent_pipeline_structure_getter = getattr(self.agent_runner, 'pipeline_structure_getter', None)
        sub_agent_runner = AgentRunner(
            config_result=sub_config_result,
            agent_bus=sub_agent_bus,
            pipeline_structure_getter=parent_pipeline_structure_getter,
        )
        
        # Create a new RunnerCompiler for the sub-pipeline
        sub_runner_compiler = RunnerCompiler(
            agent_runner=sub_agent_runner,
            logger=self.logger,
            populate_upstream_context_func=self.populate_upstream_context_func,
            output_manager=self.output_manager,
            gate_lookup_func=self.gate_lookup_func,
            pipeline_runner_gate_handler_func=self.pipeline_runner_gate_handler_func,
            config_result=sub_config_result,
        )
        sub_runner_compiler.pipeline_config = merged_config
        
        # Compile the sub-pipeline pattern
        compiled_sub_pattern = sub_runner_compiler.compile(sub_pattern, is_top_level=True)
        
        # Import PipelineStepRunner (will create it next)
        from topaz_agent_kit.core.execution_patterns import PipelineStepRunner
        
        # Create PipelineStepRunner
        pipeline_runner = PipelineStepRunner(
            pipeline_id=pipeline_id,
            compiled_pattern_runner=compiled_sub_pattern,
            input_mapping=input_mapping,
            sub_pipeline_config=sub_pipeline_config,
            config_result=sub_config_result,
            populate_upstream_context_func=self.populate_upstream_context_func,
            output_manager=self.output_manager,
        )
        
        # Check if step has condition - wrap in ConditionalStepRunner
        if "condition" in step_config:
            condition = step_config["condition"]
            on_false = step_config.get("on_false")
            self.logger.debug(
                "Wrapping pipeline step {} with condition: {}, on_false: {}", pipeline_id, condition, on_false
            )
            return ConditionalStepRunner(pipeline_runner, condition, on_false=on_false)
        
        return pipeline_runner
