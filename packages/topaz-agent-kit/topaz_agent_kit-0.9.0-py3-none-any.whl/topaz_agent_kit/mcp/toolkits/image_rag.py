from typing import List, Dict
from chromadb import PersistentClient

from topaz_agent_kit.core.exceptions import MCPError
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.mcp.decorators import tool_metadata, ToolTimeout
from topaz_agent_kit.models.model_factory import ModelFactory
from topaz_agent_kit.utils.embedding_utils import GenericEmbeddingFunction
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

from fastmcp import FastMCP

class ImageRAGMCPTools:
    """
    ImageRAGMCPTools provides image processing and retrieval capabilities.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize ImageRAG.

        Expected kwargs:
            db_path (str): Path for ChromaDB storage (required)
            embedding_model (str): Embedding model name (optional)
        """
        self._logger = Logger("MCP.ImageRAG")
        
        # Initialize ChromaDB
        db_path = kwargs.get("db_path")
        if not db_path:
            self._logger.error("db_path is required for ImageRAG initialization")
            raise MCPError("db_path is required for ImageRAG initialization")

        # Store embedding model for later use
        self._embedding_model = kwargs.get("embedding_model")

        try:
            # Don't create the database file yet - lazy initialization
            self._db_path = db_path
            self._client = None
            self._logger.success("ImageRAG initialized successfully (lazy mode) at: {}", db_path)
        except Exception as e:
            self._logger.error("Failed to initialize ImageRAG: {}", e)

    def _get_client(self):
        """Lazy initialization of ChromaDB client"""
        if self._client is None:
            # Check if database exists
            import os
            if not os.path.exists(self._db_path):
                self._logger.warning("ChromaDB database does not exist yet: {}", self._db_path)
                return None
            
            try:
                self._client = PersistentClient(path=self._db_path)
                self._logger.debug("ChromaDB client initialized lazily: {}", self._db_path)
            except Exception as e:
                self._logger.error("Failed to initialize ChromaDB client: {}", e)
                return None
        
        return self._client
    
    def _get_embedding_function(self):
        """Create embedding function using the configured model"""
        if not self._embedding_model:
            self._logger.warning("No embedding model configured, using default")
            return None
        
        try:
            
            # Create the embedding model (returns tuple: model, model_name)
            embedding_model, model_name = ModelFactory.get_embedding_model(self._embedding_model)
            self._logger.input("Using embedding model: {}", model_name)
            
            # Use shared embedding function
            embedding_fn = GenericEmbeddingFunction(embedding_model, model_name, self._logger)
            
            self._logger.debug("Created embedding function for model: {}", self._embedding_model)
            return embedding_fn
            
        except Exception as e:
            self._logger.error("Failed to create embedding function: {}", e)
            return None

    def register(self, mcp: FastMCP) -> None:

        @tool_metadata(timeout=ToolTimeout.QUICK)
        @mcp.tool(name="image_rag_query_images")
        def query_images(query: str, top_k: int = 3) -> List[Dict]:
            """
            Query images using OCR text content.

            Parameters:
                query: Search query (searches extracted OCR text).
                top_k: Number of top matching images to retrieve.

            Returns:
                List of dicts: Each dict contains image metadata and extracted text.
            """
            self._logger.input("query_images INPUT: query={}, top_k={}", query, top_k)
            
            try:
                # Lazy client initialization
                client = self._get_client()
                if client is None:
                    self._logger.warning("ChromaDB client not available - database may not exist yet")
                    return []
                
                # Check if images collection exists
                collections = client.list_collections()
                collection_names = [c.name for c in collections]
                
                if "images" not in collection_names:
                    self._logger.warning("Images collection not found. Available collections: {}", collection_names)
                    return []
                
                # Get embedding function for consistent dimensions
                embedding_fn = self._get_embedding_function()
                collection = client.get_collection(name="images", embedding_function=embedding_fn)
                
                # Query using extracted text
                results = collection.query(query_texts=[query], n_results=top_k)
                
                result = [
                    {
                        "filename": md.get("file_name"),
                        "extracted_text": doc,
                        "metadata": {
                            "width": md.get("width"),
                            "height": md.get("height"),
                            "format": md.get("format"),
                            "file_size": md.get("file_size"),
                            "upload_date": md.get("upload_date"),
                            "has_text": md.get("has_text")
                        },
                        "score": score
                    }
                    for doc, md, score in zip(results["documents"][0], results["metadatas"][0], results["distances"][0])
                ]
                
                self._logger.output("query_images OUTPUT: {}", result)
                return result
                
            except Exception as e:
                error_msg = f"Failed to query images: {e}"
                self._logger.error("query_images ERROR: {}", error_msg)
                return []


        @tool_metadata(timeout=ToolTimeout.QUICK)
        @mcp.tool(name="image_rag_list_images")
        def list_images() -> List[str]:
            """
            List all image filenames in the collection.

            Returns:
                List[str]: Image filenames.
            """
            self._logger.input("list_images INPUT")
            
            try:
                # Lazy client initialization
                client = self._get_client()
                if client is None:
                    self._logger.warning("ChromaDB client not available - database may not exist yet")
                    return []
                
                # Check if images collection exists
                collections = client.list_collections()
                collection_names = [c.name for c in collections]
                
                if "images" not in collection_names:
                    self._logger.warning("Images collection not found. Available collections: {}", collection_names)
                    return []
                
                # Get embedding function for consistent dimensions
                embedding_fn = self._get_embedding_function()
                collection = client.get_collection(name="images", embedding_function=embedding_fn)
                results = collection.get()
                
                filenames = [metadata.get("file_name") for metadata in results["metadatas"]]
                filenames = [f for f in filenames if f]  # Remove None values
                
                self._logger.output("list_images OUTPUT: {}", filenames)
                return filenames
                
            except Exception as e:
                error_msg = f"Failed to list images: {e}"
                self._logger.error("list_images ERROR: {}", error_msg)
                return []