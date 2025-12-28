"""
Docling utility functions for document processing
"""

import os
from typing import Dict, Any, Optional, List
from pathlib import Path

from tiktoken import get_encoding
from transformers.tokenization_utils_base import PreTrainedTokenizerBase

from topaz_agent_kit.utils.logger import Logger


class OpenAITokenizerWrapper(PreTrainedTokenizerBase):
    """Minimal wrapper for OpenAI's tokenizer to make it compatible with HybridChunker."""

    def __init__(
        self, model_name: str = "cl100k_base", max_length: int = 8191, **kwargs
    ):
        """Initialize the tokenizer.

        Args:
            model_name: The name of the OpenAI encoding to use
            max_length: Maximum sequence length
        """
        super().__init__(model_max_length=max_length, **kwargs)
        self.tokenizer = get_encoding(model_name)
        self._vocab_size = self.tokenizer.max_token_value

    def tokenize(self, text: str, **kwargs) -> List[str]:
        """Main method used by HybridChunker."""
        return [str(t) for t in self.tokenizer.encode(text)]

    def _tokenize(self, text: str) -> List[str]:
        return self.tokenize(text)

    def encode(self, text: str, **kwargs) -> List[int]:
        """Encode text to token IDs."""
        return self.tokenizer.encode(text)

    def __len__(self) -> int:
        """Return the vocabulary size."""
        return self.vocab_size

    def _convert_token_to_id(self, token: str) -> int:
        return int(token)

    def _convert_id_to_token(self, index: int) -> str:
        return str(index)

    def get_vocab(self) -> Dict[str, int]:
        return dict(enumerate(range(self.vocab_size)))

    @property
    def vocab_size(self) -> int:
        return self._vocab_size

    def save_vocabulary(self, *args) -> tuple:
        return ()

    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        """Class method to match HuggingFace's interface."""
        return cls()


class DoclingUtils:
    """Utility functions for Docling document processing"""
    
    @staticmethod
    def get_document_metadata(docling_doc) -> Dict[str, Any]:
        """Extract metadata from Docling document"""
        metadata = {
            "num_pages": len(docling_doc.pages),
            "num_tables": len([item_tuple[0] for item_tuple in docling_doc.iterate_items() if hasattr(item_tuple[0], 'type') and item_tuple[0].type == 'table']),
            "num_images": len([item_tuple[0] for item_tuple in docling_doc.iterate_items() if hasattr(item_tuple[0], 'type') and item_tuple[0].type == 'image']),
            "num_sections": len([item_tuple[0] for item_tuple in docling_doc.iterate_items() if hasattr(item_tuple[0], 'type') and item_tuple[0].type == 'heading']),
            "has_toc": hasattr(docling_doc, 'table_of_contents') and docling_doc.table_of_contents is not None,
        }
        return metadata
    
    @staticmethod
    def extract_tables(docling_doc) -> list:
        """Extract all tables from document as structured data"""
        tables = []
        for item_tuple in docling_doc.iterate_items():
            item = item_tuple[0]  # Extract item from tuple
            page_number = item_tuple[1]  # Extract page number from tuple (1-based)
            if hasattr(item, 'type') and item.type == 'table':
                tables.append({
                    "page": page_number,
                    "content": item.text,
                    "structure": getattr(item, 'table_data', None)
                })
        return tables
    
    @staticmethod
    def is_supported_format(file_path: str) -> bool:
        """Check if file format is supported by Docling"""
        supported_extensions = {
            '.pdf', '.docx', '.doc', '.pptx', '.ppt',
            '.html', '.htm', '.md', '.txt'
        }
        return Path(file_path).suffix.lower() in supported_extensions
