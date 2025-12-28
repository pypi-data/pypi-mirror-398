"""
Chat Database Module
Handles SQLite database operations for chat sessions, turns, and context management
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

from topaz_agent_kit.utils.logger import Logger


class ChatDatabase:
    """SQLite database manager for chat sessions, turns, and context storage"""
    
    def __init__(self, db_path: str = "data/chat.db"):
        self.logger = Logger("ChatDatabase")
        self.db_path = Path(db_path)
        
        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Chat database initialized: {}", self.db_path.absolute())
        
        # Initialize database schema
        self._initialize_schema()
    
    def _initialize_schema(self) -> None:
        """Create database tables and indexes"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create chat_sessions table - simplified
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    source TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    thread_state TEXT,
                    title TEXT DEFAULT 'New chat'
                )
            """)
            
            # Add missing columns to existing tables (if not exists)
            # SQLite doesn't support IF NOT EXISTS for ALTER TABLE, so we check first
            cursor.execute("PRAGMA table_info(chat_sessions)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'thread_state' not in columns:
                try:
                    cursor.execute("ALTER TABLE chat_sessions ADD COLUMN thread_state TEXT")
                    self.logger.info("Added thread_state column to chat_sessions table")
                except sqlite3.Error as e:
                    self.logger.warning("Failed to add thread_state column (may already exist): {}", e)
            
            if 'title' not in columns:
                try:
                    cursor.execute("ALTER TABLE chat_sessions ADD COLUMN title TEXT DEFAULT 'New chat'")
                    self.logger.info("Added title column to chat_sessions table")
                except sqlite3.Error as e:
                    self.logger.warning("Failed to add title column (may already exist): {}", e)
            
            if 'pinned' not in columns:
                try:
                    cursor.execute("ALTER TABLE chat_sessions ADD COLUMN pinned INTEGER DEFAULT 0")
                    self.logger.info("Added pinned column to chat_sessions table")
                except sqlite3.Error as e:
                    self.logger.warning("Failed to add pinned column (may already exist): {}", e)
            
            if 'pinned_order' not in columns:
                try:
                    cursor.execute("ALTER TABLE chat_sessions ADD COLUMN pinned_order INTEGER DEFAULT 0")
                    self.logger.info("Added pinned_order column to chat_sessions table")
                except sqlite3.Error as e:
                    self.logger.warning("Failed to add pinned_order column (may already exist): {}", e)
            
            # Create chat_turns table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT REFERENCES chat_sessions(id),
                    turn_number INTEGER NOT NULL,
                    turn_id TEXT,
                    entries TEXT NOT NULL DEFAULT '[]',
                    pipeline_id TEXT,
                    run_id TEXT,
                    status TEXT DEFAULT 'pending',
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT
                )
            """)
            
            # Add missing columns to existing chat_turns table (if not exists)
            cursor.execute("PRAGMA table_info(chat_turns)")
            turn_columns = [row[1] for row in cursor.fetchall()]
            
            if 'entries' not in turn_columns:
                try:
                    cursor.execute("ALTER TABLE chat_turns ADD COLUMN entries TEXT NOT NULL DEFAULT '[]'")
                    self.logger.info("Added entries column to chat_turns table")
                except sqlite3.Error as e:
                    self.logger.warning("Failed to add entries column (may already exist): {}", e)
            
            if 'feedback' not in turn_columns:
                try:
                    cursor.execute("ALTER TABLE chat_turns ADD COLUMN feedback TEXT")
                    self.logger.info("Added feedback column to chat_turns table")
                except sqlite3.Error as e:
                    self.logger.warning("Failed to add feedback column (may already exist): {}", e)
            
            if 'regenerated_by' not in turn_columns:
                try:
                    cursor.execute("ALTER TABLE chat_turns ADD COLUMN regenerated_by INTEGER REFERENCES chat_turns(id)")
                    self.logger.info("Added regenerated_by column to chat_turns table")
                except sqlite3.Error as e:
                    self.logger.warning("Failed to add regenerated_by column (may already exist): {}", e)
            
            # Create available_content table for analysis results
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS available_content (
                    file_name TEXT PRIMARY KEY,
                    file_type TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    topics TEXT NOT NULL,
                    example_questions TEXT NOT NULL,
                    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_size INTEGER,
                    word_count INTEGER
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_turns_session ON chat_turns(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_turns_turn_id ON chat_turns(turn_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_turns_pipeline ON chat_turns(pipeline_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_turns_run_id ON chat_turns(run_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_last_accessed ON chat_sessions(last_accessed)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_available_content_type ON available_content(content_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_available_content_timestamp ON available_content(analysis_timestamp)")
            
            conn.commit()
            self.logger.info("Database schema initialized successfully")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except sqlite3.Error as e:
            self.logger.error("Database error: {}", e)
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def create_chat_session(self, session_id: str, source: str = "fastapi") -> bool:
        """Create a new chat session - simplified"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO chat_sessions (id, source)
                    VALUES (?, ?)
                """, (session_id, source))
                
                conn.commit()
                self.logger.info("Created chat session: {} - {}", session_id, source)
                return True
                
        except sqlite3.Error as e:
            self.logger.error("Failed to create chat session {}: {}", session_id, e)
            return False
    
    def get_chat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get chat session by ID - simplified"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                
                return None
                
        except sqlite3.Error as e:
            self.logger.error("Failed to get chat session {}: {}", session_id, e)
            return None
    
    def update_chat_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update chat session"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Prepare update fields
                update_fields = []
                update_values = []
                
                for key, value in updates.items():
                    if key in ['history', 'usage'] and isinstance(value, (dict, list)):
                        update_fields.append(f"{key} = ?")
                        update_values.append(json.dumps(value))
                    else:
                        update_fields.append(f"{key} = ?")
                        update_values.append(value)
                
                # Add last_accessed timestamp
                update_fields.append("last_accessed = ?")
                update_values.append(datetime.now())
                
                update_values.append(session_id)
                
                query = f"UPDATE chat_sessions SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(query, update_values)
                
                conn.commit()
                self.logger.debug("Updated chat session: {}", session_id)
                return True
                
        except sqlite3.Error as e:
            self.logger.error("Failed to update chat session {}: {}", session_id, e)
            return False
    
    def create_chat_turn(self, session_id: str, turn_number: int,
                        pipeline_id: Optional[str] = None, run_id: Optional[str] = None) -> Optional[int]:
        """Create a new chat turn"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO chat_turns (
                        session_id, turn_number, pipeline_id, run_id
                    ) VALUES (?, ?, ?, ?)
                """, (session_id, turn_number, pipeline_id, run_id))
                
                turn_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info("Created chat turn: {} - turn {}", turn_id, turn_number)
                return turn_id
                
        except sqlite3.Error as e:
            self.logger.error("Failed to create chat turn: {}", e)
            return None
    
    def update_chat_turn(self, turn_id: int, updates: Dict[str, Any]) -> bool:
        """Update chat turn"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Prepare update fields
                update_fields = []
                update_values = []
                
                for key, value in updates.items():
                    if key in ['entries', 'feedback']:
                        if isinstance(value, (dict, list)):
                            update_fields.append(f"{key} = ?")
                            update_values.append(json.dumps(value))
                        else:
                            update_fields.append(f"{key} = ?")
                            update_values.append(value)
                    else:
                        update_fields.append(f"{key} = ?")
                        update_values.append(value)
                
                update_values.append(turn_id)
                
                query = f"UPDATE chat_turns SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(query, update_values)
                
                conn.commit()
                self.logger.debug("Updated chat turn: {}", turn_id)
                return True
                
        except sqlite3.Error as e:
            self.logger.error("Failed to update chat turn {}: {}", turn_id, e)
            return False
    
    def get_chat_turns(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all turns for a session"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM chat_turns 
                    WHERE session_id = ? 
                    ORDER BY turn_number ASC
                """, (session_id,))
                
                rows = cursor.fetchall()
                turns = []
                
                for row in rows:
                    turn_data = dict(row)
                    
                    # Parse JSON fields
                    for json_field in ['entries', 'feedback']:
                        if turn_data.get(json_field):
                            try:
                                turn_data[json_field] = json.loads(turn_data[json_field])
                            except (json.JSONDecodeError, TypeError):
                                # If parsing fails, keep as string
                                pass
                    
                    turns.append(turn_data)
                
                return turns
                
        except sqlite3.Error as e:
            self.logger.error("Failed to get chat turns for session {}: {}", session_id, e)
            return []
    
    def get_chat_turn_by_run_id(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get chat turn by run ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM chat_turns WHERE run_id = ?", (run_id,))
                row = cursor.fetchone()
                
                if row:
                    turn_data = dict(row)
                    
                    # Parse JSON fields
                    for json_field in ['entries', 'feedback']:
                        if turn_data.get(json_field):
                            try:
                                turn_data[json_field] = json.loads(turn_data[json_field])
                            except (json.JSONDecodeError, TypeError):
                                # If parsing fails, keep as string
                                pass
                    
                    return turn_data
                
                return None
                
        except sqlite3.Error as e:
            self.logger.error("Failed to get chat turn by run_id {}: {}", run_id, e)
            return None
    
    def get_all_sessions(self, status: str = 'active') -> List[Dict[str, Any]]:
        """Get all sessions with given status"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM chat_sessions 
                    WHERE status = ? 
                    ORDER BY last_accessed DESC
                """, (status,))
                
                rows = cursor.fetchall()
                sessions = []
                
                for row in rows:
                    session_data = dict(row)
                    
                    # Parse JSON fields
                    if session_data.get('history'):
                        session_data['history'] = json.loads(session_data['history'])
                    if session_data.get('usage'):
                        session_data['usage'] = json.loads(session_data['usage'])
                    
                    sessions.append(session_data)
                
                return sessions
                
        except sqlite3.Error as e:
            self.logger.error("Failed to get sessions with status {}: {}", status, e)
            return []
    
    def delete_chat_session(self, session_id: str) -> bool:
        """Delete chat session and all associated turns"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete associated turns first
                cursor.execute("DELETE FROM chat_turns WHERE session_id = ?", (session_id,))
                
                # Delete session
                cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
                
                conn.commit()
                self.logger.info("Deleted chat session: {}", session_id)
                return True
                
        except sqlite3.Error as e:
            self.logger.error("Failed to delete chat session {}: {}", session_id, e)
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get session counts
                cursor.execute("SELECT COUNT(*) FROM chat_sessions WHERE status = 'active'")
                active_sessions = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM chat_sessions WHERE status = 'archived'")
                archived_sessions = cursor.fetchone()[0]
                
                # Get turn counts
                cursor.execute("SELECT COUNT(*) FROM chat_turns")
                total_turns = cursor.fetchone()[0]
                
                # Get database size
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]
                
                return {
                    "active_sessions": active_sessions,
                    "archived_sessions": archived_sessions,
                    "total_turns": total_turns,
                    "database_size_bytes": db_size,
                    "database_path": str(self.db_path)
                }
                
        except sqlite3.Error as e:
            self.logger.error("Failed to get database stats: {}", e)
            return {}
    
    # =============================================================================
    # AVAILABLE CONTENT MANAGEMENT METHODS
    # =============================================================================
    
    def create_available_content(self, file_name: str, file_type: str, content_type: str, 
                               summary: str, topics: List[str], example_questions: List[str],
                               file_size: Optional[int] = None, word_count: Optional[int] = None) -> bool:
        """Create or update available content entry"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Convert lists to JSON strings
                topics_json = json.dumps(topics)
                questions_json = json.dumps(example_questions)
                
                # Insert or replace (upsert) the content
                cursor.execute("""
                    INSERT OR REPLACE INTO available_content 
                    (file_name, file_type, content_type, summary, topics, example_questions, 
                     file_size, word_count, analysis_timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (file_name, file_type, content_type, summary, topics_json, questions_json, 
                      file_size, word_count))
                
                conn.commit()
                self.logger.info("Created/updated available content for file: {}", file_name)
                return True
                
        except sqlite3.Error as e:
            self.logger.error("Failed to create available content for {}: {}", file_name, e)
            return False
    
    def get_available_content(self, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available content entries, optionally filtered by content_type"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if content_type:
                    cursor.execute("""
                        SELECT file_name, file_type, content_type, summary, topics, 
                               example_questions, analysis_timestamp, file_size, word_count
                        FROM available_content 
                        WHERE content_type = ?
                        ORDER BY analysis_timestamp DESC
                    """, (content_type,))
                else:
                    cursor.execute("""
                        SELECT file_name, file_type, content_type, summary, topics, 
                               example_questions, analysis_timestamp, file_size, word_count
                        FROM available_content 
                        ORDER BY analysis_timestamp DESC
                    """)
                
                rows = cursor.fetchall()
                results = []
                
                for row in rows:
                    # Convert JSON strings back to lists
                    topics = json.loads(row['topics']) if row['topics'] else []
                    example_questions = json.loads(row['example_questions']) if row['example_questions'] else []
                    
                    results.append({
                        "file_name": row['file_name'],
                        "file_type": row['file_type'],
                        "content_type": row['content_type'],
                        "summary": row['summary'],
                        "topics": topics,
                        "example_questions": example_questions,
                        "analysis_timestamp": row['analysis_timestamp'],
                        "file_size": row['file_size'],
                        "word_count": row['word_count']
                    })
                
                self.logger.debug("Retrieved {} available content entries", len(results))
                return results
                
        except sqlite3.Error as e:
            self.logger.error("Failed to get available content: {}", e)
            return []
    
    def update_available_content(self, file_name: str, **updates) -> bool:
        """Update available content entry with provided fields"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                update_fields = []
                update_values = []
                
                for field, value in updates.items():
                    if field in ['topics', 'example_questions'] and isinstance(value, list):
                        # Convert lists to JSON
                        update_fields.append(f"{field} = ?")
                        update_values.append(json.dumps(value))
                    elif field in ['summary', 'file_type', 'content_type']:
                        update_fields.append(f"{field} = ?")
                        update_values.append(value)
                    elif field in ['file_size', 'word_count']:
                        update_fields.append(f"{field} = ?")
                        update_values.append(value)
                
                if not update_fields:
                    self.logger.warning("No valid fields to update for file: {}", file_name)
                    return False
                
                # Add timestamp update
                update_fields.append("analysis_timestamp = CURRENT_TIMESTAMP")
                
                query = f"UPDATE available_content SET {', '.join(update_fields)} WHERE file_name = ?"
                update_values.append(file_name)
                
                cursor.execute(query, update_values)
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info("Updated available content for file: {}", file_name)
                    return True
                else:
                    self.logger.warning("No content found to update for file: {}", file_name)
                    return False
                
        except sqlite3.Error as e:
            self.logger.error("Failed to update available content for {}: {}", file_name, e)
            return False
    
    def get_available_content_by_filename(self, file_name: str) -> Optional[Dict[str, Any]]:
        """Get available content entry by filename"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT file_name, file_type, content_type, summary, topics, 
                           example_questions, file_size, word_count, analysis_timestamp
                    FROM available_content 
                    WHERE file_name = ?
                """, (file_name,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        "file_name": result[0],
                        "file_type": result[1],
                        "content_type": result[2],
                        "summary": result[3],
                        "topics": json.loads(result[4]) if result[4] else [],
                        "example_questions": json.loads(result[5]) if result[5] else [],
                        "file_size": result[6],
                        "word_count": result[7],
                        "analysis_timestamp": result[8]
                    }
                return None
                    
        except sqlite3.Error as e:
            self.logger.error("Failed to get available content for {}: {}", file_name, e)
            return None
    
    def delete_available_content_by_filename(self, file_name: str) -> bool:
        """Delete available content entry by filename"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM available_content 
                    WHERE file_name = ?
                """, (file_name,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    self.logger.info("Deleted available content for file: {}", file_name)
                    return True
                else:
                    self.logger.warning("No available content found for file: {}", file_name)
                    return False
                    
        except sqlite3.Error as e:
            self.logger.error("Failed to delete available content for {}: {}", file_name, e)
            return False
    
    def delete_available_content(self, file_name: str) -> bool:
        """Delete available content entry"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM available_content WHERE file_name = ?", (file_name,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info("Deleted available content for file: {}", file_name)
                    return True
                else:
                    self.logger.warning("No content found to delete for file: {}", file_name)
                    return False
                
        except sqlite3.Error as e:
            self.logger.error("Failed to delete available content for {}: {}", file_name, e)
            return False