"""
File type detection and routing utilities for Topaz Agent Kit
Handles intelligent routing of files to appropriate ingestor agents
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum

class FileType(Enum):
    DOCUMENT = "document"
    IMAGE = "image"
    UNSUPPORTED = "unsupported"

class FileTypeDetector:
    """Handles file type detection and routing logic"""
    
    # Document file extensions
    DOCUMENT_EXTENSIONS = {
        '.pdf', '.txt', '.docx', '.doc', '.md', '.csv', '.json', 
        '.ppt', '.pptx', '.xls', '.xlsx', '.html', '.rtf'
    }
    
    # Image file extensions
    IMAGE_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', 
        '.webp', '.svg', '.ico'
    }
    
    
    @classmethod
    def detect_file_type(cls, file_path: str) -> FileType:
        """Detect file type based on extension"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in cls.DOCUMENT_EXTENSIONS:
            return FileType.DOCUMENT
        elif file_ext in cls.IMAGE_EXTENSIONS:
            return FileType.IMAGE
        else:
            return FileType.UNSUPPORTED
    
    
    @classmethod
    def categorize_files(cls, file_paths: List[str]) -> Dict[FileType, List[str]]:
        """Categorize multiple files by type"""
        categorized = {
            FileType.DOCUMENT: [],
            FileType.IMAGE: [],
            FileType.UNSUPPORTED: []
        }
        
        for file_path in file_paths:
            file_type = cls.detect_file_type(file_path)
            categorized[file_type].append(file_path)
        
        return categorized
    
    
    @classmethod
    def validate_file_support(cls, file_path: str) -> Tuple[bool, Optional[str]]:
        """Check if file is supported and return error message if not"""
        file_type = cls.detect_file_type(file_path)
        
        if file_type == FileType.UNSUPPORTED:
            file_ext = Path(file_path).suffix.lower()
            supported_extensions = sorted(cls.DOCUMENT_EXTENSIONS | cls.IMAGE_EXTENSIONS)
            return False, f"Unsupported file type '{file_ext}'. Supported types: {', '.join(supported_extensions)}"
        
        return True, None
    
    @classmethod
    def get_supported_extensions(cls) -> Dict[str, List[str]]:
        """Get all supported file extensions by category"""
        return {
            "documents": sorted(list(cls.DOCUMENT_EXTENSIONS)),
            "images": sorted(list(cls.IMAGE_EXTENSIONS))
        }