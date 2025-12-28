"""
Shared embedding utilities for ChromaDB compatibility
"""

from typing import List, Any
from chromadb.utils.embedding_functions import EmbeddingFunction
from chromadb.api.types import Documents, Embeddings
from topaz_agent_kit.core.exceptions import ModelError
from topaz_agent_kit.utils.logger import Logger


def create_embeddings(embedding_client, model_name: str, texts: List[str], logger: Logger) -> List[List[float]]:
    """
    Core embedding logic shared by all components.
    Works with any embedding model configured in the YAML file.
    
    Args:
        embedding_client: Embedding model client instance (e.g., OpenAI, Azure OpenAI, etc.)
        model_name: Name of the embedding model
        texts: List of texts to embed
        logger: Logger instance for error reporting
        
    Returns:
        List of embedding vectors
        
    Raises:
        ModelError: If embedding generation fails
    """
    try:
        embeddings = []
        for text in texts:
            response = embedding_client.embeddings.create(
                model=model_name,
                input=text
            )
            embeddings.append(response.data[0].embedding)
        return embeddings
    except Exception as e:
        logger.error("Failed to generate embeddings with model {}: {}", model_name, e)
        raise ModelError(f"Failed to generate embeddings with model {model_name}: {e}")


class GenericEmbeddingFunction(EmbeddingFunction):
    """
    Shared ChromaDB-compatible embedding function for any embedding model.
    Used by ContentIngester, DocRAG, and ImageRAG toolkits.
    Works with any embedding model configured in the YAML file.
    """
    
    def __init__(self, embedding_client, model_name: str, logger: Logger):
        self._embedding_client = embedding_client
        self._model_name = model_name
        self._logger = logger
    
    def __call__(self, inputs: Documents) -> Embeddings:
        """Generate embeddings for input texts using the configured embedding model."""
        return create_embeddings(
            self._embedding_client, 
            self._model_name, 
            inputs, 
            self._logger
        )