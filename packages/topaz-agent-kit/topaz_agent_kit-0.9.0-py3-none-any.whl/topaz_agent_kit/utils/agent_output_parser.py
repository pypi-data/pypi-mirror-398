"""
Utility class for parsing and validating agent outputs.
Provides consistent JSON parsing and validation across all agents.
"""

import json
from typing import Any, Dict, List
from topaz_agent_kit.core.exceptions import AgentError
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.json_utils import JSONUtils
from jsonschema import validate, ValidationError

class AgentOutputParser:
    """Parse and validate agent outputs with consistent error handling"""
    
    def __init__(self, agent_label: str = "Agent"):
        self.logger = Logger(agent_label)
    
    @staticmethod
    def extract_text_content(output: Any, agent_label: str = "Agent") -> str:
        """Extract text content from various agent output formats
        
        Handles different framework response structures:
        - Semantic Kernel: ChatMessageContent with items[].text
        - String: Direct JSON string (strips markdown code blocks)
        - Dict: Already parsed dictionary
        - Other objects: Try common text attributes
        
        Args:
            output: Agent output (various types)
            agent_label: Label for logging
            
        Returns:
            Extracted text content as string (cleaned of markdown)
        """
        logger = Logger(agent_label)
        
        # Already a string - return as is
        if isinstance(output, str):
            return output
        
        # Already a dict - convert to JSON string for consistency
        if isinstance(output, dict):
            return json.dumps(output)
        
        # Try Semantic Kernel structure: ChatMessageContent with items
        if hasattr(output, 'items') and output.items:
            try:
                # Get text from first TextContent item
                if hasattr(output.items[0], 'text'):
                    logger.debug(f"Extracted text from ChatMessageContent.items[0].text")
                    return output.items[0].text
            except (IndexError, AttributeError) as e:
                logger.debug(f"Failed to extract from items: {e}")
        
        # Try common text attributes
        for attr in ['content', 'text', 'message', 'output']:
            if hasattr(output, attr):
                value = getattr(output, attr)
                if isinstance(value, str):
                    logger.debug(f"Extracted text from .{attr} attribute")
                    return value
        
        # Last resort: convert to string
        logger.debug(f"Converting {type(output)} to string as fallback")
        return str(output)
    
    @staticmethod
    def parse_agent_output(
        output: Any, 
        required_fields: List[str] = None, 
        agent_label: str = "Agent",
        agent_id: str = None,
        lenient: bool = False
    ) -> Dict[str, Any]:
        """Parse agent output with validation
        
        Args:
            output: Agent output (string, dict, or framework-specific object)
            required_fields: List of required field names
            agent_label: Label for logging
            agent_id: Agent ID to inject into output if not present
            lenient: If True, use lenient parsing (extract partial data, log warnings instead of failing)
                    This is useful for extractor/evaluator/scorer agents that may return incomplete JSON
            
        Returns:
            Parsed output as dictionary with agent_id injected if provided
            
        Raises:
            AgentError: If output is invalid or missing required fields (unless lenient=True)
        """
        logger = Logger(agent_label)
        
        # First, extract text content from various formats
        text_content = AgentOutputParser.extract_text_content(output, agent_label)
        
        # If already a dict (extract_text_content returned JSON string), parse it
        if isinstance(text_content, str):
            # Use JSONUtils for robust JSON parsing with automatic fixes
            # For lenient mode, try expect_json=True first to get better error messages
            # If that fails, fall back to expect_json=False
            if lenient:
                try:
                    parsed = JSONUtils.parse_json_from_text(text_content, expect_json=True)
                except ValueError:
                    # If strict parsing fails, try lenient parsing
                    logger.warning(f"Strict JSON parsing failed for {agent_label}, attempting lenient parsing")
                    parsed = JSONUtils.parse_json_from_text(text_content, expect_json=False)
            else:
                # expect_json=False allows plain text responses (like CrewAI sometimes returns)
                parsed = JSONUtils.parse_json_from_text(text_content, expect_json=False)
            logger.debug(f"Successfully parsed agent output using JSONUtils")
        else:
            parsed = text_content
        
        # Handle content wrapping - if we got {"content": "..."}, try to extract JSON from the content
        # This happens when JSON parsing fails and falls back to content wrapper
        if isinstance(parsed, dict) and len(parsed) == 1 and "content" in parsed:
            content_value = parsed["content"]
            if isinstance(content_value, str):
                # The content might be malformed JSON that failed to parse, OR it might be legitimate plain text
                # Try parsing it again with expect_json=False to enable balanced JSON extraction
                # This allows _extract_all_balanced to find valid JSON objects even if the overall structure is broken
                logger.warning(f"Output wrapped in 'content', attempting to extract JSON from content for {agent_label}")
                try:
                    # Use expect_json=False to enable balanced JSON extraction for malformed JSON
                    # This will use _extract_all_balanced to find and extract valid JSON objects from the text
                    extracted = JSONUtils.parse_json_from_text(content_value, expect_json=False)
                    if isinstance(extracted, dict):
                        # Check if we got a valid JSON object (not wrapped in content again)
                        if "content" not in extracted or len(extracted) > 1:
                            # Successfully extracted a valid JSON object
                            parsed = extracted
                            logger.info(f"Successfully extracted JSON from content wrapper for {agent_label}")
                        else:
                            # Still wrapped in content - check if it's the same content (legitimate plain text)
                            # vs different content (extraction attempted but failed)
                            extracted_content = extracted.get("content", "")
                            if extracted_content == content_value:
                                # Same content: this is legitimate plain text, not malformed JSON
                                # Keep the content wrapper as-is (acceptable for group chat patterns, etc.)
                                logger.debug(f"Keeping content wrapper for {agent_label} (legitimate plain text response)")
                            else:
                                # Different content but still wrapped: extraction attempted but couldn't find valid JSON
                                # Only add error in strict mode (not lenient)
                                if not lenient:
                                    logger.warning(f"Could not extract valid JSON from content wrapper for {agent_label}, JSON may be too malformed")
                                    parsed["error"] = f"Failed to parse JSON output. Raw content: {content_value[:200]}..."
                                else:
                                    # Lenient mode: keep the content wrapper without error
                                    logger.debug(f"Keeping content wrapper for {agent_label} (lenient mode allows plain text)")
                    else:
                        logger.warning(f"Extracted non-dict from content wrapper for {agent_label}, keeping wrapper")
                except Exception as e:
                    # If extraction fails, log the error but keep the content wrapper
                    # Only add error field in strict mode (not lenient)
                    logger.warning(f"Could not extract JSON from content wrapper for {agent_label}: {e}")
                    if not lenient:
                        # Add error field to help with debugging (only in strict mode)
                        parsed["error"] = f"Failed to parse JSON output. Raw content: {content_value[:200]}..."
                    # In lenient mode, keep the content wrapper without error (plain text is acceptable)
        
        # Ensure output is a dictionary
        if not isinstance(parsed, dict):
            if lenient:
                logger.warning(f"Agent output is not a dictionary: {type(parsed)}, wrapping in error structure")
                parsed = {
                    "error": f"Agent output is not a dictionary, got {type(parsed)}. Raw output: {str(parsed)[:200]}"
                }
            else:
                logger.error(f"Agent output is not a dictionary: {type(parsed)}")
                raise AgentError(f"Agent output must be a dictionary, got {type(parsed)}")
        
        # Inject agent_id if provided and not already present
        if agent_id and "agent_id" not in parsed:
            parsed["agent_id"] = agent_id
            logger.debug(f"Injected agent_id: {agent_id}")
        
        # Validate required fields
        if required_fields:
            missing_fields = [field for field in required_fields if field not in parsed]
            if missing_fields:
                if lenient:
                    # In lenient mode, log warning and add error field instead of raising
                    logger.warning(f"Missing required fields for {agent_label}: {missing_fields}. Adding to error field.")
                    if "error" not in parsed:
                        parsed["error"] = f"Missing required fields: {missing_fields}"
                    else:
                        # Append to existing error
                        existing_error = parsed["error"]
                        parsed["error"] = f"{existing_error}. Missing required fields: {missing_fields}"
                else:
                    logger.error(f"Missing required fields: {missing_fields}")
                    raise AgentError(f"Agent output missing required fields: {missing_fields}")
            else:
                logger.debug(f"All required fields present: {required_fields}")
        
        return parsed
    
    @staticmethod
    def validate_output_schema(output: Dict[str, Any], schema: Dict[str, Any], agent_label: str = "Agent") -> bool:
        """Validate output against a JSON schema
        
        Args:
            output: Agent output dictionary
            schema: JSON schema for validation
            agent_label: Label for logging
            
        Returns:
            True if valid, False otherwise
        """
        logger = Logger(agent_label)
        
        try:
            validate(instance=output, schema=schema)
            logger.debug("Output validation successful")
            return True
        except ValidationError as e:
            logger.error(f"Output validation failed: {e}")
            return False
    
    @staticmethod
    def extract_field(output: Any, field_name: str, default: Any = None, agent_label: str = "Agent") -> Any:
        """Extract a specific field from agent output with fallback
        
        Args:
            output: Agent output
            field_name: Name of field to extract
            default: Default value if field not found
            agent_label: Label for logging
            
        Returns:
            Field value or default
        """
        logger = Logger(agent_label)
        
        try:
            parsed = AgentOutputParser.parse_agent_output(output, agent_label=agent_label)
            value = parsed.get(field_name, default)
            
            if value is None:
                logger.warning(f"Field '{field_name}' not found in output, using default: {default}")
            
            return value
        except Exception as e:
            logger.warning(f"Failed to extract field '{field_name}': {e}, using default: {default}")
            return default 