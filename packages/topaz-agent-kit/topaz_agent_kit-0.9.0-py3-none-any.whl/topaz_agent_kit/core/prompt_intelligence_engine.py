"""
Prompt Intelligence Engine - Simplified Variable Analysis

This module analyzes YAML pipeline configurations and generates intelligent code for agents.
With the new "everything from upstream" approach, complexity is dramatically reduced.

ROLE:
- Analyzes YAML agent configurations to detect variables from prompts/templates
- Generates smart variable population code (everything from upstream)
- Provides complete transparency about population methods
- Generates clean, maintainable agent code with detailed variable documentation

HOW IT WORKS:
1. analyze_agent_config(): Parses YAML config and detects variables
2. generate_agent_variables_code(): Generates variable population logic

ARCHITECTURE:
- Base classes handle ALL execution logic (prompt rendering, LLM calls, etc.)
- Generated agents focus ONLY on variable handling and optional customization
- No execution method overrides unless custom logic is explicitly needed
- Clean separation between core functionality and custom behavior
- Complete transparency about variable population methods

USAGE:
- Called by AgentGenerator during agent scaffolding
- Analyzes pipeline.yml to understand agent requirements
- Generates code that integrates with base agent classes
- Focuses on maintainability, user customization, and transparency
"""

import re
from typing import Any, Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass

from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.json_utils import JSONUtils
import json


@dataclass
class VariableInfo:
    """Enhanced information about a variable found in YAML configuration"""
    name: str  # Full variable name as it appears in template (e.g., "user_text", "parser_agent.user_text", "parser_agent.user_text if condition else default")
    source: str  # 'prompt', 'task', 'inline', 'file', 'jinja'
    context: str  # Where the variable was found
    population_method: str  # How Prompt Intelligence Engine suggests populating it
    suggested_value: str  # The actual code used to populate it
    upstream_agent: Optional[str] = None  # If from upstream agent
    is_required: bool = True
    default_value: Optional[str] = None
    output_structure: Dict[str, Any] = None  # Expected output structure
    # NEW FIELDS:
    variable_type: str = "simple"  # "simple", "prefixed", "expression"
    agent_id: Optional[str] = None  # For prefixed variables (e.g., "parser_agent" from "parser_agent.user_text")
    variable_name: Optional[str] = None  # For prefixed variables (e.g., "user_text" from "parser_agent.user_text")
    expression: Optional[str] = None  # For expression variables (full expression string)
    loop_variable: Optional[str] = None  # If this variable references a loop variable (e.g., "eval_result" from {% for eval_result in ... %})
    loop_list_variable: Optional[str] = None  # The list variable that the loop variable iterates over (e.g., "requirements_evaluator_list")


class PromptIntelligenceEngine:
    """
    Analyzes YAML configuration to understand agent requirements and generate appropriate code.
    
    Simplified version that assumes everything comes from upstream context.
    """
    
    def __init__(self):
        self.logger = Logger("PromptIntelligenceEngine")
        
        # Variable patterns to detect (order matters - more specific first)
        # Patterns are checked in order, so simple patterns before complex ones
        self.variable_patterns = [
            # Simple variables with default values (most specific)
            r'\{\{\s*(\w+):([^}]+)\}\}',  # {{variable_name:default_value}}
            r'\{\{\s*(\w+)\.(\w+):([^}]+)\}\}',  # {{agent_id.variable_name:default}}
            # Prefixed variables (agent_id.variable_name)
            r'\{\{\s*(\w+)\.(\w+)\s*\}\}',  # {{agent_id.variable_name}}
            # Simple variables (backward compatible)
            r'\{\{\s*(\w+)\s*\}\}',  # {{variable_name}} with optional whitespace
            # Context.get() pattern
            r'\{\{\s*context\.get\([\'"](\w+)[\'"]\)',  # {{ context.get('variable_name')
            # Jinja2 filters
            r'\{\{\s*(\w+)\s*\|\s*\w+',  # {{variable_name | filter}}
            # Expressions (catch-all - must be last)
            r'\{\{\s*([^}]+)\}\}',  # {{expression}} - any content between {{}}
        ]
        
        # Variables that are truly system-level and always available
        # These should not appear in INPUTS tab even if used in YAML templates
        # Note: user_text is NOT in this list - if it's explicitly used in inputs section, it should appear in INPUTS tab
        self.system_variables = {
            "context", "pipeline_data"  # These are framework-level, not user variables
        }
        
        # Jinja2 built-in variables that should not be treated as user variables
        # These are only available in specific contexts (e.g., loop.index0 inside {% for %} loops)
        # and should not appear in INPUTS tab or be resolved from context
        self.jinja2_builtins = {
            "loop.index0", "loop.index", "loop.first", "loop.last", "loop.length",
            "loop.revindex", "loop.revindex0", "loop.cycle", "loop.depth", "loop.depth0",
            "loop.previtem", "loop.nextitem"
        }
        
        # Loop context variables (injected by LoopRunner, e.g., supplier_loop.index)
        # These are runtime-injected context variables, not user variables
        # Pattern: <loop_context_key>.index, <loop_context_key>.iteration, etc.
        self.loop_context_patterns = [
            r'^\w+_loop\.(index|iteration)$',  # e.g., supplier_loop.index, supplier_loop.iteration
        ]
    
    def analyze_agent_config(self, agent_config: Dict[str, Any], project_dir: Optional[Path] = None, agent_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze agent configuration to understand its requirements.
        
        Args:
            agent_config: Agent configuration from pipeline.yml
            project_dir: Base directory for resolving file paths
            agent_context: Rich context including pipeline structure, upstream data, etc.
            
        Returns:
            Dictionary containing analysis results
        """
        agent_id = agent_config.get("id", "unknown")
        agent_type = agent_config.get("type", "unknown")
        
        self.logger.info(f"Analyzing {agent_type} agent: {agent_id} with Prompt Intelligence Engine")
        
        analysis = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "variables": [],
            "prompt_variables": [],
            "task_variables": [],
            "custom_variables": [],
            "unknown_variables": [],  # Variables detected but value source unclear
            "generation_hints": []
        }
        
        # Store project_dir for file resolution
        self.project_dir = Path(project_dir) if project_dir else None
        
        # Analyze prompt configuration (for non-framework-specific prompts)
        if "prompt" in agent_config:
            prompt_vars = self._analyze_prompt_config(agent_config["prompt"], f"prompt for {agent_id}")
            analysis["prompt_variables"] = prompt_vars
            analysis["variables"].extend(prompt_vars)
            
        # Analyze CrewAI-specific configuration
        if agent_type == "crewai":
            task_vars = self._analyze_crewai_config(agent_config, agent_id)
            analysis["task_variables"] = task_vars
            analysis["variables"].extend(task_vars)
        else:
            prompt_vars = self._analyze_instruction_inputs_config(agent_config, agent_id)
            analysis["prompt_variables"] = prompt_vars
            analysis["variables"].extend(prompt_vars)
        
        # Identify custom variables (not in common sets)
        # VariableInfo.name is already the content (without {{}}), so use it directly
        all_var_names = {var.name for var in analysis["variables"]}
        custom_vars = all_var_names - self.system_variables
        analysis["custom_variables"] = sorted(list(custom_vars))
        
        # Identify unknown variables (variables that can't be determined)
        unknown_vars = []
        for var in analysis["variables"]:
            if var.name in custom_vars:
                # Check if we can suggest a reasonable default
                suggested_value = self._suggest_default_value(var.name)
                if self._is_truly_unknown_variable(var.name, suggested_value):
                    unknown_vars.append(var.name)
        
        analysis["unknown_variables"] = unknown_vars
        
        # Generate hints for code generation
        analysis["generation_hints"] = self._generate_code_hints(analysis)
        
        
        for var in analysis["variables"]:
            self.logger.input(f"Variable: {var.name}") 

        self.logger.success(f"Prompt Intelligence Engine analysis complete: {len(analysis['variables'])} variables found")
        
        return analysis 
    
    def _analyze_prompt_config(self, prompt_config: Dict[str, Any], context: str) -> List[VariableInfo]:
        """Analyze prompt configuration for variables"""
        variables = []
        
        # Handle inline prompts
        if "inline" in prompt_config:
            inline_text = prompt_config["inline"]
            vars_found = self._extract_variables_from_text(inline_text, context)
            variables.extend(vars_found)
            
            # Also analyze for output requirements
            output_structure = self._extract_output_structure_from_text(inline_text, context)
            
            # Store this information in the variables for later use
            for var in vars_found:
                var.output_structure = output_structure
        
        # Handle file-based prompts
        if "file" in prompt_config:
            file_path = prompt_config["file"]
            vars_found = self._extract_variables_from_file(file_path, context)
            variables.extend(vars_found)
        
        # Handle Jinja templates
        if "jinja" in prompt_config:
            jinja_path = prompt_config["jinja"]
            vars_found = self._extract_variables_from_file(jinja_path, context)
            variables.extend(vars_found)
        
        return variables
    
    def _analyze_crewai_config(self, agent_config: Dict[str, Any], agent_id: str) -> List[VariableInfo]:
        """Analyze CrewAI-specific configuration for variables"""
        variables = []
        
        # Check if CrewAI fields are nested under 'prompt' (new structure)
        prompt_config = agent_config.get("prompt", {})
        
        # Analyze role, goal, backstory for variables
        for field in ["role", "goal", "backstory"]:
            if field in prompt_config:  # Look under prompt, not top-level
                field_value = prompt_config[field]
                if isinstance(field_value, dict) and "inline" in field_value:
                    inline_text = field_value["inline"]
                    vars_found = self._extract_variables_from_text(inline_text, f"{field} for {agent_id}")
                    variables.extend(vars_found)
        
        # Analyze task configuration
        if "task" in prompt_config:  # Look under prompt, not top-level
            task_config = prompt_config["task"]
            # Handle nested description structure for CrewAI tasks
            if isinstance(task_config, dict) and "description" in task_config:
                task_vars = self._analyze_prompt_config(task_config["description"], f"task.description for {agent_id}")
                variables.extend(task_vars)
            else:
                task_vars = self._analyze_prompt_config(task_config, f"task for {agent_id}")
                variables.extend(task_vars)
        
        return variables

    def _analyze_instruction_inputs_config(self, agent_config: Dict[str, Any], agent_id: str) -> List[VariableInfo]:
        """Analyze system and user_input specific configuration for variables"""
        variables = []
        
        # Analyze prompt configuration with system/user_input sections
        if "prompt" in agent_config:
            prompt_config = agent_config["prompt"]
            
            # Handle instruction section (static, no variables)
            if "instruction" in prompt_config:
                instruction_config = prompt_config["instruction"]
                self.logger.debug(f"Found instruction prompt for {agent_id} - static content, no variables")
                
                # Could analyze for output structure, but no variables
                if isinstance(instruction_config, dict) and "inline" in instruction_config:
                    _ = self._extract_output_structure_from_text(instruction_config["inline"], f"instruction for {agent_id}")
                    # Store output structure for later use if needed
            
            # Handle inputs section (may contain variables)
            if "inputs" in prompt_config:
                inputs_config = prompt_config["inputs"]
                vars_found = self._analyze_prompt_config(inputs_config, f"inputs for {agent_id}")
                variables.extend(vars_found)
                self.logger.debug(f"Found inputs prompt for {agent_id} - analyzed for variables")
        
        return variables
    
    def _extract_variables_from_text(self, text: str, context: str) -> List[VariableInfo]:
        """Extract variables from text using pattern matching"""
        variables = []
        seen_variables = set()  # Track to avoid duplicates
        
        # First, identify Jinja2 {% set %} variables to trace back to source variables
        # Pattern: {% set local_var = source_var %} or {% set local_var = [source_var] %}
        # Also handle nested assignments like {% set supplier_data = item.supplier if ... %}
        set_var_to_source = {}  # e.g., {"requirements_evaluator_list": "rfp_rsp_eval_requirements_evaluator"}
        set_var_to_loop_var = {}  # e.g., {"supplier_data": "item"} - tracks {% set %} vars that reference loop variables
        
        # Pattern 1: Simple assignments
        set_patterns = [
            r'{%\s*set\s+(\w+)\s*=\s*(\w+)\s*%}',  # {% set var = source %}
            r'{%\s*set\s+(\w+)\s*=\s*\[(\w+)\]\s*%}',  # {% set var = [source] %}
        ]
        for pattern in set_patterns:
            for match in re.finditer(pattern, text):
                local_var = match.group(1)
                source_var = match.group(2)
                # Only map if source_var looks like an upstream agent variable (contains underscore or is a known pattern)
                # This helps avoid mapping to Jinja2 built-ins or other local variables
                if '_' in source_var or '.' in source_var:
                    set_var_to_source[local_var] = source_var
                    self.logger.debug(f"Found Jinja2 set variable in {context}: {local_var} = {source_var}")
        
        # Pattern 2: Nested assignments inside loops (e.g., {% set supplier_data = item.supplier if ... %})
        # Find all {% for %} blocks first to know which variables are loop variables
        loop_vars_in_template = set()
        # Pattern to match {% for var in ... %} (handles range(), variables, .items(), etc.)
        # Handles both single var and comma-separated vars (e.g., "instance_id, instance_data")
        for_match_prelim = re.finditer(r'{%\s*for\s+([^%]+?)\s+in\s+[^%]+%}', text)
        for match in for_match_prelim:
            loop_vars_str = match.group(1).strip()
            # Handle comma-separated loop variables (e.g., "instance_id, instance_data")
            loop_var_parts = [v.strip() for v in loop_vars_str.split(',')]
            for loop_var in loop_var_parts:
                loop_vars_in_template.add(loop_var)
        
        # Track which {% set %} variables are defined inside {% for %} blocks
        # Find all {% for %} ... {% endfor %} blocks and identify {% set %} variables inside them
        vars_set_inside_loops = set()
        # Pattern to match {% for var in ... %} ... {% endfor %} (handles range(), variables, .items(), etc.)
        # Handles both single var and comma-separated vars (e.g., "instance_id, instance_data")
        for_match_blocks = re.finditer(r'{%\s*for\s+([^%]+?)\s+in\s+[^%]+%}(.*?){%\s*endfor\s*%}', text, re.DOTALL)
        for match in for_match_blocks:
            loop_vars_str = match.group(1).strip()  # Can be single var or "var1, var2"
            loop_content = match.group(2)  # Content inside the loop
            # Parse loop variables (can be single or comma-separated)
            loop_var_parts = [v.strip() for v in loop_vars_str.split(',')]
            loop_vars_list = loop_var_parts  # All loop variables in this block
            # Find all {% set %} variables inside this loop block
            set_inside_loop = re.finditer(r'{%\s*set\s+(\w+)\s*=', loop_content)
            for set_match in set_inside_loop:
                var_name = set_match.group(1)
                vars_set_inside_loops.add(var_name)
                self.logger.debug(f"Found variable set inside loop in {context}: {var_name} (defined inside {{% for %}} block with loop vars: {loop_vars_list})")
        
        # Add all variables set inside loops to set_var_to_loop_var (regardless of what they're assigned to)
        for var_name in vars_set_inside_loops:
            if var_name not in set_var_to_loop_var:
                # Mark as loop variable (no direct loop var reference, but set inside loop)
                set_var_to_loop_var[var_name] = None
                self.logger.debug(f"Marked variable '{var_name}' as loop variable (set inside {{% for %}} block)")
        
        # Now find {% set %} variables that reference loop variables
        nested_set_pattern = r'{%\s*set\s+(\w+)\s*=\s*(\w+)(?:\.\w+)?(?:\s+if\s+[^%]+)?\s*%}'  # {% set var = loop_var.field if ... %}
        for match in re.finditer(nested_set_pattern, text):
            set_var = match.group(1)
            potential_loop_var = match.group(2)
            # If variable references a loop variable, mark it with that loop var
            if potential_loop_var in loop_vars_in_template:
                set_var_to_loop_var[set_var] = potential_loop_var
                self.logger.debug(f"Found nested set variable in {context}: {set_var} = {potential_loop_var} (loop variable)")
        
        # Identify loop variable names and their corresponding list variables from {% for %} blocks
        # Pattern: {% for loop_var in list_var %} ... {% endfor %}
        # Store mapping: loop_var -> (list_var, actual_source_var)
        # Also map nested {% set %} variables that reference loop variables
        loop_var_to_list = {}  # e.g., {"eval_result": ("requirements_evaluator_list", "rfp_rsp_eval_requirements_evaluator")}
        nested_var_to_loop_var = {}  # e.g., {"supplier_data": "item"} - maps nested vars to their loop vars
        
        # Pattern to match {% for var in ... %} and extract both loop var and list expression
        # Handles:
        # - Simple: {% for i in list %}
        # - Function calls: {% for i in range(...) %}
        # - Dictionary items: {% for instance_id, instance_data in agent_instances.items() %}
        for_match = re.finditer(r'{%\s*for\s+([^%]+?)\s+in\s+([^%]+?)\s*%}', text)
        for match in for_match:
            loop_vars_str = match.group(1).strip()  # Can be single var or "var1, var2"
            list_expr = match.group(2).strip()  # Can be a variable or expression like "range(...)" or "agent.items()"
            
            # Handle dictionary .items() pattern: {% for key_var, value_var in agent_instances.items() %}
            # This pattern can have any variable names, not just instance_id/instance_data
            if '.items()' in list_expr:
                # Extract base variable before .items()
                base_var = list_expr.replace('.items()', '').strip()
                # Parse loop variables (can be single or comma-separated)
                # Generic handling: split by comma and add ALL loop variables to loop_var_to_list
                loop_var_parts = [v.strip() for v in loop_vars_str.split(',')]
                # Add all loop variables from the comma-separated list
                # For .items(), typically there are 2 variables (key, value), but we handle any number generically
                for loop_var in loop_var_parts:
                    loop_var_to_list[loop_var] = (base_var, base_var)
                self.logger.debug(f"Found dictionary items loop in {context}: {loop_var_parts} iterate over {base_var}.items()")
            else:
                # Regular loop pattern: {% for loop_var in list_expr %}
                loop_var = loop_vars_str.split(',')[0].strip()  # Take first if comma-separated
                # Extract the base variable from the expression (e.g., "math_repeater_parser.problem_count" from "range(math_repeater_parser.problem_count)")
                # For simple cases, list_expr is the variable name
                # For function calls, extract the argument
                list_var = list_expr
                if '(' in list_expr and ')' in list_expr:
                    # Extract argument from function call (e.g., "range(math_repeater_parser.problem_count)" -> "math_repeater_parser.problem_count")
                    arg_match = re.search(r'\(([^)]+)\)', list_expr)
                    if arg_match:
                        list_var = arg_match.group(1).strip()
                # Check if list_var is a Jinja2 {% set %} variable - if so, use the source variable
                actual_source = set_var_to_source.get(list_var, list_var)
                loop_var_to_list[loop_var] = (list_var, actual_source)
                self.logger.debug(f"Found loop variable in {context}: {loop_var} iterates over {list_expr} (source: {actual_source})")
        
        # Map nested {% set %} variables to their loop variables and source lists
        for nested_var, loop_var in set_var_to_loop_var.items():
            if loop_var is None:
                # Variable is set inside loop but doesn't directly reference a loop variable
                # Find the loop variable from the containing loop (use the first loop var found)
                # This is a fallback - ideally we'd track which loop contains which set statements
                if loop_var_to_list:
                    # Use the first loop variable as a placeholder
                    first_loop_var = list(loop_var_to_list.keys())[0]
                    list_var, actual_source = loop_var_to_list[first_loop_var]
                    nested_var_to_loop_var[nested_var] = (first_loop_var, list_var, actual_source)
                    self.logger.debug(f"Found variable set inside loop in {context}: {nested_var} -> loop var: {first_loop_var}, list: {list_var}, source: {actual_source}")
            elif loop_var in loop_var_to_list:
                list_var, actual_source = loop_var_to_list[loop_var]
                nested_var_to_loop_var[nested_var] = (loop_var, list_var, actual_source)
                self.logger.debug(f"Found nested variable in {context}: {nested_var} -> loop var: {loop_var}, list: {list_var}, source: {actual_source}")
        
        # Track which loop variables are used (even in expressions) so we can expand them for INPUTS tab
        # This is separate from adding them as variables - we want to expand them even if they're in expressions
        # For .items() patterns, we only expand the VALUE variable (second one), not the KEY variable (first one)
        loop_vars_to_expand_tracking = {}  # {loop_var_name: source_var}
        
        # Track which variables are keys vs values in .items() patterns
        # For {% for key_var, value_var in dict.items() %}, key_var is at index 0, value_var is at index 1
        items_pattern_key_vars = set()  # Variables that are keys in .items() patterns (should NOT be expanded)
        items_pattern_value_vars = set()  # Variables that are values in .items() patterns (SHOULD be expanded)
        
        # Identify key vs value variables in .items() patterns
        for_match_items = re.finditer(r'{%\s*for\s+([^%]+?)\s+in\s+([^%]+?)\.items\(\)\s*%}', text)
        for match in for_match_items:
            loop_vars_str = match.group(1).strip()
            base_var = match.group(2).strip()
            loop_var_parts = [v.strip() for v in loop_vars_str.split(',')]
            if len(loop_var_parts) >= 2:
                # First variable is the key, second is the value
                key_var = loop_var_parts[0]
                value_var = loop_var_parts[1]
                items_pattern_key_vars.add(key_var)
                items_pattern_value_vars.add(value_var)
                self.logger.debug(f"Identified .items() pattern: key='{key_var}', value='{value_var}' for dict '{base_var}'")
        
        # Extract all {{...}} blocks first
        all_matches = []
        for pattern in self.variable_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                full_match = match.group(0)  # Full {{...}} block
                if full_match not in seen_variables:
                    seen_variables.add(full_match)
                    all_matches.append((full_match, match))
        
        # First pass: Track loop variables even in expressions (for expansion)
        # For .items() patterns, we expand the VALUE variable (e.g., solver_data) but not the KEY variable (e.g., instance_id)
        # This allows showing solver_data[0], solver_data[1], etc. in the INPUTS tab
        for full_match, match in all_matches:
            content = full_match.strip('{}').strip()
            content_parts = re.split(r'[.\s|]', content)
            
            # Check if it references a nested variable (e.g., supplier_data)
            if content_parts and content_parts[0] in nested_var_to_loop_var:
                nested_var = content_parts[0]
                loop_var, list_var, source_var = nested_var_to_loop_var[nested_var]
                # Check if this is from a .items() pattern
                if loop_var in loop_var_to_list:
                    list_var_check, source_var_check = loop_var_to_list[loop_var]
                    # If list_var equals source_var, it's from .items() pattern
                    if list_var_check == source_var_check and list_var_check == source_var:
                        # For .items() patterns, only expand VALUE variables, not KEY variables
                        if nested_var in items_pattern_value_vars:
                            self.logger.debug(f"Allowing expansion of .items() VALUE variable '{nested_var}' (will expand dictionary values)")
                            loop_vars_to_expand_tracking[nested_var] = source_var
                        elif nested_var in items_pattern_key_vars:
                            self.logger.debug(f"Skipping expansion of .items() KEY variable '{nested_var}' (keys are not expanded)")
                        continue
                loop_vars_to_expand_tracking[nested_var] = source_var
            # Check if it references a direct loop variable (e.g., eval_result, score_result, solver_data)
            elif content_parts and content_parts[0] in loop_var_to_list:
                loop_var = content_parts[0]
                list_var, source_var = loop_var_to_list[loop_var]
                # For .items() patterns, list_var equals source_var
                if list_var == source_var:
                    # This is from .items() pattern - only expand VALUE variable, not KEY variable
                    if loop_var in items_pattern_value_vars:
                        self.logger.debug(f"Allowing expansion of .items() VALUE variable '{loop_var}' (will expand dictionary values)")
                        loop_vars_to_expand_tracking[loop_var] = source_var
                    elif loop_var in items_pattern_key_vars:
                        self.logger.debug(f"Skipping expansion of .items() KEY variable '{loop_var}' (keys are not expanded)")
                    # Continue to next match (don't add to tracking for key vars)
                    continue
                else:
                    # Regular loop (not .items()) - always expand
                    self.logger.debug(f"Allowing expansion of regular loop variable '{loop_var}' (will expand list values)")
                    loop_vars_to_expand_tracking[loop_var] = source_var
        
        # Process each unique match
        for full_match, match in all_matches:
            # Extract content between {{ and }}
            content = full_match.strip('{}').strip()
            
            # Check if this variable is a loop variable or references a loop variable
            # Expressions that reference loop variables (e.g., "supplier_data.supplier_id if supplier_data.supplier_id else ...")
            # should NOT be treated as top-level variables for INPUTS tab - they only exist inside {% for %} loops
            loop_var_name = None
            actual_source_var = None
            is_loop_var_expression = False
            
            # First check if it's a nested {% set %} variable (e.g., supplier_data, solver_result)
            content_parts = re.split(r'[.\s|]', content)
            if content_parts and content_parts[0] in nested_var_to_loop_var:
                nested_var = content_parts[0]
                loop_var, list_var, source_var = nested_var_to_loop_var[nested_var]
                loop_var_name = nested_var  # Use nested var name for expansion
                actual_source_var = source_var
                # ALL references to nested loop variables should be filtered out (they only exist inside loops)
                is_loop_var_expression = True
                self.logger.debug(f"Filtering out nested loop variable '{content}' in {context} (only valid inside {{% for %}} loop)")
            # Also check if variable is set inside a loop (even if not in nested_var_to_loop_var mapping)
            elif content_parts and content_parts[0] in set_var_to_loop_var:
                # This variable was set inside a loop - filter it out as it's only valid inside the loop
                is_loop_var_expression = True
                self.logger.debug(f"Filtering out variable '{content}' in {context} (set inside {{% for %}} loop, only valid inside loop)")
            elif loop_var_to_list:
                # Check if content starts with a direct loop variable name (e.g., i, eval_result, score_result)
                if content_parts and content_parts[0] in loop_var_to_list:
                    loop_var_name = content_parts[0]
                    list_var, source_var = loop_var_to_list[loop_var_name]
                    actual_source_var = source_var
                    # ALL references to loop variables should be filtered out (they only exist inside loops)
                    # This includes simple references like "i" and expressions like "i + 1"
                    is_loop_var_expression = True
                    self.logger.debug(f"Filtering out loop variable '{content}' in {context} (only valid inside {{% for %}} loop)")
            
            # Skip complex expressions that reference loop variables - they only exist inside {% for %} loops
            if is_loop_var_expression:
                continue
            
            # Skip nested context.upstream[...] patterns - these are internal context access, not real variables
            # Examples: context.upstream[instance_id].parsed.problem_text, context.upstream[agent_id].parsed
            if content.strip().startswith('context.upstream'):
                self.logger.debug(f"Filtering out nested context.upstream access '{content}' in {context} (internal context access, not a real variable)")
                continue
            
            # Determine variable type and extract components
            var_info = self._parse_variable_content(content, context, full_match)
            if var_info:
                # Mark loop variables so they can be expanded in the INPUTS tab
                # Use the actual source variable (upstream agent) instead of Jinja2 local variable
                if loop_var_name and actual_source_var and not is_loop_var_expression:
                    var_info.loop_variable = loop_var_name
                    var_info.loop_list_variable = actual_source_var  # Use actual source, not Jinja2 local
                variables.append(var_info)
        
        # Store loop vars to expand for code generation (even if they were in expressions)
        # This will be accessed in generate_agent_variables_code
        # This tracks which loop variables should be expanded for INPUTS tab
        # For .items() patterns, only VALUE variables are tracked (KEY variables are excluded)
        if loop_vars_to_expand_tracking:
            # Store as a class-level attribute that can be accessed during code generation
            self._loop_vars_to_expand = loop_vars_to_expand_tracking
            self.logger.debug(f"Stored {len(loop_vars_to_expand_tracking)} loop variables for expansion: {list(loop_vars_to_expand_tracking.keys())}")
        
        return variables
    
    def _parse_variable_content(self, content: str, context: str, full_match: str) -> Optional[VariableInfo]:
        """Parse variable content and create VariableInfo with appropriate type
        
        Args:
            content: Content between {{}} (e.g., "user_text", "agent_id.field", "agent_id.field if condition else default")
            context: Context where variable was found
            full_match: Full {{...}} block for reference
        
        Returns:
            VariableInfo with name set to content (for Jinja2 dict key), or None if it's a Jinja2 built-in
        """
        # Filter out Jinja2 built-in variables (e.g., loop.index0, loop.index, etc.)
        # These are only available in specific contexts and should not be treated as user variables
        if self._is_jinja2_builtin(content):
            self.logger.debug(f"Skipping Jinja2 built-in variable: {content}")
            return None
        
        # Check if it's an expression (contains operators/keywords)
        if self._is_expression(content):
            population_method = f"self._resolve_input_variable(context, '{content}')"
            suggested_value = population_method
            
            return VariableInfo(
                name=content,  # Jinja2 dict key is the content (without {{}})
                source="prompt",
                context=context,
                population_method=population_method,
                suggested_value=suggested_value,
                upstream_agent=None,
                variable_type="expression",
                expression=content
            )
        
        # Check if it has default value syntax: variable:default
        if ':' in content and not self._is_expression(content):
            parts = content.split(':', 1)
            var_part = parts[0].strip()
            default_value = parts[1].strip()
            
            # Check if prefixed: agent_id.variable_name:default
            if '.' in var_part:
                agent_id, var_name = var_part.split('.', 1)
                population_method = f"self._get_variable_from_context(context, '{var_part}') or {default_value}"
                suggested_value = population_method
                
                return VariableInfo(
                    name=content,  # Jinja2 dict key includes default syntax
                    source="prompt",
                    context=context,
                    population_method=population_method,
                    suggested_value=suggested_value,
                    upstream_agent=agent_id,
                    default_value=default_value,
                    variable_type="prefixed",
                    agent_id=agent_id,
                    variable_name=var_name
                )
            else:
                # Simple variable with default
                population_method = f"self._get_variable_from_context(context, '{var_part}') or {default_value}"
                suggested_value = population_method
                
                return VariableInfo(
                    name=content,  # Jinja2 dict key includes default syntax
                    source="prompt",
                    context=context,
                    population_method=population_method,
                    suggested_value=suggested_value,
                    upstream_agent=None,
                    default_value=default_value,
                    variable_type="simple"
                )
        
        # Check if prefixed: agent_id.variable_name
        if '.' in content and not self._is_expression(content):
            parts = content.split('.')
            agent_id = parts[0]
            var_name = '.'.join(parts[1:])  # Join remaining parts in case of multi-part paths
            
            # Check if this is an array-indexed variable with loop context (e.g., supplier_response_paths[supplier_loop.index])
            # These should be left for Jinja2 to evaluate dynamically, not pre-resolved
            if '[' in var_name and ']' in var_name:
                bracket_start = var_name.find('[')
                bracket_end = var_name.find(']')
                if bracket_start < bracket_end:
                    index_expr = var_name[bracket_start + 1:bracket_end]
                    # Check if index expression contains loop context variable
                    if self._is_loop_context_variable(index_expr):
                        # This is an array-indexed variable with loop context - treat as expression for Jinja2 to evaluate
                        # We'll provide the base array and let Jinja2 evaluate the indexing
                        population_method = f"self._resolve_input_variable(context, '{content}')"
                        suggested_value = population_method
                        
                        return VariableInfo(
                            name=content,  # Jinja2 dict key is the full expression
                            source="prompt",
                            context=context,
                            population_method=population_method,
                            suggested_value=suggested_value,
                            upstream_agent=agent_id,
                            variable_type="expression",  # Treat as expression so Jinja2 evaluates it
                            expression=content
                        )
            
            # Check if this is a multi-part path (3+ parts, e.g., gate_id.context_key.field)
            # Use _resolve_input_variable for multi-part paths as it can handle nested paths via expression evaluator
            if len(parts) > 2:
                population_method = f"self._resolve_input_variable(context, '{content}')"
                suggested_value = population_method
                
                return VariableInfo(
                    name=content,  # Jinja2 dict key is the full path
                    source="prompt",
                    context=context,
                    population_method=population_method,
                    suggested_value=suggested_value,
                    upstream_agent=agent_id,
                    variable_type="prefixed",  # Still prefixed, but uses _resolve_input_variable
                    agent_id=agent_id,
                    variable_name=var_name
                )
            
            # Standard 2-part prefixed variable (agent_id.variable_name)
            population_method, suggested_value = self._suggest_population_method(content, context)
            
            return VariableInfo(
                name=content,  # Jinja2 dict key is agent_id.variable_name
                source="prompt",
                context=context,
                population_method=population_method,
                suggested_value=suggested_value,
                upstream_agent=agent_id,
                variable_type="prefixed",
                agent_id=agent_id,
                variable_name=var_name
            )
        
        # Simple variable
        population_method, suggested_value = self._suggest_population_method(content, context)
        
        return VariableInfo(
            name=content,  # Jinja2 dict key is just the variable name
            source="prompt",
            context=context,
            population_method=population_method,
            suggested_value=suggested_value,
            upstream_agent=None,
            variable_type="simple"
        )
    
    def _is_loop_context_variable(self, content: str) -> bool:
        """Check if content is a loop context variable (e.g., supplier_loop.index)
        
        Args:
            content: Variable content to check
            
        Returns:
            True if it's a loop context variable
        """
        # Check for loop context variables (e.g., "supplier_loop.index")
        for pattern in self.loop_context_patterns:
            if re.match(pattern, content):
                return True
        return False
    
    def _is_jinja2_builtin(self, content: str) -> bool:
        """Check if content is a Jinja2 built-in variable that should be filtered out
        
        Args:
            content: Variable content to check
            
        Returns:
            True if it's a Jinja2 built-in (e.g., loop.index0, loop.index, etc.) or loop context variable
        """
        # Check for exact matches (e.g., "loop.index0")
        if content in self.jinja2_builtins:
            return True
        
        # Check for loop context variables (e.g., "supplier_loop.index")
        if self._is_loop_context_variable(content):
            return True
        
        # Check for expressions containing Jinja2 built-ins (e.g., "loop.index0 + 1")
        # Split by operators and check if any part is a built-in
        # Split on common operators but keep the operators
        parts = re.split(r'(\s*[+\-*/%]\s*|\s+if\s+|\s+else\s+|\s+and\s+|\s+or\s+|\s+not\s+)', content, flags=re.IGNORECASE)
        for part in parts:
            part_stripped = part.strip()
            if part_stripped in self.jinja2_builtins:
                return True
            # Also check if part matches loop context pattern
            if self._is_loop_context_variable(part_stripped):
                return True
        
        return False
    
    def _is_expression(self, content: str) -> bool:
        """Check if content is an expression (contains operators/keywords)"""
        # Check for Jinja2 filter syntax (|)
        if '|' in content:
            return True
        expression_keywords = [' if ', ' else ', ' AND ', ' OR ', ' NOT ', ' == ', ' != ', ' > ', ' < ', ' >= ', ' <= ', 'len(', 'contains', 'starts_with', 'ends_with']
        content_upper = content.upper()
        return any(keyword.upper() in content_upper for keyword in expression_keywords)
    
    def _extract_output_structure_from_text(self, text: str, context: str) -> Dict[str, Any]:
        """Extract expected output structure from text content"""
        structure = {}
        
        # Look for JSON output examples
        json_pattern = r'\{[^{}]*"[^"]*"[^{}]*\}'
        json_matches = re.findall(json_pattern, text)
        
        for match in json_matches:
            # Skip Jinja2 template syntax (e.g., {% if ... %}, {{ variable }}, or expressions with operators)
            if '{%' in match or '{{' in match or any(op in match for op in [' and ', ' or ', ' == ', ' != ', ' >= ', ' <= ', ' > ', ' < ']):
                continue
            
            # Use JSONUtils for robust JSON parsing with automatic fixes
            try:
                parsed = JSONUtils.parse_json_from_text(match, expect_json=True)
                if isinstance(parsed, dict):
                    # Only keep simple string values, not template text
                    for key, value in parsed.items():
                        if isinstance(value, str) and not value.startswith('<') and not value.endswith('>'):
                            structure[key] = "string"
                        elif isinstance(value, str) and value.startswith('<') and value.endswith('>'):
                            # This is template text, extract the field name
                            _ = value.strip('<>').split()[0] if value.strip('<>') else key
                            structure[key] = "string"
            except ValueError:
                # Skip invalid JSON matches
                continue

        
        # Look for specific output field mentions
        output_patterns = [
            r'Output.*?\{([^}]+)\}',
            r'Return.*?\{([^}]+)\}',
            r'Expected.*?\{([^}]+)\}'
        ]
        
        for pattern in output_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Parse field names from the match
                field_pattern = r'"([^"]+)"'
                fields = re.findall(field_pattern, match)
                for field in fields:
                    # Only add if it's not template text
                    if not field.startswith('<') and not field.endswith('>'):
                        structure[field] = "string"
        
        return structure
    
    def _extract_variables_from_file(self, file_path: str, context: str) -> List[VariableInfo]:
        """Extract variables from file content"""
        try:
            # Resolve the file path relative to the base directory
            file_path_obj = Path(file_path)
            
            # If we have a project_dir, try to resolve relative to it first
            if hasattr(self, 'project_dir') and self.project_dir:
                full_path = self.project_dir / file_path
                if full_path.exists():
                    file_path_obj = full_path
                elif not file_path_obj.exists():
                    # Try common locations relative to project_dir
                    possible_paths = [
                        self.project_dir / file_path,
                        self.project_dir.parent / file_path,
                        Path(".") / file_path,
                        Path("projects/") / file_path,
                        Path("templates") / file_path
                    ]
                    
                    for path in possible_paths:
                        if path.exists():
                            file_path_obj = path
                            break
                    else:
                        self.logger.warning(f"Could not find file: {file_path} (project_dir: {self.project_dir})")
                        return []
            elif not file_path_obj.exists():
                # Try to find it in common locations
                possible_paths = [
                    Path("projects/") / file_path,
                    Path("templates") / file_path,
                    Path("prompts") / file_path,
                    Path(".") / file_path
                ]
                
                for path in possible_paths:
                    if path.exists():
                        file_path_obj = path
                        break
                else:
                    self.logger.warning(f"Could not find file: {file_path}")
                    return []
            
            # Read the file content
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.logger.debug(f"Reading file: {file_path_obj} ({len(content)} chars)")
            
            # Extract variables from the file content
            variables = self._extract_variables_from_text(content, f"file: {file_path}")
            
            # Also extract output structure
            output_structure = self._extract_output_structure_from_text(content, f"file: {file_path}")
            
            # Store this information in the variables
            for var in variables:
                var.output_structure = output_structure
            
            return variables
            
        except Exception as e:
            self.logger.warning(f"Failed to read file {file_path}: {e}")
            return []
    
    def _generate_code_hints(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate hints for code generation based on analysis"""
        hints = []
        
        agent_type = analysis["agent_type"]
        custom_vars = analysis["custom_variables"]
        unknown_vars = analysis["unknown_variables"]
        
        # Variable handling hints
        if custom_vars:
            hints.append(f"Custom variables detected: {', '.join(custom_vars)}")
            hints.append("Override get_agent_variables to populate custom variables")
        
        # Unknown variables hints
        if unknown_vars:
            hints.append(f"Unknown variables requiring user input: {', '.join(unknown_vars)}")
            hints.append("Check generated code for required fixes")
        
        # Prompt/task hints
        if analysis["prompt_variables"]:
            hints.append(f"Prompt variables: {len(analysis['prompt_variables'])}")
        if analysis["task_variables"]:
            hints.append(f"Task variables: {len(analysis['task_variables'])}")
        
        return hints
    
    def generate_agent_variables_code(self, analysis: Dict[str, Any], agent_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate code for the get_agent_variables method based on analysis.
        
        Args:
            analysis: Analysis result from analyze_agent_config
            agent_context: Rich context including pipeline structure, upstream data, etc.
            
        Returns:
            Python code string for the method
        """
        variables_list = analysis["variables"]
        unknown_vars = analysis["unknown_variables"]
        
        # Filter to only custom variables (exclude system variables)
        # Get cleaned names for comparison
        custom_var_names = analysis.get("custom_variables", [])
        custom_vars = [var for var in variables_list if var.name.strip('{}').strip() in custom_var_names or (var.variable_type == "expression" and var.expression in custom_var_names)]
        
        # Sort by variable name to maintain alphabetical order (matching analysis["custom_variables"] order)
        custom_vars.sort(key=lambda v: v.name)
        
        # IMPORTANT: Only variables from inputs section are detected and generated.
        # Instruction section is static and does not use variable rendering.
        # All variables in custom_vars are from inputs section (instruction variables are not detected).
        
        # Track which variable names came from inputs section (all of them, since instruction doesn't have variables)
        inputs_section_var_names = {var.name for var in custom_vars}  # All variables are from inputs section
        
        if not custom_vars:
            # Do not emit a return here; the stub template adds a single
            # return variables at the end to avoid duplicate returns.
            return """        # Get base variables from parent class
        variables = self._get_base_agent_variables(context)
        
        # No variables from inputs section, so INPUTS tab will be empty
        self._inputs_section_variables = set()"""
        
        # For loop variables, we need to expand them to show values for each iteration
        # Collect expanded variable names for INPUTS tab (e.g., eval_result[0], eval_result[1])
        expanded_var_names = set(inputs_section_var_names)
        loop_vars_to_expand = {}  # Track loop vars and their list vars for expansion
        
        # First, collect loop variables from VariableInfo objects (simple references)
        for var_info in custom_vars:
            if var_info.loop_variable and var_info.loop_list_variable:
                loop_var = var_info.loop_variable
                list_var = var_info.loop_list_variable
                loop_vars_to_expand[loop_var] = list_var
                # Add the original variable name (for Jinja2 rendering)
                # The expanded keys will be added dynamically at runtime
        
        # Also check if we tracked loop variables from expressions (they were filtered out but still need expansion)
        # These are stored in self._loop_vars_to_expand during _extract_variables_from_text
        if hasattr(self, '_loop_vars_to_expand') and self._loop_vars_to_expand:
            for loop_var, source_var in self._loop_vars_to_expand.items():
                if loop_var not in loop_vars_to_expand:
                    loop_vars_to_expand[loop_var] = source_var
                    self.logger.debug(f"Found loop variable '{loop_var}' in expressions - will expand for INPUTS tab using source '{source_var}'")
            # Clear after use to avoid stale data in next generation
            delattr(self, '_loop_vars_to_expand')
        
        # Convert to sorted list for deterministic code generation (sets have non-deterministic ordering)
        # We generate it as set(sorted_list) so the string representation is always the same
        inputs_section_var_names_sorted = sorted(inputs_section_var_names)
        
        # Generate code for custom variables - indented to match template placeholder (4 spaces)
        code_lines = [
            "# Get base variables from parent class",
            "        variables = self._get_base_agent_variables(context)",
            "",
            "        # Prompt Intelligence Engine detected these variables from inputs section:",
            "        # All variables are from inputs section (instruction section is static, no variables)",
            "        # Store which variables came from inputs section for INPUTS tab filtering",
        ]
        
        # Add code to expand loop variables and add their keys to _inputs_section_variables
        if loop_vars_to_expand:
            code_lines.append("        # Expand loop variables for INPUTS tab (show values for each iteration)")
            code_lines.append("        expanded_loop_vars = {}")
            for loop_var, list_var in loop_vars_to_expand.items():
                code_lines.append(f"        expanded_{loop_var} = self._expand_loop_variable(context, '{list_var}', '{loop_var}')")
                code_lines.append(f"        expanded_loop_vars.update(expanded_{loop_var})")
            code_lines.append("        # Combine original variable names with expanded loop variable keys")
            code_lines.append(f"        inputs_section_var_names_with_expanded = {repr(inputs_section_var_names_sorted)} + list(expanded_loop_vars.keys())")
            code_lines.append("        self._inputs_section_variables = set(inputs_section_var_names_with_expanded)")
        else:
            code_lines.append(f"        self._inputs_section_variables = set({repr(inputs_section_var_names_sorted)})")
        
        code_lines.extend([
            "",
            "        # Add variables from inputs section (for Jinja2 rendering)",
            "        variables.update({"
        ])
        
        for var_info in custom_vars:
            var_name = var_info.name  # This is the content (without {{}}) used as Jinja2 dict key
            
            if var_name in unknown_vars:
                # Mark unknown variables with explicit placeholder that will cause immediate error
                code_lines.append("            # ⚠️  VARIABLE DETECTED BUT VALUE UNKNOWN - USER MUST PROVIDE:")
                code_lines.append(f"            \"{var_name}\": \"VARIABLE_REQUIRES_USER_INPUT\",  # ← Immediate error")
            else:
                # Check if this is a loop variable - if so, expand it to show values for each iteration
                if var_info.loop_variable and var_info.loop_list_variable:
                    # This is a loop variable - resolve it by getting the list and expanding it
                    # For INPUTS tab, we'll show it as expanded keys (loop_var[0], loop_var[1], etc.)
                    # The expanded keys are already added to _inputs_section_variables above
                    # For Jinja2 rendering, we still need the original variable name
                    loop_var = var_info.loop_variable
                    list_var = var_info.loop_list_variable
                    code_lines.append(f"            # Loop variable: {loop_var} iterates over {list_var}")
                    code_lines.append("            # Expanded keys (loop_var[0], loop_var[1], etc.) are added to variables below")
                    code_lines.append(f"            # Note: Original variable '{var_name}' is for Jinja2 rendering inside {{% for %}} loop")
                    code_lines.append("            # For Jinja2, the loop variable exists only inside the {% for %} block, so we don't add it here")
                    code_lines.append("            # Expanded loop variable keys are added via expanded_loop_vars above")
                elif var_info.variable_type == "expression":
                    # Expression variables use _resolve_input_variable
                    # Escape single quotes in expression for Python string
                    expression_escaped = var_info.expression.replace("'", "\\'")
                    code_lines.append(f"            \"{var_name}\": self._resolve_input_variable(context, '{expression_escaped}'),")
                elif var_info.variable_type == "prefixed":
                    # Prefixed variables: Add them to variables dict so they show up in INPUTS tab.
                    # 
                    # Why we add them:
                    # - Users explicitly put {{math_strategist.steps}} in their YAML, so it should show in INPUTS tab
                    # - We resolve them using _get_variable_from_context() which gets the value from upstream agent
                    # 
                    # Note: Jinja2 can access these in two ways:
                    # 1. Via the explicit key: variables["math_strategist.steps"] (what we're adding here)
                    # 2. Via the agent dict: variables["math_strategist"]["steps"] (from _get_base_agent_variables())
                    # Both work, and the explicit key takes precedence in Jinja2 rendering.
                    prefixed_name = f"{var_info.agent_id}.{var_info.variable_name}"
                    # Check if this is a multi-part path (3+ parts) - use _resolve_input_variable for nested paths
                    if len(prefixed_name.split('.')) > 2:
                        # Multi-part path (e.g., gate_id.context_key.field) - use _resolve_input_variable
                        # which can handle nested paths via expression evaluator
                        code_lines.append(f"            \"{var_name}\": self._resolve_input_variable(context, '{prefixed_name}'),")
                    else:
                        # Standard 2-part path (agent_id.variable_name) - use _get_variable_from_context
                        code_lines.append(f"            \"{var_name}\": self._get_variable_from_context(context, '{prefixed_name}'),")
                else:
                    # Simple variables use existing logic
                    code_lines.append(f"            \"{var_name}\": {var_info.suggested_value},")
        
        code_lines.extend([
            "        })",
            "",
        ])
        
        # Add expanded loop variable keys to variables dict for INPUTS tab
        if loop_vars_to_expand:
            code_lines.append("        # Add expanded loop variable keys to variables dict for INPUTS tab display")
            code_lines.append("        variables.update(expanded_loop_vars)")
            code_lines.append("")
        
        # Note: Instance-specific variables from input_mapping are automatically added by
        # _get_base_agent_variables() via _add_instance_context_variables(), so no need to call it here
        
        return "\n".join(code_lines)
    
    def generate_population_logic(self, analysis: Dict[str, Any]) -> str:
        """Generate variable population logic with transparency"""
        custom_vars = analysis["custom_variables"]
        
        if not custom_vars:
            return "        # # No custom variables detected - using base implementation"
        
        logic = ["        # # How variables are populated:"]
        
        for var_name in custom_vars:
            # Everything comes from upstream now
            population_method = f"self._get_upstream_variable(context, 'auto', '{var_name}')"
            
            logic.append(f"        # # How '{var_name}' is populated:")
            logic.append(f"        # variables['{var_name}'] = {population_method}")
            logic.append("")
        
        return "\n".join(logic)
    
    def generate_override_examples(self, analysis: Dict[str, Any]) -> str:
        """Generate dynamic override examples based on actual variables"""
        custom_vars = analysis["custom_variables"]
        
        if not custom_vars:
            return "        # # No variables to override in this agent"
        
        examples = []
        for var_name in custom_vars:
            examples.extend([
                f"        # # Override '{var_name}' with custom logic:",
                f"        # variables['{var_name}'] = \"custom {var_name}\"  # ⚠️ Overrides automatic population",
                "        # # OR with computed value:",
                f"        # variables['{var_name}'] = self._custom_{var_name}_generator()  # ⚠️ Overrides automatic population",
                ""
            ])
        
        return "\n".join(examples)
    
    def generate_required_fixes(self, analysis: Dict[str, Any]) -> str:
        """Generate dynamic required fixes based on unknown variables"""
        unknown_vars = analysis["unknown_variables"]
        
        if not unknown_vars:
            return "        # # No unknown variables detected - all variables have clear value sources"
        
        fixes = []
        for var_name in unknown_vars:
            fixes.extend([
                f"        # # Fix for '{var_name}' (detected but value source unclear):",
                f"        # variables['{var_name}'] = self._calculate_value(data, context)",
                 "        # # OR get from specific source:",
                f"        # variables['{var_name}'] = data.get('{var_name}') or \"default_value\"",
                ""
            ])
        
        return "\n".join(fixes)
    
    def _suggest_default_value(self, var_name: str, agent_context: Optional[Dict[str, Any]] = None) -> str:
        """Suggest a reasonable default value for a variable based on intelligent analysis"""
        # All variables come from context - _get_variable_from_context handles main context, HITL, and upstream
        return f"self._get_variable_from_context(context, '{var_name}')"
    
    def _suggest_population_method(self, var_name: str, context: str, agent_context: Optional[Dict[str, Any]] = None) -> tuple[str, str]:
        """
        Suggest how to populate a variable based on intelligent analysis.
        
        Returns:
            tuple: (population_method, suggested_value)
        """
        # All variables come from context - _get_variable_from_context handles main context, HITL, and upstream
        population_method = f"self._get_variable_from_context(context, '{var_name}')"
        return population_method, population_method
    
    def _is_truly_unknown_variable(self, var_name: str, suggested_value: str) -> bool:
        """
        Determine if a variable is truly unknown (no clear population method).
        
        With our simplified approach, variables are only unknown if they can't be
        populated from context (main context, HITL, or upstream).
        """
        # Check if the suggested value is the standard context lookup pattern
        standard_context = f"self._get_variable_from_context(context, '{var_name}')"
        
        if suggested_value == standard_context:
            # This is a standard variable - NOT unknown
            return False
        else:
            # This has a custom population method - NOT unknown
            return False
    
    # Note: Execution method generation removed - base classes handle all execution logic
    # Generated agents now focus only on variable handling and optional customization 