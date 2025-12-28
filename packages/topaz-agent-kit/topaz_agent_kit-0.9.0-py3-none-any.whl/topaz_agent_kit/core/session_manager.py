"""
Session Manager Module
Handles session lifecycle, context management, and automatic cleanup
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from topaz_agent_kit.core.chat_storage import ChatStorage, ChatSession, ChatTurn
from topaz_agent_kit.utils.logger import Logger


@dataclass
class SessionRestoreResult:
    """Result of session restoration"""
    session: ChatSession
    turns: List[ChatTurn]


class SessionManager:
    """Manages chat sessions and automatic cleanup"""
    
    def __init__(self, chat_storage: ChatStorage):
        self.logger = Logger("SessionManager")
        self.chat_storage = chat_storage
        self.logger.info("Session manager initialized")
    
    # === SESSION LIFECYCLE MANAGEMENT ===
    
    def create_session(self, source: str = "cli") -> str:
        """Create a new chat session using flat schema"""
        self.logger.info("Creating new session (source={}): flat schema", source)
        session_id = self.chat_storage.create_session(source)
        self.logger.success("Session created successfully: {}", session_id)
        return session_id
    
    def restore_session(self, session_id: str) -> SessionRestoreResult:
        """Restore a session with full context and history"""
        self.logger.info("Restoring session: {}", session_id)
        
        # Get session
        session = self.chat_storage.get_session(session_id)
        if not session:
            raise RuntimeError(f"Session not found: {session_id}")
        
        # Get all turns
        turns = self.chat_storage.get_turns_for_session(session_id)
        
        # Update last accessed
        self.chat_storage.db.update_chat_session(session_id, {
            "last_accessed": datetime.now()
        })
        
        result = SessionRestoreResult(
            session=session,
            turns=turns
        )
        
        self.logger.success("Session restored: {} turns", len(turns))
        return result
    
    
    def archive_session(self, session_id: str, reason: str = "manual") -> bool:
        """Archive a session (soft delete)"""
        self.logger.info("Archiving session: {} - {}", session_id, reason)
        
        success = self.chat_storage.db.update_chat_session(session_id, {
            "status": "archived"
        })
        
        if success:
            self.logger.success("Session archived: {}", session_id)
        else:
            self.logger.error("Failed to archive session: {}", session_id)
        
        return success
    
    def delete_session(self, session_id: str) -> bool:
        """Permanently delete a session and all its data"""
        self.logger.info("Deleting session: {}", session_id)
        
        success = self.chat_storage.delete_session(session_id)
        if success:
            self.logger.success("Session deleted: {}", session_id)
        else:
            self.logger.error("Failed to delete session: {}", session_id)
        
        return success
    