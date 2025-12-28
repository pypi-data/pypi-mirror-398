import ast
import math
import operator as op
import re
import json as _json
from topaz_agent_kit.core.exceptions import ModelError
from topaz_agent_kit.utils.json_utils import JSONUtils
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.mcp_utils import invoke_llm
from sympy import (
    symbols, Eq, solve, sympify, log, exp,
    sin, cos, tan, pi, diff, integrate,
    solve_univariate_inequality
)

from fastmcp import FastMCP


class MathMCPTools:
    def __init__(self, **kwargs):
        self._llm = kwargs.get("llm")
        self._logger = Logger("MCP.Math")

    def register(self, mcp: FastMCP) -> None:
        @mcp.tool(name="math_multiply")
        def multiply(a: float | int, b: float | int) -> float:
            """
            Multiply two numbers (supports integers and decimals).

            Args:
                a (float | int): First number.
                b (float | int): Second number.

            Returns:
                float: Product of a and b.
            """
            self._logger.input("multiply INPUT: a={}, b={}", a, b)
            result = float(a) * float(b)
            self._logger.output("multiply OUTPUT: {}", result)
            return result

        def _split_sentences(text: str):
            self._logger.input("split_sentences INPUT: text_len={}", len(text or ""))
            parts = re.split(r"(?<=[.!?])\s+", text.strip())
            result = [p for p in parts if p]
            self._logger.output("split_sentences OUTPUT: {}", result)
            return result
            
        @mcp.tool(name="math_summarize")
        def summarize(text: str, max_sentences: int = 3, max_chars: int = 280) -> str:
            """
            Produce a concise extractive summary by taking up to max_sentences sentences within max_chars.

            Args:
                text (str): Text to summarize.
                max_sentences (int): Maximum number of sentences to include in the summary.
                max_chars (int): Maximum number of characters to include in the summary.
            
            Returns:
                str: Summary of the text.
            """
            self._logger.input("summarize INPUT: text_len={}, max_sentences={}, max_chars={}", len(text or ""), max_sentences, max_chars)
            sentences = _split_sentences(text)
            if not sentences:
                return ""
            summary = []
            total = 0
            for s in sentences:
                s_trim = s.strip()
                if not s_trim:
                    continue
                if len(summary) < max_sentences and total + len(s_trim) <= max_chars:
                    summary.append(s_trim)
                    total += len(s_trim) + 1
                else:
                    break
            result = " ".join(summary)
            self._logger.output("summarize OUTPUT: {}", result)
            return result if result else (sentences[0][: max_chars - 3] + "...")

        @mcp.tool(name="math_llm_summarize")
        def llm_summarize(text: str, max_words: int = 120, tone: str = "concise") -> str:
            """
            Summarize using the configured LLM. Falls back to extractive summarize if LLM unavailable.

            Args:
                text (str): Text to summarize.
                max_words (int): Maximum number of words to include in the summary.
                tone (str): Tone of the summary.

            Returns:
                str: Summary of the text.
            """
            self._logger.input("llm_summarize INPUT: text_len={}, max_words={}, tone={}", len(text or ""), max_words, tone)
            if not text:
                return ""
            if self._llm is not None:
                try:
                    prompt = (
                        f"Summarize the following text in <= {max_words} words. Use a {tone} tone.\n\nText:\n{text}"
                    )
                    out = invoke_llm(self._llm, prompt)
                    self._logger.output("llm_summarize ok: text_len={}, out_len={}", len(text), len(out))
                    self._logger.output("llm_summarize OUTPUT: {}", out)
                    return out
                except Exception as e:
                    self._logger.error("llm_summarize ERROR: {}", e)
            return summarize(text, max_sentences=3, max_chars=max(80, max_words * 8))

        
        @mcp.tool(name="math_extract_quantities")
        def extract_quantities(text: str) -> str:
            """Extract numeric quantities and simple units from text as JSON.

            Args:
                text (str): Text to extract quantities from.

            Returns:
                str: JSON string containing extracted quantities.
            """
            self._logger.input("extract_quantities INPUT: '{}'", text)
            nums = re.findall(r"(?<![\w/])(\d+(?:\.\d+)?)(?![\w/])", text)
            fracs = re.findall(r"(\d+\s*/\s*\d+)", text)
            pcts = re.findall(r"(\d+(?:\.\d+)?)\s*%", text)
            units = re.findall(r"\b(cup|cups|bag|bags|dozen|gross|half|quarter|third|weeks?|days?)\b", text, flags=re.IGNORECASE)
            data = {
                "numbers": nums,
                "fractions": [f.replace(" ", "") for f in fracs],
                "percents": pcts,
                "units": units,
            }
            try:
                import json as _json
                result = _json.dumps(data)
                self._logger.output("extract_quantities OUTPUT: {}", result)
                return result
            except Exception:
                result = str(data)
                self._logger.warning("extract_quantities OUTPUT: {}", result)
                return result

        @mcp.tool(name="math_llm_parse_math_problem")
        def llm_parse_math_problem(problem: str, format: str = "json") -> str:
            """
            Use LLM to parse a math problem into {expression, steps}.

            Args:
                problem (str): Math problem to parse.
                format (str): Format of the output.

            Returns:
                str: Parsed math problem as JSON string with keys:
                    - "expression": sanitized string suitable for solver
                    - "steps": list of concise steps
            """
            self._logger.input("llm_parse_math_problem INPUT: '{}' (format: {})", problem, format)

            if not problem:
                self._logger.warning("llm_parse_math_problem ERROR: empty problem")
                return "Error: empty problem"

            # LLM prompt using triple quotes
            prompt = f"""
                    You are a math planner. Parse the problem into a safe Python expression for computation, using only:
                    - Arithmetic: +, -, *, /, **, parentheses
                    - Equations: = for equality, ; to separate multiple equations
                    - Functions: log(x), exp(x), sin(x), cos(x), tan(x)
                    - Derivatives: d/dx(...)
                    - Integrals: ∫(...)

                    Rules:
                    - For multiple equations, separate them with ';', not 'and'
                    - Use explicit variable names
                    - Return ONLY strict JSON: {{"expression": str, "steps": list[str]}}
                    - Expression should be suitable for sanitize_expression and solver tools

                    Problem: {problem}
                    """
            try:
                self._logger.input("llm_parse_math_problem LLM prompt: {}", prompt)
                text = invoke_llm(self._llm, prompt)
                self._logger.output("llm_parse_math_problem LLM OUTPUT: {}", text)
                return text
            except Exception as e:
                self._logger.error("llm_parse_math_problem ERROR: {}", e)
                return f"Error calling LLM: {e}"


        @mcp.tool(name="math_evaluate_expression")
        def evaluate_expression(expression: str) -> str:
            """
            Safely evaluate an arithmetic expression like '(12 + 8) * 3 - 5**2'.

            Args:
                expression (str): Math expression to evaluate.

            Returns:
                str: Evaluated result as string, or error message.
            """
            self._logger.input("evaluate_expression INPUT: '{}'", expression)
            try:
                # Validate expression safely
                _sanitize_expr_side(expression)  # raises error if invalid

                # Safe eval using restricted namespace
                allowed_names = {"__builtins__": None, "math": math}
                value = eval(expression, allowed_names, {})
                self._logger.output("evaluate_expression OUTPUT: {}", value)
                return str(value)

            except Exception as e:
                self._logger.error("evaluate_expression ERROR: {}", e)
                return f"Error evaluating expression: {e}"


        @mcp.tool(name="math_percentage_of")
        def percentage_of(value: float, percent: float) -> float:
            """Return percent% of value (e.g., percentage_of(200, 15) -> 30).

            Args:
                value (float): Value to calculate percentage of.
                percent (float): Percentage to calculate.

            Returns:
                float: Percentage of value.
            """
            self._logger.input("percentage_of INPUT: value={}, percent={}", value, percent)
            result = (value * percent) / 100.0
            self._logger.output("percentage_of OUTPUT: {}", result)
            return result   


        @mcp.tool(name="math_percent_change")
        def percent_change(old: float, new: float) -> str:
            """Return absolute and percent change from old to new as a descriptive string.

            Args:
                old (float): Old value.
                new (float): New value.

            Returns:
                str: Descriptive string of the change.
            """
            self._logger.input("percent_change INPUT: old={}, new={}", old, new)
            abs_change = new - old
            pct = (abs_change / old * 100.0) if old != 0 else float("inf")
            result = f"absolute_change: {abs_change}, percent_change: {pct}%"
            self._logger.output("percent_change OUTPUT: {}", result)
            return result


        @mcp.tool(name="math_fraction_to_decimal")
        def fraction_to_decimal(numerator: float, denominator: float) -> float:
            """Convert a fraction to decimal. denominator must not be 0.

            Args:
                numerator (float): Numerator of the fraction.
                denominator (float): Denominator of the fraction.

            Returns:
                float: Decimal representation of the fraction.
            """
            self._logger.input("fraction_to_decimal INPUT: numerator={}, denominator={}", numerator, denominator)
            if denominator == 0:
                raise ModelError("denominator must not be 0")
            result = numerator / denominator
            self._logger.output("fraction_to_decimal OUTPUT: {}", result)
            return result


        @mcp.tool(name="math_ceil_divide")
        def ceil_divide(total: float, unit_size: float) -> int:
            """Return ceil(total / unit_size). unit_size must be > 0. Useful for packaging, trips, batches.

            Args:
                total (float): Total value.
                unit_size (float): Size of the unit.

            Returns:
                int: Ceil of the division.
            """
            self._logger.input("ceil_divide INPUT: total={}, unit_size={}", total, unit_size)
            if unit_size <= 0:
                raise ModelError("unit_size must be > 0")
            result = math.ceil(total / unit_size)
            self._logger.output("ceil_divide OUTPUT: {}", result)
            return result


        @mcp.tool(name="math_solve_equations")
        def solve_equations(equations: list[str], variables: list[str]):
            """
            Solve one or more equations for the given variables.

            Args:
                equations (list[str]): List of equations as strings, e.g. ["2*x + y = 5", "x - y = 1"].
                                    Each equation must contain an '=' sign.
                variables (list[str]): List of variable names to solve for, e.g. ["x", "y"].

            Returns:
                list[dict]: List of solutions. Each solution is a dictionary mapping variables to values.
                            Values are returned as strings for JSON compatibility.
            """
            try:
                self._logger.input("solve_equations INPUT: equations={}, variables={}", equations, variables)
                syms = symbols(" ".join(variables))
                eqs = []
                for eq in equations:
                    lhs_str, rhs_str = eq.split("=")
                    lhs = sympify(lhs_str)
                    rhs = sympify(rhs_str)
                    eqs.append(Eq(lhs, rhs))

                solutions = solve(eqs, syms, dict=True)
                result = [{str(k): str(v) for k, v in sol.items()} for sol in solutions]
                self._logger.output("solve_equations OUTPUT: {}", result)
                return result
            except Exception as e:
                self._logger.error("solve_equations ERROR: {}", e)
                return {"error": str(e)}


        @mcp.tool(name="math_solve_inequality")
        def solve_inequality(inequality: str, variable: str = "x"):
            """
            Solve a single-variable inequality.

            Args:
                inequality (str): Inequality expression as a string, e.g. "x + 3 < 7".
                                Supports <, <=, >, >=.
                variable (str): Variable to solve for (default: "x").

            Returns:
                str: Solution interval or inequality result as a string.
            """
            try:
                self._logger.input("solve_inequality INPUT: inequality={}, variable={}", inequality, variable)
                var = symbols(variable)

                if "<=" in inequality:
                    lhs, rhs = inequality.split("<=")
                    ineq = sympify(lhs) <= sympify(rhs)
                elif ">=" in inequality:
                    lhs, rhs = inequality.split(">=")
                    ineq = sympify(lhs) >= sympify(rhs)
                elif "<" in inequality:
                    lhs, rhs = inequality.split("<")
                    ineq = sympify(lhs) < sympify(rhs)
                elif ">" in inequality:
                    lhs, rhs = inequality.split(">")
                    ineq = sympify(lhs) > sympify(rhs)
                else:
                    raise ValueError("Inequality must contain <, >, <=, or >=")

                solution = solve_univariate_inequality(ineq, var)
                result = {"solution": str(solution)}
                self._logger.output("solve_inequality OUTPUT: {}", result)
                return result
            except Exception as e:
                self._logger.error("solve_inequality ERROR: {}", e)
                return {"error": str(e)}


        @mcp.tool(name="math_compute_log")
        def compute_log(value: str, base: str = None):
            """
            Compute logarithm of a value.

            Args:
                value (str): The value to compute the logarithm for (e.g. "100").
                base (str, optional): Base of the logarithm. If None, natural log is used.

            Returns:
                str: Logarithm result as a string.
            """
            try:
                self._logger.input("compute_log INPUT: value={}, base={}", value, base)
                val = sympify(value)
                if base:
                    b = sympify(base)
                    result = log(val, b)
                else:
                    result = log(val)
                result = {"result": str(result)}
                self._logger.output("compute_log OUTPUT: {}", result)
                return result
            except Exception as e:
                self._logger.error("compute_log ERROR: {}", e)
                return {"error": str(e)}


        @mcp.tool(name="math_compute_exp")
        def compute_exp(value: str):
            """
            Compute the exponential of a value (e^value).

            Args:
                value (str): Value to compute exp for, e.g. "2".

            Returns:
                str: Exponential result as a string.
            """
            try:
                self._logger.input("compute_exp INPUT: value={}", value)
                val = sympify(value)
                result = {"result": str(exp(val))}
                self._logger.output("compute_exp OUTPUT: {}", result)
                return result
            except Exception as e:
                self._logger.error("compute_exp ERROR: {}", e)
                return {"error": str(e)}


        @mcp.tool(name="math_trig_functions")
        def trig_functions(angle: str, unit: str = "radians"):
            """
            Compute sine, cosine, and tangent of an angle.

            Args:
                angle (str): The angle value, e.g. "90".
                unit (str): "radians" (default) or "degrees".

            Returns:
                dict: Dictionary with keys "sin", "cos", and "tan". Values are strings.
            """
            try:
                self._logger.input("trig_functions INPUT: angle={}, unit={}", angle, unit)
                angle_val = sympify(angle)
                if unit == "degrees":
                    angle_val = angle_val * pi / 180

                result = {
                    "sin": str(sin(angle_val).simplify()),
                    "cos": str(cos(angle_val).simplify()),
                    "tan": str(tan(angle_val).simplify())
                }
                self._logger.output("trig_functions OUTPUT: {}", result)
                return result
            except Exception as e:
                self._logger.error("trig_functions ERROR: {}", e)
                return {"error": str(e)}


        @mcp.tool(name="math_differentiate")
        def differentiate(expr: str, variable: str = "x"):
            """
            Differentiate an expression with respect to a variable.

            Args:
                expr (str): Expression to differentiate, e.g. "x**2 + 3*x + 5".
                variable (str): Variable to differentiate with respect to (default "x").

            Returns:
                str: Derivative as a string.
            """
            try:
                self._logger.input("differentiate INPUT: expr={}, variable={}", expr, variable)
                var = symbols(variable)
                expression = sympify(expr)
                result = {"result": str(diff(expression, var))}
                self._logger.output("differentiate OUTPUT: {}", result)
                return result
            except Exception as e:
                self._logger.error("differentiate ERROR: {}", e)
                return {"error": str(e)}


        @mcp.tool(name="math_integrate_expr")
        def integrate_expr(expr: str, variable: str = "x"):
            """
            Integrate an expression with respect to a variable.

            Args:
                expr (str): Expression to integrate, e.g. "x**2".
                variable (str): Variable to integrate with respect to (default "x").

            Returns:
                str: Integral as a string.
            """
            try:
                self._logger.input("integrate_expr INPUT: expr={}, variable={}", expr, variable)
                var = symbols(variable)
                expression = sympify(expr)
                result = {"result": str(integrate(expression, var))}
                self._logger.output("integrate_expr OUTPUT: {}", result)
                return result
            except Exception as e:
                self._logger.error("integrate_expr ERROR: {}", e)
                return {"error": str(e)}


        _ops = {
            ast.Add: op.add,
            ast.Sub: op.sub,
            ast.Mult: op.mul,
            ast.Div: op.truediv,
            ast.Pow: op.pow,
            ast.USub: op.neg,
        }

        _allowed_functions = {"sin", "cos", "tan", "log", "exp", "sqrt", "abs", "floor", "ceil", "round", "min", "max"}

        @mcp.tool(name="math_sanitize_expression")
        def sanitize_expression(expression: str) -> str:
            """
            Validate and normalize math expressions, including equations.
            - Converts '^' to '**'
            - Replaces '==' with '='
            - Replaces ' and ' with ';'
            - Supports multiple equations separated by ';'
            - Rejects unsupported tokens and functions

            Args:
                expression (str): Expression to sanitize.

            Returns:
                str: Sanitized math expression string.
            """
            try:
                self._logger.input("sanitize_expression INPUT: expression={}", expression)
                expression = expression.replace('==', '=').replace(' and ', ';').strip()
                equations = [part.strip() for part in expression.split(';') if part.strip()]
                sanitized = []
                for eq in equations:
                    if '=' in eq:
                        lhs, rhs = eq.split('=', 1)
                        lhs_clean = _sanitize_expr_side(lhs)
                        rhs_clean = _sanitize_expr_side(rhs)
                        sanitized.append(f"{lhs_clean} = {rhs_clean}")
                    else:
                        sanitized.append(_sanitize_expr_side(eq))
                result = "; ".join(sanitized)
                self._logger.output("sanitize_expression OUTPUT: {}", result)
                return result
            except Exception as e:
                self._logger.error("sanitize_expression ERROR: {}", e)
                return f"Error: {e}"

        def _sanitize_expr_side(expr: str) -> str:
            """Safely validate one side of an equation or expression."""
            self._logger.input("sanitize_expr_side INPUT: expr={}", expr)
            expr = expr.replace('^', '**').strip()
            try:
                parsed = ast.parse(expr, mode="eval")
                _check_ast_safe(parsed.body)
                self._logger.output("sanitize_expr_side OUTPUT: {}", expr)
                return expr
            except Exception as e:
                self._logger.error("sanitize_expr_side ERROR: {}", e)
                raise ModelError(f"invalid expression: {e}")

        def _check_ast_safe(node):
            """Recursively validate AST nodes for safety."""
            self._logger.input("check_ast_safe INPUT: node={}", node)
            if isinstance(node, ast.BinOp):
                if type(node.op) not in _ops:
                    raise ModelError(f"Unsupported operator {node.op}")
                _check_ast_safe(node.left)
                _check_ast_safe(node.right)
            elif isinstance(node, ast.UnaryOp):
                if type(node.op) not in _ops:
                    self._logger.error("check_ast_safe ERROR: Unsupported unary operator {}", node.op)
                    raise ModelError(f"Unsupported unary operator {node.op}")
                _check_ast_safe(node.operand)
            elif isinstance(node, ast.Num):
                self._logger.output("check_ast_safe OUTPUT: {}", node.n)
                return
            elif isinstance(node, ast.Name):
                self._logger.output("check_ast_safe OUTPUT: {}", node.id)
                return  # variable name allowed
            elif isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name) or node.func.id not in _allowed_functions:
                    self._logger.error("check_ast_safe ERROR: Unsupported function {}", getattr(node.func, 'id', None))
                    raise ModelError(f"Unsupported function: {getattr(node.func, 'id', None)}")
                for arg in node.args:
                    _check_ast_safe(arg)
            else:
                self._logger.error("check_ast_safe ERROR: Unsupported node type: {}", type(node))
                raise ModelError(f"Unsupported node type: {type(node)}")




        