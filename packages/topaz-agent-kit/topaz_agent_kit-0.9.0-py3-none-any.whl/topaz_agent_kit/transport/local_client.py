from typing import Any, Dict, Optional

from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.transport.types import Protocol


class LocalClient:
    """Client for handling local (in-process) agent calls"""
    
    def __init__(self, agents_by_id: Dict[str, Any], emitter: Any = None):
        self.agents_by_id = agents_by_id
        self.emitter = emitter
        self._logger = Logger("LocalClient")
    
    async def send(self, protocol: Protocol, *, sender: str, recipient: str, 
                   content: Dict[str, Any]) -> Dict[str, Any]:
        """Handle local agent calls - always uses IN-PROC regardless of configured protocol"""
        
        # Get the agent instance
        ag = self.agents_by_id.get(recipient)
        if ag is None:
            self._logger.warning("Local agent not found: {}", recipient)
            return {"error": f"agent not found: {recipient}"}
        
        # Execute agent locally (no protocol message creation needed)
        return await self._execute_agent(ag, recipient, content)
    
    async def _execute_agent(self, agent: Any, recipient: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent locally with initialization"""
        try:
            # Initialize agent if not already initialized
            if hasattr(agent, 'initialize') and not agent.is_initialized():
                context_data = content.get("context", {})
                init_context = {
                    "model": context_data.get("model"),
                    "mcp_tools": context_data.get("mcp_tools", []),
                    "project_dir": context_data.get("project_dir"),
                    "emitter": context_data.get("emitter"),
                    "mcp_client": context_data.get("mcp_client")
                }
                await agent.initialize(init_context)
                self._logger.debug("Initialized local agent {}", recipient)
            
            # Prepare execution data
            execution_data = {
                "text": content.get("text", ""),
                "input": content.get("input", ""),
                "node_id": recipient,
            }
            
            # Prepare context
            context = content.get("context", {})
            # Include execution data in context so agents can access it
            context.update(execution_data)
            
            # Execute the agent (all agents have async execute method)
            result = await agent.execute(context)
            
            # Result is clean - agent_inputs stay in context only
            response = {"content": result if isinstance(result, dict) else {"result": str(result)}}
            return response
            
        except Exception as e:
            self._logger.error("Local agent {} execution failed: {}", recipient, e)
            return {"error": str(e)}