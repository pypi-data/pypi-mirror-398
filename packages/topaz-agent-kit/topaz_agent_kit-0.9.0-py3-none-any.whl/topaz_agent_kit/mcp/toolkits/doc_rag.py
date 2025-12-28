from typing import List, Dict
from chromadb import PersistentClient

from topaz_agent_kit.core.exceptions import MCPError
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.mcp.decorators import tool_metadata, ToolTimeout
from topaz_agent_kit.models.model_factory import ModelFactory
from topaz_agent_kit.utils.embedding_utils import GenericEmbeddingFunction
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

from fastmcp import FastMCP

class DocRAGMCPTools:
    """
    DocRAGMCPTools provides a complete Retrieval-Augmented Generation (RAG) service for text documents.
    This class is designed to be used as an MCP toolkit, exposing all methods as MCP tools.
    """
    def __init__(self, **kwargs):
        """
        Initialize DocRAG.

        Expected kwargs:
            db_path (str): Path for ChromaDB storage (required)
            embedding_model (str): Embedding model name (optional)
        """
        self._logger = Logger("MCP.DocRAG")

        # Initialize ChromaDB
        db_path = kwargs.get("db_path")
        if not db_path:
            self._logger.error("db_path is required for DocRAG initialization")
            raise MCPError("db_path is required for DocRAG initialization")

        # Store embedding model for later use
        self._embedding_model = kwargs.get("embedding_model")

        try:
            # Don't create the database file yet - lazy initialization
            self._db_path = db_path
            self._client = None
            self._logger.success("DocRAG initialized successfully (lazy mode) at: {}", db_path)
        except Exception as e:
            self._logger.error("Failed to initialize DocRAG: {}", e)

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

        @mcp.tool(name="doc_rag_query_document")
        def query_document(query: str, top_k: int = 3) -> List[Dict]:
            """
            Query the global document collection using semantic search.

            Parameters:
                query: User's question or search text.
                top_k: Number of top matching chunks to retrieve.

            Returns:
                List of dicts: Each dict contains:
                    - 'document': Document name
                    - 'source': Metadata (page, paragraph, slide, row, etc.)
                    - 'text': Chunk text
                    - 'score': Similarity score
                    - 'upload_date': When document was uploaded
            """
            self._logger.input("query_document INPUT: query={}, top_k={}", query, top_k)
            
            try:
                # Lazy client initialization
                client = self._get_client()
                if client is None:
                    self._logger.warning("ChromaDB client not available - database may not exist yet")
                    return []
                
                # Check if documents collection exists
                collections = client.list_collections()
                collection_names = [c.name for c in collections]
                
                if "documents" not in collection_names:
                    self._logger.warning("Documents collection not found. Available collections: {}", collection_names)
                    return []
                
                # Get embedding function for consistent dimensions
                embedding_fn = self._get_embedding_function()
                collection = client.get_collection(name="documents", embedding_function=embedding_fn)
                results = collection.query(query_texts=[query], n_results=top_k)
                
                result = [
                    {
                        "document": md.get("file_name"),
                        "page": md.get("page", 0),  # Extract page number for citation formatting
                        "chunk_id": md.get("chunk_id", 0),  # Extract chunk_id for citation formatting
                        "source": {k: v for k, v in md.items() if k not in ["file_name", "file_hash", "file_size", "upload_date", "page", "chunk_id"]},
                        "text": doc,
                        "score": score,
                        "upload_date": md.get("upload_date"),
                    }
                    for doc, md, score in zip(results["documents"][0], results["metadatas"][0], results["distances"][0])
                ]
                self._logger.output("query_document OUTPUT: {}", result)
                return result
                
            except Exception as e:
                error_msg = f"Failed to query documents: {e}"
                self._logger.error("query_document ERROR: {}", error_msg)
                return []

        @tool_metadata(timeout=ToolTimeout.QUICK)
        @mcp.tool(name="doc_rag_list_documents")
        def list_documents() -> List[str]:
            """
            List all document names in the global collection.

            Returns:
                List[str]: Unique document names.
            """
            self._logger.input("list_documents INPUT: listing all documents")
            
            try:
                # Lazy client initialization
                client = self._get_client()
                if client is None:
                    self._logger.warning("ChromaDB client not available - database may not exist yet")
                    return []
                
                # Check if documents collection exists
                collections = client.list_collections()
                collection_names = [c.name for c in collections]
                
                if "documents" not in collection_names:
                    self._logger.warning("Documents collection not found. Available collections: {}", collection_names)
                    return []
                
                # Get embedding function for consistent dimensions
                embedding_fn = self._get_embedding_function()
                collection = client.get_collection(name="documents", embedding_function=embedding_fn)
                all_docs = collection.get()["metadatas"]
                
                result = list({m["file_name"] for m in all_docs if "file_name" in m})
                self._logger.output("list_documents OUTPUT: {}", result)
                return result
                
            except Exception as e:
                self._logger.error("list_documents ERROR: {}", e)
                return []

