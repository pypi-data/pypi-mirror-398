"""
AG-UI Service - Lightweight Wrapper
Provides specialized functionality for AG-UI protocol integration
"""

from typing import Any, Dict, List, Optional
from ag_ui.core import EventType
from topaz_agent_kit.utils.logger import Logger


class AGUIService:
    """Lightweight wrapper for AG-UI specific logic"""
    
    def __init__(self):
        self.logger = Logger("AGUIService")
        self.hitl_gates: Dict[str, Dict] = {}
        self.session_state: Dict[str, Any] = {}
    
    # === HITL MANAGEMENT ===
    def create_hitl_gate(self, gate_id: str, title: str, content: str, options: List[str]) -> Dict[str, Any]:
        """Create HITL approval gate"""
        self.hitl_gates[gate_id] = {
            "title": title,
            "content": content,
            "options": options,
            "status": "pending"
        }
        
        self.logger.info("Created HITL gate: {} with {} options", gate_id, len(options))
        
        return {
            "gate_id": gate_id,
            "title": title,
            "content": content,
            "options": options,
            "status": "pending"
        }
    
    def resolve_hitl_gate(self, gate_id: str, decision: str, actor: str = "user") -> Dict[str, Any]:
        """Resolve HITL gate"""
        if gate_id in self.hitl_gates:
            self.hitl_gates[gate_id]["status"] = "resolved"
            self.hitl_gates[gate_id]["decision"] = decision
            self.hitl_gates[gate_id]["actor"] = actor
            
            self.logger.info("Resolved HITL gate: {} with decision: {} by {}", gate_id, decision, actor)
            
            return {
                "gate_id": gate_id,
                "decision": decision,
                "actor": actor,
                "status": "resolved"
            }
        else:
            self.logger.warning("HITL gate not found: {}", gate_id)
            return {}
    
    def get_hitl_gate(self, gate_id: str) -> Optional[Dict[str, Any]]:
        """Get HITL gate status"""
        return self.hitl_gates.get(gate_id)
    
    def list_hitl_gates(self) -> List[str]:
        """List all HITL gate IDs"""
        return list(self.hitl_gates.keys())
    
    # === SESSION MANAGEMENT ===
    def update_session_state(self, key: str, value: Any) -> None:
        """Update session state"""
        self.session_state[key] = value
        self.logger.debug("Updated session state: {} = {}", key, type(value).__name__)
    
    def get_session_state(self, key: str, default: Any = None) -> Any:
        """Get session state"""
        return self.session_state.get(key, default)
    
    def clear_session_state(self) -> None:
        """Clear all session state"""
        self.session_state.clear()
        self.logger.info("Cleared session state")
    
    def get_all_session_state(self) -> Dict[str, Any]:
        """Get all session state"""
        return self.session_state.copy()
    
    # === CONVERSATION MANAGEMENT ===
    def create_conversation_turn(self, turn_id: str, user_message: str) -> Dict[str, Any]:
        """Create new conversation turn"""
        turn_data = {
            "turn_id": turn_id,
            "user_message": user_message,
            "timestamp": self._get_timestamp(),
            "status": "started"
        }
        
        self.logger.info("Created conversation turn: {}", turn_id)
        return turn_data
    
    def complete_conversation_turn(self, turn_id: str, assistant_response: str) -> Dict[str, Any]:
        """Complete conversation turn"""
        turn_data = {
            "turn_id": turn_id,
            "assistant_response": assistant_response,
            "timestamp": self._get_timestamp(),
            "status": "completed"
        }
        
        self.logger.info("Completed conversation turn: {}", turn_id)
        return turn_data
    
    # === ERROR HANDLING ===
    def handle_error(self, error_type: str, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle errors with context"""
        error_data = {
            "error_type": error_type,
            "message": message,
            "context": context or {},
            "timestamp": self._get_timestamp()
        }
        
        self.logger.error("Handled error: {} - {}", error_type, message)
        return error_data
    
    # === UTILITY METHODS ===
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "hitl_gates_count": len(self.hitl_gates),
            "session_state_keys": len(self.session_state),
            "active_gates": [gate_id for gate_id, gate in self.hitl_gates.items() if gate.get("status") == "pending"]
        }
    
    # === EVENT CONVERSION ===
    def convert_event(self, internal_event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert internal events to AG-UI protocol events.
        This handles specific internal events that need conversion.
        """
        event_type = internal_event.get("type", "")
        
        try:
            # Handle specific internal events that need conversion
            if event_type == "gate_approval_required":
                return [self._handle_gate_approval_required(internal_event)]
            elif event_type == "hitl_result":
                return [self._handle_hitl_result(internal_event)]
            elif event_type == "hitl_request":
                self.logger.info("Converting hitl_request event: {}", internal_event.get("gate_id"))
                return [self._handle_hitl_request(internal_event)]
            
            # If it's already an AG-UI event, pass it through
            if event_type in EventType.__members__.values():
                return [internal_event]
            
            # Otherwise, wrap as a RAW event
            return [{
                "type": EventType.RAW,
                "data": internal_event
            }]
                
        except Exception as e:
            self.logger.error("Failed to convert event {}: {}", event_type, e)
            return [{
                "type": EventType.RAW,
                "data": internal_event
            }]

    def _handle_gate_approval_required(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert internal gate_approval_required to AG-UI CUSTOM event"""
        return {
            "type": EventType.CUSTOM,
            "name": "gate_approval_required",
            "value": {
                "gate_id": event.get("gate_id"),
                "node_id": event.get("node_id"),
                "title": event.get("title"),
                "description": event.get("description"),
                "fields": event.get("fields"),
                "deadline_at_ms": event.get("deadline_at_ms"),
                "timeout_ms": event.get("timeout_ms"),
                "requested_at_ms": event.get("requested_at_ms"),
                "on_timeout": event.get("on_timeout"),
            }
        }

    def _handle_hitl_result(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert internal hitl_result to AG-UI CUSTOM event"""
        return {
            "type": EventType.CUSTOM,
            "name": "hitl_result",
            "value": {
                "gate_id": event.get("gate_id"),
                "decision": event.get("decision"),
                "reason": event.get("reason"),
                "actor": event.get("actor"),
                "data": event.get("data"),
            }
        }

    def _handle_hitl_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert internal hitl_request to AG-UI CUSTOM event and create gate"""
        gate_id = event.get("gate_id")
        title = event.get("title", "Approval Required")
        description = event.get("description", "")
        fields = event.get("fields", [])
        
        self.logger.info("Processing HITL request: gate_id={}, title={}", gate_id, title)
        
        # Create the gate in the service
        options = ["approve", "reject"]  # Default options
        self.create_hitl_gate(gate_id, title, description, options)
        
        return {
            "type": EventType.CUSTOM,
            "name": "hitl_request",
            "value": {
                "gate_id": gate_id,
                "node_id": event.get("node_id"),
                "title": title,
                "description": description,
                "fields": fields,
                "buttons": event.get("buttons", {}),
                "deadline_at_ms": event.get("deadline_at_ms"),
                "timeout_ms": event.get("timeout_ms"),
                "requested_at_ms": event.get("requested_at_ms"),
                "on_timeout": event.get("on_timeout"),
            }
        }