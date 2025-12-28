from typing import Any
import json
import re

from topaz_agent_kit.utils.logger import Logger

class JSONUtils:

    _logger = Logger("JSONUtils")
    
    @staticmethod
    def parse_json_from_text(text: str, expect_json: bool = False) -> Any:
        """Best-effort JSON extraction from freeform text (LLM/tool outputs).

        Args:
            text: Input text to parse
            expect_json: If True, raises error for non-JSON content. If False, 
                        returns {"content": text} for plain text.

        Strategy:
        - Strip markdown code fences (``` or ```json) if present
        - Try json.loads on the whole string
        - Try incremental fixes for common LLM JSON issues
        - Fallback: extract ALL balanced JSON objects/arrays and choose best candidate
        - If nothing parses and expect_json=False, return {"content": text}
        - If nothing parses and expect_json=True, raise ValueError
        """
        JSONUtils._logger.debug("JSONUtils.parse_json_from_text INPUT: '{}'", text)
        
        if not isinstance(text, str):
            JSONUtils._logger.debug("JSONUtils: Input is not string, returning as-is")
            return text
        s = text.strip()

        # Strip fenced code blocks like ```json\n...\n``` or variations with optional spaces and CRLF
        # Accept optional language tag whitespace and optional final newline before closing fence
        m = re.match(r"^```[a-zA-Z]*[ \t]*\r?\n([\s\S]*?)\r?\n?```[ \t]*$", s)
        if m:
            s = m.group(1).strip()
            JSONUtils._logger.debug("JSONUtils: Stripped markdown fences, content: '{}'", s)

        # Also handle inline one-line fence pattern like ```json{...}```
        if s.startswith("```") and s.endswith("```") and "\n" not in s:
            try:
                inner = s.strip('`')
                # Remove optional language tag prefix (e.g., json)
                inner = re.sub(r"^[a-zA-Z]+[ \t]*", "", inner)
                s = inner.strip()
                JSONUtils._logger.debug("JSONUtils: Stripped single-line markdown fences, content: '{}'", s)
            except Exception:
                pass

        # Direct parse
        try:
            result = json.loads(s)
            JSONUtils._logger.debug("JSONUtils: Direct parse successful: {}", result)
            return result
        except json.JSONDecodeError as e:
            JSONUtils._logger.debug("JSONUtils: Direct parse failed at line {} col {}: {}", e.lineno, e.colno, e.msg)
        except Exception as e:
            JSONUtils._logger.debug("JSONUtils: Direct parse failed: {}", e)
        
        # Try incremental fixes for common LLM JSON issues
        fixes = [
            ("remove_comments", JSONUtils._remove_json_comments),
            ("fix_trailing_commas", JSONUtils._fix_trailing_commas),
            ("fix_unquoted_keys", JSONUtils._fix_unquoted_keys),
            ("fix_latex_math", JSONUtils._fix_latex_math),
            ("fix_control_chars", JSONUtils._fix_control_chars),
        ]
        
        # Try each fix individually first
        for fix_name, fix_func in fixes:
            try:
                fixed_s = fix_func(s)
                if fixed_s != s:  # Only try if something was actually fixed
                    result = json.loads(fixed_s)
                    JSONUtils._logger.debug("JSONUtils: {} fix successful: {}", fix_name, result)
                    return result
            except json.JSONDecodeError as e:
                JSONUtils._logger.debug("JSONUtils: {} fix failed at line {} col {}: {}", fix_name, e.lineno, e.colno, e.msg)
            except Exception as e:
                JSONUtils._logger.debug("JSONUtils: {} fix failed: {}", fix_name, e)
        
        # Try applying all fixes in sequence for complex cases
        try:
            current_s = s
            for fix_name, fix_func in fixes:
                current_s = fix_func(current_s)
            
            if current_s != s:  # Only try if something was actually fixed
                result = json.loads(current_s)
                JSONUtils._logger.debug("JSONUtils: Sequential fixes successful: {}", result)
                return result
        except json.JSONDecodeError as e:
            JSONUtils._logger.debug("JSONUtils: Sequential fixes failed at line {} col {}: {}", e.lineno, e.colno, e.msg)
        except Exception as e:
            JSONUtils._logger.debug("JSONUtils: Sequential fixes failed: {}", e)

        # Try to handle single-quoted JSON (common in Python string representations)
        try:
            import ast
            # Use ast.literal_eval to safely parse single-quoted strings
            result = ast.literal_eval(s)
            # Convert back to proper JSON string and parse
            json_string = json.dumps(result)
            result = json.loads(json_string)
            JSONUtils._logger.debug("JSONUtils: Single-quote parse successful: {}", result)
            return result
        except Exception as e:
            JSONUtils._logger.debug("JSONUtils: Single-quote parse failed: {}", e)

        # Find ALL balanced objects or arrays in order
        def _extract_all_balanced(src: str) -> list[str]:
            results: list[str] = []
            i = 0
            while i < len(src):
                # Find next opener
                j_obj = src.find("{", i)
                j_arr = src.find("[", i)
                if j_obj == -1 and j_arr == -1:
                    break
                start = j_obj if j_obj != -1 and (j_arr == -1 or j_obj < j_arr) else j_arr
                open_ch = src[start]
                close_ch = "}" if open_ch == "{" else "]"
                depth = 0
                for k in range(start, len(src)):
                    ch = src[k]
                    if ch == open_ch:
                        depth += 1
                    elif ch == close_ch:
                        depth -= 1
                        if depth == 0:
                            results.append(src[start : k + 1])
                            i = k + 1
                            break
                else:
                    # Unbalanced tail; stop
                    break
            return results

        candidates = _extract_all_balanced(s)
        parsed_candidates: list[Any] = []
        for idx, cand in enumerate(candidates):
            try:
                parsed = json.loads(cand)
                parsed_candidates.append(parsed)
            except Exception:
                continue

        if parsed_candidates:
            # Selection policy: prefer dicts, then arrays; prefer the LAST candidate; among dicts, pick the one with most keys
            dicts = [p for p in parsed_candidates if isinstance(p, dict)]
            if dicts:
                # Prefer last with max keys
                dicts_with_keys = [(len(list(d.keys())), i, d) for i, d in enumerate(dicts)]
                dicts_with_keys.sort(key=lambda x: (x[0], x[1]))
                best = dicts_with_keys[-1][2]
                JSONUtils._logger.debug("JSONUtils: Selected best dict candidate with {} keys", len(best.keys()))
                return best
            arrays = [p for p in parsed_candidates if isinstance(p, list)]
            if arrays:
                best_arr = arrays[-1]
                JSONUtils._logger.debug("JSONUtils: Selected last array candidate with length {}", len(best_arr))
                return best_arr

        JSONUtils._logger.debug("JSONUtils: All parsing failed")
        
        if expect_json:
            # Check if the text looks like it should be JSON (starts with { or [)
            if text.strip().startswith(('{', '[')):
                JSONUtils._logger.error("JSONUtils: Expected JSON but parsing failed: {}", text[:100])
                raise ValueError(f"Expected JSON but parsing failed: {text[:100]}...")
            else:
                JSONUtils._logger.error("JSONUtils: Expected JSON but got plain text: {}", text[:100])
                raise ValueError(f"Expected JSON but got plain text: {text[:100]}...")
        else:
            # Return plain text wrapped in a simple structure
            JSONUtils._logger.debug("JSONUtils: Returning plain text as content structure")
            return {"content": text}

    @staticmethod
    def _remove_json_comments(text: str) -> str:
        """Remove JSON comments (// and /* */) from text"""
        # Remove // comments
        text = re.sub(r'//.*$', '', text, flags=re.MULTILINE)
        # Remove /* */ comments
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        return text.strip()

    @staticmethod
    def _fix_trailing_commas(text: str) -> str:
        """Fix trailing commas in JSON objects and arrays"""
        # Fix trailing commas in objects and arrays
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        return text

    @staticmethod
    def _fix_unquoted_keys(text: str) -> str:
        """Fix unquoted object keys (common LLM mistake)"""
        # Fix unquoted object keys - be careful not to break string values
        # This regex looks for word characters followed by colon, but not inside strings
        def fix_key(match):
            key = match.group(1)
            # Only fix if it's not already quoted and looks like a key
            if not key.startswith('"') and not key.startswith("'"):
                return f'"{key}":'
            return match.group(0)
        
        # Match word characters followed by colon, but avoid strings
        text = re.sub(r'(\w+)(\s*:)', fix_key, text)
        return text

    @staticmethod
    def _fix_latex_math(text: str) -> str:
        """Fix LaTeX-style math notation in JSON strings"""
        def fix_string_content(match):
            string_content = match.group(1)
            # Fix LaTeX math delimiters: \( and \) should be \\( and \\)
            fixed_content = string_content.replace('\\(', '\\\\( ').replace('\\)', '\\\\) ')
            return f'"{fixed_content}"'
        
        # Find all string values and fix their content
        text = re.sub(r'"([^"]*(?:\\.[^"]*)*)"', fix_string_content, text)
        return text

    @staticmethod
    def _fix_control_chars(text: str) -> str:
        """Fix unescaped control characters in JSON strings"""
        def fix_string_content(match):
            string_content = match.group(1)
            # Fix unescaped control characters within the string
            fixed_content = string_content.replace('\\n', '\\\\n').replace('\\t', '\\\\t').replace('\\r', '\\\\r')
            return f'"{fixed_content}"'
        
        # Find all string values and fix their content
        text = re.sub(r'"([^"]*(?:\\.[^"]*)*)"', fix_string_content, text)
        return text

    @staticmethod
    def normalize_for_ui(content: Any) -> Any:
        """
        Normalize any content to the format expected by the UI.
        
        This method handles various content formats and converts them to a consistent
        structure that the UI can properly render, especially for markdown fields.
        
        Args:
            content: Raw content (string, dict, RunResponse object, or other)
            
        Returns:
            Normalized content in UI-expected format
        """
        try:
            # Step 0: Handle RunResponse objects and other objects with .content attribute
            if hasattr(content, 'content'):
                JSONUtils._logger.debug("Extracting content from object with .content attribute")
                content = content.content
            
            # Step 1: Parse JSON from text (handles markdown fences, multi-block, etc.)
            parsed_content = JSONUtils.parse_json_from_text(content)
            
            # Step 2: Handle wrapped results (e.g., {result: "```json\n{...}\n```"} or {content: "{...}"})
            if isinstance(parsed_content, dict) and len(parsed_content) == 1:
                # Check for 'result' key first
                if 'result' in parsed_content:
                    inner_result = parsed_content['result']
                    if isinstance(inner_result, str):
                        # Try to parse the inner result as JSON
                        inner_parsed = JSONUtils.parse_json_from_text(inner_result)
                        if isinstance(inner_parsed, dict):
                            # Use the inner JSON object
                            parsed_content = inner_parsed
                            JSONUtils._logger.debug("Normalized wrapped result (extracted keys: {})", 
                                                 list(inner_parsed.keys()))
                        else:
                            # Inner result is not JSON, keep as string
                            parsed_content = inner_parsed
                            JSONUtils._logger.debug("Normalized wrapped result (inner content is string)")
                    else:
                        # Inner result is not a string, use as-is
                        parsed_content = inner_result
                        JSONUtils._logger.debug("Normalized wrapped result (inner content is not string)")
                # Check for 'content' key
                elif 'content' in parsed_content:
                    inner_content = parsed_content['content']
                    if isinstance(inner_content, str):
                        # Try to parse the inner content as JSON
                        inner_parsed = JSONUtils.parse_json_from_text(inner_content)
                        if isinstance(inner_parsed, dict):
                            # Use the inner JSON object
                            parsed_content = inner_parsed
                            JSONUtils._logger.debug("Normalized wrapped content (extracted keys: {})", 
                                                 list(inner_parsed.keys()))
                        else:
                            # Inner content is not JSON, keep as string
                            parsed_content = inner_parsed
                            JSONUtils._logger.debug("Normalized wrapped content (inner content is string)")
                    else:
                        # Inner content is not a string, use as-is
                        parsed_content = inner_content
                        JSONUtils._logger.debug("Normalized wrapped content (inner content is not string)")
            
            # Step 3: Handle deeply nested JSON (e.g., result key containing another JSON string)
            if isinstance(parsed_content, dict) and 'result' in parsed_content:
                result_value = parsed_content['result']
                if isinstance(result_value, str):
                    # Try to parse the result value as JSON
                    try:
                        nested_parsed = JSONUtils.parse_json_from_text(result_value)
                        if isinstance(nested_parsed, dict):
                            # Use the nested JSON object
                            parsed_content = nested_parsed
                            JSONUtils._logger.debug("Normalized deeply nested result (extracted keys: {})", 
                                                 list(nested_parsed.keys()))
                    except Exception as e:
                        JSONUtils._logger.debug("Failed to parse nested result: {}", e)
            
            # Step 4: Unwrap trivial containers and ensure structure
            if isinstance(parsed_content, list) and len(parsed_content) == 1 and isinstance(parsed_content[0], dict):
                parsed_content = parsed_content[0]

            # Step 5: Enhanced content unwrapping - handle cases where actual data is under 'content' key
            if isinstance(parsed_content, dict):
                # Check if we have a 'content' key with meaningful data
                if 'content' in parsed_content and isinstance(parsed_content['content'], dict):
                    content_data = parsed_content['content']
                    # If content contains actual data (not just metadata), prefer it
                    if len(content_data) > 1 or (len(content_data) == 1 and 'content' not in content_data):
                        JSONUtils._logger.debug("Unwrapping nested content structure (keys: {})", 
                                             list(content_data.keys()))
                        parsed_content = content_data
                
                JSONUtils._logger.debug("Normalized content for UI (keys: {})", 
                                     list(parsed_content.keys()))
                return parsed_content
            elif isinstance(parsed_content, str):
                # If it's still a string, wrap it in a simple structure
                return {"content": parsed_content}
            else:
                # For other types, convert to string and wrap
                return {"content": str(parsed_content)}
                
        except Exception as e:
            JSONUtils._logger.error("Failed to normalize content for UI: {}", e)
            # Fallback: return the original content wrapped in a simple structure
            return {"content": str(content)}

    @staticmethod
    def extract_variable_from_output(output: Any, var_name: str) -> Any:
        """
        Extract a specific variable from agent output of any type.
        
        Args:
            output: The output to extract from (dict, string, or other)
            var_name: Name of the variable to extract
            
        Returns:
            Variable value if found, None otherwise
        """
        # Case 1: Dictionary output (most common)
        if isinstance(output, dict):
            return output.get(var_name)
        
        # Case 2: String output (needs JSON parsing)
        elif isinstance(output, str):
            # Skip empty strings
            if not output.strip():
                return None
            
            try:
                parsed = JSONUtils.parse_json_from_text(output)
                if isinstance(parsed, dict):
                    return parsed.get(var_name)
            except Exception:
                # Silently fail - this is expected for non-JSON strings
                pass
        
        # Case 3: Other types (None, int, list, etc.)
        else:
            JSONUtils._logger.debug(f"Unexpected output type: {type(output)} for variable {var_name}")
           
        return None

