"""
Database Manager Module
Centralized database operations for sessions and turns
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from topaz_agent_kit.core.chat_storage import ChatStorage
from topaz_agent_kit.core.exceptions import DatabaseError
from topaz_agent_kit.core.session_manager import SessionManager, SessionRestoreResult
from topaz_agent_kit.utils.logger import Logger


class DatabaseManager:
    """Centralized database operations for sessions and turns"""
    
    def __init__(self, chat_storage: ChatStorage, session_manager: SessionManager):
        if not chat_storage:
            raise DatabaseError("ChatStorage is required for DatabaseManager")
        if not session_manager:
            raise DatabaseError("SessionManager is required for DatabaseManager")
            
        self._chat_storage = chat_storage
        self._session_manager = session_manager
        self.logger = Logger("DatabaseManager")
    
    # === SESSION MANAGEMENT ===
    
    def create_session(self, source: str = "cli") -> str:
        """Create a new session using SessionManager (flat schema)."""
        return self._session_manager.create_session(source)
    
    def get_session(self, session_id: str) -> Optional[Any]:
        """Get a session by ID"""
        return self._chat_storage.get_session(session_id)

    def restore_session(self, session_id: str) -> SessionRestoreResult:
        """Restore a session with full context and history"""
        return self._session_manager.restore_session(session_id)

    def get_all_sessions(self, status: str = 'active') -> List[Any]:
        """Get all sessions"""
        return self._chat_storage.get_all_sessions(status)

    def get_turns_for_session(self, session_id: str) -> List[Any]:
        """Get turns for a session"""
        return self._chat_storage.get_turns_for_session(session_id)
    
    def update_turn_entries(self, turn_id: str, entries: List[Dict[str, Any]]) -> bool:
        """Update entries for a turn"""
        return self._chat_storage.update_turn_entries(turn_id, entries)
    
    def get_turn_entries(self, turn_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get entries for a turn"""
        return self._chat_storage.get_turn_entries(turn_id)
    
    def get_all_session_entries(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all entries for a session (merged from all turns)"""
        return self._chat_storage.get_all_session_entries(session_id)
    
    def get_turn_by_run_id(self, run_id: str) -> Optional[Any]:
        """Get turn by run ID"""
        return self._chat_storage.get_turn_by_run_id(run_id)
    
    def update_session_thread_state(self, session_id: str, thread_state: str) -> bool:
        """Update session thread state in database"""
        return self._chat_storage.db.update_chat_session(session_id, {"thread_state": thread_state})
    
    def get_session_thread_state(self, session_id: str) -> Optional[str]:
        """Get session thread state from database"""
        session = self._chat_storage.get_session(session_id)
        if session and hasattr(session, 'thread_state'):
            return session.thread_state
        return None
    
    def update_session_title(self, session_id: str, title: str) -> bool:
        """Update session title in database"""
        return self._chat_storage.db.update_chat_session(session_id, {"title": title})
    
    def get_session_title(self, session_id: str) -> Optional[str]:
        """Get session title from database"""
        session = self._chat_storage.get_session(session_id)
        if session and hasattr(session, 'title'):
            return session.title
        return None
    
    def update_session_pinned(self, session_id: str, pinned: bool, pinned_order: Optional[int] = None) -> bool:
        """Update session pinned status in database"""
        updates = {"pinned": 1 if pinned else 0}
        if pinned:
            # When pinning, use provided pinned_order or keep existing
            if pinned_order is not None:
                updates["pinned_order"] = pinned_order
        else:
            # When unpinning, clear pinned_order to 0
            updates["pinned_order"] = 0
        return self._chat_storage.db.update_chat_session(session_id, updates)
    
    def update_pinned_order(self, session_id: str, pinned_order: int) -> bool:
        """Update session pinned order in database"""
        return self._chat_storage.db.update_chat_session(session_id, {"pinned_order": pinned_order})
    
    # === TURN MANAGEMENT ===
    
    def start_turn(self, session_id: str, user_message: str, pipeline_id: Optional[str] = None, run_id: Optional[str] = None) -> Tuple[int, str, str]:
        """Start a new turn and return (db_turn_id, turn_id, run_id)"""
        db_turn_id, turn_id, generated_run_id = self._chat_storage.start_turn(session_id, user_message, pipeline_id, run_id)
        
        self.logger.info("Turn started: {} (DB: {}, Run: {})", turn_id, db_turn_id, generated_run_id)
        return db_turn_id, turn_id, generated_run_id
    
    def update_turn_progress(self, turn_id: str, updates: Dict[str, Any]) -> bool:
        """Update turn with progressive changes during execution"""
        # Handle append operations for lists
        processed_updates = {}
        for key, value in updates.items():
            if key in ['pipeline_events', 'assistant_responses'] and isinstance(value, list):
                # Get existing data and append
                turn = self._chat_storage.get_turn_by_turn_id(turn_id)
                if not turn:
                    raise DatabaseError(f"Turn not found for update: {turn_id}")
                    
                existing = getattr(turn, key, []) or []
                processed_updates[key] = existing + value
            else:
                processed_updates[key] = value
        
        success = self._chat_storage.update_turn(turn_id, processed_updates)
        if not success:
            raise DatabaseError(f"Failed to update turn progress: {turn_id}")
            
        self.logger.debug("Turn progress updated: {} - {}", turn_id, list(updates.keys()))
        return True
    
    def complete_turn(self, turn_id: str) -> bool:
        """Complete a chat turn"""
        return self._chat_storage.complete_turn(
            turn_id=turn_id
        )
    
    def update_turn_status(self, turn_id: str, status: str, updates: Optional[Dict[str, Any]] = None) -> bool:
        """Update turn status and optional additional fields"""
        turn_updates = {"status": status}
        
        if updates:
            turn_updates.update(updates)
        
        success = self._chat_storage.update_turn(turn_id, turn_updates)
        if not success:
            raise DatabaseError(f"Failed to update turn status: {turn_id}")
        
        self.logger.debug("Turn status updated: {} -> {}", turn_id, status)
        return True
    
    def complete_turn_success(self, turn_id: str, final_data: Dict[str, Any]) -> bool:
        """Complete a successful turn (legacy method - use complete_turn or update_turn_status)"""
        return self.update_turn_status(turn_id, "completed", final_data)
    
    def complete_turn_failure(self, turn_id: str, error_data: Dict[str, Any]) -> bool:
        """Complete a failed turn (legacy method - use update_turn_status)"""
        return self.update_turn_status(turn_id, "failed", error_data)
    
    # === CONTENT AWARENESS ===
    
    def get_available_content(self, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available content entries, optionally filtered by content_type"""
        try:
            return self._chat_storage.get_available_content(content_type)
        except Exception as e:
            self.logger.error("Failed to get available content: {}", e)
            return []
    
    def get_available_content_by_filename(self, file_name: str) -> Optional[Dict[str, Any]]:
        """Get available content entry by filename"""
        return self._chat_storage.get_available_content_by_filename(file_name)
    
    def delete_available_content_by_filename(self, file_name: str) -> bool:
        """Delete available content entry by filename"""
        return self._chat_storage.delete_available_content_by_filename(file_name)
    
    def create_available_content(self, file_name: str, file_type: str, content_type: str, 
                               summary: str, topics: List[str], example_questions: List[str],
                               file_size: Optional[int] = None, word_count: Optional[int] = None) -> bool:
        """Create or update available content entry"""
        return self._chat_storage.create_available_content(
            file_name, file_type, content_type, summary, topics, example_questions, file_size, word_count
        )