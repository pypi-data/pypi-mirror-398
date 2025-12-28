"""
File Storage Service
Handles original file storage and retrieval for document preview functionality
"""

import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from topaz_agent_kit.utils.logger import Logger


class FileStorageError(Exception):
    """Custom exception for file storage errors"""
    pass


class FileStorageService:
    """Service for managing original file storage and retrieval"""
    
    def __init__(self, rag_files_path: str = "./data/rag_files", user_files_path: str = "./data/user_files"):
        self.logger = Logger("FileStorageService")
        self.rag_files_path = Path(rag_files_path)
        self.user_files_path = Path(user_files_path)
        
        # RAG storage paths (for ingestion)
        self.rag_documents_path = self.rag_files_path / "documents"
        self.rag_images_path = self.rag_files_path / "images"
        
        # Ensure directories exist
        self._ensure_directories()
        
        self.logger.info("FileStorageService initialized:")
        self.logger.info("  RAG files: {}", self.rag_files_path.absolute())
        self.logger.info("  User files: {}", self.user_files_path.absolute())
    
    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist"""
        try:
            # Create RAG storage directories
            self.rag_documents_path.mkdir(parents=True, exist_ok=True)
            self.rag_images_path.mkdir(parents=True, exist_ok=True)
            
            # Create user files base directory
            self.user_files_path.mkdir(parents=True, exist_ok=True)
            
            self.logger.debug("Storage directories ensured:")
            self.logger.debug("  RAG: {}", self.rag_files_path)
            self.logger.debug("  User: {}", self.user_files_path)
        except Exception as e:
            self.logger.error("Failed to create storage directories: {}", e)
            raise FileStorageError(f"Failed to create storage directories: {e}")
    
    def _get_file_type_path(self, file_type: str, storage_type: str = "rag") -> Path:
        """Get the appropriate storage path based on file type and storage type"""
        if storage_type == "session":
            # Session files go directly to user_files_path (no subdirectories)
            return self.user_files_path
        else:
            # RAG files go to type-specific subdirectories
            if file_type.lower() in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp']:
                return self.rag_images_path
            else:
                return self.rag_documents_path
    
    def _generate_file_id(self, filename: str) -> str:
        """Generate unique file ID with timestamp prefix"""
        timestamp = int(time.time() * 1000)
        return f"{timestamp}_{filename}"
    
    def _calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def store_file(self, file_content: bytes, filename: str, file_type: str, 
                   storage_type: str = "session", session_id: str = None) -> Dict[str, Any]:
        """
        Store file and return storage information
        
        Args:
            file_content: Raw file content as bytes
            filename: Original filename
            file_type: File type/extension
            storage_type: "rag" for ingestion or "session" for attachment
            session_id: Required for session storage, ignored for RAG
            
        Returns:
            Dict with storage information including file_id, path, hash, etc.
        """
        try:
            if storage_type == "session" and not session_id:
                raise ValueError("session_id required for session storage")
            
            # Generate unique file ID
            file_id = self._generate_file_id(filename)
            
            # Calculate file hash for duplicate detection
            file_hash = self._calculate_file_hash(file_content)
            
            # Get appropriate storage path
            if storage_type == "session":
                # Session files go to user_files/{session_id}/
                session_path = self.user_files_path / session_id
                session_path.mkdir(parents=True, exist_ok=True)
                storage_path = session_path
            else:
                # RAG files go to type-specific subdirectories
                storage_path = self._get_file_type_path(file_type, storage_type)
            
            # Use file_id as storage filename (already contains timestamp_filename)
            storage_filename = file_id
            file_path = storage_path / storage_filename
            
            # Check for duplicates by hash (only for RAG storage)
            if storage_type == "rag":
                existing_file = self._find_file_by_hash(file_hash)
                if existing_file:
                    self.logger.info("File with identical content already exists: {}", existing_file['file_id'])
                    return {
                        "file_id": existing_file['file_id'],
                        "path": str(existing_file['path']),
                        "filename": filename,
                        "file_type": file_type,
                        "file_size": len(file_content),
                        "file_hash": file_hash,
                        "storage_path": str(existing_file['path']),
                        "upload_date": existing_file.get('upload_date', datetime.now().isoformat()),
                        "status": "duplicate"
                    }
            
            # Write file to storage
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Verify file was written correctly
            if not file_path.exists() or file_path.stat().st_size != len(file_content):
                raise FileStorageError("File write verification failed")
            
            self.logger.info("File stored successfully: {} -> {} (type: {})", filename, file_path, storage_type)
            
            return {
                "file_id": file_id,
                "path": str(file_path),
                "filename": filename,
                "file_type": file_type,
                "file_size": len(file_content),
                "file_hash": file_hash,
                "storage_path": str(file_path),
                "upload_date": datetime.now().isoformat(),
                "status": "stored",
                "storage_type": storage_type,
                "session_id": session_id if storage_type == "session" else None
            }
            
        except Exception as e:
            self.logger.error("Failed to store file {}: {}", filename, e)
            raise FileStorageError(f"Failed to store file {filename}: {e}")
    
    def get_file_path(self, file_id: str, session_id: str = None) -> Optional[Path]:
        """
        Get file path by file ID
        
        Args:
            file_id: Unique file identifier
            session_id: Optional session ID for session files
            
        Returns:
            Path object if file exists, None otherwise
        """
        try:
            # If session_id provided, check session storage first
            if session_id:
                session_path = self.user_files_path / session_id / file_id
                if session_path.is_file():
                    return session_path
            
            # Search in RAG storage directories
            for search_path in [self.rag_documents_path, self.rag_images_path]:
                file_path = search_path / file_id
                if file_path.is_file():
                    return file_path
            
            # If no session_id but file not found in RAG, search all session directories
            if not session_id:
                for session_dir in self.user_files_path.iterdir():
                    if session_dir.is_dir():
                        session_file_path = session_dir / file_id
                        if session_file_path.is_file():
                            return session_file_path
            
            self.logger.warning("File not found: {}", file_id)
            return None
            
        except Exception as e:
            self.logger.error("Error finding file {}: {}", file_id, e)
            return None
    
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get file information by file ID
        
        Args:
            file_id: Unique file identifier
            
        Returns:
            Dict with file information if found, None otherwise
        """
        try:
            file_path = self.get_file_path(file_id)
            if not file_path:
                return None
            
            # Extract original filename from storage filename
            storage_filename = file_path.name
            if '_' in storage_filename:
                # Format: {timestamp}_{filename}
                # Find the first underscore to separate timestamp from filename
                first_underscore = storage_filename.find('_')
                if first_underscore > 0:
                    original_filename = storage_filename[first_underscore + 1:]
                else:
                    original_filename = storage_filename
            else:
                original_filename = storage_filename
            
            # Get file stats
            stat = file_path.stat()
            
            return {
                "file_id": file_id,
                "filename": original_filename,
                "path": str(file_path),
                "file_size": stat.st_size,
                "upload_date": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "file_type": file_path.suffix.lower().lstrip('.')
            }
            
        except Exception as e:
            self.logger.error("Error getting file info for {}: {}", file_id, e)
            return None
    
    def serve_file(self, file_id: str) -> Optional[bytes]:
        """
        Serve file content for API responses
        
        Args:
            file_id: Unique file identifier
            
        Returns:
            File content as bytes if found, None otherwise
        """
        try:
            file_path = self.get_file_path(file_id)
            if not file_path:
                return None
            
            with open(file_path, 'rb') as f:
                return f.read()
                
        except Exception as e:
            self.logger.error("Error serving file {}: {}", file_id, e)
            return None
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete file from storage
        
        Args:
            file_id: Unique file identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            file_path = self.get_file_path(file_id)
            if not file_path:
                self.logger.warning("File not found for deletion: {}", file_id)
                return False
            
            # Delete the file
            file_path.unlink()
            
            self.logger.info("File deleted successfully: {}", file_id)
            return True
            
        except Exception as e:
            self.logger.error("Error deleting file {}: {}", file_id, e)
            return False
    
    def _find_file_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        Find existing file by content hash
        
        Args:
            file_hash: SHA-256 hash of file content
            
        Returns:
            Dict with file information if found, None otherwise
        """
        try:
            # Search in both directories
            for search_path in [self.rag_documents_path, self.rag_images_path]:
                for file_path in search_path.glob("*"):
                    if file_path.is_file():
                        try:
                            with open(file_path, 'rb') as f:
                                content = f.read()
                                if self._calculate_file_hash(content) == file_hash:
                                    # Extract file_id from filename
                                    filename = file_path.name
                                    if '_' in filename:
                                        file_id = filename.split('_')[0]
                                    else:
                                        file_id = filename
                                    
                                    return {
                                        "file_id": file_id,
                                        "path": file_path,
                                        "upload_date": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat()
                                    }
                        except Exception:
                            # Skip files that can't be read
                            continue
            
            return None
            
        except Exception as e:
            self.logger.error("Error finding file by hash: {}", e)
            return None
    
    def list_files(self, file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all stored files (RAG files only)
        
        Args:
            file_type: Optional filter by file type ('documents' or 'images')
            
        Returns:
            List of file information dictionaries
        """
        try:
            files = []
            
            # Determine which directories to search
            search_paths = []
            if file_type == 'documents':
                search_paths = [self.rag_documents_path]
            elif file_type == 'images':
                search_paths = [self.rag_images_path]
            else:
                search_paths = [self.rag_documents_path, self.rag_images_path]
            
            for search_path in search_paths:
                for file_path in search_path.glob("*"):
                    if file_path.is_file():
                        # Extract file_id and original filename from storage filename
                        storage_filename = file_path.name
                        if '_' in storage_filename:
                            # Format: {timestamp}_{filename}
                            # Find the first underscore that separates timestamp from filename
                            first_underscore = storage_filename.find('_')
                            if first_underscore > 0:
                                timestamp_part = storage_filename[:first_underscore]
                                original_filename = storage_filename[first_underscore + 1:]
                                file_id = storage_filename  # The storage filename IS the file_id
                                
                                # Verify timestamp is numeric
                                if timestamp_part.isdigit():
                                    # Get file stats
                                    stat = file_path.stat()
                                    
                                    # Determine file type from extension
                                    file_extension = original_filename.split('.')[-1].lower() if '.' in original_filename else ''
                                    file_type = file_extension
                                    
                                    # Build file info directly instead of calling get_file_info
                                    file_info = {
                                        "file_id": file_id,
                                        "filename": original_filename,
                                        "file_type": file_type,
                                        "file_size": stat.st_size,
                                        "file_hash": "",  # We don't have hash info here
                                        "storage_path": str(file_path),
                                        "upload_date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                        "status": "stored",
                                        "storage_type": "rag"
                                    }
                                    files.append(file_info)
            
            # Sort by upload date (newest first)
            files.sort(key=lambda x: x['upload_date'], reverse=True)
            
            return files
            
        except Exception as e:
            self.logger.error("Error listing files: {}", e)
            return []
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics
        
        Returns:
            Dict with storage statistics
        """
        try:
            total_files = 0
            total_size = 0
            documents_count = 0
            images_count = 0
            
            for file_path in [self.rag_documents_path, self.rag_images_path]:
                for file in file_path.glob("*"):
                    if file.is_file():
                        total_files += 1
                        total_size += file.stat().st_size
                        
                        if file_path == self.rag_documents_path:
                            documents_count += 1
                        else:
                            images_count += 1
            
            return {
                "total_files": total_files,
                "total_size": total_size,
                "documents_count": documents_count,
                "images_count": images_count,
                "rag_files_path": str(self.rag_files_path.absolute()),
                "user_files_path": str(self.user_files_path.absolute())
            }
            
        except Exception as e:
            self.logger.error("Error getting storage stats: {}", e)
            return {
                "total_files": 0,
                "total_size": 0,
                "documents_count": 0,
                "images_count": 0,
                "rag_files_path": str(self.rag_files_path.absolute()),
                "user_files_path": str(self.user_files_path.absolute()),
                "error": str(e)
            }
    
    def list_session_files(self, session_id: str) -> List[Dict[str, Any]]:
        """
        List files for a specific session
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of file information dictionaries
        """
        try:
            files = []
            session_path = self.user_files_path / session_id
            
            if not session_path.exists():
                return files
            
            for file_path in session_path.glob("*"):
                if file_path.is_file():
                    # Extract original filename from storage filename
                    storage_filename = file_path.name
                    if '_' in storage_filename:
                        first_underscore = storage_filename.find('_')
                        if first_underscore > 0:
                            original_filename = storage_filename[first_underscore + 1:]
                        else:
                            original_filename = storage_filename
                    else:
                        original_filename = storage_filename
                    
                    # Get file stats
                    stat = file_path.stat()
                    
                    # Determine file type from extension
                    file_extension = original_filename.split('.')[-1].lower() if '.' in original_filename else ''
                    
                    file_info = {
                        "file_id": storage_filename,
                        "filename": original_filename,
                        "file_type": file_extension,
                        "file_size": stat.st_size,
                        "storage_path": str(file_path),
                        "upload_date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "session_id": session_id,
                        "storage_type": "session"
                    }
                    files.append(file_info)
            
            # Sort by upload date (newest first)
            files.sort(key=lambda x: x['upload_date'], reverse=True)
            
            return files
            
        except Exception as e:
            self.logger.error("Error listing session files for {}: {}", session_id, e)
            return []
    
    def delete_session_file(self, file_id: str, session_id: str) -> bool:
        """
        Delete a session file
        
        Args:
            file_id: File identifier
            session_id: Session identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            session_path = self.user_files_path / session_id / file_id
            
            if not session_path.exists():
                self.logger.warning("Session file not found: {} in session {}", file_id, session_id)
                return False
            
            session_path.unlink()
            self.logger.info("Session file deleted successfully: {} from session {}", file_id, session_id)
            return True
            
        except Exception as e:
            self.logger.error("Error deleting session file {} from session {}: {}", file_id, session_id, e)
            return False
    
    def cleanup_session_files(self, session_id: str) -> bool:
        """
        Clean up all files for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            session_path = self.user_files_path / session_id
            
            if not session_path.exists():
                return True
            
            # Remove all files in session directory
            for file_path in session_path.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
            
            # Remove session directory if empty
            try:
                session_path.rmdir()
            except OSError:
                # Directory not empty, that's fine
                pass
            
            self.logger.info("Session files cleaned up for session: {}", session_id)
            return True
            
        except Exception as e:
            self.logger.error("Error cleaning up session files for {}: {}", session_id, e)
            return False
