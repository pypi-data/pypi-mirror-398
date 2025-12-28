"""
Chat Storage Module
High-level abstraction for chat session and turn management
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from topaz_agent_kit.core.chat_database import ChatDatabase
from topaz_agent_kit.core.exceptions import DatabaseError
from topaz_agent_kit.utils.logger import Logger


@dataclass
class ChatSession:
    """Chat session data structure - simplified"""
    id: str
    source: str
    created_at: datetime
    last_accessed: datetime
    status: str = 'active'
    thread_state: Optional[str] = None
    title: str = 'New chat'
    pinned: bool = False
    pinned_order: int = 0


@dataclass
class ChatTurn:
    """Chat turn data structure"""
    id: int
    session_id: str
    turn_number: int
    turn_id: str
    entries: List[Dict[str, Any]]  # Entry[] array from this turn
    pipeline_id: Optional[str]
    run_id: Optional[str]
    status: str
    started_at: datetime
    error_message: Optional[str]
    feedback: Optional[Dict[str, Any]] = None  # Feedback data (type, comment, timestamp)


class ChatStorage:
    """High-level chat storage abstraction"""
    
    def __init__(self, db_path: str):
        self.logger = Logger("ChatStorage")
        self.db = ChatDatabase(db_path)
        self.logger.info("Chat storage initialized")
    
    # === SESSION MANAGEMENT ===
    
    def create_session(self, source: str = "fastapi") -> str:
        """Create a new chat session - simplified"""
        session_id = str(int(datetime.now().timestamp() * 1000))  # No "session_" prefix
        
        success = self.db.create_chat_session(session_id, source)
        if success:
            self.logger.info("Created new session: {}", session_id)
            return session_id
        else:
            raise DatabaseError("Failed to create session")
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get chat session by ID - simplified"""
        session_data = self.db.get_chat_session(session_id)
        if not session_data:
            return None

        # Normalize pinned and pinned_order fields
        raw_pinned = session_data.get('pinned', 0)
        pinned = bool(raw_pinned) if isinstance(raw_pinned, int) else bool(raw_pinned)
        raw_order = session_data.get('pinned_order', 0)
        try:
            pinned_order = int(raw_order)
        except (TypeError, ValueError):
            pinned_order = 0

        return ChatSession(
            id=session_data['id'],
            source=session_data['source'],
            status=session_data['status'],
            created_at=datetime.fromisoformat(session_data['created_at']),
            last_accessed=datetime.fromisoformat(session_data['last_accessed']),
            thread_state=session_data.get('thread_state'),
            title=session_data.get('title', 'New chat'),
            pinned=pinned,
            pinned_order=pinned_order,
        )
    
    
    # === TURN MANAGEMENT ===
    
    def start_turn(self, session_id: str, user_message: str, pipeline_id: Optional[str] = None, run_id: Optional[str] = None) -> Tuple[int, str, str]:
        """Start a new chat turn"""
        # Get next turn number
        turns = self.db.get_chat_turns(session_id)
        turn_number = len(turns) + 1
        
        # Generate turn ID
        turn_id = f"turn_{int(datetime.now().timestamp() * 1000)}"
        
        # Use provided run_id or generate one
        if not run_id:
            run_id = f"{session_id}_{turn_number}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create turn
        db_turn_id = self.db.create_chat_turn(session_id, turn_number, pipeline_id, run_id)
        if not db_turn_id:
            raise DatabaseError(f"Failed to create turn for session: {session_id}")
        
        # Update turn with turn_id
        self.db.update_chat_turn(db_turn_id, {"turn_id": turn_id})
        
        self.logger.info("Started turn: {} (run_id: {})", turn_number, run_id)
        return db_turn_id, turn_id, run_id
    
    def update_turn(self, turn_id: str, updates: Dict[str, Any]) -> bool:
        """Update chat turn with new data"""
        # Find turn by turn_id
        turn = self.get_turn_by_turn_id(turn_id)
        if not turn:
            self.logger.error("Turn not found: {}", turn_id)
            return False
        
        return self.db.update_chat_turn(turn.id, updates)
    
    def complete_turn(self, turn_id: str) -> bool:
        """Complete a chat turn"""
        updates = {
            "status": "completed"
        }
        
        success = self.update_turn(turn_id, updates)
        return success
    
    def get_turn(self, turn_id: int) -> Optional[ChatTurn]:
        """Get chat turn by database ID"""
        turns = self.db.get_chat_turns("")  # Get all turns
        for turn_data in turns:
            if turn_data['id'] == turn_id:
                return self._convert_to_chat_turn(turn_data)
        return None
    
    def get_turn_by_turn_id(self, turn_id: str) -> Optional[ChatTurn]:
        """Get chat turn by turn_id"""
        # Search across all sessions for the turn_id
        all_sessions = self.db.get_all_sessions()
        for session_data in all_sessions:
            turns = self.db.get_chat_turns(session_data['id'])
            for turn_data in turns:
                if turn_data.get('turn_id') == turn_id:
                    return self._convert_to_chat_turn(turn_data)
        return None
    
    def get_turns_for_session(self, session_id: str) -> List[ChatTurn]:
        """Get all turns for a session"""
        turns_data = self.db.get_chat_turns(session_id)
        return [self._convert_to_chat_turn(turn_data) for turn_data in turns_data]
    
    def get_turn_by_run_id(self, run_id: str) -> Optional[ChatTurn]:
        """Get chat turn by run ID"""
        turn_data = self.db.get_chat_turn_by_run_id(run_id)
        return self._convert_to_chat_turn(turn_data) if turn_data else None
    
    
    # === ENTRIES MANAGEMENT ===
    
    def update_turn_entries(self, turn_id: str, entries: List[Dict[str, Any]]) -> bool:
        """Update entries for a turn"""
        return self.update_turn(turn_id, {"entries": entries})
    
    def get_turn_entries(self, turn_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get entries for a turn"""
        turn = self.get_turn_by_turn_id(turn_id)
        if not turn:
            return None
        return turn.entries
    
    def get_all_session_entries(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all entries for a session (merged from all turns)"""
        turns = self.get_turns_for_session(session_id)
        all_entries = []
        for turn in turns:
            if turn.entries:
                all_entries.extend(turn.entries)
        return all_entries
    
    # === UTILITY METHODS ===
    
    def _convert_to_chat_turn(self, turn_data: Dict[str, Any]) -> ChatTurn:
        """Convert database turn data to ChatTurn object"""
        # Parse feedback if it exists
        feedback = None
        if turn_data.get('feedback'):
            try:
                import json
                if isinstance(turn_data['feedback'], str):
                    feedback = json.loads(turn_data['feedback'])
                else:
                    feedback = turn_data['feedback']
            except (json.JSONDecodeError, TypeError):
                feedback = None
        
        return ChatTurn(
            id=turn_data['id'],
            session_id=turn_data['session_id'],
            turn_number=turn_data['turn_number'],
            turn_id=turn_data.get('turn_id', ''),
            entries=turn_data.get('entries', []),
            pipeline_id=turn_data.get('pipeline_id'),
            run_id=turn_data.get('run_id'),
            status=turn_data['status'],
            started_at=datetime.fromisoformat(turn_data['started_at']),
            error_message=turn_data.get('error_message'),
            feedback=feedback
        )
    
    
    def get_all_sessions(self, status: str = 'active') -> List[ChatSession]:
        """Get all sessions with given status - simplified"""
        sessions_data = self.db.get_all_sessions(status)
        return [
            ChatSession(
                id=session_data['id'],
                source=session_data['source'],
                status=session_data['status'],
                created_at=datetime.fromisoformat(session_data['created_at']),
                last_accessed=datetime.fromisoformat(session_data['last_accessed']),
                thread_state=session_data.get('thread_state'),
                title=session_data.get('title', 'New chat'),
                pinned=bool(session_data.get('pinned', 0)) if isinstance(session_data.get('pinned', 0), int) else bool(session_data.get('pinned', False)),
                pinned_order=int(session_data.get('pinned_order', 0) or 0),
            )
            for session_data in sessions_data
        ]
    
    def delete_session(self, session_id: str) -> bool:
        """Delete chat session and all associated turns"""
        return self.db.delete_chat_session(session_id)
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        return self.db.get_database_stats()
    
    # === LLM-BASED SESSION SUMMARY ===
    
    
    # === AVAILABLE CONTENT MANAGEMENT ===
    
    def create_available_content(self, file_name: str, file_type: str, content_type: str, 
                               summary: str, topics: List[str], example_questions: List[str],
                               file_size: Optional[int] = None, word_count: Optional[int] = None) -> bool:
        """Create or update available content entry"""
        return self.db.create_available_content(
            file_name, file_type, content_type, summary, topics, example_questions, file_size, word_count
        )
    
    def get_available_content(self, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available content entries, optionally filtered by content_type"""
        return self.db.get_available_content(content_type)
    
    def get_available_content_by_filename(self, file_name: str) -> Optional[Dict[str, Any]]:
        """Get available content entry by filename"""
        return self.db.get_available_content_by_filename(file_name)
    
    def delete_available_content_by_filename(self, file_name: str) -> bool:
        """Delete available content entry by filename"""
        return self.db.delete_available_content_by_filename(file_name)
    
    def update_available_content(self, file_name: str, **updates) -> bool:
        """Update available content entry with provided fields"""
        return self.db.update_available_content(file_name, **updates)
    
    def delete_available_content(self, file_name: str) -> bool:
        """Delete available content entry"""
        return self.db.delete_available_content(file_name)