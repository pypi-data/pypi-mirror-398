"""
PyMuPDF PDF Highlighter

This module provides PDF highlighting functionality using PyMuPDF (fitz).
It integrates with the FastAPI application to serve highlighted PDFs on-demand.
"""

import fitz  # PyMuPDF
import tempfile
import io
import hashlib
from pathlib import Path
from typing import Optional
from topaz_agent_kit.utils.logger import Logger

class PDFHighlighter:
    """Highlighter for highlighting text in PDF documents using PyMuPDF"""
    
    def __init__(self):
        self._logger = Logger("PDFHighlighter")
        self.temp_dir = Path(tempfile.gettempdir()) / "topaz_pdf_highlights"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Clean up old files with long names (from before hash-based fix)
        self._cleanup_old_cache_files()
        
        # Set up periodic cleanup (optional - can be enabled later)
        self.max_cache_size = 100  # Maximum number of cached files
        self.max_cache_age_hours = 24  # Maximum age in hours
    
    def highlight_pdf(
        self, 
        pdf_content: bytes, 
        search_text: str, 
        highlight_color: tuple = (1, 1, 0),  # Yellow by default
        page_number: Optional[int] = None
    ) -> Optional[bytes]:
        """
        Highlight text in a PDF document using in-memory processing
        
        Args:
            pdf_content: PDF file content as bytes
            search_text: Text to search for and highlight
            highlight_color: RGB color tuple (0-1 range), default is yellow
            page_number: Specific page to highlight (None for all pages)
            
        Returns:
            Highlighted PDF content as bytes, or None if error
        """
        try:
            # Open PDF document from memory
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            self._logger.info("Opened PDF with {} pages", doc.page_count)
            
            total_highlights = 0
            
            # Determine which pages to process
            if page_number is not None:
                pages_to_process = [page_number - 1]  # Convert to 0-based index
                if page_number > doc.page_count:
                    self._logger.warning("Page number {} exceeds document pages {}", page_number, doc.page_count)
                    return None
                self._logger.info("Highlighting only page {} (0-based: {})", page_number, page_number - 1)
            else:
                pages_to_process = range(doc.page_count)
                self._logger.info("Highlighting all {} pages", doc.page_count)
            
            # Process each page
            for page_idx in pages_to_process:
                page = doc[page_idx]
                
                # Try multi-part text search to handle text split across columns/pages
                highlights_added = self._highlight_text_multipart(page, search_text, highlight_color)
                total_highlights += highlights_added
                
                self._logger.info("Added {} highlights for '{}' on page {}", 
                                highlights_added, search_text, page_idx + 1)
            
            # Save to memory buffer
            output_buffer = io.BytesIO()
            doc.save(output_buffer, garbage=4, deflate=True, clean=True)
            doc.close()
            
            highlighted_content = output_buffer.getvalue()
            
            self._logger.success("Successfully highlighted {} instances of '{}'", 
                           total_highlights, search_text)
            return highlighted_content
                
        except Exception as e:
            self._logger.error("Error highlighting PDF: {}", e)
            return None
    
    def _highlight_text_multipart(self, page, search_text: str, highlight_color: tuple) -> int:
        """
        Highlight text using multi-part search to handle text split across columns/pages.
        
        PRIORITY ORDER:
        1. Exact match (highest priority - returns immediately if found)
        2. Phrase-based search (split by sentences) - only if no exact match
        3. Word-based search (split by words) - only if no phrase match
        
        Args:
            page: PyMuPDF page object
            search_text: Text to highlight
            highlight_color: RGB color tuple
            
        Returns:
            Number of highlights added
        """
        total_highlights = 0
        
        # PRIORITY 1: Try exact match first (highest priority)
        self._logger.debug("PRIORITY 1: Searching for exact match of '{}'", search_text)
        exact_instances = page.search_for(search_text)
        self._logger.debug("Search result: {} instances found", len(exact_instances) if exact_instances else 0)
        if exact_instances:
            self._logger.debug("✅ EXACT MATCH FOUND: {} instances of '{}'", len(exact_instances), search_text)
            for i, inst in enumerate(exact_instances):
                text_at_location = page.get_textbox(inst)
                self._logger.debug("Instance {}: rectangle={}, text='{}'", i+1, inst, text_at_location)
                try:
                    self._logger.debug("Creating highlight {} for instance: {}", i+1, inst)
                    highlight = page.add_highlight_annot(inst)
                    highlight.set_colors(stroke=highlight_color)
                    highlight.update()
                    total_highlights += 1
                    self._logger.debug("✅ Highlight {} created successfully", i+1)
                except Exception as e:
                    self._logger.error("❌ Failed to create highlight {}: {}", i+1, e)
            return total_highlights  # Return immediately - no fallback needed
        
        self._logger.warning("❌ No exact match found, falling back to substring-based search")
        
        # PRIORITY 2: Try substring-based search (progressive shortening)
        # This handles text split across columns better than sentence splitting
        self._logger.debug("PRIORITY 2: Trying substring-based search")
        substring_highlights = 0
        
        # Try progressively shorter substrings
        text_length = len(search_text)
        chunk_sizes = [text_length, text_length // 2, text_length // 3, text_length // 4]
        
        for chunk_size in chunk_sizes:
            if chunk_size < 50:  # Don't go too small
                break
                
            # Split text into overlapping chunks at word boundaries
            overlap_words = max(5, chunk_size // 20)  # ~5 words overlap
            words = search_text.split()
            chunks = []
            
            start_word = 0
            while start_word < len(words):
                # Calculate end word index for this chunk
                end_word = min(start_word + (chunk_size // 5), len(words))  # ~5 chars per word
                
                # Create chunk from words
                chunk_words = words[start_word:end_word]
                chunk = " ".join(chunk_words)
                
                if len(chunk) > 20:  # Only meaningful chunks
                    chunks.append(chunk)
                
                # Move start to create overlap
                start_word = end_word - overlap_words
                if start_word >= len(words) - overlap_words:
                    break
            
            # Also try searching for individual sentences/phrases that might be in different text blocks
            sentences = search_text.split('. ')
            if len(sentences) > 1:
                # Add individual sentences as chunks
                for sentence in sentences:
                    if len(sentence.strip()) > 20:
                        chunks.append(sentence.strip())
                
                # Add sentence pairs for better coverage
                for i in range(len(sentences) - 1):
                    pair = sentences[i] + '. ' + sentences[i + 1]
                    if len(pair.strip()) > 20 and len(pair.strip()) < chunk_size * 2:
                        chunks.append(pair.strip())
            
            self._logger.debug("Trying {} chunks of size ~{}", len(chunks), chunk_size)
            
            for i, chunk in enumerate(chunks):
                self._logger.debug("Chunk {}: '{}'", i+1, chunk[:100] + "..." if len(chunk) > 100 else chunk)
                instances = page.search_for(chunk)
                self._logger.debug("Chunk {} found {} instances", i+1, len(instances) if instances else 0)
                for inst in instances:
                    highlight = page.add_highlight_annot(inst)
                    highlight.set_colors(stroke=highlight_color)
                    highlight.update()
                    substring_highlights += 1
            
            if substring_highlights > 0:
                self._logger.debug("✅ SUBSTRING MATCH FOUND: {} substring-based highlights", substring_highlights)
                return substring_highlights
        
        # PRIORITY 3: Try phrase-based search (only if substring search fails)
        sentences = self._split_into_sentences(search_text)
        if len(sentences) > 1:
            self._logger.debug("PRIORITY 3: Trying phrase-based search with {} sentences", len(sentences))
            phrase_highlights = 0
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 10:  # Only search for meaningful sentences
                    instances = page.search_for(sentence)
                    for inst in instances:
                        highlight = page.add_highlight_annot(inst)
                        highlight.set_colors(stroke=highlight_color)
                        highlight.update()
                        phrase_highlights += 1
            if phrase_highlights > 0:
                self._logger.debug("✅ PHRASE MATCH FOUND: {} phrase-based highlights", phrase_highlights)
                return phrase_highlights
        
        self._logger.warning("❌ NO MATCHES FOUND: '{}' using any strategy", search_text)
        return 0
    
    def _split_into_sentences(self, text: str) -> list:
        """Split text into sentences for phrase-based search"""
        import re
        
        # First try to split by sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # If we have very long sentences, try to split them further
        # Look for natural break points like "They can", "These agents", etc.
        refined_sentences = []
        for sentence in sentences:
            if len(sentence) > 200:  # Very long sentence
                # Try to split on common transition phrases
                parts = re.split(r'\s+(They can|These agents|They have|They are|They will|They also)', sentence)
                if len(parts) > 1:
                    # Reconstruct parts with the transition phrase
                    for i in range(0, len(parts), 2):
                        if i + 1 < len(parts):
                            refined_sentences.append(parts[i] + " " + parts[i + 1])
                        else:
                            refined_sentences.append(parts[i])
                else:
                    refined_sentences.append(sentence)
            else:
                refined_sentences.append(sentence)
        
        return refined_sentences
    
    def _split_into_meaningful_words(self, text: str) -> list:
        """Split text into meaningful words for word-based search"""
        import re
        # Remove punctuation and split by whitespace
        words = re.findall(r'\b\w+\b', text)
        # Filter out very short words and common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        meaningful_words = [word.lower() for word in words if len(word) > 2 and word.lower() not in stop_words]
        return meaningful_words
    
    def get_cached_highlighted_pdf(
        self, 
        file_id: str, 
        search_text: str, 
        page_number: Optional[int] = None
    ) -> Optional[bytes]:
        """
        Get cached highlighted PDF or create new one
        
        Args:
            file_id: Unique file identifier
            search_text: Text to highlight
            page_number: Specific page to highlight (None for all pages)
            
        Returns:
            Highlighted PDF content as bytes, or None if error
        """
        # Create hash-based cache key to avoid long filenames
        cache_data = f"{file_id}_{search_text}_{page_number or 'all'}"
        cache_key = hashlib.md5(cache_data.encode()).hexdigest()
        cache_file = self.temp_dir / f"{cache_key}.pdf"
        
        self._logger.debug("🔍 Cache lookup - file_id: '{}', search_text: '{}', page: {}, cache_key: '{}'", 
                        file_id, search_text, page_number, cache_key)
        
        # Check if cached version exists
        if cache_file.exists():
            self._logger.debug("✅ CACHE HIT: Using cached highlighted PDF: {}", cache_file)
            try:
                with open(cache_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                self._logger.warning("Error reading cached PDF: {}", e)
        else:
            self._logger.debug("❌ CACHE MISS: No cached file found: {}", cache_file)
        
        return None
    
    def cache_highlighted_pdf(
        self, 
        file_id: str, 
        search_text: str, 
        highlighted_content: bytes,
        page_number: Optional[int] = None
    ) -> bool:
        """
        Cache highlighted PDF for future use
        
        Args:
            file_id: Unique file identifier
            search_text: Text that was highlighted
            highlighted_content: Highlighted PDF content
            page_number: Specific page that was highlighted (None for all pages)
            
        Returns:
            True if cached successfully, False otherwise
        """
        try:
            # Create hash-based cache key to avoid long filenames
            cache_data = f"{file_id}_{search_text}_{page_number or 'all'}"
            cache_key = hashlib.md5(cache_data.encode()).hexdigest()
            cache_file = self.temp_dir / f"{cache_key}.pdf"
            
            # Write to cache
            with open(cache_file, 'wb') as f:
                f.write(highlighted_content)
            
            self._logger.success("Cached highlighted PDF: {}", cache_file)
            return True
            
        except Exception as e:
            self._logger.error("Error caching highlighted PDF: {}", e)
            return False
    
    def clear_cache(self, file_id: Optional[str] = None) -> int:
        """
        Clear cached highlighted PDFs
        
        Args:
            file_id: Specific file ID to clear cache for (None for all)
            
        Returns:
            Number of files cleared
        """
        try:
            cleared_count = 0
            
            if file_id:
                # Clear cache for specific file
                pattern = f"{file_id}_*.pdf"
                for cache_file in self.temp_dir.glob(pattern):
                    cache_file.unlink()
                    cleared_count += 1
            else:
                # Clear all cache
                for cache_file in self.temp_dir.glob("*.pdf"):
                    cache_file.unlink()
                    cleared_count += 1
            
            self._logger.success("Cleared {} cached highlighted PDFs", cleared_count)
            return cleared_count
            
        except Exception as e:
            self._logger.error("Error clearing cache: {}", e)
            return 0
    
    def _cleanup_old_cache_files(self) -> int:
        """
        Clean up old cache files with long names (from before hash-based fix)
        
        Returns:
            Number of files cleaned up
        """
        try:
            cleaned_count = 0
            
            # Look for files with long names (containing underscores and spaces)
            for cache_file in self.temp_dir.glob("*.pdf"):
                filename = cache_file.name
                
                # Check if it's an old-style filename (contains spaces or very long)
                if len(filename) > 50 or ' ' in filename or filename.count('_') > 2:
                    try:
                        cache_file.unlink()
                        cleaned_count += 1
                        self._logger.debug("Cleaned up old cache file: {}", filename)
                    except Exception as e:
                        self._logger.warning("Error cleaning up old file {}: {}", filename, e)
            
            if cleaned_count > 0:
                self._logger.success("Cleaned up {} old cache files", cleaned_count)
            
            return cleaned_count
            
        except Exception as e:
            self._logger.error("Error cleaning up old cache files: {}", e)
            return 0
    
    def cleanup_expired_cache(self) -> int:
        """
        Clean up expired cache files based on age
        
        Returns:
            Number of files cleaned up
        """
        try:
            import time
            cleaned_count = 0
            current_time = time.time()
            max_age_seconds = self.max_cache_age_hours * 3600
            
            for cache_file in self.temp_dir.glob("*.pdf"):
                try:
                    file_age = current_time - cache_file.stat().st_mtime
                    if file_age > max_age_seconds:
                        cache_file.unlink()
                        cleaned_count += 1
                        self._logger.debug("Cleaned up expired cache file: {}", cache_file.name)
                except Exception as e:
                    self._logger.warning("Error checking/cleaning file {}: {}", cache_file.name, e)
            
            if cleaned_count > 0:
                self._logger.success("Cleaned up {} expired cache files", cleaned_count)
            
            return cleaned_count
            
        except Exception as e:
            self._logger.error("Error cleaning up expired cache: {}", e)
            return 0
    
    def get_cache_stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            cache_files = list(self.temp_dir.glob("*.pdf"))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                "file_count": len(cache_files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "cache_directory": str(self.temp_dir),
                "max_cache_size": self.max_cache_size,
                "max_cache_age_hours": self.max_cache_age_hours
            }
        except Exception as e:
            self._logger.error("Error getting cache stats: {}", e)
            return {}


# No global instance - let consumers create their own instances
# This allows for better testing, configuration, and dependency injection
