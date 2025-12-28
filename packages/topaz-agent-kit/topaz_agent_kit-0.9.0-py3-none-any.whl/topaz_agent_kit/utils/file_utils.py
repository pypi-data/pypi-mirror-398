"""
File utilities for detecting file types and reading files.
"""
from pathlib import Path
from typing import Dict, List, Literal, Any
import base64
from PIL import Image
import mimetypes
import re

from topaz_agent_kit.utils.logger import Logger


class FileUtils:
    """Utilities for file type detection and reading"""
    
    # Image extensions
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif', '.svg', '.ico'}
    
    # Document extensions  
    DOCUMENT_EXTENSIONS = {'.pdf', '.txt', '.docx', '.doc', '.md', '.csv', '.json', '.ppt', '.pptx', '.xls', '.xlsx', '.html', '.rtf'}
    
    @staticmethod
    def detect_file_type(file_path: str) -> Literal["image", "document", "other"]:
        """Detect file type by extension"""
        ext = Path(file_path).suffix.lower()
        if ext in FileUtils.IMAGE_EXTENSIONS:
            return "image"
        elif ext in FileUtils.DOCUMENT_EXTENSIONS:
            return "document"
        return "other"
    
    @staticmethod
    def read_image_file(file_path: str) -> Dict[str, Any]:
        """Read image file and return data with metadata"""
        logger = Logger("FileUtils")
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                raise FileNotFoundError(f"Image file not found: {file_path}")
            
            # Read image bytes
            with open(file_path, 'rb') as f:
                image_bytes = f.read()
            
            # Get image metadata using PIL
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
                    format_name = img.format or 'unknown'
            except Exception as e:
                logger.warning("Failed to get image metadata: {}", e)
                width, height = None, None
                format_name = 'unknown'
            
            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                # Fallback based on extension
                ext = path_obj.suffix.lower()
                mime_map = {
                    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                    '.png': 'image/png', '.gif': 'image/gif',
                    '.webp': 'image/webp', '.bmp': 'image/bmp',
                    '.tiff': 'image/tiff', '.tif': 'image/tiff',
                    '.svg': 'image/svg+xml', '.ico': 'image/x-icon'
                }
                mime_type = mime_map.get(ext, 'image/jpeg')
            
            return {
                "path": str(file_path),
                "name": path_obj.name,
                "data": image_bytes,
                "base64": FileUtils.encode_bytes_to_base64(image_bytes),
                "metadata": {
                    "width": width,
                    "height": height,
                    "format": format_name,
                    "mime_type": mime_type,
                    "size_bytes": len(image_bytes)
                }
            }
        except Exception as e:
            logger.error("Failed to read image file {}: {}", file_path, e)
            raise
    
    @staticmethod
    def read_document_file(file_path: str) -> Dict[str, Any]:
        """Read document file and return bytes and text with metadata"""
        logger = Logger("FileUtils")
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                raise FileNotFoundError(f"Document file not found: {file_path}")
            
            # Read file as bytes (for DataContent)
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
            
            # Try to read as text for text-based documents (fallback)
            text = ""
            try:
                # Only try text extraction for text-based formats
                ext = path_obj.suffix.lower()
                text_extensions = {'.txt', '.md', '.csv', '.json', '.html', '.rtf'}
                if ext in text_extensions:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
            except Exception:
                # If text reading fails, that's okay - we have bytes
                pass
            
            # Get file metadata
            stat = path_obj.stat()
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                # Fallback based on extension
                ext = path_obj.suffix.lower()
                mime_map = {
                    '.pdf': 'application/pdf',
                    '.txt': 'text/plain', '.md': 'text/markdown',
                    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    '.doc': 'application/msword',
                    '.csv': 'text/csv', '.json': 'application/json',
                    '.html': 'text/html', '.rtf': 'application/rtf',
                    '.ppt': 'application/vnd.ms-powerpoint',
                    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                    '.xls': 'application/vnd.ms-excel',
                    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                }
                mime_type = mime_map.get(ext, 'application/octet-stream')
            
            return {
                "path": str(file_path),
                "name": path_obj.name,
                "data": file_bytes,  # bytes for DataContent (may not be JSON-serializable)
                "base64": FileUtils.encode_bytes_to_base64(file_bytes),  # base64-encoded for JSON serialization
                "text": text,  # extracted text (if available)
                "metadata": {
                    "size_bytes": stat.st_size,
                    "mime_type": mime_type
                }
            }
        except Exception as e:
            logger.error("Failed to read document file {}: {}", file_path, e)
            raise
    
    @staticmethod
    def detect_urls(text: str) -> List[str]:
        """Detect URLs in text using regex"""
        # Pattern for URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:!?]'
        urls = re.findall(url_pattern, text)
        return list(set(urls))  # Remove duplicates
    
    @staticmethod
    def detect_url_type(url: str) -> Literal["image", "document", "other"]:
        """Detect URL type by extension"""
        # Parse URL to get path
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Check for image extensions
        if any(path.endswith(ext) for ext in FileUtils.IMAGE_EXTENSIONS):
            return "image"
        
        # Check for document extensions
        if any(path.endswith(ext) for ext in FileUtils.DOCUMENT_EXTENSIONS):
            return "document"
        
        # Check for image patterns in path
        if any(f'/image/{ext}' in path for ext in FileUtils.IMAGE_EXTENSIONS) or \
           'image' in path.split('/')[-1].lower():
            return "image"
        
        return "other"
    
    @staticmethod
    def get_url_media_type(url: str, url_type: str = None) -> str:
        """Get MIME type for URL based on extension"""
        if url_type is None:
            url_type = FileUtils.detect_url_type(url)
        
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Use mimetypes to guess
        mime_type, _ = mimetypes.guess_type(path)
        if mime_type:
            return mime_type
        
        # Fallback based on detected type
        if url_type == "image":
            # Default to jpeg if can't determine
            ext = Path(path).suffix.lower()
            mime_map = {
                '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.png': 'image/png', '.gif': 'image/gif',
                '.webp': 'image/webp', '.bmp': 'image/bmp',
                '.tiff': 'image/tiff', '.tif': 'image/tiff',
                '.svg': 'image/svg+xml', '.ico': 'image/x-icon'
            }
            return mime_map.get(ext, 'image/jpeg')
        elif url_type == "document":
            ext = Path(path).suffix.lower()
            mime_map = {
                '.pdf': 'application/pdf',
                '.txt': 'text/plain', '.md': 'text/markdown',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.doc': 'application/msword',
                '.csv': 'text/csv', '.json': 'application/json',
                '.html': 'text/html', '.rtf': 'application/rtf'
            }
            return mime_map.get(ext, 'application/octet-stream')
        
        return 'application/octet-stream'
    
    @staticmethod
    def is_image_url(url: str) -> bool:
        """Check if URL points to an image (deprecated - use detect_url_type instead)"""
        return FileUtils.detect_url_type(url) == "image"
    
    @staticmethod
    def encode_bytes_to_base64(data: bytes) -> str:
        """Encode bytes to base64 string"""
        return base64.b64encode(data).decode('utf-8')

