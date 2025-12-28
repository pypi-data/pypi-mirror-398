from typing import Any, Dict

from topaz_agent_kit.transport.types import TransportMode, Protocol
from topaz_agent_kit.transport.local_client import LocalClient
from topaz_agent_kit.transport.a2a_sdk_client import A2ASDKClient

class DualTransportClient:
    def __init__(self, base_url: str, agents_by_id: Dict[str, Any] = None, mode: TransportMode = None, 
                 emitter: Any = None, config: Dict[str, Any] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.agents_by_id = agents_by_id or {}
        self.emitter = emitter
        self.config = config or {}
        # Auto-detect mode if not provided
        self.mode = mode or (TransportMode.LOCAL if base_url.startswith("local://") else TransportMode.REMOTE)

    async def send(self, protocol: str, *, sender: str, recipient: str, content: Dict[str, Any]) -> Dict[str, Any]:
        # Convert string to Protocol enum - fail fast if invalid
        if not protocol:
            raise ValueError("Protocol must be specified")
        
        try:
            protocol_enum = Protocol(protocol.lower())
        except ValueError:
            raise ValueError(f"Unsupported protocol: {protocol}. Only 'a2a' and 'in-proc' are supported.")
        
        # Route to local or remote client
        if self.mode == TransportMode.LOCAL:
            client = LocalClient(agents_by_id=self.agents_by_id, emitter=self.emitter)
            return await client.send(protocol_enum, sender=sender, recipient=recipient, 
                                   content=content)
        else:
            # Always use A2A for remote
            client = A2ASDKClient(
                url=self.base_url,
                timeout=self.config.get("timeout", 30000),
                retry_attempts=self.config.get("retry_attempts", 3),
                emitter=self.emitter
            )
            result = await client.send_message(
                sender=sender,
                recipient=recipient,
                content=content
            )
            # Result is clean - agent_inputs stay in context only
            response = {"content": result if isinstance(result, dict) else {"result": str(result)}}
            return response

