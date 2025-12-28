"""
Output Manager for processing intermediate and final outputs with TEXT_MESSAGE events.
"""

import json
from typing import Any, Dict, List, Optional
from jinja2 import Template

from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.json_utils import JSONUtils
from topaz_agent_kit.core.ag_ui_event_emitter import AGUIEventEmitter


class OutputManager:
    """Manages intermediate and final outputs with TEXT_MESSAGE events for UI reactivity."""
    
    def __init__(self, pipeline_config: Dict[str, Any]):
        self.pipeline_config = pipeline_config
        self.logger = Logger("OutputManager")
        
        # Get outputs configuration
        self.outputs_config = pipeline_config.get("outputs", {})
        self.intermediate_configs = self.outputs_config.get("intermediate", [])
        self.final_config = self.outputs_config.get("final", {})
        
        self.logger.info("OutputManager initialized with {} intermediate outputs", len(self.intermediate_configs))
    
    def process_intermediate_output(self, node_id: str, node_output: Any, emitter: AGUIEventEmitter) -> Optional[Dict[str, Any]]:
        """Process intermediate output for a specific node and emit TEXT_MESSAGE events."""
        # Find intermediate output config for this node
        intermediate_config = None
        for config in self.intermediate_configs:
            if config.get("node") == node_id:
                intermediate_config = config
                break
        
        if not intermediate_config:
            return None
        
        try:
            # Extract value using selectors
            extracted_value = self._extract_value(node_output, intermediate_config.get("selectors", []))
            if extracted_value is None:
                self.logger.warning("No value extracted for intermediate output from node: {}", node_id)
                return None
            
            # Apply transformation if specified
            transformed_value = self._apply_transform(extracted_value, intermediate_config.get("transform"))
            
            # Emit TEXT_MESSAGE events for UI reactivity
            self._emit_intermediate_output_events(node_id, transformed_value, emitter)
            
            return {
                "node_id": node_id,
                "value": transformed_value,
                "config": intermediate_config
            }
            
        except Exception as e:
            self.logger.error("Failed to process intermediate output for node {}: {}", node_id, e)
            return None
    
    def process_final_output(self, results: Dict[str, Any], emitter: AGUIEventEmitter) -> Optional[str]:
        """Process final output and emit TEXT_MESSAGE events."""
        if not self.final_config:
            self.logger.info("No final output configuration found")
            return None
        
        try:
            node_id = self.final_config.get("node")
            selectors = self.final_config.get("selectors", [])
            # Defensive check: ensure selectors is a list (not None)
            if selectors is None:
                selectors = []
            transform = self.final_config.get("transform")
            
            # NEW: Support transform-only mode (no node/selectors required)
            if not node_id or not selectors:
                if not transform:
                    self.logger.warning("Final output config requires either (node + selectors) or transform")
                    return None
                
                # Transform-only mode: pass full results dict to template
                self.logger.info("Processing final output in transform-only mode")
                self.logger.debug("Results dict keys for template: {}", list(results.keys()))
                template = Template(transform)
                final_text = template.render(results=results)
                return final_text
            
            # Legacy mode: extract from specific node
            # Get the node output
            node_output = results.get(node_id)
            if not node_output:
                self.logger.warning(
                    "No output found for final output node: {}. Available keys in results: {}",
                    node_id,
                    list(results.keys()) if isinstance(results, dict) else "results is not a dict"
                )
                return None
            
            # Extract value using selectors
            selector_mode = self.final_config.get("selector_mode", "first")  # Default to "first" for backward compatibility
            extracted_value = self._extract_value(node_output, selectors, selector_mode)
            if extracted_value is None:
                self.logger.warning("No value extracted for final output from node: {}", node_id)
                return None
            
            # Apply transformation if specified
            # Pass both extracted_value (as 'value') and full results dict
            final_text = self._apply_transform(extracted_value, transform, results)
            
            # Don't emit TEXT_MESSAGE events for final output - this will be handled by orchestrator
            # The orchestrator's _build_assistant_responses method already handles final output emission
            
            return final_text
            
        except Exception as e:
            self.logger.error("Failed to process final output: {}", e)
            return None
    
    def _extract_value(self, node_output: Any, selectors: List[str], selector_mode: str = "first") -> Optional[Any]:
        """Extract value from node output using selectors."""
        if not selectors:
            return node_output
        
        # Normalize the output for processing
        # Handle case where node_output is None
        if node_output is None:
            self.logger.warning("node_output is None, cannot extract value")
            return None
        
        parsed_obj = JSONUtils.normalize_for_ui(node_output)
        if parsed_obj is None:
            self.logger.warning("normalized output is None, cannot extract value")
            return None
        
        # Handle multiple selectors based on selector_mode
        if len(selectors) > 1 and selector_mode == "all":
            # Return a dictionary with all available values
            extracted_values = {}
            for selector in selectors:
                # Defensive check: skip None or non-string selectors
                if selector is None or not isinstance(selector, str) or not selector.strip():
                    continue
                
                try:
                    # Handle nested selectors (e.g., "data.final.answer")
                    current = parsed_obj
                    for part in selector.split('.'):
                        if isinstance(current, dict) and part in current:
                            current = current[part]
                        else:
                            current = None
                            break
                    
                    # Check after processing all parts of the selector
                    if current is not None and current != "":
                        # Use the last part of the selector as the key
                        # Defensive check: ensure selector is still valid (not None) before splitting
                        if selector and isinstance(selector, str):
                            key = selector.split('.')[-1]
                            extracted_values[key] = current
                            
                except Exception as e:
                    self.logger.debug("Selector '{}' failed: {}", selector, e)
                    continue
            
            # Return the dictionary if we found any values, otherwise return None
            return extracted_values if extracted_values else None
        
        # For single selector or selector_mode="first", return the first available value (original behavior)
        for selector in selectors:
            # Defensive check: skip None or non-string selectors
            if selector is None or not isinstance(selector, str) or not selector.strip():
                continue
            
            try:
                # Handle nested selectors (e.g., "data.final.answer")
                current = parsed_obj
                for part in selector.split('.'):
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        current = None
                        break
                
                if current is not None and current != "":
                    return current
                    
            except Exception as e:
                self.logger.debug("Selector '{}' failed: {}", selector, e)
                continue
        
        return None
    
    def _apply_transform(self, value: Any, transform: Optional[str], results: Dict[str, Any] = None) -> str:
        """Apply Jinja2 transformation to the extracted value.
        
        Args:
            value: The extracted value to transform
            transform: Jinja2 template string
            results: Optional full results dict to make available in template
        """
        if not transform or not transform.strip():
            return str(value)
        
        try:
            template = Template(transform)
            # Pass value and obj for backward compatibility, plus results if provided
            context = {"value": value, "obj": value}
            if results is not None:
                context["results"] = results
            return template.render(**context)
        except Exception as e:
            self.logger.warning("Transform failed, using raw value: {}", e)
            return str(value)
    
    def _emit_intermediate_output_events(self, node_id: str, value: str, emitter: AGUIEventEmitter) -> None:
        """Emit TEXT_MESSAGE events for intermediate output."""
        try:
            # Start text message
            message_id = emitter.text_message_start(role="assistant")
            
            # Add content with node context
            content = f"[{node_id}] {value}"
            emitter.text_message_content(message_id, content)
            
            # End text message
            emitter.text_message_end(message_id)
            
            self.logger.info("Emitted intermediate output TEXT_MESSAGE events for node: {}", node_id)
            
        except Exception as e:
            self.logger.error("Failed to emit intermediate output events: {}", e)
    
    def has_intermediate_outputs(self) -> bool:
        """Check if there are intermediate outputs configured."""
        return len(self.intermediate_configs) > 0
    
    def has_final_output(self) -> bool:
        """Check if there is a final output configured."""
        return bool(self.final_config)
    
    def get_intermediate_nodes(self) -> List[str]:
        """Get list of nodes that have intermediate outputs configured."""
        return [config.get("node") for config in self.intermediate_configs if config.get("node")]