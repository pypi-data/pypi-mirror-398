"""
Shared utilities for document and image ingestion tools
Provides consistent JSON output formatting across DocRAG and ImageRAG toolkits
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

class IngestionResult:
    """Utility class for formatting ingestion results in JSON format"""
    
    @staticmethod
    def create_file_result(
        filename: str,
        status: str,
        file_size: int,
        message: str,
        chunks_created: Optional[int] = None,
        text_length: Optional[int] = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized file result entry
        
        Args:
            filename: Name of the file
            status: Processing status (processed, skipped, overwritten, failed)
            file_size: File size in bytes
            message: Detailed processing message
            chunks_created: Number of chunks created (for documents)
            text_length: Length of extracted text (for images)
            error: Error message if processing failed
            
        Returns:
            Dict containing file result information
        """
        result = {
            "filename": filename,
            "status": status,
            "file_size": file_size,
            "message": message
        }
        
        # Add document-specific fields
        if chunks_created is not None:
            result["chunks_created"] = chunks_created
            
        # Add image-specific fields
        if text_length is not None:
            result["text_length"] = text_length
            
        # Add error field if present
        if error:
            result["error"] = error
            
        return result
    
    @staticmethod
    def create_summary(
        total_files: int,
        processed: int,
        skipped: int,
        overwritten: int,
        failed: int,
        total_chunks: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized summary
        
        Args:
            total_files: Total number of files processed
            processed: Number of files successfully processed
            skipped: Number of files skipped (duplicates)
            overwritten: Number of files overwritten
            failed: Number of files that failed to process
            total_chunks: Total chunks created (for documents)
            
        Returns:
            Dict containing summary information
        """
        summary = {
            "total_files": total_files,
            "processed": processed,
            "skipped": skipped,
            "overwritten": overwritten,
            "failed": failed
        }
        
        # Add document-specific field
        if total_chunks is not None:
            summary["total_chunks"] = total_chunks
            
        return summary
    
    @staticmethod
    def create_json_output(
        files_processed: List[Dict[str, Any]],
        summary: Dict[str, Any],
        tools_used: Dict[str, int],
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create the complete JSON output structure
        
        Args:
            files_processed: List of file processing results
            summary: Summary statistics
            tools_used: Dictionary of tools used and their counts
            error: Global error message if any
            
        Returns:
            Complete JSON output structure
        """
        result = {
            "files_processed": files_processed,
            "summary": summary,
            "tools_used": tools_used
        }
        
        if error:
            result["error"] = error
            
        return result
    
    @staticmethod
    def parse_status_from_message(message: str) -> str:
        """
        Parse status from a processing message
        
        Args:
            message: Processing message string
            
        Returns:
            Status string (processed, skipped, overwritten, failed)
        """
        if "already exists with identical content" in message:
            return "skipped"
        elif "existed with different content. Overwriting" in message:
            return "overwritten"
        elif "Failed to" in message or "error" in message.lower():
            return "failed"
        elif "Ingested" in message:
            return "processed"
        else:
            return "unknown"
    
    @staticmethod
    def extract_chunks_from_message(message: str) -> Optional[int]:
        """
        Extract chunk count from a processing message
        
        Args:
            message: Processing message string
            
        Returns:
            Number of chunks created, or None if not found
        """
        import re
        chunk_match = re.search(r'Ingested (\d+) chunks', message)
        if chunk_match:
            return int(chunk_match.group(1))
        return None
    
    @staticmethod
    def extract_text_length_from_message(message: str) -> Optional[int]:
        """
        Extract text length from an image processing message
        
        Args:
            message: Processing message string
            
        Returns:
            Length of extracted text, or None if not found
        """
        import re
        text_match = re.search(r'extracted (\d+) characters of text', message)
        if text_match:
            return int(text_match.group(1))
        return None
    
    @staticmethod
    def extract_file_size_from_message(message: str) -> Optional[int]:
        """
        Extract file size from a processing message
        
        Args:
            message: Processing message string
            
        Returns:
            File size in bytes, or None if not found
        """
        import re
        size_match = re.search(r'\(([0-9,]+) bytes\)', message)
        if size_match:
            # Remove commas and convert to int
            size_str = size_match.group(1).replace(',', '')
            return int(size_str)
        return None