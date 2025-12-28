"""
Official A2A SDK client implementation for MVP2.5.1
Replaces HTTP-based communication with native A2A SDK calls
"""

from typing import Any, Dict, Optional

from a2a.client import A2ACardResolver, ClientFactory, ClientConfig
from a2a.types import Message, Task, TaskStatusUpdateEvent, TaskArtifactUpdateEvent, AgentCard, Part, Role, TextPart
import httpx
import json
import uuid

from topaz_agent_kit.core.exceptions import CommunicationError
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.json_utils import JSONUtils


class A2ASDKClient:
    """Official A2A SDK client with proper error handling and logging"""
    
    def __init__(self, url: str, timeout: int = 30000, retry_attempts: int = 3, emitter: Optional[Any] = None):
        """
        Initialize A2A SDK client
        
        Args:
            url: Remote agent service URL
            timeout: Request timeout in milliseconds
            retry_attempts: Number of retry attempts on failure
            emitter: Event emitter for protocol events
        """
        # Normalize URL: convert 0.0.0.0 to 127.0.0.1 for client connections
        # 0.0.0.0 is a bind address (listen on all interfaces), not a destination address
        if "0.0.0.0" in url:
            url = url.replace("0.0.0.0", "127.0.0.1")
        
        self.url = url
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.emitter = emitter
        self.logger = Logger("A2ASDKClient")
        self.client = None
        self.agent_card = None
        
        self.logger.debug("Created A2A SDK client for URL: {} (timeout: {}ms)", url, timeout)
    
    async def _ensure_client(self):
        """Ensure A2A client is initialized"""
        if self.client is not None:
            return
        
        try:
            # Create httpx client with redirect following
            httpx_client = httpx.AsyncClient(
                timeout=self.timeout/1000,  # Convert to seconds
                follow_redirects=True  # Follow redirects automatically
            )
            
            # Initialize A2A card resolver with the full URL
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=self.url
            )
            
            # Fetch agent card
            self.agent_card = await resolver.get_agent_card()
            self.logger.debug("Fetched agent card: {}", self.agent_card.name)
            
            # Create A2A client
            config = ClientConfig(httpx_client=httpx_client)
            client_factory = ClientFactory(config)
            self.client = client_factory.create(card=self.agent_card)
            
            self.logger.success("A2A client initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize A2A client: {}", e)
            raise CommunicationError(f"A2A client initialization failed: {str(e)}")
    
    async def send_message(self, sender: str, recipient: str, content: Dict[str, Any], 
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send message using official A2A SDK with proper error handling
        
        Args:
            sender: Sender agent ID
            recipient: Recipient agent ID
            content: Message content
            metadata: Optional metadata
            
        Returns:
            Response from the remote agent
            
        Raises:
            CommunicationError: If A2A communication fails
        """
        try:
            await self._ensure_client()
            
            self.logger.input("Sending A2A message: content_keys={}", 
                             len(content) if isinstance(content, dict) else 0)
            
            # Create A2A message with proper structure
            # Send content as JSON to preserve structure for remote agents
            content_json = json.dumps(content, default=str)
            message = Message(
                role=Role.user,
                messageId=str(uuid.uuid4()),
                parts=[Part(root=TextPart(text=content_json))]
            )
            
            # Send message and collect responses
            responses = []
            async for response in self.client.send_message(message):
                responses.append(response)
                self.logger.debug("Received A2A response: {}", response)
            
            # Convert responses to our expected format
            if responses:
                # Extract text from the last response
                last_response = responses[-1]
                if hasattr(last_response, 'parts') and last_response.parts:
                    text_parts = []
                    for part in last_response.parts:
                        if hasattr(part, 'root') and hasattr(part.root, 'text'):
                            text_parts.append(part.root.text)
                    result_text = " ".join(text_parts)
                else:
                    result_text = str(last_response)
                
                # Try to parse as JSON - A2A service now sends full result structure as JSON
                try:
                    parsed_content = JSONUtils.parse_json_from_text(result_text)
                    if isinstance(parsed_content, dict):
                        # Check if this is an error response
                        if "error" in parsed_content:
                            error_msg = parsed_content.get("error", "")
                            # Only log error if it's non-empty (successful runs may have empty error field)
                            if error_msg:
                                self.logger.error("A2A agent {} returned error: {}", recipient, error_msg)
                                # Return error structure for proper handling
                                return {"content": parsed_content, "error": error_msg, "responses": len(responses)}
                            # Empty error field - treat as success, continue with normal response
                        
                        # Full result structure (may include agent_inputs at top level)
                        # agent_inputs will be extracted by AgentRunner._extract_and_emit_step_input()
                        response = {"content": parsed_content, "responses": len(responses)}
                        # Preserve agent_inputs if present (for step_input extraction)
                        if "agent_inputs" in parsed_content:
                            response["agent_inputs"] = parsed_content["agent_inputs"]
                        return response
                except (json.JSONDecodeError, TypeError):
                    pass  # Not JSON, continue with text response
                
                self.logger.success("A2A response received from agent: {} with length: {} chars", recipient, len(result_text))
                return {"content": result_text, "responses": len(responses)}
            else:
                self.logger.warning("No response received from A2A agent: {}", recipient)
                return {"content": "No response received", "responses": 0}
            
        except Exception as e:
            self.logger.error("A2A SDK client error: {} for agent: {}", str(e), recipient)
            raise CommunicationError(f"A2A communication failed: {str(e)}")
    
    async def close(self):
        """Close the A2A client"""
        if self.client and hasattr(self.client, 'close'):
            await self.client.close()
        self.client = None
        self.agent_card = None