"""
Fallback document extractors for when Docling fails
"""
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

from topaz_agent_kit.utils.logger import Logger


class FallbackDocumentExtractor:
    """Fallback document extractor using PyPDF/PyMuPDF when Docling fails"""
    
    def __init__(self):
        self.logger = Logger("FallbackExtractor")
    
    def extract_text_with_pypdf(self, file_path: str) -> Dict[str, Any]:
        """Extract text using PyPDF (pure Python, no external dependencies)"""
        try:
            import pypdf
            
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                
                text_content = []
                page_texts = []
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_content.append(page_text)
                            page_texts.append({
                                "page": page_num,
                                "text": page_text,
                                "word_count": len(page_text.split())
                            })
                    except Exception as e:
                        self.logger.warning("Failed to extract text from page {}: {}", page_num, e)
                        continue
                
                full_text = "\n\n".join(text_content)
                
                return {
                    "success": True,
                    "method": "pypdf",
                    "text": full_text,
                    "pages": page_texts,
                    "total_pages": len(pdf_reader.pages),
                    "word_count": len(full_text.split()),
                    "metadata": {
                        "extractor": "pypdf",
                        "num_pages": len(pdf_reader.pages),
                        "has_text": bool(full_text.strip())
                    }
                }
                
        except ImportError:
            self.logger.error("PyPDF not available - install with: pip install pypdf")
            return {"success": False, "error": "PyPDF not available"}
        except Exception as e:
            self.logger.error("PyPDF extraction failed: {}", e)
            return {"success": False, "error": str(e)}
    
    def extract_text_with_pymupdf(self, file_path: str) -> Dict[str, Any]:
        """Extract text using PyMuPDF (high performance, better text extraction)"""
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(file_path)
            text_content = []
            page_texts = []
            
            for page_num in range(doc.page_count):
                try:
                    page = doc[page_num]
                    page_text = page.get_text()
                    
                    if page_text.strip():
                        text_content.append(page_text)
                        page_texts.append({
                            "page": page_num + 1,  # 1-based page numbering
                            "text": page_text,
                            "word_count": len(page_text.split())
                        })
                except Exception as e:
                    self.logger.warning("Failed to extract text from page {}: {}", page_num + 1, e)
                    continue
            
            doc.close()
            full_text = "\n\n".join(text_content)
            
            return {
                "success": True,
                "method": "pymupdf",
                "text": full_text,
                "pages": page_texts,
                "total_pages": doc.page_count,
                "word_count": len(full_text.split()),
                "metadata": {
                    "extractor": "pymupdf",
                    "num_pages": doc.page_count,
                    "has_text": bool(full_text.strip())
                }
            }
            
        except ImportError:
            self.logger.error("PyMuPDF not available - install with: pip install pymupdf")
            return {"success": False, "error": "PyMuPDF not available"}
        except Exception as e:
            self.logger.error("PyMuPDF extraction failed: {}", e)
            return {"success": False, "error": str(e)}
    
    def extract_text_fallback(self, file_path: str) -> Dict[str, Any]:
        """
        Try fallback extractors in order of preference:
        1. PyMuPDF (best quality)
        2. PyPDF (pure Python fallback)
        """
        self.logger.info("Attempting fallback text extraction for: {}", file_path)
        
        # Try PyMuPDF first (better quality)
        result = self.extract_text_with_pymupdf(file_path)
        if result["success"]:
            self.logger.success("PyMuPDF extraction successful")
            return result
        
        # Try PyPDF as fallback
        result = self.extract_text_with_pypdf(file_path)
        if result["success"]:
            self.logger.success("PyPDF extraction successful")
            return result
        
        # Both failed
        self.logger.error("All fallback extractors failed")
        return {
            "success": False,
            "error": "All fallback extractors failed",
            "method": "none"
        }


class FallbackChunker:
    """Fallback chunking using simple text splitting when Docling chunkers fail"""
    
    def __init__(self, tokenizer=None):
        self.logger = Logger("FallbackChunker")
        self.tokenizer = tokenizer
    
    def chunk_text_simple(self, text: str, max_tokens: int = 4096, overlap_tokens: int = 200) -> List[Dict[str, Any]]:
        """
        Simple text chunking using character-based splitting
        This is a basic fallback when Docling's advanced chunkers can't be used
        """
        try:
            # Simple character-based chunking
            chunk_size = max_tokens * 4  # Rough approximation: 4 chars per token
            overlap_size = overlap_tokens * 4
            
            chunks = []
            start = 0
            chunk_id = 0
            
            while start < len(text):
                end = start + chunk_size
                
                # Try to break at sentence boundary
                if end < len(text):
                    # Look for sentence endings within the last 200 characters
                    search_start = max(start, end - 200)
                    sentence_end = text.rfind('.', search_start, end)
                    if sentence_end > start:
                        end = sentence_end + 1
                
                chunk_text = text[start:end].strip()
                if chunk_text:
                    chunks.append({
                        "text": chunk_text,
                        "metadata": {
                            "chunk_id": chunk_id,
                            "page": 0,  # Fallback doesn't have page info
                            "section": "",
                            "chunk_type": "paragraph",
                            "has_table": False,
                            "hierarchy_level": 0,
                            "extractor": "fallback"
                        }
                    })
                    chunk_id += 1
                
                # Move start position with overlap
                start = end - overlap_size
                if start >= len(text):
                    break
            
            self.logger.info("Created {} chunks using simple text splitting", len(chunks))
            return chunks
            
        except Exception as e:
            self.logger.error("Simple chunking failed: {}", e)
            # Ultimate fallback: single chunk
            return [{
                "text": text,
                "metadata": {
                    "chunk_id": 0,
                    "page": 0,
                    "section": "",
                    "chunk_type": "paragraph",
                    "has_table": False,
                    "hierarchy_level": 0,
                    "extractor": "fallback",
                    "error": str(e)
                }
            }]
    
    def chunk_text_with_hybrid_chunker(self, text: str, max_tokens: int = 4096) -> List[Dict[str, Any]]:
        """
        Use Docling's HybridChunker with plain text input
        This preserves some of Docling's token-aware chunking capabilities
        """
        try:
            from docling.document_converter.document import Document
            from docling.document_converter.document_converter_result import DocumentConverterResult
            from docling.chunking.hybrid_chunker import HybridChunker
            
            # Create a minimal Document object for HybridChunker
            # This is a workaround to use Docling's chunker with plain text
            doc = Document()
            
            # Add text as a single item
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.document import DocumentItem
            
            # Create a simple document item
            item = DocumentItem(
                text=text,
                type="paragraph",
                page_number=1
            )
            doc.items = [item]
            
            # Use HybridChunker
            hybrid_chunker = HybridChunker(
                tokenizer=self.tokenizer,
                max_tokens=max_tokens,
                overlap_tokens=200
            )
            
            chunks_generator = hybrid_chunker.chunk(doc)
            chunks = list(chunks_generator)
            
            # Convert to our format
            formatted_chunks = []
            for i, chunk in enumerate(chunks):
                formatted_chunks.append({
                    "text": chunk.text,
                    "metadata": {
                        "chunk_id": i,
                        "page": 0,  # Fallback doesn't have page info
                        "section": "",
                        "chunk_type": "paragraph",
                        "has_table": False,
                        "hierarchy_level": 0,
                        "extractor": "hybrid_fallback"
                    }
                })
            
            self.logger.info("Created {} chunks using HybridChunker fallback", len(formatted_chunks))
            return formatted_chunks
            
        except Exception as e:
            self.logger.warning("HybridChunker fallback failed: {}, using simple chunking", e)
            return self.chunk_text_simple(text, max_tokens)
