from typing import Any, Dict, List

import json
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.json_utils import JSONUtils


logger = Logger("SummaryRenderer")


def render_summary(results: Dict[str, Any], pipeline_config: Dict[str, Any] | None = None) -> str:
    logger.debug("Rendering summary from {} results", len(results) if results else 0)
    
    if not results:
        return "Done."

    # Get all result keys (no specific order needed for pattern-based execution)
    try:
        result_keys = list(results.keys())
        # Use the last key as the "final" result (arbitrary choice for pattern execution)
        last_node = result_keys[-1] if result_keys else None
        last_val = results.get(last_node) if last_node else None
        
        logger.debug("Last node: {}, last_val type: {}, last_val: {}", last_node, type(last_val).__name__, str(last_val)[:200])
        
        if isinstance(last_val, dict):
            # Log what fields are available in the last result
            available_keys = list(last_val.keys())
            logger.debug("Available keys in last result: {}", available_keys)
            
            # Get output fields from pipeline configuration
            output_keys = []
            logger.debug("Pipeline config provided: {}", pipeline_config is not None)
            if pipeline_config:
                logger.debug("Pipeline config keys: {}", list(pipeline_config.keys()) if isinstance(pipeline_config, dict) else "not a dict")
                logger.debug("Has outputs: {}", "outputs" in pipeline_config if isinstance(pipeline_config, dict) else False)
            if pipeline_config and "outputs" in pipeline_config and "final" in pipeline_config["outputs"]:
                final_output = pipeline_config["outputs"]["final"]
                logger.debug("Final output config: {}", final_output)
                if "selectors" in final_output:
                    output_keys = [selector for selector in final_output["selectors"] if selector != "error"]
                    logger.debug("Using pipeline-defined output keys: {}", output_keys)
            
            # Fallback to default keys if no pipeline config
            if not output_keys:
                output_keys = ["summary", "result", "final_answer", "answer", "message", "text", "output"]
                logger.debug("Using default output keys: {}", output_keys)
            
            # Try to find meaningful output
            for key in output_keys:
                val = last_val.get(key)
                if isinstance(val, str) and val.strip():
                    candidate = val.strip()
                    # Try to parse JSON-ish content and surface meaningful fields
                    try:
                        parsed = JSONUtils.parse_json_from_text(candidate)
                        if isinstance(parsed, dict):
                            # Prefer 'final_answer', then 'message'/'validation_message', then 'result'
                            inner = (
                                parsed.get("final_answer")
                                or parsed.get("message")
                                or parsed.get("validation_message")
                                or parsed.get("result")
                            )
                            if isinstance(inner, str) and inner.strip():
                                summary = inner.strip()
                            else:
                                summary = json.dumps(parsed, indent=2, default=str)
                        else:
                            summary = candidate
                    except Exception:
                        summary = candidate
                    logger.debug("Found output in key '{}': {} chars", key, len(summary))
                    break
            else:
                # If no string output found, try to create a meaningful summary
                if "status" in last_val and last_val["status"] != "ok":
                    summary = f"Status: {last_val['status']}"
                elif "error" in last_val:
                    summary = f"Error: {last_val['error']}"
                elif "agent" in last_val and "task" in last_val:
                    # This looks like a placeholder result, try to get more info
                    task_desc = last_val.get("task", {}).get("description", "")
                    if task_desc and not task_desc.startswith("Process: "):
                        summary = f"Task: {task_desc}"
                    else:
                        summary = "Agent executed but no detailed output available"
                else:
                    # As a safety, stringify but avoid showing full JSON blobs
                    try:
                        summary = json.dumps(last_val, default=str)[:200] + ("..." if len(json.dumps(last_val, default=str)) > 200 else "")
                    except (TypeError, ValueError):
                        summary = str(last_val)[:200] + ("..." if len(str(last_val)) > 200 else "")
        elif hasattr(last_val, 'content') and isinstance(last_val.content, str) and last_val.content.strip():
            # Handle Agno RunResponse objects and similar objects with content attribute
            content = last_val.content.strip()
            # Use JSONUtils to properly parse and format JSON content
            parsed = JSONUtils.parse_json_from_text(content)
            if isinstance(parsed, dict) or isinstance(parsed, list):
                # If it's valid JSON, format it nicely with safe serialization
                try:
                    summary = json.dumps(parsed, indent=2, default=str)
                except (TypeError, ValueError) as e:
                    logger.debug("JSON serialization failed, using string representation: {}", e)
                    summary = str(parsed)
            else:
                # If parsing failed, use the original content
                summary = content
            logger.debug("Found content output: {} chars (parsed from {} chars)", len(summary), len(content))
        elif hasattr(last_val, 'content'):
            # Debug: log what we found for content attribute
            logger.debug("Found content attribute but not string: type={}, value={}", type(last_val.content), last_val.content)
            # Try to convert to string if possible
            if last_val.content:
                summary = str(last_val.content).strip()
                logger.debug("Converted content to string: {} chars", len(summary))
            else:
                logger.debug("Content attribute is empty or None")
                summary = "No meaningful output available"
        elif hasattr(last_val, 'result') and isinstance(last_val.result, str) and last_val.result.strip():
            # Handle objects with result attribute
            summary = last_val.result.strip()
            logger.debug("Found result output: {} chars", len(summary))
        elif isinstance(last_val, str) and last_val.strip():
            summary = last_val.strip()
            logger.debug("Found string output: {} chars", len(summary))
        else:
            # Fallback: concatenate all values
            # Iterate through all results (no specific order for pattern execution)
            parts = []
            for node, v in results.items():
                if not v:
                    continue
                if isinstance(v, dict):
                    for key in ("summary", "result", "final_answer", "answer", "message", "text", "output"):
                        val = v.get(key)
                        if isinstance(val, str) and val.strip():
                            parts.append(val.strip())
                            break
                    else:
                        # Try to extract meaningful info from dict
                        if "error" in v:
                            parts.append(f"Error: {v['error']}")
                        elif "status" in v and v["status"] != "ok":
                            parts.append(f"Status: {v['status']}")
                        else:
                            # Safe string conversion for dict objects
                            try:
                                # First try to convert to JSON with safe serialization
                                json_str = json.dumps(v, default=str)
                                parts.append(json_str[:100])
                            except (TypeError, ValueError) as e:
                                logger.debug("JSON serialization failed for dict: {}", e)
                                # Fallback to string conversion
                                try:
                                    parts.append(str(v)[:100])
                                except Exception as e2:
                                    logger.debug("String conversion also failed: {}", e2)
                                    parts.append("Unable to convert to string")
                elif hasattr(v, 'content') and isinstance(v.content, str) and v.content.strip():
                    # Handle Agno RunResponse objects and similar objects with content attribute
                    content = v.content.strip()
                    # Use JSONUtils to properly parse and format JSON content
                    parsed = JSONUtils.parse_json_from_text(content)
                    if isinstance(parsed, dict) or isinstance(parsed, list):
                        # If it's valid JSON, format it nicely with safe serialization
                        try:
                            cleaned_content = json.dumps(parsed, indent=2, default=str)
                        except (TypeError, ValueError) as e:
                            logger.debug("JSON serialization failed, using string representation: {}", e)
                            cleaned_content = str(parsed)
                    else:
                        # If parsing failed, use the original content
                        cleaned_content = content
                    parts.append(cleaned_content)
                elif hasattr(v, 'result') and isinstance(v.result, str) and v.result.strip():
                    # Handle objects with result attribute
                    parts.append(v.result.strip())
                else:
                    # Safe string conversion for any other type
                    try:
                        parts.append(str(v)[:100])
                    except Exception as e:
                        logger.debug("String conversion failed for type {}: {}", type(v).__name__, e)
                        parts.append(f"Unable to convert {type(v).__name__} to string")
            summary = parts[-1] if parts else "No meaningful output available"
    except Exception as e:
        logger.warning("Error in summary rendering: {}", e)
        logger.info("Exception type: {}, details: {}", type(e).__name__, str(e))
        logger.info("Results keys: {}", list(results.keys()) if results else None)
        # Safe fallback with proper error handling
        parts = []
        for v in results.values():
            if v is not None:
                try:
                    parts.append(str(v))
                except Exception as e2:
                    logger.debug("Failed to convert value to string in fallback: {}", e2)
                    parts.append("Unable to convert value")
        summary = "; ".join(parts) if parts else "Error rendering summary"
    
    logger.debug("Summary rendered: {} chars", len(summary))
    return summary

