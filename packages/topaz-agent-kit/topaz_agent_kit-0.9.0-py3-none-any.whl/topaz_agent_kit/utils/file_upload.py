"""
File upload utilities for Topaz Agent Kit
Handles file validation, metadata creation, and turn creation for both FastAPI and CLI
"""

import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from topaz_agent_kit.core.exceptions import DatabaseError
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.file_type_detector import FileTypeDetector
from topaz_agent_kit.core.content_ingester import DocumentIngester, ImageIngester

logger = Logger("FileUpload")

# Configuration constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
# Note: File extensions are now managed by FileTypeDetector

class FileUploadError(Exception):
    """Custom exception for file upload errors"""
    pass

class FileValidator:
    """Handles file validation logic"""
    
    @staticmethod
    def validate_file_size(file_size: int) -> None:
        """Validate file size against maximum limit"""
        if file_size > MAX_FILE_SIZE:
            raise FileUploadError(f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB")
    
    @staticmethod
    def validate_file_type(file_path: str) -> str:
        """Validate file type and return extension"""
        is_supported, error_message = FileTypeDetector.validate_file_support(file_path)
        if not is_supported:
            raise FileUploadError(error_message)
        return Path(file_path).suffix.lower()
    
    @staticmethod
    def validate_file_exists(file_path: str) -> None:
        """Validate that file exists"""
        if not os.path.exists(file_path):
            raise FileUploadError(f"File not found: {file_path}")

class FileMetadata:
    """Handles file metadata creation"""
    
    @staticmethod
    def create_metadata_from_path(file_path: str) -> Dict[str, Any]:
        """Create file metadata from file path (CLI usage)"""
        file_stat = os.stat(file_path)
        filename = os.path.basename(file_path)
        file_ext = FileValidator.validate_file_type(file_path)
        
        FileValidator.validate_file_size(file_stat.st_size)
        
        return {
            "filename": filename,
            "size": file_stat.st_size,
            "type": file_ext,
            "path": file_path,
            "uploaded_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def create_metadata_from_content(filename: str, file_content: bytes, temp_path: str) -> Dict[str, Any]:
        """Create file metadata from file content (FastAPI usage)"""
        file_size = len(file_content)
        file_ext = FileValidator.validate_file_type(filename)
        
        FileValidator.validate_file_size(file_size)
        
        return {
            "filename": filename,
            "size": file_size,
            "type": file_ext,
            "path": temp_path,
            "uploaded_at": datetime.now().isoformat()
        }

class FileUploadHandler:
    """Handles file upload processing and turn creation"""
    
    def __init__(self, orchestrator=None, emitter=None):
        self.orchestrator = orchestrator
        self.emitter = emitter
        self.logger = Logger("FileUploadHandler")
        self._progress_active = False
        self._progress_thread = None
        
        # Initialize direct ingesters
        self._init_ingesters()
    
    def _show_progress_bar(self, filename: str, progress: int = 0, file_size: int = 0, uploaded_size: int = 0):
        """Show progress bar for file upload or agent execution"""
        if not self._progress_active:
            return
            
        bar_length = 20
        filled_length = int(bar_length * progress // 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        if file_size > 0:
            # File upload progress with size info
            size_mb = file_size / (1024 * 1024)
            uploaded_mb = uploaded_size / (1024 * 1024)
            self.logger.info(f"\r📁 Uploading {filename}... [{bar}] {progress}% ({uploaded_mb:.1f}MB/{size_mb:.1f}MB)", end="", flush=True)
        else:
            # Agent execution progress
            self.logger.info(f"\r🔄 Processing {filename}... [{bar}] {progress}%", end="", flush=True)
    
    def _start_progress_bar(self, filename: str, file_size: int = 0):
        """Start progress bar animation"""
        self._progress_active = True
        self._progress_thread = threading.Thread(target=self._animate_progress, args=(filename, file_size))
        self._progress_thread.daemon = True
        self._progress_thread.start()
    
    def _animate_progress(self, filename: str, file_size: int = 0):
        """Animate progress bar from 0% to 100%"""
        for progress in range(0, 101, 5):
            if not self._progress_active:
                break
            uploaded_size = int(file_size * progress / 100) if file_size > 0 else 0
            self._show_progress_bar(filename, progress, file_size, uploaded_size)
            time.sleep(0.1)  # Update every 100ms
    
    def _stop_progress_bar(self, filename: str, success: bool = True):
        """Stop progress bar and show final result"""
        self._progress_active = False
        if self._progress_thread:
            self._progress_thread.join(timeout=0.1)
        
        if success:
            self.logger.info(f"\r🔄 Processing {filename}... [████████████████████] 100% Complete")
        else:
            self.logger.info(f"\r🔄 Processing {filename}... Failed")
        self.logger.info()  # New line
    
    def _init_ingesters(self):
        """Initialize content ingesters for bypassing MCP tools"""
        try:
            # Get ChromaDB path and models from orchestrator's configuration
            db_path = self._get_chromadb_path()
            embedding_model = self._get_embedding_model()
            vision_model = self._get_vision_model()
            
            # Initialize Docling-based ingesters
            self.document_ingester = DocumentIngester(db_path, embedding_model, vision_model, emitter=self.emitter)
            self.image_ingester = ImageIngester(db_path, embedding_model, vision_model, emitter=self.emitter)
            
            self.logger.info("Docling-based content ingesters initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize content ingesters: {}", e)
            # Set to None to fall back to agent-based processing
            self.document_ingester = None
            self.image_ingester = None

    def upload_only(self, file_paths: List[str], original_filenames: Optional[List[str]] = None) -> Dict[str, Any]:
        """CLI-only upload step: validates and acknowledges files, emits one STATE_SNAPSHOT per file.
        This does not call content ingesters; it returns metadata for orchestrator step 2.
        """
        try:
            all_results = []
            for i, file_path in enumerate(file_paths):
                try:
                    FileValidator.validate_file_exists(file_path)
                    file_size = os.path.getsize(file_path)
                    FileValidator.validate_file_size(file_size)
                    FileValidator.validate_file_type(file_path)
                    filename = original_filenames[i] if original_filenames and i < len(original_filenames) else os.path.basename(file_path)

                    # Emit upload completion snapshot
                    if self.emitter and hasattr(self.emitter, 'step_output'):
                        self.emitter.step_output(
                            node_id="file_uploader",
                            result={
                                "filename": filename,
                                "status": "uploaded",
                                "file_size": file_size,
                                "content_type": Path(file_path).suffix.lower().lstrip('.') or "unknown"
                            },
                            status="completed"
                        )

                    all_results.append({
                        "file_path": file_path,
                        "filename": filename,
                        "file_size": file_size,
                        "status": "uploaded",
                    })
                except Exception as e:
                    all_results.append({
                        "file_path": file_path,
                        "filename": os.path.basename(file_path),
                        "file_size": 0,
                        "status": "failed",
                        "error": str(e)
                    })
            failed = [r for r in all_results if r.get("status") == "failed"]
            summary = f"{len(all_results) - len(failed)} uploaded, {len(failed)} failed"
            return {"success": len(failed) == 0, "summary": summary, "results": all_results}
        except Exception as e:
            self.logger.error("Failed during upload_only: {}", e)
            return {"success": False, "summary": f"Failed during upload: {str(e)}", "results": []}
    
    def _get_chromadb_path(self) -> str:
        """Get ChromaDB path from configuration"""
        if not self.orchestrator or not hasattr(self.orchestrator, 'validated_config'):
            self.logger.error("Orchestrator or validated_config not available")
            raise DatabaseError("Orchestrator or validated_config not available")
        
        config = self.orchestrator.validated_config
        if not hasattr(config, 'chromadb_path'):
            self.logger.error("chromadb_path not found in validated configuration")
            raise DatabaseError("chromadb_path not found in validated configuration")
        
        chromadb_path = config.chromadb_path
        if not chromadb_path:
            self.logger.error("chromadb_path is empty in configuration")
            raise DatabaseError("chromadb_path is empty in configuration")
        
        # Resolve relative paths relative to project directory
        if not os.path.isabs(chromadb_path) and self.orchestrator._project_dir:
            return os.path.join(self.orchestrator._project_dir, chromadb_path)
        return chromadb_path
    
    def _get_embedding_model(self) -> str:
        """Get embedding model from configuration"""
        if not self.orchestrator or not hasattr(self.orchestrator, 'validated_config'):
            self.logger.error("Orchestrator or validated_config not available")
            raise DatabaseError("Orchestrator or validated_config not available")
        
        config = self.orchestrator.validated_config
        if not hasattr(config, 'embedding_model'):
            self.logger.error("embedding_model not found in validated configuration")
            raise DatabaseError("embedding_model not found in validated configuration")
        
        embedding_model = config.embedding_model
        if not embedding_model:
            self.logger.error("embedding_model is empty in configuration")
            raise DatabaseError("embedding_model is empty in configuration")
        
        return embedding_model
    
    def _get_vision_model(self) -> str:
        """Get vision model from configuration"""
        if not self.orchestrator or not hasattr(self.orchestrator, 'validated_config'):
            self.logger.error("Orchestrator or validated_config not available")
            raise DatabaseError("Orchestrator or validated_config not available")
        
        config = self.orchestrator.validated_config
        if not hasattr(config, 'vision_model'):
            self.logger.error("vision_model not found in validated configuration")
            raise DatabaseError("vision_model not found in validated configuration")
        
        vision_model = config.vision_model
        if not vision_model:
            self.logger.error("vision_model is empty in configuration")
            raise DatabaseError("vision_model is empty in configuration")
        
        return vision_model
    
    async def process_files(self, session_id: str, file_paths: List[str], user_message: Optional[str] = None, original_filenames: Optional[List[str]] = None) -> Dict[str, Any]:
        """Process file uploads using content ingestion (handles both single and multiple files)"""
        try:
            total_files = len(file_paths)
            all_results = []
            success_count = 0
            skipped_count = 0
            failed_count = 0
            
            # Initialize file storage service for CLI consistency
            file_storage = None
            try:
                from topaz_agent_kit.core.file_storage import FileStorageService
                # Get files path from orchestrator config
                if hasattr(self.orchestrator, 'validated_config') and self.orchestrator.validated_config:
                    rag_files_path = getattr(self.orchestrator.validated_config, 'rag_files_path', './data/rag_files')
                    user_files_path = getattr(self.orchestrator.validated_config, 'user_files_path', './data/user_files')
                    
                    if not Path(rag_files_path).is_absolute():
                        # Get project directory from orchestrator
                        project_dir = getattr(self.orchestrator, '_project_dir', '.')
                        rag_files_path = str(Path(project_dir) / rag_files_path)
                    if not Path(user_files_path).is_absolute():
                        project_dir = getattr(self.orchestrator, '_project_dir', '.')
                        user_files_path = str(Path(project_dir) / user_files_path)
                    
                    file_storage = FileStorageService(rag_files_path, user_files_path)
                    self.logger.info("File storage initialized for CLI consistency: rag={}, user={}", rag_files_path, user_files_path)
                else:
                    self.logger.warning("File paths not configured - CLI files will not be stored for consistency")
            except Exception as e:
                self.logger.warning("Failed to initialize file storage for CLI: {}", e)
            
            # Create turn if there's a user message
            turn_id = None
            if user_message and user_message.strip():
                turn_id = self.orchestrator._chat_storage.start_turn(
                    session_id=session_id,
                    user_message=user_message,
                    pipeline_id=None
                )
            
            for i, file_path in enumerate(file_paths):
                # Use original filename if provided, otherwise use temp filename
                filename = original_filenames[i] if original_filenames and i < len(original_filenames) else os.path.basename(file_path)
                try:
                    # Validate file
                    FileValidator.validate_file_exists(file_path)
                    FileValidator.validate_file_size(os.path.getsize(file_path))
                    FileValidator.validate_file_type(file_path)
                    
                    # Store original file for consistency with FastAPI (CLI enhancement)
                    storage_result = None
                    if file_storage:
                        try:
                            with open(file_path, 'rb') as f:
                                file_content = f.read()
                            
                            file_ext = Path(file_path).suffix.lower().lstrip('.') if Path(file_path).suffix else 'unknown'
                            storage_result = file_storage.store_file(
                                file_content=file_content,
                                filename=filename,
                                file_type=file_ext,
                                storage_type="rag", # always rag here given this will be called only in RAG upload cases
                            )
                            self.logger.info("File stored for CLI consistency: {} -> {}", filename, storage_result.get('file_id', 'unknown'))
                        except Exception as e:
                            self.logger.warning("Failed to store file for CLI consistency: {}", e)
                    
                    # Determine file type and use appropriate ingester
                    file_ext = Path(file_path).suffix.lower()
                    is_image = file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif']
                    
                    if is_image:
                        if not self.image_ingester:
                            raise FileUploadError("Image ingester not available")
                        result = self.image_ingester.ingest_image(file_path, original_filename=filename)
                    else:
                        if not self.document_ingester:
                            raise FileUploadError("Document ingester not available")
                        result = self.document_ingester.ingest_document(file_path, original_filename=filename)
                    
                    # Only show progress bar for files that actually need processing
                    if result["status"] not in ["skipped", "failed"]:
                        # Start progress bar for actual processing
                        self._start_progress_bar(filename)
                        # Simulate processing time for progress bar
                        time.sleep(0.5)  # Brief processing simulation
                        self._stop_progress_bar(filename, success=True)
                    
                    # Create comprehensive file result
                    file_result = {
                        "file_path": file_path,
                        "filename": filename,
                        "file_id": result.get("file_id"),  # Use actual ChromaDB ID from ingester
                        "file_type": file_ext[1:] if file_ext else "unknown",
                        "content_type": "image" if is_image else "document",
                        "file_size": result["file_size"],
                        "status": result["status"],
                        "message": result["message"],
                        "extracted_text": "",  # Will be populated from ingester
                        "word_count": 0,  # Will be calculated from extracted text
                    }
                    
                    # Add storage information for CLI consistency
                    if storage_result:
                        file_result["storage_info"] = {
                            "file_id": storage_result.get("file_id"),
                            "filename": storage_result.get("filename"),
                            "file_size": storage_result.get("file_size"),
                            "file_type": storage_result.get("file_type"),
                            "upload_date": storage_result.get("upload_date"),
                            "status": storage_result.get("status", "stored")
                        }
                    
                    # Add file-specific information from ingester results
                    if is_image and "text_length" in result:
                        file_result["text_length"] = result["text_length"]
                        file_result["extracted_text"] = result.get("extracted_text", f"Image: {filename}")
                        file_result["word_count"] = result.get("word_count", 0)
                    elif not is_image and "chunks_created" in result:
                        file_result["chunks_created"] = result["chunks_created"]
                        file_result["extracted_text"] = result.get("extracted_text", f"Document: {filename}")
                        file_result["word_count"] = result.get("word_count", 0)
                    
                    if result["status"] == "failed":
                        file_result["error"] = result.get("error", "Unknown error")
                    
                    # Note: file_uploader STATE_SNAPSHOT is emitted by upload_only (CLI step 1)
                    
                    # Log appropriate message based on status
                    if result["status"] == "skipped":
                        self.logger.info("File skipped using content ingestion: {} - {}", filename, result["message"])
                        skipped_count += 1
                    elif result["status"] == "failed":
                        self.logger.error("File processing failed using content ingestion: {} - {}", filename, result["message"])
                        failed_count += 1
                    else:
                        self.logger.info("File processed successfully using content ingestion: {} ({})", filename, result["status"])
                        success_count += 1
                    
                    all_results.append(file_result)
                    
                except Exception as e:
                    self._stop_progress_bar(filename, success=False)
                    self.logger.error("Failed to process file {}: {}", file_path, e)
                    failed_count += 1
                    all_results.append({
                        "file_path": file_path,
                        "filename": os.path.basename(file_path),
                        "file_id": "",
                        "file_type": "unknown",
                        "content_type": "unknown",
                        "file_size": 0,
                        "status": "failed",
                        "message": f"Failed to process file: {str(e)}",
                        "extracted_text": "",
                        "word_count": 0,
                        "error": str(e)
                    })
            
            # Create detailed summary
            if skipped_count > 0 and success_count == 0 and failed_count == 0:
                summary = f"{total_files} files skipped (already exist)"
            elif failed_count > 0:
                summary = f"{failed_count} failed, {success_count} processed, {skipped_count} skipped"
            elif skipped_count > 0:
                summary = f"{success_count} processed, {skipped_count} skipped"
            else:
                summary = f"{total_files} files processed successfully"
            
            # Note: Content analyzer will be triggered by orchestrator after file upload
            
            return {
                "success": failed_count == 0,  # Success if no files failed
                "summary": summary,
                "turn_id": turn_id,
                "total_files": total_files,
                "success_count": success_count,
                "skipped_count": skipped_count,
                "failed_count": failed_count,
                "results": all_results
            }
            
        except Exception as e:
            self.logger.error("Failed to process files with content ingestion: {}", e)
            return {
                "success": False,
                "summary": f"Failed to process files: {str(e)}",
                "turn_id": None,
                "total_files": len(file_paths),
                "success_count": 0,
                "skipped_count": 0,
                "failed_count": len(file_paths),
                "results": []
            }
    

def get_allowed_extensions() -> set:
    """Get the set of allowed file extensions"""
    return FileTypeDetector.DOCUMENT_EXTENSIONS | FileTypeDetector.IMAGE_EXTENSIONS

def get_max_file_size() -> int:
    """Get the maximum file size limit"""
    return MAX_FILE_SIZE