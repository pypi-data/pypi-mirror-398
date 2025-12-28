"""
Docling-based Content Ingester
Enhanced document understanding with structure preservation and semantic chunking
"""

import base64
import hashlib
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from chromadb import PersistentClient
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.chunking import HierarchicalChunker, HybridChunker
from PIL import Image

from topaz_agent_kit.core.exceptions import ModelError
from topaz_agent_kit.models.model_factory import ModelFactory
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.utils.embedding_utils import GenericEmbeddingFunction

# Suppress macOS CoreAnalytics warnings
os.environ.setdefault('COREANALYTICS_DISABLE', '1')


class ContentIngester:
    """Base class for content ingestion using Docling"""
    
    def __init__(self, db_path: str, embedding_model_name: str, vision_model_name: Optional[str] = None, emitter: Optional[Any] = None):
        self.logger = Logger("ContentIngester")
        self.db_path = db_path
        self.embedding_model_name = embedding_model_name
        self.vision_model_name = vision_model_name
        self.emitter = emitter
        
        # Validate required parameters
        if not embedding_model_name:
            self.logger.error("embedding_model_name is required")
            raise ValueError("embedding_model_name is required")
        
        # Initialize ChromaDB
        self._client = PersistentClient(path=db_path)
        
        # Create embedding function
        self._embedding_fn = self._create_embedding_function()
        
        # Initialize Docling converter (lazy initialization)
        self._docling_converter = None
        
        # Get tokenizer for embedding model (for HybridChunker)
        self._tokenizer = self._get_embedding_tokenizer()
    
    def _create_embedding_function(self):
        """Create embedding function using ModelFactory"""
        try:
            embedding_client, model_name = ModelFactory.get_embedding_model(self.embedding_model_name)
            self.logger.success("GenericEmbeddingFunction initialized with model: {}", model_name)
            return GenericEmbeddingFunction(embedding_client, model_name, self.logger)
        except Exception as e:
            self.logger.error("Failed to create embedding function: {}", e)
            raise ModelError(f"Failed to create embedding function: {e}")
    
    def _get_embedding_tokenizer(self):
        """Get tokenizer for the embedding model using OpenAI tokenizer wrapper"""
        try:
            # Use OpenAI tokenizer wrapper like working examples
            from topaz_agent_kit.utils.docling_utils import OpenAITokenizerWrapper
            
            # Map common embedding models to tokenizers
            tokenizer_map = {
                'text-embedding-ada-002': 'cl100k_base',
                'text-embedding-3-small': 'cl100k_base',
                'text-embedding-3-large': 'cl100k_base',
            }
            
            encoding_name = tokenizer_map.get(self.embedding_model_name, 'cl100k_base')
            return OpenAITokenizerWrapper(model_name=encoding_name)
        except Exception as e:
            self.logger.warning("Failed to load tokenizer, using default: {}", e)
            # Fallback to simple whitespace tokenizer
            return None
    
    def _get_docling_converter(self) -> DocumentConverter:
        """Lazy initialization of Docling converter with optimal settings"""
        if self._docling_converter is None:
            self.logger.info("Initializing Docling DocumentConverter...")
            
            # Configure PDF processing options optimized for MPS acceleration
            pdf_options = PdfPipelineOptions()
            pdf_options.do_table_structure = True  # Extract table structure (MPS supported)
            pdf_options.do_ocr = True  # Enable OCR for scanned PDFs (MPS supported)
            # Note: Formula and code enrichment disabled for MPS compatibility
            # pdf_options.do_formula_enrichment = True  # Disabled - forces CPU fallback
            # pdf_options.do_code_enrichment = True  # Disabled - forces CPU fallback
            
            # Create converter with configuration
            self._docling_converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_options)
                }
            )
            
            self.logger.success("Docling DocumentConverter initialized with MPS-optimized options")
        
        return self._docling_converter
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _extract_text_with_llm_vision(self, image_data: bytes, filename: str, page_num: int) -> str:
        """Extract text from image using LLM vision model (kept for image ingestion)"""
        try:
            # Encode image to base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            # Get vision model
            if not self.vision_model_name:
                raise ModelError("Vision model not configured")
            
            vision_client, model_name = ModelFactory.get_vision_model(self.vision_model_name)
            vision_model_name = 'gpt-4o' if 'azure' in model_name.lower() else model_name
            
            # Create vision message
            messages = [{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract all text from this image. Preserve formatting, structure, and layout. Include tables, headers, and body text. Return only extracted text."
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"}
                    }
                ]
            }]
            
            # Call vision model
            response = vision_client.chat.completions.create(
                model=vision_model_name,
                messages=messages,
                max_tokens=4000,
                temperature=0.1
            )
            
            extracted_text = response.choices[0].message.content
            return extracted_text if extracted_text else ""
        except Exception as e:
            self.logger.error("LLM vision extraction failed: {}", e)
            return ""


class DocumentIngester(ContentIngester):
    """Docling-based document ingestion with advanced chunking"""
    
    def __init__(self, db_path: str, embedding_model_name: str, vision_model_name: Optional[str] = None, emitter: Optional[Any] = None):
        super().__init__(db_path, embedding_model_name, vision_model_name, emitter)
        self.logger = Logger("DocumentIngester")
    
    def ingest_document(self, file_path: str, overwrite: bool = False, original_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Ingest document using Docling with two-stage chunking
        
        Parameters:
            file_path: Path to document file
            overwrite: Whether to replace existing document
            original_filename: Original filename if using temp file
            
        Returns:
            Dict with ingestion result
        """
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Get file info
            filename = original_filename if original_filename else os.path.basename(file_path)
            file_ext = Path(file_path).suffix.lower()
            file_size = os.path.getsize(file_path)
            
            # Calculate file hash for duplicate detection
            file_hash = self._calculate_file_hash(file_path)
            
            # Generate unique file ID
            file_id = f"{filename}_{int(time.time() * 1000)}"
            
            # Check for duplicates
            duplicate_check = self._check_duplicate_document(file_hash, filename)
            
            if duplicate_check["duplicate_type"] == "exact_match":
                existing_doc = duplicate_check["existing_document"]
                return {
                    "status": "skipped",
                    "message": f"Document '{filename}' already exists (uploaded {existing_doc.get('upload_date', 'unknown')}). Skipped.",
                    "file_name": filename,
                    "file_id": file_id,
                    "file_hash": file_hash,
                    "file_size": file_size,
                    "chunks_created": 0,
                    "word_count": 0
                }
            
            # Handle name match (overwrite)
            overwrite_happened = False
            if duplicate_check["duplicate_type"] == "name_match":
                if overwrite:
                    collection = self._client.get_or_create_collection(
                        name="documents",
                        embedding_function=self._embedding_fn
                    )
                    collection.delete(where={"file_name": filename})
                    overwrite_happened = True
                    self.logger.info("Overwriting existing document: {}", filename)
                else:
                    return {
                        "status": "skipped",
                        "message": f"Document '{filename}' already exists. Use overwrite=True to replace.",
                        "file_name": filename,
                        "file_id": file_id,
                        "file_hash": file_hash,
                        "file_size": file_size,
                        "chunks_created": 0,
                        "word_count": 0
                    }
            
            # Convert document using Docling with fallback
            self.logger.info("Converting document with Docling: {}", filename)
            docling_doc = None
            fallback_result = None
            
            try:
                converter = self._get_docling_converter()
                result = converter.convert(file_path)
                docling_doc = result.document
                self.logger.success("Docling conversion successful for: {}", filename)
            except RuntimeError as e:
                error_msg = str(e)
                if "could not find the page-dimensions" in error_msg:
                    self.logger.warning("PDF has page tree structure incompatible with Docling parser: {}", filename)
                    self.logger.warning("Attempting fallback extraction...")
                else:
                    self.logger.warning("Docling conversion failed: {}, attempting fallback...", str(e))
                
                # Try fallback extraction
                from topaz_agent_kit.utils.fallback_extractors import FallbackDocumentExtractor
                fallback_extractor = FallbackDocumentExtractor()
                fallback_result = fallback_extractor.extract_text_fallback(file_path)
                
                if not fallback_result["success"]:
                    raise Exception(f"Both Docling and fallback extraction failed for {filename}: {fallback_result.get('error', 'Unknown error')}")
                
                self.logger.success("Fallback extraction successful using: {}", fallback_result["method"])
            except Exception as e:
                self.logger.warning("Docling conversion failed: {}, attempting fallback...", str(e))
                
                # Try fallback extraction
                from topaz_agent_kit.utils.fallback_extractors import FallbackDocumentExtractor
                fallback_extractor = FallbackDocumentExtractor()
                fallback_result = fallback_extractor.extract_text_fallback(file_path)
                
                if not fallback_result["success"]:
                    raise Exception(f"Both Docling and fallback extraction failed for {filename}: {fallback_result.get('error', 'Unknown error')}")
                
                self.logger.success("Fallback extraction successful using: {}", fallback_result["method"])
            
            # Chunking pipeline
            if docling_doc is not None:
                # Use Docling's advanced chunking
                chunks = self._chunk_document(docling_doc)
            else:
                # Use fallback chunking
                chunks = self._chunk_document_fallback(fallback_result)
            
            # Calculate word count from chunks
            total_text = " ".join([chunk["text"] for chunk in chunks])
            word_count = len(total_text.split())
            
            # Ingest into ChromaDB
            collection = self._client.get_or_create_collection(
                name="documents",
                embedding_function=self._embedding_fn
            )
            
            if overwrite:
                collection.delete(where={"file_name": filename})
            
            # Upsert chunks with enhanced metadata
            for i, chunk in enumerate(chunks):
                enhanced_metadata = {
                    **chunk["metadata"],
                    "file_name": filename,
                    "file_hash": file_hash,
                    "file_size": file_size,
                    "upload_date": datetime.now().isoformat()
                }
                
                collection.upsert(
                    documents=[chunk["text"]],
                    ids=[f"{file_id}_{i}"],
                    metadatas=[enhanced_metadata]
                )
            
            status = "overwritten" if overwrite_happened else "processed"
            message = f"Document '{filename}' {status}: {len(chunks)} chunks, {word_count} words"
            
            self.logger.success(message)
            
            # Extract text for content analyzer
            extracted_text = "\n\n".join([chunk["text"] for chunk in chunks])
            
            result = {
                "status": status,
                "message": message,
                "file_name": filename,
                "file_id": file_id,
                "file_hash": file_hash,
                "file_size": file_size,
                "chunks_created": len(chunks),
                "word_count": word_count,
                "extracted_text": extracted_text
            }
            
            # Emit agent snapshot if emitter available
            if self.emitter and hasattr(self.emitter, "step_output"):
                self.emitter.step_output(
                    node_id="content_ingester",
                    result={
                        "filename": filename,
                        "status": status,
                        "chunks_created": len(chunks),
                        "word_count": word_count,
                        "file_size": file_size
                    },
                    status="completed"
                )
            
            return result
            
        except Exception as e:
            self.logger.error("Failed to ingest document {}: {}", file_path, e)
            return {
                "status": "failed",
                "message": f"Failed to ingest: {str(e)}",
                "file_name": os.path.basename(file_path) if os.path.exists(file_path) else "unknown",
                "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                "error": str(e)
            }
    
    def _chunk_document(self, docling_doc) -> List[Dict[str, Any]]:
        """
        Two-stage chunking pipeline: HierarchicalChunker → HybridChunker
        
        Stage 1: Preserve document structure (sections, tables, lists)
        Stage 2: Refine oversized chunks with token-aware splitting
        
        Token limits optimized for Azure OpenAI embedding models (8191 tokens max):
        - HierarchicalChunker: 6144 tokens (75% of limit for maximum context)
        - HybridChunker: 4096 tokens (50% of limit for optimal balance)
        """
        try:
            # Stage 1: Hierarchical chunking for structure preservation
            self.logger.debug("Stage 1: Hierarchical chunking...")
            hierarchical_chunker = HierarchicalChunker(
                max_tokens=6144,  # Use 75% of 8191 limit for better context
                include_metadata=True
            )
            initial_chunks_generator = hierarchical_chunker.chunk(docling_doc)
            
            # Convert generator to list to work with it
            initial_chunks = list(initial_chunks_generator)
            self.logger.debug("Created {} initial chunks", len(initial_chunks))
            
            # Stage 2: Hybrid chunking for token compliance
            self.logger.debug("Stage 2: Token-aware refinement...")
            final_chunks = []
            
            for chunk in initial_chunks:
                # Estimate token count (rough approximation if tokenizer unavailable)
                estimated_tokens = len(chunk.text.split()) * 1.3  # ~1.3 tokens per word
                
                if estimated_tokens > 4096:  # Split chunks that exceed 4096 tokens
                    # Use HybridChunker for oversized chunks
                    hybrid_chunker = HybridChunker(
                        tokenizer=self._tokenizer,
                        max_tokens=4096,  # Use 50% of 8191 limit for optimal balance
                        overlap_tokens=200  # Good overlap for context preservation
                    )
                    refined_chunks_generator = hybrid_chunker.chunk(chunk)
                    # Convert generator to list
                    refined_chunks = list(refined_chunks_generator)
                    final_chunks.extend(refined_chunks)
                    self.logger.debug("Split chunk into {} refined chunks", len(refined_chunks))
                else:
                    # Keep chunk as-is if within limits
                    final_chunks.append(chunk)
            
            self.logger.success("Final chunk count: {}", len(final_chunks))
            
            # Convert to format expected by ChromaDB
            formatted_chunks = []
            for i, chunk in enumerate(final_chunks):
                # Extract page number from chunk provenance
                page_number = 0
                
                # Get page number from chunk.meta.doc_items[0].prov[0].page_no
                if hasattr(chunk, 'meta') and chunk.meta and hasattr(chunk.meta, 'doc_items') and chunk.meta.doc_items:
                    first_item = chunk.meta.doc_items[0]
                    if hasattr(first_item, 'prov') and first_item.prov:
                        page_number = first_item.prov[0].page_no
                
                # Extract metadata from Docling chunk
                metadata = {
                    "chunk_id": i,
                    "page": page_number,  # Use extracted page number
                    "section": getattr(chunk, 'section_title', ''),
                    "chunk_type": getattr(chunk, 'chunk_type', 'paragraph'),
                    "has_table": getattr(chunk, 'has_table', False),
                    "hierarchy_level": getattr(chunk, 'hierarchy_level', 0)
                }
                
                formatted_chunks.append({
                    "text": chunk.text,
                    "metadata": metadata
                })
            
            return formatted_chunks
            
        except Exception as e:
            self.logger.error("Chunking failed: {}", e)
            # Fallback: treat entire document as single chunk
            return [{
                "text": docling_doc.export_to_markdown(),
                "metadata": {"chunk_id": 0, "page": 0, "error": str(e)}
            }]
    
    def _chunk_document_fallback(self, fallback_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fallback chunking when Docling's document converter fails
        Uses Docling's HybridChunker with plain text when possible, otherwise simple text splitting
        """
        try:
            from topaz_agent_kit.utils.fallback_extractors import FallbackChunker
            
            fallback_chunker = FallbackChunker(tokenizer=self._tokenizer)
            
            # Try to use Docling's HybridChunker with plain text first
            if self._tokenizer is not None:
                self.logger.info("Attempting HybridChunker fallback...")
                chunks = fallback_chunker.chunk_text_with_hybrid_chunker(
                    fallback_result["text"], 
                    max_tokens=4096
                )
            else:
                self.logger.info("No tokenizer available, using simple text chunking...")
                chunks = fallback_chunker.chunk_text_simple(
                    fallback_result["text"],
                    max_tokens=4096
                )
            
            # Enhance metadata with page information if available
            if "pages" in fallback_result and fallback_result["pages"]:
                self.logger.info("Enhancing chunks with page information...")
                enhanced_chunks = []
                
                for chunk in chunks:
                    # Try to determine page number from chunk text
                    page_number = 0
                    chunk_text = chunk["text"]
                    
                    # Simple heuristic: find page numbers in text
                    for page_info in fallback_result["pages"]:
                        if page_info["text"] in chunk_text or chunk_text in page_info["text"]:
                            page_number = page_info["page"]
                            break
                    
                    # Update metadata
                    chunk["metadata"]["page"] = page_number
                    chunk["metadata"]["extractor"] = fallback_result["method"]
                    
                    enhanced_chunks.append(chunk)
                
                chunks = enhanced_chunks
            
            self.logger.success("Fallback chunking completed: {} chunks created", len(chunks))
            return chunks
            
        except Exception as e:
            self.logger.error("Fallback chunking failed: {}", e)
            # Ultimate fallback: single chunk
            return [{
                "text": fallback_result["text"],
                "metadata": {
                    "chunk_id": 0,
                    "page": 0,
                    "section": "",
                    "chunk_type": "paragraph",
                    "has_table": False,
                    "hierarchy_level": 0,
                    "extractor": fallback_result.get("method", "unknown"),
                    "error": str(e)
                }
            }]
    
    def _check_duplicate_document(self, file_hash: str, filename: str) -> Dict[str, Any]:
        """Check for duplicate documents"""
        try:
            collection = self._client.get_or_create_collection(
                name="documents",
                embedding_function=self._embedding_fn
            )
            
            # Check for exact hash match
            existing = collection.get(where={"file_hash": file_hash})
            if existing["ids"]:
                return {
                    "duplicate_type": "exact_match",
                    "existing_document": existing["metadatas"][0]
                }
            
            # Check for name match
            existing = collection.get(where={"file_name": filename})
            if existing["ids"]:
                return {
                    "duplicate_type": "name_match",
                    "existing_document": existing["metadatas"][0]
                }
            
            return {"duplicate_type": "none"}
            
        except Exception as e:
            self.logger.warning("Error checking duplicates: {}", e)
            return {"duplicate_type": "none"}


class ImageIngester(ContentIngester):
    """Image ingestion with LLM vision (unchanged from current implementation)"""
    
    def __init__(self, db_path: str, embedding_model_name: str, vision_model_name: Optional[str] = None, emitter: Optional[Any] = None):
        super().__init__(db_path, embedding_model_name, vision_model_name, emitter)
        self.logger = Logger("ImageIngester")
    
    def ingest_image(self, file_path: str, overwrite: bool = False, original_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Ingest image using LLM vision for OCR
        
        Parameters:
            file_path: Path to image file
            overwrite: Whether to replace existing image
            original_filename: Original filename if using temp file
            
        Returns:
            Dict with ingestion result
        """
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Get file info
            filename = original_filename if original_filename else os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            # Calculate file hash for duplicate detection
            file_hash = self._calculate_file_hash(file_path)
            
            # Generate unique file ID
            file_id = f"{filename}_{int(time.time() * 1000)}"
            
            # Check for duplicates
            duplicate_check = self._check_duplicate_image(file_hash, filename)
            
            if duplicate_check["duplicate_type"] == "exact_match":
                existing_img = duplicate_check["existing_image"]
                return {
                    "status": "skipped",
                    "message": f"Image '{filename}' already exists (uploaded {existing_img.get('upload_date', 'unknown')}). Skipped.",
                    "file_name": filename,
                    "file_id": file_id,
                    "file_hash": file_hash,
                    "file_size": file_size,
                    "text_length": 0,
                    "word_count": 0
                }
            
            # Handle name match (overwrite)
            overwrite_happened = False
            if duplicate_check["duplicate_type"] == "name_match":
                if overwrite:
                    collection = self._client.get_or_create_collection(
                        name="images",
                        embedding_function=self._embedding_fn
                    )
                    collection.delete(where={"file_name": filename})
                    overwrite_happened = True
                    self.logger.info("Overwriting existing image: {}", filename)
                else:
                    return {
                        "status": "skipped",
                        "message": f"Image '{filename}' already exists. Use overwrite=True to replace.",
                        "file_name": filename,
                        "file_id": file_id,
                        "file_hash": file_hash,
                        "file_size": file_size,
                        "text_length": 0,
                        "word_count": 0
                    }
            
            # Extract text using LLM vision
            self.logger.info("Extracting text from image using LLM vision: {}", filename)
            
            # Load image
            with open(file_path, 'rb') as f:
                image_data = f.read()
            
            # Extract text using LLM vision
            extracted_text = self._extract_text_with_llm_vision(image_data, filename, 0)
            
            if not extracted_text.strip():
                return {
                    "status": "failed",
                    "message": "No text extracted from image",
                    "file_name": filename,
                    "file_id": file_id,
                    "file_hash": file_hash,
                    "file_size": file_size,
                    "error": "No text extracted"
                }
            
            # Calculate word count
            word_count = len(extracted_text.split())
            
            # Ingest into ChromaDB
            collection = self._client.get_or_create_collection(
                name="images",
                embedding_function=self._embedding_fn
            )
            
            if overwrite:
                collection.delete(where={"file_name": filename})
            
            # Create metadata
            metadata = {
                "file_name": filename,
                "file_hash": file_hash,
                "file_size": file_size,
                "upload_date": datetime.now().isoformat(),
                "text_length": len(extracted_text),
                "word_count": word_count
            }
            
            # Upsert image
            collection.upsert(
                documents=[extracted_text],
                ids=[file_id],
                metadatas=[metadata]
            )
            
            status = "overwritten" if overwrite_happened else "processed"
            message = f"Image '{filename}' {status}: {word_count} words extracted"
            
            self.logger.success(message)
            
            result = {
                "status": status,
                "message": message,
                "file_name": filename,
                "file_id": file_id,
                "file_hash": file_hash,
                "file_size": file_size,
                "text_length": len(extracted_text),
                "word_count": word_count,
                "extracted_text": extracted_text
            }
            
            # Emit agent snapshot if emitter available
            if self.emitter and hasattr(self.emitter, "step_output"):
                self.emitter.step_output(
                    node_id="image_ingester",
                    result={
                        "filename": filename,
                        "status": status,
                        "text_length": len(extracted_text),
                        "word_count": word_count,
                        "file_size": file_size
                    },
                    status="completed"
                )
            
            return result
            
        except Exception as e:
            self.logger.error("Failed to ingest image {}: {}", file_path, e)
            return {
                "status": "failed",
                "message": f"Failed to ingest: {str(e)}",
                "file_name": os.path.basename(file_path) if os.path.exists(file_path) else "unknown",
                "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                "error": str(e)
            }
    
    def _check_duplicate_image(self, file_hash: str, filename: str) -> Dict[str, Any]:
        """Check for duplicate images"""
        try:
            collection = self._client.get_or_create_collection(
                name="images",
                embedding_function=self._embedding_fn
            )
            
            # Check for exact hash match
            existing = collection.get(where={"file_hash": file_hash})
            if existing["ids"]:
                return {
                    "duplicate_type": "exact_match",
                    "existing_image": existing["metadatas"][0]
                }
            
            # Check for name match
            existing = collection.get(where={"file_name": filename})
            if existing["ids"]:
                return {
                    "duplicate_type": "name_match",
                    "existing_image": existing["metadatas"][0]
                }
            
            return {"duplicate_type": "none"}
            
        except Exception as e:
            self.logger.warning("Error checking duplicates: {}", e)
            return {"duplicate_type": "none"}