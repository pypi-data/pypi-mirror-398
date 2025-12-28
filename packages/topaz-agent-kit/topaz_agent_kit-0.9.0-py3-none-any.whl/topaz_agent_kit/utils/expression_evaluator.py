"""Expression evaluator for conditional node execution.

Supports shorthand variable syntax that automatically resolves from context.

Supported Expression Types:
- Boolean: AND, OR, NOT
- Comparison: ==, !=, >, <, >=, <=
- Ternary: A if B else C (e.g., "value if condition else 'default'")
- String: contains, starts_with, ends_with
- Membership: IN, NOT IN
- Null checks: IS NULL, IS NOT NULL
- Functions: len(array)
- Grouping: Parentheses ()
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.json_utils import JSONUtils

def evaluate_expression(expression: str, context: Dict[str, Any]) -> bool:
    """Convenience function to evaluate expression string to boolean.
    
    Args:
        expression: Expression string to evaluate
        context: Context dictionary with agent outputs and root context
    
    Returns:
        bool: Evaluation result
    
    Raises:
        ValueError: If expression is invalid or variables not found
    
    Examples:
        evaluate_expression("score > 80", context)
        evaluate_expression("tier == 'gold' AND risk < 0.5", context)
        evaluate_expression("(amount > 1000 OR approved == true) AND status != 'blocked'", context)
    """
    evaluator = ExpressionEvaluator(context)
    return evaluator.evaluate(expression)


def evaluate_expression_value(expression: str, context: Dict[str, Any]) -> Any:
    """Convenience function to evaluate expression and return actual value.
    
    This is used for input variable expressions that need to return
    strings, numbers, or other types, not just booleans.
    
    Args:
        expression: Expression string to evaluate
        context: Context dictionary with agent outputs and root context
    
    Returns:
        Any: Evaluation result (can be string, number, bool, etc.)
    
    Raises:
        ValueError: If expression is invalid or variables not found
    
    Examples:
        evaluate_expression_value("parser_agent.user_text if parser_agent.user_text else 'default'", context)
        evaluate_expression_value("len(upstream_agent.items) if upstream_agent.items else 0", context)
    """
    evaluator = ExpressionEvaluator(context)
    return evaluator.evaluate_value(expression)


class ExpressionEvaluator:
    """Evaluate conditional expressions with shorthand variable syntax."""
    
    def __init__(self, context: Dict[str, Any]):
        self.context = context
        self.logger = Logger("ExpressionEvaluator")
    
    def evaluate(self, expression: str) -> bool:
        """Evaluate expression string to boolean.
        
        Args:
            expression: Expression string (e.g., "score > 80 AND tier == 'gold'")
        
        Returns:
            bool: Evaluation result
        
        Raises:
            ValueError: If expression is invalid
        """
        # Tokenize
        tokens = self._tokenize(expression)
        self.logger.debug("Tokens: {}", tokens)
        
        # Parse
        ast = self._parse(tokens)
        self.logger.debug("AST: {}", ast)
        
        # Evaluate
        result = self._evaluate_node(ast)
        self.logger.debug("Result: {}", result)
        
        return bool(result)
    
    def evaluate_value(self, expression: str) -> Any:
        """Evaluate expression string and return actual value (not just boolean).
        
        This is used for input variable expressions that need to return
        strings, numbers, or other types, not just booleans.
        
        Args:
            expression: Expression string (e.g., "parser_agent.user_text if parser_agent.user_text else 'default'")
        
        Returns:
            Any: Evaluation result (can be string, number, bool, etc.)
        
        Raises:
            ValueError: If expression is invalid
        """
        # Tokenize
        tokens = self._tokenize(expression)
        self.logger.debug("Tokens: {}", tokens)
        
        # Parse
        ast = self._parse(tokens)
        self.logger.debug("AST: {}", ast)
        
        # Evaluate (returns actual value, not coerced to bool)
        result = self._evaluate_node(ast)
        self.logger.debug("Result: {}", result)
        
        return result
    
    def _tokenize(self, expression: str) -> List[str]:
        """Split expression into tokens.
        
        Handles:
        - Operators: ==, !=, >=, <=, >, <, AND, OR, NOT
        - Ternary: IF, ELSE (for A if B else C expressions)
        - Literals: strings (single/double quotes), numbers, booleans
        - Identifiers: agent_id.field.nested (variable references)
        - Parentheses: ( )
        """
        tokens = []
        i = 0
        expression = expression.strip()
        
        while i < len(expression):
            # Skip whitespace
            if expression[i].isspace():
                i += 1
                continue
            
            # Handle 2-character operators
            if i + 1 < len(expression):
                two_char = expression[i:i+2]
                if two_char in ['==', '!=', '>=', '<=']:
                    tokens.append(two_char)
                    i += 2
                    continue
            
            # Handle multi-character operators
            if expression[i:i+3].upper() == 'AND':
                tokens.append('AND')
                i += 3
                continue
            if expression[i:i+2].upper() == 'OR':
                tokens.append('OR')
                i += 2
                continue
            if expression[i:i+3].upper() == 'NOT':
                tokens.append('NOT')
                i += 3
                continue
            
            # Handle 'IS NULL', 'IS NOT NULL'
            if i + 7 <= len(expression) and expression[i:i+7].upper() == 'IS NULL':
                tokens.append('IS NULL')
                i += 7
                continue
            if i + 11 <= len(expression) and expression[i:i+11].upper() == 'IS NOT NULL':
                tokens.append('IS NOT NULL')
                i += 11
                continue
            
            # Handle 'NOT IN' (only if followed by whitespace or end)
            if i + 6 <= len(expression) and expression[i:i+6].upper() == 'NOT IN':
                # Check that it's not part of a longer identifier
                if i + 6 >= len(expression) or not (expression[i+6].isalnum() or expression[i+6] == '_' or expression[i+6] == '.'):
                    tokens.append('NOT IN')
                    i += 6
                    continue
            # Handle 'IN' (only if followed by whitespace or end, not part of identifier)
            if i + 2 <= len(expression) and expression[i:i+2].upper() == 'IN':
                # Check that it's not part of a longer identifier
                if i + 2 >= len(expression) or not (expression[i+2].isalnum() or expression[i+2] == '_' or expression[i+2] == '.'):
                    tokens.append('IN')
                    i += 2
                    continue
            
            # Handle 'IF' keyword (for ternary expressions: A if B else C)
            if i + 2 <= len(expression) and expression[i:i+2].upper() == 'IF':
                # Check that it's not part of a longer identifier
                if i + 2 >= len(expression) or not (expression[i+2].isalnum() or expression[i+2] == '_' or expression[i+2] == '.'):
                    tokens.append('IF')
                    i += 2
                    continue
            # Handle 'ELSE' keyword (for ternary expressions)
            if i + 4 <= len(expression) and expression[i:i+4].upper() == 'ELSE':
                # Check that it's not part of a longer identifier
                if i + 4 >= len(expression) or not (expression[i+4].isalnum() or expression[i+4] == '_' or expression[i+4] == '.'):
                    tokens.append('ELSE')
                    i += 4
                    continue
            
            # Handle single character operators
            if expression[i] in ['>', '<', '(', ')']:
                tokens.append(expression[i])
                i += 1
                continue
            
            # Handle strings (single or double quotes)
            if expression[i] in ['"', "'"]:
                quote = expression[i]
                i += 1
                start = i
                while i < len(expression) and expression[i] != quote:
                    if expression[i] == '\\':
                        i += 1  # Skip escaped character
                    i += 1
                # Mark string literals distinctly to avoid confusion with identifiers
                tokens.append(("__str__", expression[start:i]))
                i += 1
                continue
            
            # Handle identifiers, numbers, booleans/null, and function calls
            if expression[i].isalnum() or expression[i] == '_' or expression[i] == '.':
                start = i
                # Allow alphanumeric, underscore, dot for identifiers
                while i < len(expression) and (expression[i].isalnum() or expression[i] in ['_', '.']):
                    i += 1
                token = expression[start:i]
                # Normalize for boolean/null tokens (case-insensitive)
                token_lower = token.lower()
                if token_lower == 'true':
                    tokens.append(True)
                    continue
                if token_lower == 'false':
                    tokens.append(False)
                    continue
                if token_lower in ['null', 'none']:
                    tokens.append(None)
                    continue

                # Try to parse as number
                try:
                    if '.' in token:
                        tokens.append(float(token))
                    else:
                        tokens.append(int(token))
                except ValueError:
                    # Keep as identifier - will handle function calls in parser
                    tokens.append(token)
                continue
            
            # Unknown character
            raise ValueError(f"Unexpected character: {expression[i]} at position {i}")
        
        return tokens
    
    def _parse(self, tokens: List[str]) -> Dict[str, Any]:
        """Parse tokens into AST using recursive descent.
        
        Grammar:
            expr := ternary_expr
            ternary_expr := or_expr (IF or_expr ELSE ternary_expr)?
            or_expr := and_expr (OR and_expr)*
            and_expr := not_expr (AND not_expr)*
            not_expr := NOT not_expr | comparison
            comparison := term (op term)?
            term := literal | variable | (expr) | function
        """
        if not tokens:
            raise ValueError("Empty expression")
        
        tokens_with_index = [tokens, 0]
        ast = self._parse_ternary(tokens_with_index)
        
        if tokens_with_index[1] < len(tokens):
            raise ValueError(f"Unexpected tokens after expression: {tokens[tokens_with_index[1]:]}")
        
        return ast
    
    def _parse_ternary(self, ti: List) -> Dict[str, Any]:
        """Parse ternary expression: A if B else C (right-associative).
        
        Python syntax: value_if_true if condition else value_if_false
        Example: math_strategist.expression if math_strategist.expression else 'No expression provided'
        """
        # Parse the value_if_true part
        true_value = self._parse_or(ti)
        
        # Check for ternary: IF condition ELSE value_if_false
        if ti[1] < len(ti[0]) and ti[0][ti[1]] == 'IF':
            ti[1] += 1  # consume 'IF'
            condition = self._parse_or(ti)
            
            if ti[1] >= len(ti[0]) or ti[0][ti[1]] != 'ELSE':
                raise ValueError("Expected 'else' after 'if' in ternary expression")
            
            ti[1] += 1  # consume 'ELSE'
            # Right-associative: A if B else (C if D else E)
            false_value = self._parse_ternary(ti)
            
            return {
                "type": "ternary",
                "condition": condition,
                "true_value": true_value,
                "false_value": false_value
            }
        
        return true_value
    
    def _parse_or(self, ti: List) -> Dict[str, Any]:
        """Parse OR expression."""
        left = self._parse_and(ti)
        
        while ti[1] < len(ti[0]) and ti[0][ti[1]] == 'OR':
            ti[1] += 1  # consume 'OR'
            right = self._parse_and(ti)
            left = {"type": "or", "left": left, "right": right}
        
        return left
    
    def _parse_and(self, ti: List) -> Dict[str, Any]:
        """Parse AND expression."""
        left = self._parse_not(ti)
        
        while ti[1] < len(ti[0]) and ti[0][ti[1]] == 'AND':
            ti[1] += 1  # consume 'AND'
            right = self._parse_not(ti)
            left = {"type": "and", "left": left, "right": right}
        
        return left
    
    def _parse_not(self, ti: List) -> Dict[str, Any]:
        """Parse NOT expression."""
        if ti[1] < len(ti[0]) and ti[0][ti[1]] == 'NOT':
            ti[1] += 1  # consume 'NOT'
            operand = self._parse_not(ti)
            return {"type": "not", "operand": operand}
        
        return self._parse_comparison(ti)
    
    def _parse_comparison(self, ti: List) -> Dict[str, Any]:
        """Parse comparison or term."""
        left = self._parse_term(ti)
        
        # Check for comparison operators (case-insensitive for word operators)
        if ti[1] < len(ti[0]) and isinstance(ti[0][ti[1]], str):
            op_raw = ti[0][ti[1]]
            op = op_raw.lower()
            # Handle unary operators (is null, is not null) - no right operand
            if op in ['is null', 'is not null']:
                ti[1] += 1  # consume operator
                return {"type": "comparison", "operator": op, "left": left, "right": None}
            # Handle binary operators - require right operand
            elif op in ['==', '!=', '>', '<', '>=', '<=', 'contains', 'starts_with', 
                      'ends_with', 'in', 'not in']:
                ti[1] += 1  # consume operator
                right = self._parse_term(ti)
                return {"type": "comparison", "operator": op, "left": left, "right": right}
        
        return left
    
    def _parse_term(self, ti: List) -> Dict[str, Any]:
        """Parse term (literal, variable, function call, or parenthesized expression)."""
        if ti[1] >= len(ti[0]):
            raise ValueError("Unexpected end of expression")
        
        token = ti[0][ti[1]]
        
        # Parentheses
        if token == '(':
            ti[1] += 1  # consume '('
            # Parse as ternary to allow ternary expressions inside parentheses
            expr = self._parse_ternary(ti)
            if ti[1] >= len(ti[0]) or ti[0][ti[1]] != ')':
                raise ValueError("Missing closing parenthesis")
            ti[1] += 1  # consume ')'
            return expr
        
        # Function call (e.g., len(...))
        if isinstance(token, str) and ti[1] + 1 < len(ti[0]) and ti[0][ti[1] + 1] == '(':
            func_name = token
            ti[1] += 2  # consume function name and '('
            
            # Parse arguments (single argument for now)
            args = []
            if ti[1] < len(ti[0]) and ti[0][ti[1]] != ')':
                # Parse first argument
                args.append(self._parse_or(ti))
            
            # Consume ')'
            if ti[1] >= len(ti[0]) or ti[0][ti[1]] != ')':
                raise ValueError("Missing closing parenthesis for function call")
            ti[1] += 1
            
            return {"type": "function", "name": func_name, "args": args}
        
        # Literals: numbers and booleans
        if isinstance(token, (int, float, bool)):
            ti[1] += 1
            return {"type": "literal", "value": token}
        
        # String literal (tokenizer marks as tuple ("__str__", value))
        if isinstance(token, tuple) and len(token) == 2 and token[0] == "__str__":
            ti[1] += 1
            return {"type": "literal", "value": token[1]}
        
        # Variable
        ti[1] += 1
        return {"type": "variable", "name": token}
    
    def _evaluate_node(self, node: Dict[str, Any]) -> Any:
        """Recursively evaluate AST node."""
        node_type = node.get("type")
        
        if node_type == "ternary":
            # Evaluate ternary: condition ? true_value : false_value
            # But our syntax is: true_value if condition else false_value
            condition_result = self._evaluate_node(node["condition"])
            if condition_result:
                return self._evaluate_node(node["true_value"])
            else:
                return self._evaluate_node(node["false_value"])
        elif node_type == "or":
            return self._evaluate_node(node["left"]) or self._evaluate_node(node["right"])
        elif node_type == "and":
            return self._evaluate_node(node["left"]) and self._evaluate_node(node["right"])
        elif node_type == "not":
            return not self._evaluate_node(node["operand"])
        elif node_type == "comparison":
            return self._evaluate_comparison(node)
        elif node_type == "variable":
            return self._resolve_variable(node["name"])
        elif node_type == "literal":
            return node["value"]
        elif node_type == "function":
            return self._evaluate_function(node)
        else:
            raise ValueError(f"Unknown node type: {node_type}")
    
    def _resolve_variable(self, var_name: str) -> Any:
        """Resolve shorthand variable to context value.
        
        Resolution order:
        1. If contains '.': Try context.upstream[first_part].parsed[rest]
        2. For pipeline paths (pipeline_id.node_id.field): Try context.upstream[pipeline_id].nodes[node_id].parsed[field]
        3. For pipeline intermediate (pipeline_id.intermediate.output_id.field): Try context.upstream[pipeline_id].intermediate[output_id].value[field]
        4. Fallback: Try context.upstream[first_part][rest] (direct)
        5. Fallback: Try context.hitl[first_part][rest] (for gate results)
        6. Fallback: Try context[first_part][rest] (root context)
        7. Fallback: Try context[var_name] (simple variable)
        8. Error if not found
        
        Examples:
            "claim_analyzer.fraud_prob" -> context.upstream["claim_analyzer"]["parsed"]["fraud_prob"]
            "math_repeater.math_repeater_parser.problem_count" -> context.upstream["math_repeater"]["nodes"]["math_repeater_parser"]["parsed"]["problem_count"]
            "math_repeater.intermediate.output_id.field" -> context.upstream["math_repeater"]["intermediate"]["output_id"]["value"]["field"]
            "math_repeater.report_md" -> context.upstream["math_repeater"]["parsed"]["report_md"] (final output)
            "user_text" -> context["user_text"]
            "ag_email_approval.decision" -> context.hitl["ag_email_approval"]["decision"]
            "claim_analyzer.details.amount" -> context.upstream["claim_analyzer"]["parsed"]["details"]["amount"]
        """
        if "." in var_name:
            parts = var_name.split(".")
            first_part = parts[0]
            field_path = parts[1:]
            
            # Try upstream first
            upstream = self.context.get("upstream", {})
            if first_part in upstream:
                node_data = upstream[first_part]
                
                # Handle accumulated loop results (list of results from multiple iterations)
                # When accumulate_results is true, upstream context contains lists instead of single dicts
                if isinstance(node_data, list):
                    if not node_data:
                        return None  # Empty list
                    # Use the last element (most recent iteration's result)
                    node_data = node_data[-1]
                    # Handle nested lists (list of lists) - keep extracting until we get a dict
                    # This can happen with nested loops where outer loop accumulates results
                    while isinstance(node_data, list):
                        if not node_data:
                            return None  # Empty nested list
                        node_data = node_data[-1]
                    # If still not a dict after extraction, return None
                    if not isinstance(node_data, dict):
                        return None
                
                # Check if this is a pipeline output (has "nodes" or "intermediate" keys)
                if isinstance(node_data, dict) and ("nodes" in node_data or "intermediate" in node_data):
                    # This is a pipeline output
                    if len(field_path) >= 2 and field_path[0] == "intermediate":
                        # Pipeline intermediate output: pipeline_id.intermediate.output_id.field
                        output_id = field_path[1]
                        remaining_path = field_path[2:]
                        intermediate_dict = node_data.get("intermediate", {})
                        if output_id in intermediate_dict:
                            value = intermediate_dict[output_id].get("value", {})
                            for field in remaining_path:
                                if isinstance(value, dict) and field in value:
                                    value = value[field]
                                else:
                                    return None  # Field not found, return None instead of raising
                            return value
                        else:
                            return None  # Intermediate output not found, return None instead of raising
                    elif len(field_path) >= 2:
                        # Pipeline node output: pipeline_id.node_id.field
                        node_id = field_path[0]
                        remaining_path = field_path[1:]
                        nodes_dict = node_data.get("nodes", {})
                        if node_id in nodes_dict:
                            node_output = nodes_dict[node_id]
                            if isinstance(node_output, dict) and "parsed" in node_output:
                                value = node_output["parsed"]
                                # If parsed is a string, try to parse it as JSON
                                if isinstance(value, str):
                                    
                                    try:
                                        value = JSONUtils.parse_json_from_text(value, expect_json=False)
                                    except Exception:
                                        value = None
                            else:
                                value = node_output
                            if isinstance(value, dict):
                                for field in remaining_path:
                                    if isinstance(value, dict) and field in value:
                                        value = value[field]
                                    else:
                                        return None  # Field not found, return None instead of raising
                                return value
                            else:
                                return None  # Value is not a dict after parsing
                        else:
                            return None  # Node not found, return None instead of raising
                    else:
                        # Pipeline final output: pipeline_id.field
                        if "parsed" in node_data:
                            value = node_data["parsed"]
                            # If parsed is a string, try to parse it as JSON
                            if isinstance(value, str):
                                try:
                                    value = JSONUtils.parse_json_from_text(value, expect_json=False)
                                except Exception:
                                    value = None
                        else:
                            value = node_data.get("result", node_data)
                        if isinstance(value, dict):
                            for field in field_path:
                                if isinstance(value, dict) and field in value:
                                    value = value[field]
                                else:
                                    return None  # Field not found, return None instead of raising
                            return value
                        else:
                            return None  # Value is not a dict after parsing
                
                # Regular agent output (not pipeline)
                # Check if it has 'parsed' structure
                if isinstance(node_data, dict) and "parsed" in node_data:
                    value = node_data["parsed"]
                    # If parsed is a string, try to parse it as JSON
                    if isinstance(value, str):
                        try:
                            value = JSONUtils.parse_json_from_text(value, expect_json=False)
                        except Exception:
                            value = None
                    # Now follow the field path
                    if isinstance(value, dict):
                        for field in field_path:
                            if isinstance(value, dict) and field in value:
                                value = value[field]
                            else:
                                return None  # Field not found, return None instead of raising
                        return value
                    else:
                        return None  # Parsed data is not a dict after parsing
                else:
                    # Direct access to upstream node data
                    value = node_data
                    for field in field_path:
                        if isinstance(value, dict) and field in value:
                            value = value[field]
                        else:
                            return None  # Field not found, return None instead of raising
                    return value
            
            # Try HITL gates (for gate results like ag_email_approval.decision)
            # CRITICAL: Use case-insensitive matching for gate IDs (e.g., "Option_Selection_Gate" -> "option_selection_gate")
            hitl = self.context.get("hitl", {})
            hitl_key = first_part
            if first_part not in hitl:
                # Try case-insensitive match (lowercase)
                hitl_key = first_part.lower()
            if hitl_key in hitl:
                gate_result = hitl[hitl_key]
                if isinstance(gate_result, dict):
                    value = gate_result
                    resolved_all_fields = True
                    # Also try case-insensitive field matching
                    for field in field_path:
                        if isinstance(value, dict):
                            # Try exact match first
                            if field in value:
                                value = value[field]
                            # Try case-insensitive match (lowercase)
                            elif field.lower() in value:
                                value = value[field.lower()]
                            # Try case-insensitive match with underscore normalization
                            elif field.replace("_", "").lower() in {
                                k.replace("_", "").lower()
                                for k in value.keys()
                                if isinstance(k, str)
                            }:
                                matching_key = next(
                                    (
                                        k
                                        for k in value.keys()
                                        if isinstance(k, str)
                                        and k.replace("_", "").lower()
                                        == field.replace("_", "").lower()
                                    ),
                                    None,
                                )
                                if matching_key:
                                    value = value[matching_key]
                                else:
                                    resolved_all_fields = False
                                    break
                            else:
                                # Field not found in gate_result - allow fallback to root context
                                resolved_all_fields = False
                                break
                        else:
                            # Not a dict anymore - allow fallback to root context
                            resolved_all_fields = False
                            break
                    # Only return if we successfully resolved the entire field path from HITL data
                    if resolved_all_fields:
                        return value
            
            # CRITICAL: Check root context for gate data stored at full path (e.g., option_selection_gate.selected_option_id)
            # Pipeline runner stores gate data at gate_id.context_key (full path like "option_selection_gate.selected_option_id"),
            # not nested under gate_id. So for "option_selection_gate.selected_option_id.value", we need to:
            # 1. First check if the full path exists directly (for cases where the full path is stored)
            # 2. Then check if the base path exists and navigate to the last field
            # CRITICAL: Use case-insensitive matching for gate paths
            if len(field_path) > 0:
                # Try the full path first (e.g., "option_selection_gate.selected_option_id.value")
                if var_name in self.context:
                    return self.context[var_name]
                # Try case-insensitive full path (lowercase)
                var_name_lower = var_name.lower()
                if var_name_lower in self.context:
                    return self.context[var_name_lower]
                
                # Try the path without the last field (e.g., "option_selection_gate.selected_option_id" for "option_selection_gate.selected_option_id.value")
                base_path = f"{first_part}.{'.'.join(field_path[:-1])}" if len(field_path) > 1 else first_part
                last_field = field_path[-1]
                
                # Try exact base_path match
                if base_path in self.context:
                    value = self.context[base_path]
                    # Navigate to the last field (case-insensitive)
                    if isinstance(value, dict):
                        if last_field in value:
                            return value[last_field]
                        elif last_field.lower() in value:
                            return value[last_field.lower()]
                    elif hasattr(value, last_field):
                        return getattr(value, last_field)
                    elif hasattr(value, last_field.lower()):
                        return getattr(value, last_field.lower())
                
                # Try case-insensitive base_path match (lowercase)
                base_path_lower = base_path.lower()
                if base_path_lower in self.context:
                    value = self.context[base_path_lower]
                    # Navigate to the last field (case-insensitive)
                    if isinstance(value, dict):
                        if last_field in value:
                            return value[last_field]
                        elif last_field.lower() in value:
                            return value[last_field.lower()]
                    elif hasattr(value, last_field):
                        return getattr(value, last_field)
                    elif hasattr(value, last_field.lower()):
                        return getattr(value, last_field.lower())
            
            # Fallback to root context with first_part only (for nested structures like gate_id.field.subfield)
            # Try exact match first
            if first_part in self.context:
                value = self.context[first_part]
                for field in field_path:
                    if isinstance(value, dict):
                        # Try exact match first
                        if field in value:
                            value = value[field]
                        # Try case-insensitive match (lowercase)
                        elif field.lower() in value:
                            value = value[field.lower()]
                        else:
                            return None  # Field not found, return None instead of raising
                    else:
                        return None
                return value
            
            # Try case-insensitive first_part match (lowercase)
            first_part_lower = first_part.lower()
            if first_part_lower in self.context:
                value = self.context[first_part_lower]
                for field in field_path:
                    if isinstance(value, dict):
                        # Try exact match first
                        if field in value:
                            value = value[field]
                        # Try case-insensitive match (lowercase)
                        elif field.lower() in value:
                            value = value[field.lower()]
                        else:
                            return None  # Field not found, return None instead of raising
                    else:
                        return None
                return value
            
            return None  # Variable not found, return None instead of raising
        else:
            # Simple variable - try HITL gates first (for consistency with dotted notation), then root context
            # CRITICAL: Use case-insensitive matching for gate IDs
            hitl = self.context.get("hitl", {})
            if var_name in hitl:
                return hitl[var_name]
            # Try case-insensitive match (lowercase)
            var_name_lower = var_name.lower()
            if var_name_lower in hitl:
                return hitl[var_name_lower]
            # Try root context
            if var_name in self.context:
                return self.context[var_name]
            # Try case-insensitive match (lowercase)
            if var_name_lower in self.context:
                return self.context[var_name_lower]
            return None  # Variable not found, return None instead of raising
    
    def _evaluate_comparison(self, node: Dict[str, Any]) -> bool:
        """Evaluate comparison operators with type coercion."""
        left = self._evaluate_node(node["left"])
        op = node["operator"]
        
        # Handle unary operators (is null, is not null) - no right operand
        if op in ["is null", "IS NULL"]:
            return left is None
        elif op in ["is not null", "IS NOT NULL"]:
            return left is not None
        
        # For binary operators, evaluate right operand
        right = self._evaluate_node(node["right"])
        
        # Type coercion for comparisons
        # "80" == 80 should be true
        if isinstance(left, str) and isinstance(right, (int, float)):
            try:
                left = float(left)
            except ValueError:
                pass
        elif isinstance(right, str) and isinstance(left, (int, float)):
            try:
                right = float(right)
            except ValueError:
                pass
        
        if op == "==":
            return left == right
        elif op == "!=":
            return left != right
        elif op == ">":
            return left > right
        elif op == "<":
            return left < right
        elif op == ">=":
            return left >= right
        elif op == "<=":
            return left <= right
        elif op == "contains":
            return str(right) in str(left)
        elif op == "starts_with":
            return str(left).startswith(str(right))
        elif op == "ends_with":
            return str(left).endswith(str(right))
        elif op == "in":
            if isinstance(right, list):
                return left in right
            return str(left) in str(right)
        elif op == "not in":
            if isinstance(right, list):
                return left not in right
            return str(left) not in str(right)
        else:
            raise ValueError(f"Unknown operator: {op}")
    
    def _evaluate_function(self, node: Dict[str, Any]) -> Any:
        """Evaluate function call (e.g., len(...))"""
        func_name = node["name"]
        args = [self._evaluate_node(arg) for arg in node["args"]]
        
        if func_name == "len":
            if len(args) != 1:
                raise ValueError(f"len() requires 1 argument, got {len(args)}")
            return len(args[0])
        else:
            raise ValueError(f"Unknown function: {func_name}()")
