"""
Simplified Graphviz generator - follows execution flow like RunnerCompiler does
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from topaz_agent_kit.utils.logger import Logger
import subprocess
import re


class GraphvizGenerator:
    """Simplified generator that processes steps sequentially like execution does."""

    def __init__(self):
        self.logger = Logger("GraphvizGenerator")
        self.gate_colors = {
            "approval": "#2196F3",
            "input": "#9C27B0",
            "selection": "#009688",
        }
        self.gate_stroke_colors = {
            "approval": "#1565C0",
            "input": "#7B1FA2",
            "selection": "#00695C",
        }

    def generate_diagram(
        self,
        project_path: Path,
        pipeline_name: str,
        pattern_config: Dict[str, Any],
        gates_config: List[Dict] = None,
        overwrite: bool = True,
        agent_title_map: Dict[str, str] = None,
        pipeline_config: Dict[str, Any] = None,
        pipeline_name_map: Dict[str, str] = None,
    ) -> Optional[Path]:
        """Generate workflow diagram using Graphviz.
        
        Args:
            project_path: Path to project root
            pipeline_name: Name of the pipeline (used for file naming)
            pattern_config: Pipeline pattern configuration
            gates_config: List of gate configurations
            overwrite: Whether to overwrite existing files
            agent_title_map: Optional mapping of agent IDs to titles from UI manifest
            pipeline_config: Full pipeline configuration (for accessing pipelines registry)
            pipeline_name_map: Optional mapping of pipeline IDs to pipeline names
        """
        try:
            dot_content = self._generate_dot(
                pattern_config, gates_config or [], agent_title_map or {}, pipeline_config, pipeline_name_map or {}
            )
            dot_file = (
                project_path
                / "ui"
                / "static"
                / "assets"
                / f"{pipeline_name}_workflow.dot"
            )
            dot_file.parent.mkdir(parents=True, exist_ok=True)
            dot_file.write_text(dot_content, encoding="utf-8")
            self.logger.debug("Generated dot file: {}", dot_file)

            svg_file = dot_file.with_suffix(".svg")
            try:
                subprocess.run(
                    ["dot", "-Tsvg", str(dot_file), "-o", str(svg_file)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.logger.success("Generated SVG: {}", svg_file)
                return svg_file
            except subprocess.CalledProcessError as e:
                self.logger.error("Failed to generate SVG: {}", e.stderr)
                return None
            except FileNotFoundError:
                self.logger.error(
                    "Graphviz 'dot' command not found. Install with: brew install graphviz"
                )
                return None

        except Exception as e:
            self.logger.error("Failed to generate diagram: {}", e)
            return None

    def _condition_references_gate_context(
        self, condition: str, gate_id: str, gate_type: str = None
    ) -> bool:
        """Check if a condition expression references a gate's context (decision, selected_option, or input fields).
        
        Args:
            condition: The condition expression string
            gate_id: The gate ID to check for
            gate_type: Gate type ("approval", "selection", or "input") to check specific patterns
            
        Returns:
            True if condition references the gate's context, False otherwise
        """
        if not condition:
            return False
        
        # Normalize condition to uppercase for case-insensitive matching
        condition_upper = condition.upper()
        gate_id_upper = gate_id.upper()
        
        # Build patterns based on gate type
        patterns = []
        
        # Approval gates: hitl.{gate_id}.decision or {gate_id}.decision
        if gate_type is None or gate_type == "approval":
            patterns.extend([
                rf"HITL\.{re.escape(gate_id_upper)}\.DECISION",
                rf"HITL\['{re.escape(gate_id)}'\]\.DECISION",
                rf'HITL\["{re.escape(gate_id)}"\]\.DECISION',
                rf"{re.escape(gate_id_upper)}\.DECISION",  # Shorthand without hitl prefix
            ])
        
        # Selection gates: hitl.{gate_id}.selected_option or {gate_id}.selected_option
        if gate_type is None or gate_type == "selection":
            patterns.extend([
                rf"HITL\.{re.escape(gate_id_upper)}\.SELECTED_OPTION",
                rf"HITL\['{re.escape(gate_id)}'\]\.SELECTED_OPTION",
                rf'HITL\["{re.escape(gate_id)}"\]\.SELECTED_OPTION',
                rf"{re.escape(gate_id_upper)}\.SELECTED_OPTION",  # Shorthand without hitl prefix
            ])
        
        # Input gates: hitl.{gate_id}.{field_name} or {gate_id}.{field_name} or context_key
        # Since field names vary, we check if condition references the gate_id at all
        # This is a broader check - any reference to gate_id suggests dependency
        if gate_type is None or gate_type == "input":
            # Check for direct gate_id reference (common pattern for input gates)
            # This will match: {gate_id}.field_name, hitl.{gate_id}.field_name, etc.
            # Use word boundary to avoid partial matches
            patterns.extend([
                rf"\b{re.escape(gate_id_upper)}\.",  # gate_id. (word boundary to avoid partial matches)
                rf"HITL\.{re.escape(gate_id_upper)}\.",
                rf"HITL\['{re.escape(gate_id)}'\]\.",
                rf'HITL\["{re.escape(gate_id)}"\]\.',
            ])
        
        for pattern in patterns:
            if re.search(pattern, condition_upper):
                return True
        
        return False

    def _capitalize_name(self, name: str) -> str:
        """Convert snake_case to Proper Case, split to new line after every two words.
        
        Also handles regular space-separated titles from UI manifests.
        
        Args:
            name: Either snake_case ID or space-separated title
            
        Returns:
            Formatted name with 2 words per line
        """
        # Remove case suffixes like _FALSE, _TRUE, etc.
        if name.endswith("_FALSE") or name.endswith("_TRUE"):
            name = name.rsplit("_", 1)[0]

        # Check if name contains underscores (snake_case) or spaces (title)
        if "_" in name:
            # Snake case: split by underscore
            words = name.split("_")
            capitalized = [word.capitalize() for word in words]
        else:
            # Space-separated title: split by space
            words = name.split()
            # Capitalize each word (preserve existing capitalization for proper nouns)
            capitalized = [word if word[0].isupper() else word.capitalize() for word in words]

        # Group words in pairs (2 words per line)
        # For names with 2 words, put each on its own line for better readability
        result_lines = []
        if len(capitalized) == 2:
            # Two words: put each on its own line
            result_lines = capitalized
        else:
            # More than 2 words: group in pairs (2 words per line)
            for i in range(0, len(capitalized), 2):
                pair = capitalized[i : i + 2]
                result_lines.append(" ".join(pair))

        # Return newline-separated string for multi-line labels
        return "\\n".join(result_lines)

    def _extract_variable_name(self, condition: str) -> str:
        """Extract simplified variable names from complex dotted notation.
        
        Transforms conditions like:
        - 'sot_question_loader.total_count > 0' -> 'total_count > 0'
        - 'agent.sub.field.value == 10' -> 'value == 10'
        - 'LEN(agent.field) > 5' -> 'LEN(field) > 5'
        
        Args:
            condition: Original condition string with potentially dotted variables
            
        Returns:
            Simplified condition with extracted variable names, or original if extraction fails
        """
        if not condition:
            return condition
        
        # Skip variable extraction for special formatting labels like TERMINATION(...) or ITERATE(...)
        # These are display labels, not conditions with dotted variables
        condition_upper = condition.upper().strip()
        if condition_upper.startswith("TERMINATION(") or condition_upper.startswith("ITERATE("):
            return condition
        
        try:
            # Pattern to match dotted variable references
            # Matches: word.word.word (any number of dots)
            # Also handles function calls: FUNC(agent.field) -> FUNC(field)
            
            # First, handle function calls with dotted arguments
            # Pattern: FUNCTION_NAME(agent.field.subfield) -> FUNCTION_NAME(subfield)
            def simplify_function_args(match):
                func_name = match.group(1)
                args = match.group(2)
                # Extract last segment from dotted path in arguments
                if '.' in args:
                    # Split by comma to handle multiple arguments
                    arg_parts = args.split(',')
                    simplified_args = []
                    for arg in arg_parts:
                        arg = arg.strip()
                        if '.' in arg:
                            # Extract last segment after final dot
                            last_segment = arg.split('.')[-1].strip()
                            simplified_args.append(last_segment)
                        else:
                            simplified_args.append(arg)
                    return f"{func_name}({', '.join(simplified_args)})"
                return match.group(0)
            
            # Handle function calls: FUNC(agent.field) or FUNC(agent.field, other)
            # Match function names (alphanumeric with underscores, starting with letter/underscore)
            condition = re.sub(
                r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]+)\)',
                simplify_function_args,
                condition,
                flags=re.IGNORECASE
            )
            
            # Now handle standalone dotted variables (not in function calls)
            # Pattern: agent.field.subfield -> subfield
            # But preserve operators, quotes, numbers, etc.
            
            # First, handle special operators like "is null", "is not null", "is not", etc.
            # Replace them with placeholders temporarily to avoid splitting issues
            # Handle both lowercase and uppercase versions since conditions may be uppercased
            # Map: placeholder -> list of operator variants
            special_ops_map = {
                '__IS_NOT_NULL__': ['is not null', 'IS NOT NULL', 'Is Not Null'],
                '__IS_NULL__': ['is null', 'IS NULL', 'Is Null'],
                '__IS_NOT__': ['is not', 'IS NOT', 'Is Not'],
                '__IS__': [' is ', ' IS ', ' Is '],
            }
            # Track which variant was used for each placeholder (for restoration)
            used_variants = {}
            condition_work = condition
            for placeholder, op_variants in special_ops_map.items():
                for op in op_variants:
                    if op in condition_work:
                        condition_work = condition_work.replace(op, placeholder)
                        used_variants[placeholder] = op  # Store the variant that was used
                        break  # Only replace once per placeholder
            
            # Better approach: Find all dotted identifiers and replace them directly
            # Pattern to match: word.word.word (dotted identifier)
            # This handles cases like: ag_email_selector.current_email_id
            def replace_dotted_var(match):
                dotted_var = match.group(0)
                # Extract last segment after final dot
                last_segment = dotted_var.split('.')[-1]
                return last_segment
            
            # Match dotted identifiers (alphanumeric with dots)
            # Pattern: identifier.identifier (at least one dot, multiple segments)
            # This pattern matches: ag_email_selector.current_email_id, agent.field.value, etc.
            # We match the full dotted path and replace with just the last segment
            condition_work = re.sub(
                r'[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)+',
                replace_dotted_var,
                condition_work,
                flags=re.IGNORECASE
            )
            
            # Restore special operators using the variant that was originally used
            for placeholder, original_op in used_variants.items():
                condition_work = condition_work.replace(placeholder, original_op)
            
            # Clean up any extra spaces
            simplified = re.sub(r'\s+', ' ', condition_work).strip()
            
            return simplified
            
        except Exception as e:
            self.logger.error("Failed to extract variable name from condition '{}': {}", condition, e)
            return condition

    def _format_multiline_condition(self, condition: str) -> str:
        """Format complex conditions with line breaks before AND/OR operators.
        
        Uses Graphviz \\l escape sequence for left-justified newlines.
        Breaks on every AND/OR operator, handling cases with or without spaces.
        
        Args:
            condition: Condition string that may contain AND/OR operators
            
        Returns:
            Formatted condition with line breaks before logical operators
        """
        if not condition:
            return condition
        
        try:
            # Check if condition contains AND/OR
            # Handle both cases: "A AND B" (with spaces) and "A OR(B)" (without space)
            if not re.search(r'\b(AND|OR)\b|(AND|OR)\(', condition, flags=re.IGNORECASE):
                # No AND/OR found, return as is
                return condition
            
            # First, normalize OR( and AND( to have a space: OR ( and AND (
            # This makes parsing easier
            condition = re.sub(r'\b(AND|OR)\(', r'\1 (', condition, flags=re.IGNORECASE)
            
            # Split on AND/OR while preserving them using capturing group
            # Pattern: \s* matches optional whitespace before, (AND|OR) captures operator, \s* matches optional whitespace after
            parts = re.split(r'\s*\b(AND|OR)\b\s*', condition, flags=re.IGNORECASE)
            
            if len(parts) == 1:
                # No split occurred, return original
                return condition
            
            # Reconstruct with line breaks before each AND/OR operator
            # Format: "condition1\lAND condition2" (operator and next condition on same line, all left-aligned)
            result = []
            
            for i, part in enumerate(parts):
                if i == 0:
                    # First part (before any operator) - add \l at start for left alignment
                    if part.strip():
                        result.append('\\l' + part)
                elif i % 2 == 1:
                    # This is an AND/OR operator (odd indices)
                    # Add line break before operator, then operator on same line
                    result.append('\\l' + part.upper())
                else:
                    # This is text after operator (even indices)
                    # Add space before the condition (operator and condition on same line)
                    if part and part[0] in '()[]{}':
                        result.append(' ' + part)
                    else:
                        result.append(' ' + part)
            
            formatted = ''.join(result)
            
            # Handle parentheses - ensure proper spacing (no extra \l after operator)
            # Format: "condition\lAND (sub_condition)" - operator and opening paren on same line
            formatted = re.sub(r'(AND|OR)\\l\s*\(', r'\1 (', formatted, flags=re.IGNORECASE)
            # If we have "condition AND(" without line break, add space: "condition AND ("
            formatted = re.sub(r'\b(AND|OR)\s*\(', r'\1 (', formatted, flags=re.IGNORECASE)
            
            return formatted
            
        except Exception as e:
            self.logger.error("Failed to format multiline condition '{}': {}", condition, e)
            return condition

    def _get_label_color(self, label: str) -> str:
        """Get appropriate font color for edge label based on its content.
        
        Args:
            label: Edge label text
            
        Returns:
            Color hex code for the label
        """
        if not label:
            return "#888"  # Default gray
        
        label_upper = label.upper().strip()
        
        # TRUE labels - green
        if label_upper == "TRUE":
            return "#4CAF50"
        
        # FALSE labels - red
        if label_upper.startswith("FALSE"):
            if "(STOP)" in label_upper:
                return "#B91C1C"  # Dark red for FALSE (STOP)
            return "#F44336"  # Red for FALSE
        
        # LOOP labels - blue
        if label_upper == "LOOP":
            return "#2196F3"
        
        # TERMINATION labels - red (loop termination conditions)
        if label_upper.startswith("TERMINATION"):
            return "#F44336"  # Red for termination
        
        # APPROVE labels - green (positive action, similar to TRUE)
        if label_upper == "APPROVE":
            return "#22C55E"  # Bright green for approve
        
        # REJECT labels - red (negative action, similar to FALSE)
        if label_upper == "REJECT":
            return "#EF4444"  # Bright red for reject
        
        # DENY labels - red (negative action, similar to REJECT)
        if label_upper == "DENY":
            return "#EF4444"  # Bright red for deny
        
        # SUBMIT labels - green (positive action, similar to APPROVE)
        if label_upper == "SUBMIT":
            return "#22C55E"  # Bright green for submit
        
        # CANCEL labels - red (negative action, similar to REJECT/DENY)
        if label_upper == "CANCEL":
            return "#EF4444"  # Bright red for cancel
        
        # DECLINE labels - red (negative action, similar to REJECT/DENY/CANCEL)
        if label_upper == "DECLINE":
            return "#EF4444"  # Bright red for decline
        
        # RETRY labels - orange (indicates retry/retry action)
        if label_upper == "RETRY":
            return "#FF9800"  # Orange for retry
        
        # Condition labels - keep original gray
        return "#888"  # Same as edge color for consistency

    def _format_edge_label(self, label: str) -> tuple[str, str]:
        """Format edge label with variable extraction, multiline formatting, and capitalization.
        
        Args:
            label: Original edge label
            
        Returns:
            Tuple of (formatted_label, font_color)
        """
        if not label:
            return label, "#888"
        
        try:
            # Special handling for TERMINATION labels: extract variables only from termination condition part
            label_upper = label.upper().strip()
            if label_upper.startswith("TERMINATION(") and label_upper.endswith(")"):
                # Extract content inside TERMINATION(...)
                content = label[11:-1]  # Remove "TERMINATION(" and ")"
                
                # Split by " | " to separate MAX part from termination condition
                parts = content.split(" | ", 1)
                
                if len(parts) == 2:
                    # Has both MAX part and termination condition
                    max_part = parts[0]
                    term_cond = parts[1]
                    
                    # Extract variable names only from termination condition part
                    simplified_term_cond = self._extract_variable_name(term_cond)
                    
                    # Convert to uppercase and format
                    formatted_max = max_part.upper()
                    formatted_term_cond = simplified_term_cond.upper()
                    
                    # Replace underscores with spaces
                    formatted_max = formatted_max.replace('_', ' ')
                    formatted_term_cond = formatted_term_cond.replace('_', ' ')
                    
                    # Format multiline for complex conditions
                    formatted_term_cond = self._format_multiline_condition(formatted_term_cond)
                    
                    # Reconstruct TERMINATION label
                    formatted = f"TERMINATION({formatted_max} | {formatted_term_cond})"
                else:
                    # Only one part (either MAX or termination condition, or combined)
                    # Extract variables from the whole content
                    simplified = self._extract_variable_name(content)
                    formatted = simplified.upper().replace('_', ' ')
                    formatted = self._format_multiline_condition(formatted)
                    formatted = f"TERMINATION({formatted})"
            else:
                # Regular label processing
                # Step 1: Extract variable names from dotted notation
                simplified = self._extract_variable_name(label)
                
                # Step 2: Convert to uppercase (existing behavior)
                formatted = simplified.upper()
                
                # Step 3: Replace underscores with spaces (existing behavior)
                formatted = formatted.replace('_', ' ')
                
                # Step 4: Format multiline for complex conditions with AND/OR
                formatted = self._format_multiline_condition(formatted)
            
            # Step 5: Get appropriate color
            color = self._get_label_color(label)
            
            return formatted, color
            
        except Exception as e:
            self.logger.error("Failed to format edge label '{}': {}", label, e)
            # Fallback: uppercase and replace underscores, use default color
            fallback = str(label).upper().replace('_', ' ')
            return fallback, "#888"

    def _generate_dot(
        self, pattern: Dict[str, Any], gates: List[Dict], agent_title_map: Dict[str, str] = None, pipeline_config: Dict[str, Any] = None, pipeline_name_map: Dict[str, str] = None
    ) -> str:
        """Generate Graphviz dot content.
        
        Args:
            pattern: Pipeline pattern configuration
            gates: List of gate configurations
            agent_title_map: Optional mapping of agent IDs to titles from UI manifest
            pipeline_config: Full pipeline configuration (for accessing pipelines registry)
            pipeline_name_map: Optional mapping of pipeline IDs to pipeline names
        """
        if agent_title_map is None:
            agent_title_map = {}
        if pipeline_name_map is None:
            pipeline_name_map = {}
        
        lines = ["digraph workflow {"]
        lines.append('  bgcolor="transparent";')
        lines.append("  rankdir=LR;")
        lines.append('  node [fontname="Arial, sans-serif", fontsize=11];')
        lines.append('  edge [fontname="Arial, sans-serif", fontsize=10];')
        lines.append("")

        # START and END
        lines.extend(
            [
                "  START [",
                '    shape=circle, label="START",',
                '    fillcolor="#4CAF50", style="filled,solid",',
                "    width=0.5, height=0.5,",
                "    fontcolor=white, fontsize=9,",
                "    fixedsize=true",
                "  ];",
                "  END [",
                '    shape=circle, label="END",',
                '    fillcolor="#F44336", style="filled,solid",',
                "    width=0.5, height=0.5,",
                "    fontcolor=white, fontsize=9,",
                "    fixedsize=true",
                "  ];",
                "",
            ]
        )

        # Process pattern
        edges = []
        nodes = set()
        gates_map = {}
        node_info_map = {}
        # Store pipeline_name_map in node_info_map for access during node definition
        node_info_map["_pipeline_name_map"] = pipeline_name_map  # Store additional info for nodes (conditions, etc.)

        # Process pattern step by step
        if pattern.get("type") == "handoff":
            # Handle root-level handoff pattern
            current = "START"
            result = self._process_step(
                pattern, current, "END", edges, nodes, gates, gates_map, node_info_map
            )

        elif pattern.get("type") == "group_chat":
            # Minimal group chat rendering: hub, participants, loop, END label
            hub_id = "GROUP_CHAT"
            nodes.add(hub_id)
            # START -> HUB
            edges.append(("START", hub_id, None))

            participants = pattern.get("participants", [])
            termination = pattern.get("termination", {})

            # HUB <-> participants
            for p in participants:
                if isinstance(p, dict) and "node" in p:
                    agent_id = p["node"].split(":")[0]
                    nodes.add(agent_id)
                    edges.append((hub_id, agent_id, None))  # solid
                    edges.append((agent_id, hub_id, "dashed"))  # dashed back

            # Self-loop on hub to indicate iteration
            edges.append((hub_id, hub_id, "LOOP"))

            # END edge label (ALL CAPS)
            end_label = None
            max_rounds = termination.get("max_rounds")
            condition = termination.get("condition")
            if max_rounds and condition:
                end_label = f"MAX {max_rounds} OR {str(condition).upper()}"
            elif max_rounds:
                end_label = f"MAX {max_rounds}"
            elif condition:
                end_label = str(condition).upper()

            edges.append((hub_id, "END", end_label))

        elif pattern.get("type") == "sequential":
            current = "START"
            steps = pattern.get("steps", [])

            for i, step in enumerate(steps):
                # Determine what comes after this step
                remaining_steps = steps[i + 1 :]
                next_target = None
                next_is_pattern = False

                if remaining_steps:
                    # Look at next step
                    next_step = remaining_steps[0]
                    if "node" in next_step:
                        next_target = next_step["node"].split(":")[0]
                        nodes.add(next_target)
                    elif "gate" in next_step:
                        gate_id = next_step["gate"]
                        gate_info = next(
                            (g for g in gates if g.get("id") == gate_id), {}
                        )
                        next_target = f"HITL: {gate_id.upper()}"
                        if gate_id not in gates_map:
                            gates_map[gate_id] = gate_info
                    elif next_step.get("type") in ("parallel", "sequential", "loop"):
                        # Next step is a pattern - mark it and find what comes after
                        next_is_pattern = True
                        # Check if current step is a conditional node and next step is a pattern with condition
                        # If so, FALSE path should go to the pattern's COND: P{idx} node
                        current_step_is_conditional = step.get("node") and step.get("condition")
                        next_step_condition = next_step.get("condition", "")
                        next_step_has_condition = bool(next_step_condition and next_step_condition.strip())
                        if current_step_is_conditional and next_step_has_condition:
                            # Predict the COND: P{idx} label for the pattern
                            # This will be used for the FALSE path of the conditional node
                            if node_info_map is not None:
                                current_counter = node_info_map.get("_cond_counter", 0)
                                predicted_idx = current_counter + 1
                                next_target = f"COND: P{predicted_idx}"
                                
                                # Store this prediction so the conditional node can use it
                                if "_predicted_pattern_conds" not in node_info_map:
                                    node_info_map["_predicted_pattern_conds"] = {}
                                # Store using the node ID (e.g., "sot_sql_executor")
                                node_id = step.get("node")
                                if node_id:
                                    # Handle node IDs that might have format like "agent_id:output_key"
                                    node_id_base = node_id.split(":")[0]
                                    node_info_map["_predicted_pattern_conds"][node_id_base] = next_target
                            else:
                                next_target = "COND: P"
                        else:
                            # Continue with existing logic
                            if len(remaining_steps) > 1:
                                after_parallel = remaining_steps[1]
                                if "gate" in after_parallel:
                                    gate_id = after_parallel["gate"]
                                    gate_info = next(
                                        (g for g in gates if g.get("id") == gate_id), {}
                                    )
                                    next_target = f"HITL: {gate_id.upper()}"
                                    if gate_id not in gates_map:
                                        gates_map[gate_id] = gate_info
                                elif "node" in after_parallel:
                                    next_target = after_parallel["node"].split(":")[0]
                                    nodes.add(next_target)
                                else:
                                    # After pattern is another pattern or end
                                    next_target = "END"
                            else:
                                next_target = "END"
                else:
                    next_target = "END"

                # Store next_is_pattern info for gate processing
                # Also check if next step has condition that references gate decision
                if "gate" in step:
                    gate_id = step["gate"]
                    # Ensure gate_info is in gates_map before setting flags
                    gate_info = gates_map.get(gate_id) or next(
                        (g for g in gates if g.get("id") == gate_id), {}
                    )
                    if gate_id not in gates_map:
                        gates_map[gate_id] = gate_info
                    # Store the step dict early so parallel pattern processor can access it
                    gate_info["_step_dict"] = step
                    gate_info["_next_is_pattern"] = next_is_pattern
                    if next_is_pattern:
                        gate_info["_next_pattern_step"] = remaining_steps[0] if remaining_steps else None
                    
                    # Store next step info for gate processing (so gate can check condition directly)
                    if remaining_steps:
                        gate_info["_next_step"] = remaining_steps[0]
                    # Update gates_map to ensure step dict is preserved
                    # Store using both original and lowercase keys for consistency
                    gates_map[gate_id] = gate_info
                    gates_map[gate_id.lower()] = gate_info
                    
                    # Check if next step (node or pattern) has condition referencing this gate's context
                    if remaining_steps:
                        next_step = remaining_steps[0]
                        next_condition = None
                        
                        # Check if next step is a node with condition
                        if "node" in next_step:
                            next_condition = next_step.get("condition", "")
                        # Check if next step is a pattern (sequential/parallel/loop) with condition
                        elif next_step.get("type") in ("sequential", "parallel", "loop"):
                            next_condition = next_step.get("condition", "")
                        
                        if next_condition:
                            # Get gate type from gate_info, or find it in gates list if not set
                            gate_type = gate_info.get("type")
                            if not gate_type:
                                # Try to find gate in gates list to get type
                                gate_from_list = next((g for g in gates if g.get("id") == gate_id), None)
                                if gate_from_list:
                                    gate_type = gate_from_list.get("type", "approval")
                                    gate_info["type"] = gate_type
                                else:
                                    gate_type = "approval"
                            
                            # Check if condition references gate context (works for all gate types now)
                            if self._condition_references_gate_context(
                                next_condition, gate_id, gate_type
                            ):
                                # Next step conditionally routes based on gate context (decision/selected_option)
                                # Suppress gate action paths - conditional node will handle routing
                                gate_info["_suppress_action_paths"] = True
                                # Update gates_map to ensure flag is preserved
                                gates_map[gate_id] = gate_info

                # If this step is a gate and next step is a parallel pattern, store the step
                # in a way that parallel processor can access it
                if "gate" in step and remaining_steps and remaining_steps[0].get("type") == "parallel":
                    gate_id = step["gate"]
                    # Ensure _step_dict is stored with both keys
                    if gate_id in gates_map:
                        gates_map[gate_id]["_step_dict"] = step
                    if gate_id.lower() in gates_map:
                        gates_map[gate_id.lower()]["_step_dict"] = step
                
                # Before processing the step, if it's a sequential pattern and next step has condition,
                # check if the sequential pattern contains a gate as last step that should be suppressed
                if step.get("type") == "sequential" and remaining_steps:
                    next_step = remaining_steps[0]
                    next_condition = None
                    if next_step.get("type") in ("sequential", "parallel", "loop"):
                        next_condition = next_step.get("condition", "")
                    
                    if next_condition:
                        # Check if this sequential pattern has a gate as its last step
                        seq_steps = step.get("steps", [])
                        if seq_steps:
                            last_step = seq_steps[-1]
                            if "gate" in last_step:
                                gate_id = last_step["gate"]
                                # Get gate type
                                gate_info = gates_map.get(gate_id) or next(
                                    (g for g in gates if g.get("id") == gate_id), {}
                                )
                                gate_type = gate_info.get("type", "approval")
                                
                                # Check if condition references this gate
                                if self._condition_references_gate_context(
                                    next_condition, gate_id, gate_type
                                ):
                                    # Suppress the gate's action paths
                                    gate_info["_suppress_action_paths"] = True
                                    gates_map[gate_id] = gate_info
                                    gates_map[gate_id.lower()] = gate_info
                
                result = self._process_step(
                    step,
                    current,
                    next_target,
                    edges,
                    nodes,
                    gates,
                    gates_map,
                    node_info_map,
                )

                # Handle None return from switch/pattern steps
                if result[0] is None:
                    # Pattern handled its own flow (e.g., switch)
                    # Keep current as is for next iteration
                    continue

                current, _ = result

            # Add final edge from last node to END only if we have a valid current
            # Skip if it's a gate or if current is still START (no steps processed)
            # Also skip if we ended with a None return (switch/handoff handled their own flow)
            if (
                current
                and current != "START"
                and current != "END"
                and not current.startswith("HITL:")
            ):
                # Check if the last step was a switch/handoff pattern by looking for its presence
                has_pattern_handled_flow = any(
                    isinstance(step, dict)
                    and (
                        step.get("type") == "switch"
                        or str(step.get("type", "")).startswith("switch")
                        or step.get("type") == "handoff"
                    )
                    for step in pattern.get("steps", [])
                )
                if not has_pattern_handled_flow:
                    edges.append((current, "END", None))

        # Consolidate switch case nodes: merge case-specific nodes (e.g., tci_results_recorder_APPROVE_RECOMMENDED)
        # into a single base node (e.g., tci_results_recorder) to avoid showing multiple identical nodes
        # Pattern matches: _APPROVE_RECOMMENDED, _REJECT, _ESCALATE, _REQUEST_INFO, _DEFAULT, etc.
        # Must start with underscore followed by uppercase letters/underscores
        switch_case_pattern = r'_([A-Z][A-Z0-9_]*)$'  # More permissive: allows numbers and multiple underscores
        
        # Find all case-specific nodes and group them by base agent ID
        # Exclude handoff nodes (HANDOFF_START, HANDOFF_END) and other special nodes
        case_node_groups = {}  # Maps base_agent_id -> set of case-specific node IDs
        for node_name in list(nodes):
            # Skip special nodes and pattern nodes
            if (node_name not in ["START", "END", "SWITCH", "HANDOFF_START", "HANDOFF_END"] and 
                not node_name.startswith("COND:") and 
                not node_name.startswith("HITL:") and 
                not node_name.startswith("CONVERGE:") and
                not node_name.startswith("HANDOFF_")):
                # Extract base node ID (remove protocol suffix if present, e.g., "node:a2a" -> "node")
                base_node_id = node_name.split(":")[0]
                switch_case_match = re.search(switch_case_pattern, base_node_id)
                if switch_case_match:
                    # This is a switch case node - extract base agent ID
                    base_agent_id = base_node_id[:switch_case_match.start()]
                    # Only consolidate if base_agent_id is not empty and case suffix is meaningful
                    if base_agent_id and len(switch_case_match.group(1)) > 0:
                        if base_agent_id not in case_node_groups:
                            case_node_groups[base_agent_id] = set()
                        case_node_groups[base_agent_id].add(node_name)
        
        # Consolidate: for each group with case nodes, merge them into the base node
        # BUT only if all case nodes have the same next node(s) - otherwise they represent different paths
        node_consolidation_map = {}  # Maps case-specific node -> base node
        for base_agent_id, case_nodes in case_node_groups.items():
            base_node = base_agent_id
            # Check if base node already exists in nodes (might have been added separately)
            base_node_exists = base_node in nodes
            
            # Only consolidate if we have case nodes
            if len(case_nodes) > 0:
                # Group case nodes by their outgoing edges (next nodes)
                # Nodes with different next nodes should NOT be consolidated
                nodes_by_next = {}  # Maps (frozenset of next nodes) -> list of case nodes
                
                for case_node in case_nodes:
                    # Find all nodes this case node connects to
                    next_nodes = set()
                    for from_node, to_node, label in edges:
                        if from_node == case_node:
                            next_nodes.add((to_node, label))  # Include label to distinguish different edge types
                    
                    # Use frozenset for hashability
                    next_nodes_key = frozenset(next_nodes)
                    if next_nodes_key not in nodes_by_next:
                        nodes_by_next[next_nodes_key] = []
                    nodes_by_next[next_nodes_key].append(case_node)
                
                # Only consolidate groups where all nodes have the same next nodes
                # AND there are multiple nodes in that group (or base exists)
                for next_nodes_key, nodes_with_same_next in nodes_by_next.items():
                    # Need at least 2 nodes with same next, OR 1 node with same next if base exists
                    should_consolidate = len(nodes_with_same_next) > 1 or base_node_exists
                    
                    if should_consolidate:
                        nodes.add(base_node)  # Ensure base node exists
                        
                        # Map all case nodes with same next to base node
                        for case_node in nodes_with_same_next:
                            node_consolidation_map[case_node] = base_node
                            # Remove case-specific node from nodes set
                            nodes.discard(case_node)
        
        # Update all edges to use consolidated nodes and deduplicate
        if node_consolidation_map:
            updated_edges = []
            seen_edges = set()  # Track (from, to, label) tuples to avoid duplicates
            
            for from_node, to_node, label in edges:
                # Update from_node if it's a case-specific node
                new_from = node_consolidation_map.get(from_node, from_node)
                # Update to_node if it's a case-specific node
                new_to = node_consolidation_map.get(to_node, to_node)
                
                # Create edge tuple for deduplication
                edge_tuple = (new_from, new_to, label)
                if edge_tuple not in seen_edges:
                    seen_edges.add(edge_tuple)
                    updated_edges.append(edge_tuple)
            
            edges = updated_edges

        # Add node definitions
        for node_name in sorted(nodes):
            if node_name not in ["START", "END"] and not node_name.startswith("HITL:"):
                if node_name == "SWITCH":
                    # Style SWITCH node as hexagon
                    # Get condition if present
                    switch_condition = ""
                    if (
                        node_name in node_info_map
                        and "condition" in node_info_map[node_name]
                    ):
                        switch_condition = node_info_map[node_name]["condition"]

                    # Simple label for SWITCH
                    switch_label = '"SWITCH"'

                    lines.extend(
                        [
                            f'  "{node_name}" [',
                            "    shape=hexagon,",
                            f"    label={switch_label},",
                            '    fillcolor="#FFC107", style="filled",',  # Amber/orange background
                            '    color="#F57C00", penwidth=2,',
                            "    width=0.8, height=0.8,",
                            "    fontsize=9, fontcolor=white,",
                            "    fixedsize=true",
                            "  ];",
                        ]
                    )
                elif node_name.startswith("CONVERGE:"):
                    # Style convergence point as small gray circle (no text)
                    # This is used to show convergence between consecutive parallel patterns
                    lines.extend(
                        [
                            f'  "{node_name}" [',
                            "    shape=circle,",
                            '    label="",',  # No text
                            '    fillcolor="#CCCCCC", style="filled",',  # Gray background
                            '    color="#888888", penwidth=2,',
                            "    width=0.3, height=0.3,",  # Smaller than COND nodes
                            "    fixedsize=true",
                            "  ];",
                        ]
                    )
                elif node_name.startswith("COND:"):
                    # Style condition node as small gray diamond (no text)
                    lines.extend(
                        [
                            f'  "{node_name}" [',
                            "    shape=diamond,",
                            '    label="",',  # No text
                            '    fillcolor="#CCCCCC", style="filled",',  # Gray background
                            '    color="#888888", penwidth=2,',
                            "    width=0.5, height=0.5,",
                            "    fixedsize=true",
                            "  ];",
                        ]
                    )
                elif node_name.startswith("HANDOFF_"):
                    # Style handoff node as small gray circle (no text)
                    lines.extend(
                        [
                            f'  "{node_name}" [',
                            "    shape=circle,",
                            '    label="",',  # No text
                            '    fillcolor="#CCCCCC", style="filled",',  # Gray background
                            '    color="#888888", penwidth=2,',
                            "    width=0.4, height=0.4,",
                            "    fixedsize=true",
                            "  ];",
                        ]
                    )
                elif node_name == "GROUP_CHAT":
                    # Group chat hub styling (ellipse, yellow theme)
                    lines.extend(
                        [
                            f'  "{node_name}" [',
                            "    shape=ellipse,",
                            '    label="GROUP CHAT\\nRound-Robin",',
                            '    fillcolor="#FFF9C4", style="filled",',
                            '    color="#FDD835", penwidth=2,',
                            "    width=2.0, height=1.2,",
                            "    fixedsize=true,",
                            "    fontsize=10",
                            "  ];",
                        ]
                    )
                else:
                    # Regular agent nodes
                    # Extract base node ID (remove :in-proc suffix if present)
                    base_node_id = node_name.split(":")[0]
                    
                    # Check if this is a switch case node (ends with _CASE_VALUE where CASE_VALUE is uppercase)
                    # Switch pattern creates nodes like "tci_results_recorder_APPROVE_RECOMMENDED"
                    # We need to strip the case suffix to get the base agent ID for UI manifest lookup
                    switch_case_pattern = r'_([A-Z][A-Z_]+)$'  # Matches _APPROVE_RECOMMENDED, _REJECT, etc.
                    switch_case_match = re.search(switch_case_pattern, base_node_id)
                    if switch_case_match:
                        # This is a switch case node - extract base agent ID
                        base_agent_id_for_switch = base_node_id[:switch_case_match.start()]
                        # Use base agent ID for lookup, but keep original base_node_id for other checks
                        lookup_node_id = base_agent_id_for_switch
                    else:
                        lookup_node_id = base_node_id
                    
                    # Check if this is an enhanced repeat instance node (ends with _inst_N or _inst_N_M for nested)
                    inst_pattern = r'_inst_(\d+)(?:_(\d+))?$'
                    inst_match = re.search(inst_pattern, base_node_id)
                    if inst_match:
                        # Extract base agent ID and instance indices
                        base_agent_id = base_node_id[:inst_match.start()]
                        parent_idx = int(inst_match.group(1))
                        nested_idx = int(inst_match.group(2)) if inst_match.group(2) else None
                        
                        # Get title from UI manifest using base agent ID
                        if base_agent_id in agent_title_map:
                            # Apply 2-word-per-line formatting to title
                            base_title = self._capitalize_name(agent_title_map[base_agent_id])
                            if nested_idx is not None:
                                # Nested repeat: show both indices (e.g., "Problem Solver\nInstance 1.1")
                                display_name = f"{base_title}\\nInstance {parent_idx + 1}.{nested_idx + 1}"
                            else:
                                # Top-level repeat: show single index
                                display_name = f"{base_title}\\nInstance {parent_idx + 1}"
                        else:
                            # Fallback: capitalize base agent ID and append index
                            base_display = self._capitalize_name(base_agent_id)
                            if nested_idx is not None:
                                display_name = f"{base_display}\\nInstance {parent_idx + 1}.{nested_idx + 1}"
                            else:
                                display_name = f"{base_display}\\nInstance {parent_idx + 1}"
                    else:
                        # Check if this is a regular repeat pattern instance
                        node_info = node_info_map.get(node_name, {})
                        is_repeat_instance = node_info.get("is_repeat_instance", False)
                        is_pipeline_instance = node_info.get("is_pipeline_instance", False)
                        
                        if is_repeat_instance:
                            # Check if it's a pipeline instance
                            if is_pipeline_instance:
                                # Pipeline repeat instance
                                base_pipeline_id = node_info.get("base_pipeline_id", base_node_id)
                                instance_index = node_info.get("instance_index", 0)
                                
                                # Get pipeline name from pipeline_name_map
                                if base_pipeline_id in pipeline_name_map:
                                    base_title = pipeline_name_map[base_pipeline_id]
                                else:
                                    # Format pipeline_id nicely
                                    base_title = self._capitalize_name(base_pipeline_id.replace("_", " "))
                                
                                display_name = f"{base_title}\\nInstance {instance_index + 1}"
                            else:
                                # Agent repeat instance
                                base_agent_id = node_info.get("base_agent_id", base_node_id)
                                instance_index = node_info.get("instance_index", 0)
                                
                                # Get title from UI manifest using base agent ID
                                if base_agent_id in agent_title_map:
                                    # Apply 2-word-per-line formatting to title
                                    base_title = self._capitalize_name(agent_title_map[base_agent_id])
                                    # Append instance index
                                    display_name = f"{base_title}\\nInstance {instance_index + 1}"
                                else:
                                    # Fallback: capitalize base agent ID and append index
                                    base_display = self._capitalize_name(base_agent_id)
                                    display_name = f"{base_display}\\nInstance {instance_index + 1}"
                        else:
                            # Check if this is a pipeline node (not an instance)
                            if base_node_id in pipeline_name_map:
                                # This is a pipeline node
                                display_name = pipeline_name_map[base_node_id]
                            elif lookup_node_id in agent_title_map:
                                # Regular agent node - use title from UI manifest if available
                                # Use lookup_node_id which has switch case suffix stripped if present
                                # Apply 2-word-per-line formatting to title
                                display_name = self._capitalize_name(agent_title_map[lookup_node_id])
                            else:
                                display_name = self._capitalize_name(node_name)
                    
                    # Determine if this is a pipeline node (check node_info or pipeline_name_map)
                    node_info = node_info_map.get(node_name, {})
                    is_pipeline = (
                        node_info.get("is_pipeline_instance", False) or
                        node_info.get("is_pipeline", False) or
                        base_node_id in pipeline_name_map or
                        node_info.get("base_pipeline_id") is not None
                    )
                    
                    # Use different color for pipeline nodes
                    if is_pipeline:
                        # Pipeline nodes: orange theme
                        fill_color = "#FFF3E0"  # Light orange background
                        stroke_color = "#FF6F00"  # Dark orange border
                    else:
                        # Agent nodes: blue theme (existing)
                        fill_color = "#E3F2FD"
                        stroke_color = "#666"
                    
                    # Calculate width based on label length (longer names need more width)
                    # Count lines in display_name (split by \n)
                    label_lines = display_name.split("\\n")
                    max_line_length = max(len(line) for line in label_lines) if label_lines else len(display_name)
                    # Base width of 1.8, add 0.1 for every 5 characters over 10
                    node_width = max(1.8, 1.8 + (max(0, max_line_length - 10) * 0.1))
                    # Cap at 2.5 to prevent nodes from getting too wide
                    node_width = min(node_width, 2.5)
                    
                    lines.extend(
                        [
                            f'  "{node_name}" [',
                            "    shape=box,",  # Explicitly set to rectangular box
                            f'    label="{display_name}",',
                            f'    fillcolor="{fill_color}", style="filled,rounded",',
                            f'    color="{stroke_color}", penwidth=2,',
                            f"    width={node_width:.2f}, height=0.75,",  # Dynamic width based on label
                            "    fixedsize=true,",
                            "    fontsize=11",  # Agent text size
                            "  ];",
                        ]
                    )

        # Add gate definitions with text labels
        for gate_id, gate_info in gates_map.items():
            gate_type = gate_info.get("type", "approval")
            gate_label = f"HITL: {gate_id.upper()}"
            gate_text = gate_type.upper()  # Just "APPROVAL", "INPUT", "SELECTION"

            # Simple label for gates
            gate_html_label = f'"{gate_text}"'

            fill_color = self.gate_colors.get(gate_type, "#FFE0B2")
            stroke_color = self.gate_stroke_colors.get(gate_type, "#FF9800")

            lines.extend(
                [
                    f'  "{gate_label}" [',
                    "    shape=diamond,",
                    f"    label={gate_html_label},",
                    f'    fillcolor="{fill_color}",',
                    '    style="filled",',
                    f'    color="{stroke_color}", penwidth=2,',
                    "    width=0.9, height=0.9,",  # Bigger size
                    "    fontsize=9, fontcolor=white,",
                    "    fixedsize=true",
                    "  ];",
                ]
            )

        lines.append("")

        # Add edges (remove duplicates and self-loops, but keep labeled self-loops for loops)
        # Allow duplicates for enhanced repeat pattern edges to show parallel sequences
        enhanced_repeat_edges = node_info_map.get("_enhanced_repeat_edges", set())
        seen = {}
        for from_node, to_node, label in edges:
            # Allow self-loops only if they have a label (loop indicators)
            if from_node == to_node and not label:
                continue
            key = (from_node, to_node, label)
            
            # Check if this is an enhanced repeat edge (should allow duplicates)
            is_enhanced_repeat_edge = (from_node, to_node) in enhanced_repeat_edges
            
            # Use same color for all arrows (works in both light and dark mode)
            arrow_color = "#888"  # Medium gray - visible in both modes
            
            # Check if this is a dotted edge for handoffs or group chat returns
            is_dotted = label in ("dotted", "dashed")
            
            if is_enhanced_repeat_edge:
                # Allow up to num_instances duplicates for enhanced repeat edges
                # Count how many times we've seen this edge
                count = seen.get(key, 0)
                # Allow duplicates up to a reasonable limit (e.g., 5 for visualization)
                if count < 5:
                    seen[key] = count + 1
                    # Render the edge (same logic as regular edges)
                    if label and not is_dotted:
                        # Format label with variable extraction, multiline, and color coding
                        display_label, label_color = self._format_edge_label(label)
                        lines.append(
                            f'  "{from_node}" -> "{to_node}" ['
                            f'    label="{display_label}",'
                            f'    color="{arrow_color}",'
                            f'    fontcolor="{label_color}",'
                            "    fontsize=9,"
                            "    penwidth=2"
                            "  ];"
                        )
                    elif is_dotted:
                        # Dotted edge for handoffs
                        lines.append(
                            f'  "{from_node}" -> "{to_node}" ['
                            f'    color="{arrow_color}",'
                            '    style="dashed",'
                            "    penwidth=1.5"
                            "  ];"
                        )
                    else:
                        lines.append(
                            f'  "{from_node}" -> "{to_node}" ['
                            f'    color="{arrow_color}",'
                            "    penwidth=1.5"
                            "  ];"
                        )
                else:
                    continue  # Skip if we've already added enough
            else:
                # Regular edge - no duplicates allowed
                if key in seen:
                    continue
                seen[key] = 1
                
                # Render the edge
                if label and not is_dotted:
                    # Format label with variable extraction, multiline, and color coding
                    display_label, label_color = self._format_edge_label(label)
                    lines.append(
                        f'  "{from_node}" -> "{to_node}" ['
                        f'    label="{display_label}",'
                        f'    color="{arrow_color}",'
                        f'    fontcolor="{label_color}",'
                        "    fontsize=9,"
                        "    penwidth=2"
                        "  ];"
                    )
                elif is_dotted:
                    # Dotted edge for handoffs
                    lines.append(
                        f'  "{from_node}" -> "{to_node}" ['
                        f'    color="{arrow_color}",'
                        '    style="dashed",'
                        "    penwidth=1.5"
                        "  ];"
                    )
                else:
                    lines.append(
                        f'  "{from_node}" -> "{to_node}" ['
                        f'    color="{arrow_color}",'
                        "    penwidth=1.5"
                        "  ];"
                    )

        lines.append("}")
        return "\n".join(lines)

    def _process_step(
        self,
        step: Dict[str, Any],
        prev_node: str,
        next_node: Optional[str],
        edges: List,
        nodes: set,
        gates: List[Dict],
        gates_map: Dict,
        node_info_map: Dict = None,
        in_parallel_pattern: bool = False,
    ) -> tuple:
        """Process a step and return (current_node, output_edges)."""

        # Generic pattern-level condition handling for sequential/parallel/loop
        pattern_type = step.get("type")
        if pattern_type in ("sequential", "parallel", "loop") and step.get("condition"):
            condition_text = step.get("condition", "").upper()

            # Create a unique conditional diamond node
            if node_info_map is not None:
                idx = node_info_map.get("_cond_counter", 0) + 1
                node_info_map["_cond_counter"] = idx
                cond_node_label = f"COND: P{idx}"
            else:
                cond_node_label = "COND: P"

            nodes.add(cond_node_label)

            # Check if there's already a FALSE edge from a conditional node pointing to this pattern's COND: P{idx}
            # This happens when a conditional node's FALSE path should go to this pattern
            predicted_cond_label = None
            if node_info_map is not None:
                current_counter = node_info_map.get("_cond_counter", 0)
                predicted_idx = current_counter + 1
                predicted_cond_label = f"COND: P{predicted_idx}"
            
            # Check if there's already a FALSE edge to the predicted COND: P{idx} node
            has_existing_false_edge = False
            if predicted_cond_label:
                for i, (from_node, to_node, label) in enumerate(edges):
                    if label == "FALSE" and to_node == predicted_cond_label:
                        has_existing_false_edge = True
                        # Update the edge to point to the actual cond_node_label
                        edges[i] = (from_node, cond_node_label, label)
                        break
            
            # Connect prev_node to condition node with condition as label
            # BUT: If there's already a FALSE edge, we still need the edge from prev_node for the TRUE path
            # However, if prev_node is a conditionally executed node that was skipped (FALSE path),
            # we shouldn't create an edge from it. But we can't know that at generation time.
            # So we'll create the edge, but the FALSE edge will take precedence in the diagram.
            edges.append((prev_node, cond_node_label, condition_text))

            # Handle FALSE path based on on_false action
            on_false = step.get("on_false")
            if on_false == "stop":
                # If on_false is "stop", FALSE path goes directly to END
                edges.append((cond_node_label, "END", "FALSE (STOP)"))
            elif isinstance(on_false, (list, dict)) and on_false:
                # on_false is a step definition (if-else pattern)
                def get_first_node_from_on_false(on_false_config):
                    """Extract the first node ID from on_false step definition."""
                    if isinstance(on_false_config, dict):
                        if "node" in on_false_config:
                            return on_false_config["node"].split(":")[0]
                        elif "gate" in on_false_config:
                            return f"HITL: {on_false_config['gate'].upper()}"
                        elif on_false_config.get("type") == "sequential":
                            steps = on_false_config.get("steps", [])
                            if steps:
                                return get_first_node_from_on_false(steps[0])
                        elif on_false_config.get("type") == "parallel":
                            steps = on_false_config.get("steps", [])
                            if steps:
                                return get_first_node_from_on_false(steps[0])
                    elif isinstance(on_false_config, list) and len(on_false_config) > 0:
                        return get_first_node_from_on_false(on_false_config[0])
                    return None
                
                first_false_node = get_first_node_from_on_false(on_false)
                if first_false_node:
                    # Connect FALSE path to first node of on_false branch
                    edges.append((cond_node_label, first_false_node, "FALSE"))
                    # Process the on_false branch
                    if isinstance(on_false, list):
                        for false_step in on_false:
                            self._process_step(false_step, cond_node_label, next_node, edges, nodes, gates, gates_map, node_info_map, in_parallel_pattern)
                    elif isinstance(on_false, dict):
                        self._process_step(on_false, cond_node_label, next_node, edges, nodes, gates, gates_map, node_info_map, in_parallel_pattern)
                else:
                    # Empty or invalid on_false - treat as continue
                    next_real = next_node or "END"
                    edges.append((cond_node_label, next_real, "FALSE"))
            else:
                # Default: FALSE path bypasses the entire pattern to next_node (or END)
                next_real = next_node or "END"
                edges.append((cond_node_label, next_real, "FALSE"))

            # Helper to extract first node from a pattern step
            def get_first_node_from_step(step_dict):
                """Extract the first node ID from a step."""
                if isinstance(step_dict, dict):
                    if "node" in step_dict:
                        return step_dict["node"].split(":")[0]
                    elif "gate" in step_dict:
                        return f"HITL: {step_dict['gate'].upper()}"
                    elif step_dict.get("type") == "sequential":
                        steps = step_dict.get("steps", [])
                        if steps:
                            return get_first_node_from_step(steps[0])
                    elif step_dict.get("type") == "parallel":
                        steps = step_dict.get("steps", [])
                        if steps:
                            # For parallel, return first node from first branch
                            return get_first_node_from_step(steps[0])
                return None

            # Extract first node from pattern to add explicit TRUE edge
            pattern_without_condition = dict(step)
            pattern_without_condition.pop("condition", None)
            first_node = get_first_node_from_step(pattern_without_condition)
            
            # Add explicit TRUE edge from condition diamond to first node
            # For loops, include entry label (max_iterations) if available
            true_label = "TRUE"
            if pattern_type == "loop":
                termination = pattern_without_condition.get("termination", {})
                max_iterations = termination.get("max_iterations") or pattern_without_condition.get("max_iterations")
                if max_iterations:
                    if isinstance(max_iterations, str):
                        true_label = f"TRUE (MAX {max_iterations.upper()})"
                    else:
                        true_label = f"TRUE (MAX {max_iterations})"
            
            if first_node and first_node not in ["START", "END"]:
                edges.append((cond_node_label, first_node, true_label))

            # Process the pattern without the condition
            return self._process_step(
                pattern_without_condition,
                cond_node_label,
                next_node,
                edges,
                nodes,
                gates,
                gates_map,
                node_info_map,
            )

        if "gate" in step:
            # Handle gate
            gate_id = step["gate"]
            # Use gate_info from gates_map if available (may have flags set by pattern processor)
            # Check both original case and lowercase
            gate_info = gates_map.get(gate_id) or gates_map.get(gate_id.lower())
            if not gate_info:
                gate_info = next((g for g in gates if g.get("id") == gate_id), {})
            # Preserve _step_dict if it was set by pattern processor (CRITICAL for parallel patterns)
            existing_step_dict = None
            if gate_id in gates_map:
                existing_step_dict = gates_map[gate_id].get("_step_dict")
            elif gate_id.lower() in gates_map:
                existing_step_dict = gates_map[gate_id.lower()].get("_step_dict")
            # Always preserve _step_dict if it exists (don't overwrite with None)
            if existing_step_dict:
                gate_info["_step_dict"] = existing_step_dict
            # Also store the current step as _step_dict if not already set
            elif "_step_dict" not in gate_info:
                gate_info["_step_dict"] = step
            # Store in gates_map using both original and lowercase keys for consistency
            gates_map[gate_id] = gate_info
            gates_map[gate_id.lower()] = gate_info
            gate_type = gate_info.get("type", "approval")

            # Define gate_label
            gate_label = f"HITL: {gate_id.upper()}"

            # Check if this gate has a condition
            gate_condition = step.get("condition", "")
            on_false = step.get("on_false")
            if gate_condition:
                # Create a conditional diamond node before the gate
                cond_node_label = f"COND: {gate_id.upper()}"
                nodes.add(cond_node_label)

                # Connect prev_node to condition node with condition as label
                condition_text = gate_condition.upper()
                edges.append((prev_node, cond_node_label, condition_text))

                # Connect condition node to gate (TRUE path)
                edges.append((cond_node_label, gate_label, "TRUE"))

                # Handle FALSE path based on on_false action
                if on_false == "stop":
                    # If on_false is "stop", FALSE path goes directly to END
                    edges.append((cond_node_label, "END", "FALSE (STOP)"))
                elif isinstance(on_false, (list, dict)) and on_false:
                    # on_false is a step definition (if-else pattern)
                    def get_first_node_from_on_false(on_false_config):
                        """Extract the first node ID from on_false step definition."""
                        if isinstance(on_false_config, dict):
                            if "node" in on_false_config:
                                return on_false_config["node"].split(":")[0]
                            elif "gate" in on_false_config:
                                return f"HITL: {on_false_config['gate'].upper()}"
                            elif on_false_config.get("type") == "sequential":
                                steps = on_false_config.get("steps", [])
                                if steps:
                                    return get_first_node_from_on_false(steps[0])
                            elif on_false_config.get("type") == "parallel":
                                steps = on_false_config.get("steps", [])
                                if steps:
                                    return get_first_node_from_on_false(steps[0])
                        elif isinstance(on_false_config, list) and len(on_false_config) > 0:
                            return get_first_node_from_on_false(on_false_config[0])
                        return None
                    
                    first_false_node = get_first_node_from_on_false(on_false)
                    if first_false_node:
                        # Connect FALSE path to first node of on_false branch
                        edges.append((cond_node_label, first_false_node, "FALSE"))
                        # Process the on_false branch
                        if isinstance(on_false, list):
                            for false_step in on_false:
                                self._process_step(false_step, cond_node_label, next_node, edges, nodes, gates, gates_map, node_info_map, in_parallel_pattern)
                        elif isinstance(on_false, dict):
                            self._process_step(on_false, cond_node_label, next_node, edges, nodes, gates, gates_map, node_info_map, in_parallel_pattern)
                    else:
                        # Empty or invalid on_false - treat as continue
                        next_real = next_node or "END"
                        edges.append((cond_node_label, next_real, "FALSE"))
                else:
                    # Default: FALSE path continues to next node (skips this gate)
                    next_real = next_node or "END"
                    edges.append((cond_node_label, next_real, "FALSE"))
            else:
                # No condition - check if prev_node already has a labeled edge to this gate
                # This handles both HITL gates and conditional diamonds
                should_add_edge = True
                # Check if there's already a labeled edge from prev_node to this gate
                for edge in edges:
                    if edge[0] == prev_node and edge[1] == gate_label and edge[2]:
                        # Previous node (gate or conditional diamond) already has a labeled edge to this gate
                        should_add_edge = False
                        break
                
                if should_add_edge:
                    edges.append((prev_node, gate_label, None))

            # Find what comes after this gate
            next_real = next_node or "END"

            # Check if next step is a pattern (set by sequential pattern processing)
            next_is_pattern = gate_info.get("_next_is_pattern", False)
            # Also check if next step is a parallel pattern specifically (we need to handle it differently)
            next_pattern_type = None
            if next_is_pattern and gate_info.get("_next_step"):
                next_step = gate_info.get("_next_step")
                if isinstance(next_step, dict) and next_step.get("type") == "parallel":
                    next_pattern_type = "parallel"
            
            # Check if we should suppress action paths (next node/pattern has condition referencing gate context)
            # First check if flag was set by pattern processor
            gate_info_from_map = gates_map.get(gate_id)
            suppress_action_paths = False
            
            if gate_info_from_map:
                suppress_action_paths = gate_info_from_map.get("_suppress_action_paths", False)
                # Update local gate_info with flag if found
                if suppress_action_paths:
                    gate_info["_suppress_action_paths"] = True
                # Also check _next_step from gates_map for fallback
                next_step_to_check = gate_info_from_map.get("_next_step")
            else:
                suppress_action_paths = gate_info.get("_suppress_action_paths", False)
                next_step_to_check = gate_info.get("_next_step")
            
            # Fallback: If flag not set, check next step directly (stored by pattern processor)
            if not suppress_action_paths and next_step_to_check:
                next_condition = None
                
                if "node" in next_step_to_check:
                    next_condition = next_step_to_check.get("condition", "")
                elif next_step_to_check.get("type") in ("sequential", "parallel", "loop"):
                    next_condition = next_step_to_check.get("condition", "")
                
                if next_condition:
                    if self._condition_references_gate_context(next_condition, gate_id, gate_type):
                        suppress_action_paths = True
                        gate_info["_suppress_action_paths"] = True
                        gates_map[gate_id] = gate_info
            
            # If suppressing action paths, don't add any edges from the gate
            # The conditional node (created when processing the next node) will handle routing
            # The edge from gate to conditional node will be created when the node processes its condition
            if suppress_action_paths:
                gate_info["_has_paths"] = True
                gates_map[gate_id] = gate_info  # Ensure flag is preserved
                # Don't add any edge here - let the conditional node handle it
                return gate_label, None

            # Add gate paths - dynamically handle ALL on_* keys
            paths_added = False
            continue_action_labels = []  # Store action labels for continue actions when next is pattern

            # Process all on_* keys dynamically (like runner_compiler does)
            for key, value in step.items():
                if key.startswith("on_") and key != "on_condition":
                    # Extract action name from key (e.g., "on_approve" -> "approve")
                    action_name = key[3:]  # Remove "on_" prefix
                    
                    if value == "continue":
                        if next_is_pattern:
                            # Next step is a pattern - store action label for pattern processing
                            # For parallel patterns, don't create edges here - parallel processor will handle it
                            if next_pattern_type == "parallel":
                                continue_action_labels.append(action_name.upper())
                                paths_added = True
                            else:
                                # Other patterns (sequential, loop) - create edge normally
                                continue_action_labels.append(action_name.upper())
                                paths_added = True
                        else:
                            # Continue to next node (normal case)
                            edges.append((gate_label, next_real, action_name))
                            paths_added = True
                    elif value == "stop":
                        # Stop at END
                        edges.append((gate_label, "END", action_name))
                        paths_added = True
                    elif value == "retry_node":
                        # Retry to a specific target node
                        retry_target = step.get("retry_target")
                        if retry_target:
                            nodes.add(retry_target)
                            edges.append((gate_label, retry_target, action_name))
                            paths_added = True
                    elif value == "skip_to_node":
                        # Skip to a specific target node
                        skip_target = step.get("skip_to")
                        if skip_target:
                            nodes.add(skip_target)
                            edges.append((gate_label, skip_target, action_name))
                            paths_added = True
                    # Handle other custom actions if needed
                    elif isinstance(value, str) and value:
                        # Any other string value is treated as a label
                        if next_is_pattern:
                            continue_action_labels.append(action_name.upper())
                            paths_added = True
                        else:
                            edges.append((gate_label, next_real, action_name))
                            paths_added = True

            # Store continue action labels for pattern processing
            if continue_action_labels:
                gate_info["_continue_action_labels"] = continue_action_labels
            # Also store the step dict for parallel pattern processor to access all actions
            gate_info["_step_dict"] = step
            # Mark that this gate has paths so next node doesn't add duplicate edge
            gate_info["_has_paths"] = paths_added
            gates_map[gate_id] = gate_info  # Ensure all info is preserved

            # Return the gate label as current node
            return gate_label, None

        elif "pipeline" in step:
            # Handle pipeline step
            pipeline_id = step["pipeline"]
            nodes.add(pipeline_id)
            
            # Mark this as a pipeline node in node_info_map
            if node_info_map is not None:
                if pipeline_id not in node_info_map:
                    node_info_map[pipeline_id] = {}
                node_info_map[pipeline_id]["is_pipeline"] = True
            
            # Check if this pipeline has a condition
            pipeline_condition = step.get("condition", "")
            
            if pipeline_condition:
                # Create a conditional diamond node before the pipeline
                cond_node_label = f"COND: {pipeline_id.upper()}"
                nodes.add(cond_node_label)
                
                # Connect prev_node to condition node with condition as label
                condition_text = pipeline_condition.upper()
                edges.append((prev_node, cond_node_label, condition_text))
                
                # Connect condition node to pipeline (TRUE path)
                edges.append((cond_node_label, pipeline_id, "TRUE"))
                
                # Store what comes after the pipeline for FALSE path
                next_real = next_node or "END"
                
                # Connect condition node to what comes after pipeline (FALSE path)
                edges.append((cond_node_label, next_real, "FALSE"))
                
                return pipeline_id, None
            else:
                # No condition - normal handling
                # Check if prev_node is a gate that already has labeled paths
                should_add_edge = True
                if prev_node.startswith("HITL:"):
                    # Check if this gate has labeled paths to this pipeline_id
                    for edge in edges:
                        if edge[0] == prev_node and edge[1] == pipeline_id and edge[2]:
                            should_add_edge = False
                            break
                
                if should_add_edge:
                    edges.append((prev_node, pipeline_id, None))
                
                # Connect pipeline to next node
                if next_node:
                    edges.append((pipeline_id, next_node, None))
                
                return pipeline_id, None
        
        elif "node" in step:
            # Handle node
            agent_id = step["node"].split(":")[0]
            nodes.add(agent_id)

            # Check if this node has a condition
            node_condition = step.get("condition", "")
            on_false = step.get("on_false")
            
            # Check if we have a stored prediction for this conditional node's FALSE path
            # This is set when the sequential loop determines next_target for a conditional node
            # followed by a pattern with condition
            stored_prediction = None
            if node_info_map and "_predicted_pattern_conds" in node_info_map:
                stored_prediction = node_info_map["_predicted_pattern_conds"].get(agent_id)
                if not stored_prediction and step.get("node"):
                    stored_prediction = node_info_map["_predicted_pattern_conds"].get(step.get("node"))

            if node_condition:
                # Create a conditional diamond node before the node
                cond_node_label = f"COND: {agent_id.upper()}"
                nodes.add(cond_node_label)

                # Always connect prev_node to condition node with condition as label
                # Even if prev is a gate with labeled paths, this edge is needed for correct flow rendering
                condition_text = node_condition.upper()
                edges.append((prev_node, cond_node_label, condition_text))

                # Connect condition node to agent (TRUE path)
                edges.append((cond_node_label, agent_id, "TRUE"))

                # Handle FALSE path based on on_false action
                if on_false == "stop":
                    # If on_false is "stop", FALSE path goes directly to END
                    edges.append((cond_node_label, "END", "FALSE (STOP)"))
                elif isinstance(on_false, (list, dict)) and on_false:
                    # on_false is a step definition (if-else pattern)
                    # Extract first node from on_false branch
                    def get_first_node_from_on_false(on_false_config):
                        """Extract the first node ID from on_false step definition."""
                        if isinstance(on_false_config, dict):
                            if "node" in on_false_config:
                                return on_false_config["node"].split(":")[0]
                            elif "gate" in on_false_config:
                                return f"HITL: {on_false_config['gate'].upper()}"
                            elif on_false_config.get("type") == "sequential":
                                steps = on_false_config.get("steps", [])
                                if steps:
                                    return get_first_node_from_on_false(steps[0])
                            elif on_false_config.get("type") == "parallel":
                                steps = on_false_config.get("steps", [])
                                if steps:
                                    return get_first_node_from_on_false(steps[0])
                        elif isinstance(on_false_config, list) and len(on_false_config) > 0:
                            return get_first_node_from_on_false(on_false_config[0])
                        return None
                    
                    first_false_node = get_first_node_from_on_false(on_false)
                    if first_false_node:
                        # Connect FALSE path to first node of on_false branch
                        edges.append((cond_node_label, first_false_node, "FALSE"))
                        # Process the on_false branch
                        if isinstance(on_false, list):
                            for false_step in on_false:
                                self._process_step(false_step, cond_node_label, next_node, edges, nodes, gates, gates_map, node_info_map, in_parallel_pattern)
                        elif isinstance(on_false, dict):
                            self._process_step(on_false, cond_node_label, next_node, edges, nodes, gates, gates_map, node_info_map, in_parallel_pattern)
                    else:
                        # Empty or invalid on_false - treat as continue
                        next_real = next_node or "END"
                        edges.append((cond_node_label, next_real, "FALSE"))
                else:
                    # Default: FALSE path continues to next node (skips this node)
                    # Check if next_node is a predicted COND: P{idx} label (pattern with condition)
                    # If so, use it directly
                    # Also check if we stored a prediction for this conditional node
                    false_target = None
                    
                    if next_node and next_node.startswith("COND: P"):
                        # next_node is already the predicted pattern condition node
                        false_target = next_node
                    elif stored_prediction:
                        # Use the stored prediction we found earlier
                        false_target = stored_prediction
                    elif node_info_map and "_predicted_pattern_conds" in node_info_map:
                        # Fallback: Check if we have a stored prediction for this conditional node
                        # Try both agent_id and the full node string
                        predicted_cond = node_info_map["_predicted_pattern_conds"].get(agent_id)
                        if not predicted_cond and step.get("node"):
                            predicted_cond = node_info_map["_predicted_pattern_conds"].get(step.get("node"))
                        if predicted_cond:
                            false_target = predicted_cond
                    
                    if false_target:
                        edges.append((cond_node_label, false_target, "FALSE"))
                    elif next_node and next_node != "END":
                        # Fallback: use next_node (might be wrong, but pattern processing will fix it)
                        edges.append((cond_node_label, next_node, "FALSE"))
                    else:
                        edges.append((cond_node_label, "END", "FALSE"))

                return agent_id, None
            else:
                # No condition - normal handling
                # CRITICAL FIX: If prev_node is None, it means we're in a parallel pattern branch
                # that should not have a previous node connection (to avoid backwards edges).
                # In this case, don't create any edges from prev_node.
                if prev_node is None:
                    # No previous node - branch starts independently
                    # Don't create any edges from prev_node
                    return agent_id, None
                
                # CRITICAL FIX: If prev_node is the same as agent_id, it means we're processing
                # a node that was returned from a parallel pattern. In this case, we should NOT
                # create an edge from prev_node to agent_id (which would be a self-loop or backwards edge).
                # Instead, the parallel pattern already created edges from its branches to this node.
                # We should skip creating the edge from prev_node to agent_id.
                actual_prev_node = prev_node
                
                # Check if this node was the target of a parallel pattern (stored in node_info_map)
                if node_info_map is not None and agent_id in node_info_map:
                    parallel_prev = node_info_map[agent_id].get("_parallel_prev_node")
                    if parallel_prev:
                        # This node was the target of a parallel pattern
                        # Don't create edge from prev_node (which is this node itself) to agent_id
                        # The parallel pattern already created edges from its branches to this node
                        should_add_edge = False
                    else:
                        # Normal case - not from parallel pattern
                        should_add_edge = True
                else:
                    # Normal case - no special handling needed
                    should_add_edge = True
                
                # Additional check: if prev_node == agent_id, definitely skip (self-loop prevention)
                if prev_node == agent_id:
                    should_add_edge = False
                
                if should_add_edge:
                    # Check if prev_node is a gate that already has labeled paths to this node
                    if prev_node.startswith("HITL:"):
                        # If we're in a parallel pattern, the parallel processor will handle
                        # creating labeled edges from gate to branches - don't add unlabeled edge
                        if in_parallel_pattern:
                            should_add_edge = False
                        else:
                            # Check if this gate has labeled paths to this agent_id
                            # (If gate has labeled paths, don't add unlabeled edge)
                            for edge in edges:
                                if edge[0] == prev_node and edge[1] == agent_id and edge[2]:
                                    # Gate already has a labeled edge to this node, skip unlabeled edge
                                    should_add_edge = False
                                    break
                            
                            # Check for suppressed action paths (conditional routing)
                            if should_add_edge:
                                gate_label_upper = prev_node[5:]  # Remove "HITL: " prefix
                                gate_id_lower = gate_label_upper.lower()  # Lowercase for lookup
                                gate_info = gates_map.get(gate_id_lower)
                                if gate_info and gate_info.get("_suppress_action_paths", False):
                                    # Gate has suppressed action paths (conditional routing)
                                    # Don't add unlabeled edge - conditional node will handle routing
                                    should_add_edge = False
                    else:
                        # Check if there's already an edge from prev_node to this node
                        # This handles cases where loop exit edges are already created
                        for edge in edges:
                            if edge[0] == prev_node and edge[1] == agent_id:
                                # Edge already exists (could be labeled or unlabeled)
                                should_add_edge = False
                                break
                    
                    if should_add_edge:
                        edges.append((prev_node, agent_id, None))

                return agent_id, None

        elif step.get("type") == "parallel":
            # Check if this is a repeat pattern
            if "repeat" in step:
                # Get parent instance index from context if available
                parent_instance_idx = getattr(self, '_current_parent_instance_idx', None)
                return self._process_repeat_pattern(
                    step, prev_node, next_node, edges, nodes, gates, gates_map, node_info_map, parent_instance_idx
                )
            
            # Handle standard parallel - recursively process all branches, connect all to next
            steps = step.get("steps", [])
            branch_terminal_nodes = []
            branch_first_nodes = []  # Track first nodes of each branch for gate connections
            
            # Check if prev_node is a gate with action labels for parallel pattern
            gate_action_labels = None
            gate_step_info = None  # Store the step dict if we can find it
            if prev_node.startswith("HITL:"):
                # Extract gate_id from prev_node (format: "HITL: GATE_ID")
                gate_label_upper = prev_node[5:]  # Remove "HITL: " prefix
                gate_id_lower = gate_label_upper.lower()  # Lowercase for lookup
                # Find gate_info by matching gate_id in gates_map or gates list
                # Try lowercase first (most common)
                gate_info = gates_map.get(gate_id_lower)
                # If not found, try original case
                if not gate_info:
                    gate_info = gates_map.get(gate_label_upper.lower())
                # If still not found, try from gates list
                if not gate_info:
                    gate_info = next(
                        (g for g in gates if g.get("id", "").lower() == gate_id_lower), {}
                    )
                    # If found in gates list, check if gates_map has _step_dict for this gate
                    # and preserve it
                    if gate_info:
                        # Check if _step_dict exists in gates_map for this gate (any case variation)
                        for key in gates_map.keys():
                            if key.lower() == gate_id_lower:
                                existing_step_dict = gates_map[key].get("_step_dict")
                                if existing_step_dict:
                                    gate_info["_step_dict"] = existing_step_dict
                                    break
                        gates_map[gate_id_lower] = gate_info
                if gate_info:
                    # Get continue action labels (actions that continue to next step)
                    gate_action_labels = gate_info.get("_continue_action_labels")
                    # If no continue action labels, try to extract from step dict if available
                    if not gate_action_labels:
                        step_dict = gate_info.get("_step_dict")
                        if step_dict:
                            # Extract all on_* actions with value "continue"
                            continue_labels = []
                            for key, value in step_dict.items():
                                if key.startswith("on_") and key != "on_condition" and value == "continue":
                                    action_name = key[3:]  # Remove "on_" prefix
                                    continue_labels.append(action_name.upper())
                            if continue_labels:
                                gate_action_labels = continue_labels
                                gate_info["_continue_action_labels"] = gate_action_labels
                                # Update gates_map with both keys
                                gates_map[gate_id_lower] = gate_info
                                gates_map[gate_label_upper.lower()] = gate_info
                        # If still no labels, try to get from gates list as last resort
                        # This handles cases where step_dict wasn't stored
                        if not gate_action_labels:
                            # Try to find the gate step from the sequential processor's context
                            # This is a fallback - normally _step_dict should be available
                            pass
                    # Also ensure gate_info is in gates_map for later use
                    if gate_id_lower not in gates_map:
                        gates_map[gate_id_lower] = gate_info
                    if gate_label_upper.lower() not in gates_map:
                        gates_map[gate_label_upper.lower()] = gate_info
            
            # CRITICAL FIX: If prev_node == next_node, it means prev_node is actually the node
            # that comes AFTER this parallel pattern (returned from a previous parallel pattern).
            # This indicates we have consecutive parallel patterns. We need to create a convergence
            # point (small dot) that all branches from the first parallel feed into, and then all
            # branches of this parallel start from that convergence point.
            actual_prev_node = prev_node
            convergence_point = None
            skip_branch_connections = False
            if prev_node == next_node and prev_node not in ["START", "END"]:
                # prev_node is the same as next_node - this is a backwards reference
                # This happens when a previous parallel pattern returned next_node as its current node
                # We need to find the actual previous nodes by checking existing edges
                # Look for nodes that have edges TO prev_node (these are the actual inputs)
                incoming_nodes = [e[0] for e in edges if e[1] == prev_node and e[0] != prev_node]
                if incoming_nodes:
                    # Multiple nodes feed into prev_node (from a previous parallel pattern)
                    # Create a convergence point node to show all branches converging
                    convergence_point = f"CONVERGE: {prev_node}"
                    nodes.add(convergence_point)
                    
                    # Connect all incoming nodes to the convergence point
                    for incoming in incoming_nodes:
                        # Remove the direct edge from incoming to prev_node (we'll go through convergence point)
                        edges[:] = [e for e in edges if not (e[0] == incoming and e[1] == prev_node)]
                        # Add edge from incoming to convergence point
                        if not any(e[0] == incoming and e[1] == convergence_point for e in edges):
                            edges.append((incoming, convergence_point, None))
                    
                    # Use convergence point as the source for this parallel's branches
                    actual_prev_node = convergence_point
                else:
                    # No incoming edges found - this might be the first step or edges not created yet
                    # In this case, don't create edges from prev_node to branches
                    # The branches will get their inputs from the previous parallel pattern's outputs
                    skip_branch_connections = True
                    actual_prev_node = None
            
            for parallel_step in steps:
                # Determine the first node/gate in this branch for gate connection
                branch_first = None
                if "node" in parallel_step:
                    branch_first = parallel_step["node"].split(":")[0]
                    nodes.add(branch_first)
                elif "gate" in parallel_step:
                    branch_gate_id = parallel_step["gate"]
                    branch_gate_info = next(
                        (g for g in gates if g.get("id") == branch_gate_id), {}
                    )
                    branch_first = f"HITL: {branch_gate_id.upper()}"
                    if branch_gate_id not in gates_map:
                        gates_map[branch_gate_id] = branch_gate_info
                
                if branch_first:
                    branch_first_nodes.append(branch_first)
                
                # Recursively process each branch step (handles nested patterns)
                # Pass a flag to indicate we're in a parallel pattern so node processor
                # knows not to add edges from gate (parallel processor will handle it)
                # Use actual_prev_node instead of prev_node to avoid backwards edges
                # If skip_branch_connections is True, pass None as prev_node to prevent backwards edges
                branch_prev = None if skip_branch_connections else (actual_prev_node if actual_prev_node else prev_node)
                branch_terminal, _ = self._process_step(
                    parallel_step,
                    branch_prev,
                    next_node,
                    edges,
                    nodes,
                    gates,
                    gates_map,
                    node_info_map,
                    in_parallel_pattern=True,  # Flag to prevent duplicate edges
                )
                
                # Track terminal nodes for each branch (skip None returns from patterns that handle their own flow)
                if branch_terminal and branch_terminal != "START" and branch_terminal != "END":
                    branch_terminal_nodes.append(branch_terminal)
            
            # If prev_node (or actual_prev_node) is a gate, handle connections to branches
            # But skip if we detected a backwards reference (prev_node == next_node)
            if not skip_branch_connections:
                gate_prev_node = actual_prev_node if actual_prev_node else prev_node
                if gate_prev_node and gate_prev_node.startswith("HITL:") and branch_first_nodes:
                    # Extract gate_id to check gate info
                    gate_label_upper = gate_prev_node[5:]  # Remove "HITL: " prefix
                    gate_id_lower = gate_label_upper.lower()
                    gate_info_for_suppress = gates_map.get(gate_id_lower)
                    
                    # Check if gate has suppressed action paths (next step has condition)
                    suppress_action_paths = False
                    if gate_info_for_suppress:
                        suppress_action_paths = gate_info_for_suppress.get("_suppress_action_paths", False)
                    
                    if suppress_action_paths:
                        # Gate action paths are suppressed - conditional node will handle routing
                        # Remove any edges from gate to branch first nodes (both labeled and unlabeled)
                        edges[:] = [e for e in edges if not (
                            e[0] == gate_prev_node and 
                            e[1] in branch_first_nodes
                        )]
                        # Don't add any edges - conditional node handles it
                    else:
                        # Gate action paths are NOT suppressed - use labeled action edges
                        # Remove any existing unlabeled edges from gate to branch first nodes
                        edges[:] = [e for e in edges if not (
                            e[0] == gate_prev_node and 
                            e[1] in branch_first_nodes and 
                            e[2] is None
                        )]
                        
                        # If gate has action labels, add labeled edges from gate to each branch's first node
                        if gate_action_labels:
                            for action_label in gate_action_labels:
                                for branch_first in branch_first_nodes:
                                    # Only add if not already present
                                    if not any(e[0] == gate_prev_node and e[1] == branch_first and e[2] == action_label for e in edges):
                                        edges.append((gate_prev_node, branch_first, action_label))
                        else:
                            # No action labels found - fallback to unlabeled edges for connectivity
                            # This ensures the diagram is complete even if extraction failed
                            # (This matches the old behavior where unlabeled edges were created)
                            for branch_first in branch_first_nodes:
                                if not any(e[0] == gate_prev_node and e[1] == branch_first for e in edges):
                                    edges.append((gate_prev_node, branch_first, None))
                elif actual_prev_node and actual_prev_node != prev_node and branch_first_nodes:
                    # actual_prev_node is different from prev_node (we corrected it)
                    # Create edges from actual_prev_node to branch first nodes
                    for branch_first in branch_first_nodes:
                        if not any(e[0] == actual_prev_node and e[1] == branch_first for e in edges):
                            edges.append((actual_prev_node, branch_first, None))
                elif actual_prev_node and not actual_prev_node.startswith("HITL:") and branch_first_nodes:
                    # actual_prev_node is a regular node (not a gate) - create edges to branches
                    for branch_first in branch_first_nodes:
                        if not any(e[0] == actual_prev_node and e[1] == branch_first for e in edges):
                            edges.append((actual_prev_node, branch_first, None))
            
            # Connect all branch terminals to next_node (if not already connected)
            # This handles the case where branches end at different nodes/gates
            if next_node and branch_terminal_nodes:
                next_real = next_node if next_node != "START" else "END"
                for terminal in branch_terminal_nodes:
                    # Skip if branch already ends at END
                    if any(e[0] == terminal and e[1] == "END" for e in edges):
                        continue
                    # Skip if terminal is a gate that already added labeled paths
                    # (gates with labeled paths already have edges, don't add unlabeled edge)
                    if terminal.startswith("HITL:"):
                        skip_terminal = False
                        for gate_id, gate_info in gates_map.items():
                            gate_label = f"HITL: {gate_id.upper()}"
                            if gate_label == terminal:
                                # If gate has labeled paths, skip adding unlabeled edge
                                if gate_info.get("_has_paths"):
                                    skip_terminal = True
                                break
                        if skip_terminal:
                            continue
                    # Only add edge if terminal doesn't already have an edge to next
                    if not any(e[0] == terminal and e[1] == next_real for e in edges):
                        edges.append((terminal, next_real, None))
            
            # Return next_node so the flow continues to what's after parallel
            # BUT: Store the parallel pattern's prev_node in node_info_map so sequential pattern
            # can use it as the correct prev_node for the next step (not next_node itself)
            if node_info_map is not None and next_node:
                if next_node not in node_info_map:
                    node_info_map[next_node] = {}
                # Store the actual previous node (before parallel) for correct edge creation
                node_info_map[next_node]["_parallel_prev_node"] = prev_node
            
            return next_node if next_node else prev_node, None

        elif step.get("type") == "sequential":
            # Nested sequential
            steps = step.get("steps", [])
            current = prev_node
            for i, sub_step in enumerate(steps):
                # Determine the next target within this nested sequence for correct FALSE bypass
                seq_next_is_pattern = False
                if i < len(steps) - 1:
                    nxt = steps[i + 1]
                    if "node" in nxt:
                        seq_next_target = nxt["node"].split(":")[0]
                        nodes.add(seq_next_target)
                    elif "gate" in nxt:
                        gate_id = nxt["gate"]
                        gate_info = next((g for g in gates if g.get("id") == gate_id), {})
                        seq_next_target = f"HITL: {gate_id.upper()}"
                        if gate_id not in gates_map:
                            gates_map[gate_id] = gate_info
                    else:
                        # Next is a pattern (sequential/parallel/loop)
                        seq_next_is_pattern = True
                        # Check if current step is a conditional node and next step is a pattern with condition
                        # If so, FALSE path should go to the pattern's COND: P{idx} node
                        current_step_is_conditional = sub_step.get("node") and sub_step.get("condition")
                        next_step_condition = nxt.get("condition", "")
                        next_step_has_condition = bool(next_step_condition and next_step_condition.strip())
                        
                        if current_step_is_conditional and next_step_has_condition:
                            # Predict the COND: P{idx} label for the pattern
                            if node_info_map is not None:
                                current_counter = node_info_map.get("_cond_counter", 0)
                                predicted_idx = current_counter + 1
                                seq_next_target = f"COND: P{predicted_idx}"
                                
                                # Store this prediction so the conditional node can use it
                                if "_predicted_pattern_conds" not in node_info_map:
                                    node_info_map["_predicted_pattern_conds"] = {}
                                # Store using the node ID
                                node_id = sub_step.get("node")
                                if node_id:
                                    node_id_base = node_id.split(":")[0]
                                    node_info_map["_predicted_pattern_conds"][node_id_base] = seq_next_target
                            else:
                                seq_next_target = "COND: P"
                        else:
                            # Find what comes after the pattern
                            if i + 2 < len(steps):
                                after_pattern = steps[i + 2]
                                if "node" in after_pattern:
                                    seq_next_target = after_pattern["node"].split(":")[0]
                                    nodes.add(seq_next_target)
                                elif "gate" in after_pattern:
                                    gate_id = after_pattern["gate"]
                                    gate_info = next((g for g in gates if g.get("id") == gate_id), {})
                                    seq_next_target = f"HITL: {gate_id.upper()}"
                                    if gate_id not in gates_map:
                                        gates_map[gate_id] = gate_info
                                else:
                                    seq_next_target = next_node
                            else:
                                seq_next_target = next_node
                else:
                    # Last sub-step uses outer next_node
                    seq_next_target = next_node

                # Store next_is_pattern info for gate processing
                # Also check if next step has condition that references gate decision
                if "gate" in sub_step:
                    gate_id = sub_step["gate"]
                    # Ensure gate_info is in gates_map before setting flags
                    gate_info = gates_map.get(gate_id) or next(
                        (g for g in gates if g.get("id") == gate_id), {}
                    )
                    if gate_id not in gates_map:
                        gates_map[gate_id] = gate_info
                    gate_info["_next_is_pattern"] = seq_next_is_pattern
                    if seq_next_is_pattern and i + 1 < len(steps):
                        gate_info["_next_pattern_step"] = steps[i + 1]
                    
                    # Store next step info for gate processing (so gate can check condition directly)
                    # Check both inner pattern steps and outer pattern's next step
                    next_step_to_check = None
                    if i + 1 < len(steps):
                        # Next step is within this nested sequential pattern
                        gate_info["_next_step"] = steps[i + 1]
                        next_step_to_check = steps[i + 1]
                    elif next_node and next_node != "END":
                        # Gate is last step in nested pattern - check outer pattern's next step
                        # We need to get the step dict from the outer pattern
                        # For now, store a marker that we need to check outer pattern
                        gate_info["_check_outer_next"] = True
                    
                    # Check if next step (node or pattern) has condition referencing this gate's context
                    if next_step_to_check:
                        next_condition = None
                        
                        # Check if next step is a node with condition
                        if "node" in next_step_to_check:
                            next_condition = next_step_to_check.get("condition", "")
                        # Check if next step is a pattern (sequential/parallel/loop) with condition
                        elif next_step_to_check.get("type") in ("sequential", "parallel", "loop"):
                            next_condition = next_step_to_check.get("condition", "")
                        
                        if next_condition:
                            # Get gate type from gate_info, or find it in gates list if not set
                            gate_type = gate_info.get("type")
                            if not gate_type:
                                # Try to find gate in gates list to get type
                                gate_from_list = next((g for g in gates if g.get("id") == gate_id), None)
                                if gate_from_list:
                                    gate_type = gate_from_list.get("type", "approval")
                                    gate_info["type"] = gate_type
                                else:
                                    gate_type = "approval"
                            
                            # Check if condition references gate context (works for all gate types now)
                            if self._condition_references_gate_context(
                                next_condition, gate_id, gate_type
                            ):
                                # Next step conditionally routes based on gate context (decision/selected_option)
                                # Suppress gate action paths - conditional node will handle routing
                                gate_info["_suppress_action_paths"] = True
                                # Update gates_map to ensure flag is preserved
                                gates_map[gate_id] = gate_info
                                gates_map[gate_id.lower()] = gate_info

                current, _ = self._process_step(
                    sub_step,
                    current,
                    seq_next_target,
                    edges,
                    nodes,
                    gates,
                    gates_map,
                    node_info_map,
                )
            return current, None

        elif step.get("type") == "loop":
            # Handle loop - body repeats until max_iterations or termination condition
            body = step.get("body", {})
            
            # Check for iterate_over mode (new list iteration pattern)
            iterate_over = step.get("iterate_over")
            loop_item_key = step.get("loop_item_key", "loop_item")
            skip_condition = step.get("skip_condition")
            
            # Extract termination config (new format) or backward-compatible max_iterations
            termination = step.get("termination", {})
            max_iterations = termination.get("max_iterations") or step.get("max_iterations")
            termination_condition = termination.get("condition")
            
            # If iterate_over is used, max_iterations is optional (safety limit only)
            # The actual termination is based on list exhaustion or termination_condition
            
            # Helper to extract first node from a body step
            def get_first_node(body_step):
                """Extract the first node ID from a body step."""
                if isinstance(body_step, dict):
                    if "node" in body_step:
                        return body_step["node"].split(":")[0]
                    elif "gate" in body_step:
                        return f"HITL: {body_step['gate'].upper()}"
                    elif body_step.get("type") == "sequential":
                        steps = body_step.get("steps", [])
                        if steps:
                            return get_first_node(steps[0])
                    elif body_step.get("type") == "parallel":
                        steps = body_step.get("steps", [])
                        if steps:
                            # For parallel, return first node from first branch
                            return get_first_node(steps[0])
                return None
            
            # Helper to check if body starts with a parallel pattern
            def body_starts_with_parallel(body_step):
                """Check if the body starts with a parallel pattern."""
                if isinstance(body_step, dict):
                    if body_step.get("type") == "parallel":
                        return True
                    elif body_step.get("type") == "sequential":
                        steps = body_step.get("steps", [])
                        if steps:
                            return body_starts_with_parallel(steps[0])
                return False

            # Get first node in loop body for loop-back edge
            first_node = get_first_node(body)
            
            # Check if body starts with a parallel pattern - if so, we need a convergence point
            starts_with_parallel = body_starts_with_parallel(body)
            loop_convergence_point = None
            if starts_with_parallel and first_node:
                # Create a convergence point before the parallel pattern
                loop_convergence_point = f"CONVERGE: LOOP-{first_node}"
                nodes.add(loop_convergence_point)
            
            # Build edge label that includes iterate_over and max_iterations info
            # This goes on the edge entering the loop (before the termination condition check)
            entry_label_parts = []
            if iterate_over:
                # Show what we're iterating over - format as ITERATE (LIST_NAME)
                iterate_path_parts = iterate_over.split('.')
                iterate_display = iterate_path_parts[-1].upper() if iterate_path_parts else iterate_over.upper()
                entry_label_parts.append(f"ITERATE ({iterate_display})")
            
            if max_iterations:
                # Show max iterations as safety limit
                if isinstance(max_iterations, str):
                    entry_label_parts.append(f"MAX {max_iterations.upper()}")
                else:
                    entry_label_parts.append(f"MAX {max_iterations}")
            
            entry_label = " | ".join(entry_label_parts) if entry_label_parts else None
            
            # Create a conditional diamond node for the loop termination condition
            # This represents the check: should we continue looping or exit?
            if termination_condition:
                # Create a unique conditional diamond node for loop condition
                if node_info_map is not None:
                    idx = node_info_map.get("_cond_counter", 0) + 1
                    node_info_map["_cond_counter"] = idx
                    loop_cond_node = f"COND: L{idx}"
                else:
                    loop_cond_node = "COND: L"
                
                nodes.add(loop_cond_node)
                
                # Build loop condition label with max_iterations and termination condition
                # This goes on the incoming edge TO the diamond
                loop_condition_label_parts = []
                
                # If iterate_over is used, this is a list-based iteration
                # Show the termination condition (when to exit) and optionally MAX as safety limit
                if iterate_over:
                    # Format iterate_over path for display (simplified)
                    # Extract just the last part of the path for brevity
                    iterate_path_parts = iterate_over.split('.')
                    iterate_display = iterate_path_parts[-1].upper() if iterate_path_parts else iterate_over.upper()
                    
                    # Add termination condition (this is the main exit condition)
                    if termination_condition:
                        # Format termination condition for display
                        # No truncation needed - multiline formatting will handle long conditions
                        term_cond_display = termination_condition.upper().strip()
                        # Remove any trailing spaces or extra parentheses
                        term_cond_display = re.sub(r'\s+\)\s*$', ')', term_cond_display)
                        term_cond_display = re.sub(r'\)\s+\)', ')', term_cond_display)
                        loop_condition_label_parts.append(term_cond_display)
                    
                    # Add max_iterations as safety limit if present
                    if max_iterations:
                        if isinstance(max_iterations, str):
                            loop_condition_label_parts.append(f"MAX {max_iterations.upper()}")
                        else:
                            loop_condition_label_parts.append(f"MAX {max_iterations}")
                else:
                    # Traditional numeric iteration
                    # Add max_iterations if present
                    if max_iterations:
                        if isinstance(max_iterations, str):
                            loop_condition_label_parts.append(f"MAX {max_iterations.upper()}")
                        else:
                            loop_condition_label_parts.append(f"MAX {max_iterations}")
                    
                    # Add termination condition
                    if termination_condition:
                        # Format termination condition for display
                        # No truncation needed - multiline formatting will handle long conditions
                        term_cond_display = termination_condition.upper().strip()
                        # Remove any trailing spaces or extra parentheses
                        term_cond_display = re.sub(r'\s+\)\s*$', ')', term_cond_display)
                        term_cond_display = re.sub(r'\)\s+\)', ')', term_cond_display)
                        loop_condition_label_parts.append(term_cond_display)
                
                loop_condition_label = " OR ".join(loop_condition_label_parts) if len(loop_condition_label_parts) > 1 else (loop_condition_label_parts[0] if loop_condition_label_parts else "LOOP")
                
                # Connect prev_node to loop condition node
                # If prev_node is a pattern-level condition node (COND: P*), label appropriately
                # Otherwise, use the entry label or loop condition label
                if prev_node.startswith("COND: P"):
                    # This is a pattern-level condition - the TRUE path enters the loop
                    # Show as TERMINATION with MAX and termination condition combined
                    label_parts = []
                    
                    # Check if entry_label contains ITERATE or MAX
                    entry_has_iterate = entry_label and "ITERATE" in entry_label.upper()
                    entry_has_max = entry_label and "MAX" in entry_label.upper()
                    
                    # If entry_label has ITERATE, always add it (it already includes MAX if needed)
                    if entry_has_iterate:
                        label_parts.append(entry_label)
                    # If entry_label has MAX but no ITERATE, add it
                    elif entry_has_max:
                        label_parts.append(entry_label) 
                    # If entry_label doesn't have MAX or is None/empty, add max_iterations separately (if it exists)
                    elif max_iterations:
                        if isinstance(max_iterations, str):
                            label_parts.append(f"MAX {max_iterations.upper()}")
                        else:
                            label_parts.append(f"MAX {max_iterations}")
                    else:
                        self.logger.warning("max_iterations is falsy and entry_label doesn't have MAX: {}", max_iterations)
                    
                    if termination_condition:
                        # Include termination condition
                        # No truncation needed - multiline formatting will handle long conditions
                        term_cond_display = termination_condition.upper().strip()
                        # Remove any trailing spaces or extra parentheses
                        term_cond_display = re.sub(r'\s+\)\s*$', ')', term_cond_display)
                        term_cond_display = re.sub(r'\)\s+\)', ')', term_cond_display)
                        label_parts.append(term_cond_display)
                    
                    if label_parts:
                        # Join with | separator and format as TERMINATION(...)
                        label_content = " | ".join(label_parts)
                        final_label = f"TERMINATION({label_content})"
                        self.logger.debug("Final TERMINATION label: {}", final_label)
                        edges.append((prev_node, loop_cond_node, final_label))
                    else:
                        # No max_iterations or termination condition, just show TERMINATION
                        self.logger.debug("No label_parts, using default TERMINATION")
                        edges.append((prev_node, loop_cond_node, "TERMINATION"))
                else:
                    # Direct connection - use entry label if available, otherwise loop condition label
                    # Include termination condition if present
                    if entry_label:
                        if termination_condition:
                            # Include both entry_label (max_iterations) and termination condition
                            # No truncation needed - multiline formatting will handle long conditions
                            term_cond_display = termination_condition.upper().strip()
                            # Remove any extra parentheses from term_cond_display to avoid double closing
                            if term_cond_display.startswith('(') and term_cond_display.endswith(')'):
                                # Already has parentheses, use as is
                                final_label = f"{entry_label} | {term_cond_display}"
                                edges.append((prev_node, loop_cond_node, final_label))
                            else:
                                # No parentheses, add them
                                final_label = f"{entry_label} | {term_cond_display}"
                                edges.append((prev_node, loop_cond_node, final_label))
                        else:
                            edges.append((prev_node, loop_cond_node, entry_label))
                    else:
                        # No entry_label - build label from max_iterations and termination_condition
                        label_parts = []
                        if max_iterations:
                            if isinstance(max_iterations, str):
                                label_parts.append(f"MAX {max_iterations.upper()}")
                            else:
                                label_parts.append(f"MAX {max_iterations}")
                        if termination_condition:
                            term_cond_display = termination_condition.upper().strip()
                            term_cond_display = re.sub(r'\s+\)\s*$', ')', term_cond_display)
                            term_cond_display = re.sub(r'\)\s+\)', ')', term_cond_display)
                            label_parts.append(term_cond_display)
                        
                        if label_parts:
                            # Use constructed label or fall back to loop_condition_label
                            constructed_label = " | ".join(label_parts)
                            edges.append((prev_node, loop_cond_node, constructed_label))
                        else:
                            # No max_iterations or termination condition, use loop_condition_label
                            edges.append((prev_node, loop_cond_node, loop_condition_label))
                
                # Termination condition logic: TRUE means exit loop, FALSE means continue loop
                # This is because termination condition is typically "success == true" or "error == false"
                # When condition is TRUE (success), we exit; when FALSE (not yet successful), we continue
                next_real = next_node or "END"
                
                # TERMINATION path: termination condition is TRUE, so exit the loop
                # Show as TRUE (green) - TERMINATION info is shown on entry edge
                edges.append((loop_cond_node, next_real, "TRUE"))
                
                # FALSE path: termination condition is FALSE, so continue looping (enter loop body)
                # If body starts with parallel, connect to convergence point; otherwise to first_node
                loop_entry_target = loop_convergence_point if loop_convergence_point else first_node
                if loop_entry_target and loop_entry_target not in ["START", "END"]:
                    edges.append((loop_cond_node, loop_entry_target, "FALSE"))
                loop_entry = loop_cond_node
            else:
                # No termination condition - use convergence point if body starts with parallel, otherwise prev_node
                if loop_convergence_point:
                    # Connect prev_node to convergence point
                    if entry_label:
                        edges.append((prev_node, loop_convergence_point, entry_label))
                    else:
                        edges.append((prev_node, loop_convergence_point, None))
                    loop_entry = loop_convergence_point
                else:
                    loop_entry = prev_node
            
            # Process body once to get the nodes and last node
            if isinstance(body, dict):
                # If we have a convergence point, use it as entry; otherwise use loop_entry
                body_entry = loop_convergence_point if loop_convergence_point else loop_entry
                # Process body with body_entry as entry point
                last_node, _ = self._process_step(
                    body,
                    body_entry,
                    None,  # Don't connect to next_node yet
                    edges,
                    nodes,
                    gates,
                    gates_map,
                    node_info_map,
                )
                
                # If no termination condition but we have an entry_label, update the edge from prev_node
                # Use convergence point if exists, otherwise first_node
                if not termination_condition and entry_label:
                    target_node = loop_convergence_point if loop_convergence_point else first_node
                    if target_node and target_node not in ["START", "END"]:
                        # Find and update the edge from prev_node to target_node
                        for i, (from_node, to_node, label) in enumerate(edges):
                            if from_node == prev_node and to_node == target_node:
                                # Update the edge label
                                if prev_node.startswith("COND: P"):
                                    # Pattern-level condition: use "TRUE (entry_label)" format
                                    # But if entry_label contains ITERATE, don't wrap in TRUE() - use entry_label directly
                                    if entry_label and "ITERATE" in entry_label.upper():
                                        edges[i] = (from_node, to_node, entry_label)
                                    else:
                                        edges[i] = (from_node, to_node, f"TRUE ({entry_label})")
                                else:
                                    # Direct connection: use entry_label
                                    edges[i] = (from_node, to_node, entry_label)
                                break

                # Fix conditional sequential FALSE paths within loop body
                # They should go to last_node (end of loop body) instead of END or next_node
                if last_node and last_node not in ["START", "END"]:
                    # Find all conditional nodes that have FALSE paths going to END or next_node
                    # These should be redirected to last_node so they loop back
                    next_real = next_node or "END"
                    # Track the loop's pattern-level condition node (if it exists)
                    # This is the COND: P* node that is prev_node if it's a pattern-level condition
                    loop_pattern_cond_node = None
                    if prev_node.startswith("COND: P"):
                        loop_pattern_cond_node = prev_node
                    
                    for i, (from_node, to_node, label) in enumerate(edges):
                        # If this is a FALSE path from a conditional node going to END or next_node
                        # and it's within the loop body, redirect it to last_node
                        # BUT exclude:
                        # - Loop exit conditions (COND: L*) - these should exit the loop
                        # - The loop's own pattern-level condition (if it exists) - this should bypass the entire pattern
                        # Note: Conditional sequential steps inside loop body also create COND: P* nodes,
                        # but they should be redirected since they're inside the loop body
                        if (from_node.startswith("COND:") and 
                            label == "FALSE" and 
                            to_node in (next_real, "END") and
                            not from_node.startswith("COND: L") and  # Don't redirect the loop exit condition
                            from_node != loop_pattern_cond_node):  # Don't redirect the loop's pattern-level condition (if it exists)
                            edges[i] = (from_node, last_node, label)
                
                # Determine loop back target
                if termination_condition:
                    loop_back_target = loop_cond_node
                else:
                    # No termination condition - loop back to convergence point if exists, otherwise first_node
                    loop_back_target = loop_convergence_point if loop_convergence_point else first_node
                    # first_node should already be updated to use loop-specific ID if needed
                
                # Handle case where last_node is None (e.g., body ends with switch pattern)
                # Find all nodes that have edges to END - these are likely terminal nodes from switch cases
                if last_node is None and loop_back_target and loop_back_target not in ["START", "END"]:
                    # Find all nodes that connect to END - these are terminal nodes from switch cases
                    # We need to redirect these to loop back to the convergence point (if parallel) or loop entry
                    terminal_nodes = []
                    for from_node, to_node, label in edges:
                        if to_node == "END" and from_node not in ["START", "END"]:
                            # Check if this node was created during body processing
                            # (it should be a node, not a pattern node like SWITCH, COND, or HITL gates)
                            # Exclude pattern nodes and special nodes
                            if (not from_node.startswith("COND:") and 
                                from_node != "SWITCH" and 
                                not from_node.startswith("HITL:") and
                                not from_node.startswith("CONVERGE:")):
                                terminal_nodes.append(from_node)
                    
                    # Remove edges from terminal nodes to END and add loop-back edges
                    # Loop back should go to convergence point if body starts with parallel, otherwise to loop entry
                    for terminal_node in set(terminal_nodes):  # Use set to avoid duplicates
                        # Remove edge to END
                        edges[:] = [e for e in edges if not (e[0] == terminal_node and e[1] == "END")]
                        # Add loop-back edge to the correct target (convergence point or loop entry)
                        if terminal_node not in ["START", "END"]:
                            edges.append((terminal_node, loop_back_target, "LOOP"))
                
                # Remove any edges FROM last_node that were created by body processing
                # (we'll add our own loop-back edge)
                # Keep edges TO last_node, only remove edges FROM last_node
                # EXCEPTION: Preserve edges FROM last_node that go TO condition nodes (COND: P*),
                # as these were created by pattern-level condition handlers before the loop
                # and represent the entry condition check (e.g., edge from agent to COND: P2)
                if last_node and last_node not in ["START", "END"]:
                    # Get all nodes in the loop body to identify which edges to remove
                    body_nodes = set()
                    def collect_body_nodes(body_step):
                        if isinstance(body_step, dict):
                            if "node" in body_step:
                                body_nodes.add(body_step["node"].split(":")[0])
                            elif "gate" in body_step:
                                body_nodes.add(f"HITL: {body_step['gate'].upper()}")
                            elif body_step.get("type") == "sequential":
                                for s in body_step.get("steps", []):
                                    collect_body_nodes(s)
                            elif body_step.get("type") == "parallel":
                                for s in body_step.get("steps", []):
                                    collect_body_nodes(s)
                    collect_body_nodes(body)
                    
                    # Remove edges FROM last_node that go TO nodes within the loop body
                    # BUT preserve edges FROM last_node that go TO condition nodes (COND: P*),
                    # as these represent pattern-level conditions created before the loop
                    edges[:] = [
                        e for e in edges if not (
                            e[0] == last_node and 
                            e[1] in body_nodes and
                            not e[1].startswith("COND: P")  # Preserve edges to pattern-level condition nodes
                        )
                    ]
                
                # Add loop-back edge from last node to loop entry point (control returns to beginning)
                if last_node and loop_back_target and last_node not in ["START", "END"] and loop_back_target not in ["START", "END"]:
                    # Label indicates this is the loop-back path
                    edges.append((last_node, loop_back_target, "LOOP"))
                
                # If no termination condition, add exit edge from convergence point or first_node
                # The exit should come from the convergence point if it exists (before parallel), otherwise first_node
                if not termination_condition:
                    exit_source = loop_convergence_point if loop_convergence_point else first_node
                    # exit_source should already be updated to use loop-specific IDs if needed (via first_node update above)
                    if exit_source and exit_source not in ["START", "END"]:
                        next_real = next_node or "END"
                        # Remove any existing edges from exit_source to next_real
                        edges[:] = [e for e in edges if not (e[0] == exit_source and e[1] == next_real)]
                        
                        # Build exit label
                        exit_label_parts = []
                        if iterate_over:
                            # List iteration: exit when list is exhausted
                            exit_label_parts.append("LIST EXHAUSTED")
                        if max_iterations:
                            # Safety limit
                            if isinstance(max_iterations, str):
                                exit_label_parts.append(f"MAX {max_iterations.upper()}")
                            else:
                                exit_label_parts.append(f"MAX {max_iterations}")
                        
                        exit_label = " OR ".join(exit_label_parts) if exit_label_parts else "EXIT"
                        edges.append((exit_source, next_real, exit_label))

                # Return loop entry point (condition node if exists, otherwise convergence point or first_node)
                if termination_condition:
                    return loop_cond_node, None
                else:
                    return loop_convergence_point if loop_convergence_point else first_node, None

            return prev_node, None

        elif step.get("type") == "switch" or str(step.get("type", "")).startswith(
            "switch"
        ):
            # Handle switch pattern - use hexagon shape for SWITCH node
            cases = step.get("cases", {})

            # Extract condition from type string (e.g., "switch(condition)")
            switch_type = step.get("type")
            if (
                isinstance(switch_type, str)
                and "(" in switch_type
                and ")" in switch_type
            ):
                # Extract condition from switch(type)
                condition_match = re.search(r"switch\((.*)\)", switch_type)
                if condition_match:
                    switch_condition = condition_match.group(1).strip()
                else:
                    switch_condition = ""
            else:
                switch_condition = ""

            switch_label = "SWITCH"

            # Add edge from prev_node to SWITCH with condition as label
            if switch_condition:
                edge_label = switch_condition.upper()
            else:
                edge_label = None
            edges.append((prev_node, switch_label, edge_label))

            # Store SWITCH condition if present
            if node_info_map is not None and switch_condition:
                node_info_map[switch_label] = {"condition": switch_condition}

            # Process each case branch - connect all steps in sequence
            for case_key, case_steps in cases.items():
                case_value = str(case_key).upper()
                case_suffix = f"_{case_value}"  # Unique suffix for this case

                # Track edges before processing to identify newly created edges
                edges_before_case = len(edges)

                # Process steps in this case sequentially
                case_prev = switch_label
                for i, case_step in enumerate(case_steps):
                    # Determine what's next in this case
                    case_next = None
                    if i < len(case_steps) - 1:
                        # Not the last step - continue to next step in case
                        next_step_in_case = case_steps[i + 1]
                        if "node" in next_step_in_case:
                            node_id = next_step_in_case["node"].split(":")[0]
                            case_next = f"{node_id}{case_suffix}"  # Add case suffix
                            nodes.add(case_next)
                        elif "gate" in next_step_in_case:
                            gate_id = next_step_in_case["gate"]
                            gate_info = next(
                                (g for g in gates if g.get("id") == gate_id), {}
                            )
                            case_next = f"HITL: {gate_id.upper()}{case_suffix}"
                    else:
                        # Last step in case - no next
                        case_next = None

                    # Process the step with modified step to use case-specific node IDs
                    step_prev = case_prev

                    # Clone the step and modify node references to be case-specific
                    modified_step = case_step.copy()
                    
                    # Helper function to recursively apply case suffix to nodes in nested patterns
                    def apply_case_suffix_to_step(step_dict, suffix):
                        """Recursively apply case suffix to all node references in a step."""
                        if isinstance(step_dict, dict):
                            # If this step has a node, apply suffix
                            if "node" in step_dict:
                                original_node = step_dict["node"]
                                node_id = original_node.split(":")[0]
                                new_node_id = f"{node_id}{suffix}"
                                protocol = (
                                    original_node.split(":")[1]
                                    if ":" in original_node
                                    else "a2a"
                                )
                                step_dict["node"] = f"{new_node_id}:{protocol}"
                            
                            # If this is a nested sequential/parallel pattern, recurse into steps
                            if step_dict.get("type") in ("sequential", "parallel"):
                                nested_steps = step_dict.get("steps", [])
                                for nested_step in nested_steps:
                                    apply_case_suffix_to_step(nested_step, suffix)
                            
                            # If this is a loop pattern, recurse into body
                            if step_dict.get("type") == "loop":
                                body = step_dict.get("body", {})
                                apply_case_suffix_to_step(body, suffix)
                        
                        return step_dict
                    
                    # Apply case suffix to this step and any nested patterns
                    apply_case_suffix_to_step(modified_step, case_suffix)

                    case_prev, _ = self._process_step(
                        modified_step,
                        case_prev,
                        case_next,
                        edges,
                        nodes,
                        gates,
                        gates_map,
                        node_info_map,
                    )

                    # Add case label to first edge after SWITCH (only for first step)
                    if i == 0:
                        # Find the first edge from SWITCH that was created during this case processing
                        # Look through edges created during this case (from edges_before_case onwards)
                        for idx in range(edges_before_case, len(edges)):
                            if (
                                edges[idx][0] == switch_label
                                and edges[idx][2] is None  # Only update unlabeled edges
                            ):
                                # Found an unlabeled edge from SWITCH - this is the case edge
                                edges[idx] = (edges[idx][0], edges[idx][1], case_value)
                                break

                    # If this is the last step in the case, connect to END
                    if i == len(case_steps) - 1 and case_prev and case_prev != "END":
                        edges.append((case_prev, "END", None))

            # Add SWITCH node to special nodes list for styling
            nodes.add(switch_label)

            # Return None to signal we handled the flow
            return None, None

        elif step.get("type") == "handoff":
            # Handle handoff pattern - LLM-driven routing to specialists
            handoffs = step.get("handoffs", [])
            orchestrator = step.get("orchestrator")

            # Create a small gray circle before handoff (represents virtual orchestrator start)
            handoff_start_id = "HANDOFF_START"
            nodes.add(handoff_start_id)
            edges.append((prev_node, handoff_start_id, None))

            # Create a small gray circle after specialists (represents virtual orchestrator end)
            handoff_end_id = "HANDOFF_END"
            nodes.add(handoff_end_id)

            # Connect to what comes after
            final_target = next_node if next_node else "END"
            edges.append((handoff_end_id, final_target, None))

            # If orchestrator is specified, show it, otherwise skip it (virtual)
            if orchestrator:
                orchestrator_id = orchestrator.split(":")[0]
                nodes.add(orchestrator_id)
                edges.append((handoff_start_id, orchestrator_id, None))
                # Connect specialists from orchestrator
                for handoff in handoffs:
                    if "node" in handoff:
                        specialist_id = handoff["node"].split(":")[0]
                        nodes.add(specialist_id)
                        edges.append((orchestrator_id, specialist_id, "dotted"))
                        edges.append((specialist_id, handoff_end_id, "dotted"))
            else:
                # No orchestrator - connect specialists directly from start circle
                for handoff in handoffs:
                    if "node" in handoff:
                        specialist_id = handoff["node"].split(":")[0]
                        nodes.add(specialist_id)
                        # Dotted edges from start circle to specialist
                        edges.append((handoff_start_id, specialist_id, "dotted"))
                        # Dotted edges from specialist to end circle
                        edges.append((specialist_id, handoff_end_id, "dotted"))

            # Return to signal handoff is complete
            return None, None

        return prev_node, None

    def _process_repeat_pattern(
        self,
        step: Dict[str, Any],
        prev_node: str,
        next_node: Optional[str],
        edges: List[tuple],
        nodes: set,
        gates: List[Dict],
        gates_map: Dict[str, Dict],
        node_info_map: Dict[str, Dict],
        parent_instance_idx: Optional[int] = None,
    ) -> tuple:
        """Process repeat pattern - creates multiple instances of the same agent or nested sequential pattern in parallel.
        
        Supports two modes:
        1. Single agent repeat: Uses 'node' field
        2. Enhanced repeat (nested sequential): Uses 'type: sequential' with 'steps' field
        
        Args:
            step: Pattern step with 'repeat' key
            prev_node: Previous node in flow
            next_node: Next node after this pattern
            edges: List of edges (from, to, label)
            nodes: Set of node IDs
            gates: List of gate configurations
            gates_map: Map of gate IDs to gate info
            node_info_map: Map of node IDs to node info
        
        Returns:
            Tuple of (terminal_node, None)
        """
        repeat_config = step.get("repeat", {})
        instances_spec = repeat_config.get("instances", 1)
        instance_id_template = repeat_config.get("instance_id_template", "{{node_id}}_instance_{{index}}")
        
        # Determine number of instances to show
        if isinstance(instances_spec, int):
            num_instances = instances_spec
            instances_label = f"{num_instances} instances"
        else:
            # It's an expression - show it as a variable (use 3 for visualization)
            num_instances = 3  # Default for visualization
            instances_label = f"{instances_spec} instances"
        
        # Check if this is enhanced repeat (nested sequential) or single agent repeat
        is_enhanced_repeat = "type" in repeat_config and repeat_config["type"] == "sequential"
        
        if is_enhanced_repeat:
            # Enhanced repeat pattern: nested sequential
            nested_steps = repeat_config.get("steps", [])
            if not nested_steps:
                self.logger.warning("Enhanced repeat pattern has no steps, skipping")
                return next_node if next_node else prev_node, None
            
            # Extract base ID from instance_id_template (e.g., "file_{{index}}" -> "file")
            base_id_for_template = "sequential"
            if "{{index}}" in instance_id_template:
                # Extract prefix before {{index}}
                parts = instance_id_template.split("{{index}}")
                if parts[0]:
                    base_id_for_template = parts[0].rstrip("_")
            
            branch_terminal_nodes = []
            branch_first_nodes = []
            
            # Track enhanced repeat edges for duplicate allowance
            # Store in node_info_map so we can check during edge rendering
            if "_enhanced_repeat_edges" not in node_info_map:
                node_info_map["_enhanced_repeat_edges"] = set()
            
            # Track instance-specific node mappings for visualization
            # Each instance needs its own visual nodes to show parallel sequences
            if "_enhanced_repeat_instance_nodes" not in node_info_map:
                node_info_map["_enhanced_repeat_instance_nodes"] = {}  # Maps (base_node_id, instance_index) -> instance_node_id
            
            # Process each instance
            for i in range(num_instances):
                # Process nested sequential pattern for this instance
                # Create instance-specific node IDs for visualization
                instance_current = prev_node  # Start from prev_node for first step
                instance_first_node = None
                instance_last_node = None
                
                # Helper function to get instance-specific node ID
                def get_instance_node_id(base_node_id: str, instance_idx: int) -> str:
                    """Get or create instance-specific node ID for visualization."""
                    key = (base_node_id, instance_idx)
                    if key not in node_info_map["_enhanced_repeat_instance_nodes"]:
                        # Create instance-specific node ID
                        instance_node_id = f"{base_node_id}_inst_{instance_idx}"
                        node_info_map["_enhanced_repeat_instance_nodes"][key] = instance_node_id
                        # Copy node info from base node
                        if base_node_id in node_info_map:
                            node_info_map[instance_node_id] = node_info_map[base_node_id].copy()
                    return node_info_map["_enhanced_repeat_instance_nodes"][key]
                
                # Process each step in the nested sequence
                for j, nested_step in enumerate(nested_steps):
                    # Determine next target within this instance's sequence
                    nested_next = None
                    if j < len(nested_steps) - 1:
                        # Not last step - determine what's next in sequence
                        next_nested_step = nested_steps[j + 1]
                        if "node" in next_nested_step:
                            base_next_id = next_nested_step["node"].split(":")[0]
                            nested_next = get_instance_node_id(base_next_id, i)
                            nodes.add(nested_next)
                        elif "gate" in next_nested_step:
                            gate_id = next_nested_step["gate"]
                            nested_next = f"HITL: {gate_id.upper()}"
                        elif next_nested_step.get("type") == "parallel" and "repeat" in next_nested_step:
                            # Nested repeat pattern - determine the terminal node
                            # For single agent repeat, we'll get the terminal from _process_step
                            nested_next = None  # Will be determined by _process_step
                        else:
                            # Pattern - will be determined by _process_step
                            nested_next = None
                    else:
                        # Last step in sequence - use next_node if available (for parallel patterns to connect correctly)
                        # This ensures parallel patterns know what comes after them
                        nested_next = next_node if next_node else None
                    
                    # Create a modified step with instance-specific node IDs
                    modified_step = nested_step.copy()
                    if "node" in modified_step:
                        base_node_id = modified_step["node"].split(":")[0]
                        instance_node_id = get_instance_node_id(base_node_id, i)
                        # Preserve protocol if present
                        if ":" in modified_step["node"]:
                            protocol = modified_step["node"].split(":")[1]
                            modified_step["node"] = f"{instance_node_id}:{protocol}"
                        else:
                            modified_step["node"] = instance_node_id
                        nodes.add(instance_node_id)
                    elif modified_step.get("type") == "parallel" and "steps" in modified_step:
                        # Recursively modify nodes within parallel pattern to have instance-specific IDs
                        # Use parent instance index format: _inst_{parent_idx}_{nested_idx}
                        def modify_parallel_steps(steps_list, nested_index=0):
                            """Recursively modify all node steps within a parallel pattern."""
                            for step_idx, step in enumerate(steps_list):
                                if "node" in step:
                                    # Extract original base node ID by removing any existing _inst_* suffix
                                    # This prevents double-nesting when step["node"] was already instanced
                                    node_id_with_protocol = step["node"].split(":")[0]
                                    # Remove any _inst_* pattern to get the original base ID
                                    base_node_id = re.sub(r'_inst_\d+(_\d+)*$', '', node_id_with_protocol)
                                    # Use parent instance index format: _inst_{parent_idx}_{nested_idx}
                                    # This creates IDs like rate_case_equity_assessor_inst_0_0, inst_0_1, etc.
                                    nested_idx = nested_index + step_idx
                                    instance_node_id = f"{base_node_id}_inst_{i}_{nested_idx}"
                                    # Store in node_info_map for consistency
                                    key = (base_node_id, i, nested_idx)
                                    if "_enhanced_repeat_instance_nodes" not in node_info_map:
                                        node_info_map["_enhanced_repeat_instance_nodes"] = {}
                                    node_info_map["_enhanced_repeat_instance_nodes"][key] = instance_node_id
                                    # Copy node info from base node
                                    if base_node_id in node_info_map:
                                        node_info_map[instance_node_id] = node_info_map[base_node_id].copy()
                                    # Preserve protocol if present
                                    if ":" in step["node"]:
                                        protocol = step["node"].split(":")[1]
                                        step["node"] = f"{instance_node_id}:{protocol}"
                                    else:
                                        step["node"] = instance_node_id
                                    nodes.add(instance_node_id)
                                elif step.get("type") == "parallel" and "steps" in step:
                                    # Nested parallel pattern - recurse with updated nested_index
                                    modify_parallel_steps(step["steps"], nested_index + step_idx)
                                elif step.get("type") == "sequential" and "steps" in step:
                                    # Nested sequential pattern - recurse with updated nested_index
                                    modify_parallel_steps(step["steps"], nested_index + step_idx)
                        
                        modify_parallel_steps(modified_step["steps"])
                    
                    # Process the modified nested step
                    # Set parent instance index context for nested repeat patterns
                    old_parent_idx = getattr(self, '_current_parent_instance_idx', None)
                    self._current_parent_instance_idx = i
                    try:
                        nested_result, _ = self._process_step(
                            modified_step,
                            instance_current,
                            nested_next,
                            edges,
                            nodes,
                            gates,
                            gates_map,
                            node_info_map,
                        )
                    finally:
                        # Restore previous parent instance index
                        if old_parent_idx is not None:
                            self._current_parent_instance_idx = old_parent_idx
                        else:
                            delattr(self, '_current_parent_instance_idx')
                    
                    # Track first and last nodes in sequence
                    if j == 0:
                        instance_first_node = nested_result if nested_result else instance_current
                        branch_first_nodes.append(instance_first_node)
                        # Mark edge from prev_node to first node as enhanced repeat edge
                        if prev_node and instance_first_node:
                            node_info_map["_enhanced_repeat_edges"].add((prev_node, instance_first_node))
                    
                    # For parallel patterns as the last step, nested_result is next_node (the recommender)
                    # We need to extract the actual terminal nodes from the parallel pattern
                    # The parallel pattern should have stored its terminal nodes in node_info_map
                    if modified_step.get("type") == "parallel" and "steps" in modified_step and j == len(nested_steps) - 1:
                        # This is a parallel pattern as the last step - extract terminal nodes
                        # The terminal nodes are the instance-specific IDs we created for nodes in the parallel pattern
                        parallel_terminal_nodes = []
                        for parallel_step in modified_step["steps"]:
                            if "node" in parallel_step:
                                # Get the instance-specific node ID that was created
                                inst_node_id = parallel_step["node"].split(":")[0]
                                parallel_terminal_nodes.append(inst_node_id)
                        
                        if parallel_terminal_nodes:
                            # Store terminal nodes for this instance
                            if not hasattr(self, '_instance_parallel_terminals'):
                                self._instance_parallel_terminals = {}
                            self._instance_parallel_terminals[i] = parallel_terminal_nodes
                            # Don't set instance_last_node - we'll use parallel_terminal_nodes instead
                        else:
                            # Fallback: use nested_result
                            if nested_result:
                                instance_last_node = nested_result
                    else:
                        # Non-parallel step or not last step: use nested_result
                        if nested_result:
                            instance_last_node = nested_result
                    
                    instance_current = nested_result if nested_result else instance_current
                
                # Terminal node for this instance is the last node in its sequence
                # For parallel patterns as last step, use all terminal nodes from the parallel pattern
                if hasattr(self, '_instance_parallel_terminals') and i in self._instance_parallel_terminals:
                    # Parallel pattern: add all terminal nodes
                    for term_node in self._instance_parallel_terminals[i]:
                        branch_terminal_nodes.append(term_node)
                        # Mark edge from terminal node to next_node as enhanced repeat edge
                        if next_node and term_node:
                            node_info_map["_enhanced_repeat_edges"].add((term_node, next_node))
                    # Clean up
                    del self._instance_parallel_terminals[i]
                elif instance_last_node:
                    branch_terminal_nodes.append(instance_last_node)
                    # Mark edge from last node to next_node as enhanced repeat edge
                    if next_node and instance_last_node:
                        node_info_map["_enhanced_repeat_edges"].add((instance_last_node, next_node))
                else:
                    # Fallback: use the last processed node
                    branch_terminal_nodes.append(instance_current if instance_current != prev_node else prev_node)
                    if next_node and instance_current != prev_node:
                        node_info_map["_enhanced_repeat_edges"].add((instance_current, next_node))
            
            # Store repeat pattern info and track enhanced repeat edges
            if base_id_for_template:
                if base_id_for_template not in node_info_map:
                    node_info_map[base_id_for_template] = {}
                node_info_map[base_id_for_template]["repeat_pattern_info"] = {
                    "instances": instances_label,
                    "instance_count": num_instances if isinstance(instances_spec, int) else instances_spec,
                    "is_enhanced_repeat": True,
                }
            
            # Store enhanced repeat edge information for duplicate allowance
            # Track edges from prev_node to first nodes, and from last nodes to next_node
            if "_enhanced_repeat_edges" not in node_info_map:
                node_info_map["_enhanced_repeat_edges"] = set()
            
            # Mark edges from prev_node to each instance's first node
            for first_node in branch_first_nodes:
                if prev_node and first_node:
                    node_info_map["_enhanced_repeat_edges"].add((prev_node, first_node))
            
            # Mark edges from each instance's last node to next_node
            for last_node in branch_terminal_nodes:
                if next_node and last_node:
                    node_info_map["_enhanced_repeat_edges"].add((last_node, next_node))
        elif "pipeline" in repeat_config:
            # NEW: Single pipeline repeat pattern
            pipeline_id = repeat_config.get("pipeline", "")
            
            branch_terminal_nodes = []
            branch_first_nodes = []
            
            # Generate instance nodes
            for i in range(num_instances):
                # Generate instance ID using template
                # If we have a parent instance index, include it in the instance ID
                if parent_instance_idx is not None:
                    # Nested repeat: create scoped instance ID
                    instance_id = f"{pipeline_id}_inst_{parent_instance_idx}_{i}"
                else:
                    # Top-level repeat: use template
                    instance_id = instance_id_template.replace("{{index}}", str(i))
                    instance_id = instance_id.replace("{{pipeline_id}}", pipeline_id)
                    instance_id = instance_id.replace("{{node_id}}", pipeline_id)  # Fallback for compatibility
                
                # Add instance node
                nodes.add(instance_id)
                branch_first_nodes.append(instance_id)
                
                # Add node info - mark as pipeline instance
                if pipeline_id not in node_info_map:
                    node_info_map[pipeline_id] = {}
                node_info_map[instance_id] = {
                    **node_info_map.get(pipeline_id, {}),
                    "is_repeat_instance": True,
                    "is_pipeline_instance": True,  # NEW: Mark as pipeline instance
                    "base_pipeline_id": pipeline_id,
                    "instance_index": i,
                }
                
                # Connect prev_node to this instance
                if prev_node:
                    # Check if prev_node is a gate with action labels
                    gate_action_labels = None
                    if prev_node.startswith("HITL:"):
                        gate_label_upper = prev_node[5:]
                        gate_id_lower = gate_label_upper.lower()
                        gate_info = gates_map.get(gate_id_lower)
                        if gate_info:
                            gate_action_labels = gate_info.get("_continue_action_labels")
                    
                    if gate_action_labels:
                        # Add labeled edges from gate to each instance
                        for action_label in gate_action_labels:
                            if not any(e[0] == prev_node and e[1] == instance_id and e[2] == action_label for e in edges):
                                edges.append((prev_node, instance_id, action_label))
                    else:
                        # Add unlabeled edge
                        if not any(e[0] == prev_node and e[1] == instance_id for e in edges):
                            edges.append((prev_node, instance_id, None))
                
                # Instance terminal is the instance itself
                branch_terminal_nodes.append(instance_id)
            
            # Store repeat pattern info
            if pipeline_id:
                if pipeline_id not in node_info_map:
                    node_info_map[pipeline_id] = {}
                node_info_map[pipeline_id]["repeat_pattern_info"] = {
                    "instances": instances_label,
                    "instance_count": num_instances if isinstance(instances_spec, int) else instances_spec,
                    "is_pipeline_repeat": True,  # NEW: Mark as pipeline repeat
                }
        else:
            # EXISTING: Single agent repeat pattern
            base_node_ref = repeat_config.get("node", "")
            base_agent_id = base_node_ref.split(":")[0] if base_node_ref else ""
            
            branch_terminal_nodes = []
            branch_first_nodes = []
            
            # Generate instance nodes
            for i in range(num_instances):
                # Generate instance ID using template
                # If we have a parent instance index, include it in the instance ID
                if parent_instance_idx is not None:
                    # Nested repeat: create scoped instance ID (e.g., problem_solver_inst_0_1)
                    instance_id = f"{base_agent_id}_inst_{parent_instance_idx}_{i}"
                else:
                    # Top-level repeat: use template
                    instance_id = instance_id_template.replace("{{index}}", str(i))
                    instance_id = instance_id.replace("{{node_id}}", base_agent_id)
                
                # Add instance node
                nodes.add(instance_id)
                branch_first_nodes.append(instance_id)
                
                # Add node info
                if base_agent_id not in node_info_map:
                    node_info_map[base_agent_id] = {}
                node_info_map[instance_id] = {
                    **node_info_map.get(base_agent_id, {}),
                    "is_repeat_instance": True,
                    "base_agent_id": base_agent_id,
                    "instance_index": i,
                }
                
                # Connect prev_node to this instance
                if prev_node:
                    # Check if prev_node is a gate with action labels
                    gate_action_labels = None
                    if prev_node.startswith("HITL:"):
                        gate_label_upper = prev_node[5:]
                        gate_id_lower = gate_label_upper.lower()
                        gate_info = gates_map.get(gate_id_lower)
                        if gate_info:
                            gate_action_labels = gate_info.get("_continue_action_labels")
                    
                    if gate_action_labels:
                        # Add labeled edges from gate to each instance
                        for action_label in gate_action_labels:
                            if not any(e[0] == prev_node and e[1] == instance_id and e[2] == action_label for e in edges):
                                edges.append((prev_node, instance_id, action_label))
                    else:
                        # Add unlabeled edge
                        if not any(e[0] == prev_node and e[1] == instance_id for e in edges):
                            edges.append((prev_node, instance_id, None))
                
                # Instance terminal is the instance itself
                branch_terminal_nodes.append(instance_id)
            
            # Store repeat pattern info
            if base_agent_id:
                if base_agent_id not in node_info_map:
                    node_info_map[base_agent_id] = {}
                node_info_map[base_agent_id]["repeat_pattern_info"] = {
                    "instances": instances_label,
                    "instance_count": num_instances if isinstance(instances_spec, int) else instances_spec,
                }
        
        # Connect all instance terminals to next_node
        if next_node and branch_terminal_nodes:
            next_real = next_node if next_node != "START" else "END"
            for terminal in branch_terminal_nodes:
                if not any(e[0] == terminal and e[1] == next_real for e in edges):
                    edges.append((terminal, next_real, None))
        
        # Return next_node so flow continues
        return next_node if next_node else prev_node, None

    def generate_workflow_diagrams(
        self, project_path: str, overwrite: bool = False
    ) -> int:
        """Generate workflow diagrams for all pipelines in a project."""
        try:
            project_dir = Path(project_path)
            pipelines_dir = project_dir / "config" / "pipelines"

            if not pipelines_dir.exists():
                self.logger.warning("Pipelines directory not found: {}", pipelines_dir)
                return 0

            # Find all YAML pipeline files
            pipeline_files = list(pipelines_dir.glob("*.yml"))
            if not pipeline_files:
                self.logger.warning("No pipeline files found in: {}", pipelines_dir)
                return 0

            self.logger.debug("Found {} pipeline files to process", len(pipeline_files))

            success_count = 0
            for pipeline_file in pipeline_files:
                try:
                    pipeline_name = pipeline_file.stem
                    import yaml

                    with open(pipeline_file, "r", encoding="utf-8") as f:
                        pipeline_config = yaml.safe_load(f)

                    pattern_config = pipeline_config.get("pattern", {})
                    gates_config = pipeline_config.get("gates", [])

                    # Load UI manifest to get agent titles
                    agent_title_map = {}
                    ui_manifest_path = (
                        project_dir / "config" / "ui_manifests" / f"{pipeline_name}.yml"
                    )
                    if ui_manifest_path.exists():
                        try:
                            with open(ui_manifest_path, "r", encoding="utf-8") as f:
                                ui_manifest = yaml.safe_load(f)
                                agents = ui_manifest.get("agents", [])
                                for agent in agents:
                                    agent_id = agent.get("id")
                                    agent_title = agent.get("title")
                                    if agent_id and agent_title:
                                        agent_title_map[agent_id] = agent_title
                            self.logger.debug(
                                "Loaded {} agent titles from UI manifest for {}",
                                len(agent_title_map),
                                pipeline_name,
                            )
                        except Exception as e:
                            self.logger.debug(
                                "Could not load UI manifest for {}: {}",
                                pipeline_name,
                                e,
                            )
                    else:
                        self.logger.debug(
                            "UI manifest not found for {}: {}",
                            pipeline_name,
                            ui_manifest_path,
                        )

                    result = self.generate_diagram(
                        project_path=project_dir,
                        pipeline_name=pipeline_name,
                        pattern_config=pattern_config,
                        gates_config=gates_config,
                        overwrite=overwrite,
                        agent_title_map=agent_title_map,
                        pipeline_config=pipeline_config,
                    )

                    if result:
                        success_count += 1
                        self.logger.info("✓ Generated: {}", pipeline_name)
                    else:
                        self.logger.warning("Failed to generate: {}", pipeline_name)

                except Exception as e:
                    self.logger.error("Error processing {}: {}", pipeline_file.name, e)
                    continue

            self.logger.success("Generated {} workflow diagrams", success_count)
            return 0 if success_count == len(pipeline_files) else 1

        except Exception as e:
            self.logger.error("Failed to generate workflow diagrams: {}", e)
            return 1
