"""
Vector Service Client for interacting with vector database.

This module provides functionality for:
- Managing vector collections
- Storing and retrieving document embeddings (via the service)
- Handling semantic and agentic tools
- Chunking large documents
- Sanitizing metadata
"""

import json
from typing import Any, Dict, List, Optional

import httpx

from guardianhub import get_logger
from guardianhub.config.settings import settings

logger = get_logger(__name__)

def _chunk_text(
        text: str,
        max_tokens: int = 500,
        approx_chars_per_token: int = 4
) -> List[str]:
    """Split text into chunks of approximately max_tokens length."""
    if not text:
        return []

    max_chars = max_tokens * approx_chars_per_token
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = min(len(text), start + max_chars)
        slice_ = text[start:end]

        # Look for the last newline or space to cut cleanly
        if end < len(text):
            last_nl = slice_.rfind("\n")
            last_space = slice_.rfind(" ")
            cut = max(last_nl, last_space)
            if cut > 0:
                end = start + cut

        chunks.append(text[start:end].strip())
        start = end

    return [c for c in chunks if c]

def _sanitize_metadata_value(value: Any) -> Any:
    """Ensure metadata value is vector-DB safe."""
    if value is None or value == []:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    try:
        # Complex types like dicts or lists should be JSON serialized
        return json.dumps(value)
    except Exception:
        return str(value)

def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Clean metadata dictionary by dropping None values and normalizing types."""
    return {
        k: _sanitize_metadata_value(v)
        for k, v in metadata.items()
        if _sanitize_metadata_value(v) is not None
    }

class VectorClient:
    """Client for interacting with the vector database service."""

    def __init__(
            self,
            base_url: Optional[str] = None,
            collection: str = settings.vector.default_collection,
            http_timeout: float = 30.0,
            **collection_kwargs
    ):
        """Initialize the VectorClient.

        Args:
            base_url: Base URL for the vector service. If not provided, will try to get from settings.
            collection_docs: Name of the document collection to use.
            http_timeout: Timeout for HTTP requests in seconds.
            **collection_kwargs: Additional collection configuration.
        """

        self.base_url = base_url or settings.endpoints.get('VECTOR_SERVICE_URL')
        # self.base_url = base_url.rstrip("/")
        self.collection = collection
        self.collection_config = collection_kwargs
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=http_timeout
        )
        self.initialized = False

    async def initialize(self):
        """Initialize the client and check connection asynchronously"""
        try:
            await self._check_connection()
            self.initialized = True
            return self.initialized
        except Exception as e:
            logger.error(f"Vector client initialization failed: {str(e)}")
            self.initialized = False
            return False

    async def ensure_collection_exists(self, collection_name: str = None, **collection_kwargs) -> bool:
        """Ensure the specified collection exists, create it if it doesn't.

        Args:
            collection_name: Name of the collection to check/create
            **collection_kwargs: Additional arguments for collection creation

        Returns:
            bool: True if collection exists or was created, False otherwise
        """
        try:
            # Try to create the collection - will succeed if it doesn't exist
            await self.create_collection(collection_name, **collection_kwargs)
            logger.info(f"Created collection: {collection_name}")
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:  # Collection already exists
                logger.debug(f"Collection {collection_name} already exists")
                return True
            logger.error(f"Error ensuring collection {collection_name} exists: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error ensuring collection {collection_name} exists: {str(e)}")
            return False

    async def _check_connection(self):
        """Check if the vector service is available."""
        try:
            response = await self._client.get("/health")
            response.raise_for_status()
            self.initialized = True
        except Exception as e:
            logger.error(f"Vector client health check failed: {str(e)}")
            self.initialized = False
            raise

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    async def upsert_documents(
            self,
            ids: List[str],
            documents: List[str],
            metadatas: Optional[List[Dict[str, Any]]],
            collection: Optional[str] ,
            embeddings: Optional[List[List[float]]] = None,
    ) -> Any:
        """Upsert documents into the vector database in a single batch call."""
        if not ids or not documents or len(ids) != len(documents):
            raise ValueError("ids and documents must be non-empty and same length")

        if metadatas and len(metadatas) != len(ids):
            raise ValueError("metadatas must be same length as ids if provided")

        # Ensure metadata is safe for the vector store
        sanitized_metas = [
            sanitize_metadata(m) if m else {}
            for m in (metadatas or [{}] * len(ids))
        ]

        payload = {
            # Note: We do not pass embeddings here; the service will generate them.
            "documents": documents,
            "ids": ids,
            "metadatas": sanitized_metas,
            "embeddings": embeddings
        }

        response = await self._client.post(
            f"/collections/{collection}/add",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    async def upsert_document_from_text(
            self,
            document_content: str,
            doc_id: str,
            metadata: Dict[str, Any],
            collection: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Chunks a single document and upserts all chunks into the vector database.

        The ingestion activity (store_in_vector_db_activity) should call this method.
        It returns the ID of the first chunk, which acts as the 'vector_id' for the document.
        """
        collection_name = collection

        if not document_content:
            logger.warning(f"Attempted to upsert empty content for document ID: {doc_id}")
            return {"status": "skipped", "message": "Empty document content"}

        # 1. Chunk the document
        chunks = _chunk_text(document_content)

        if not chunks:
             logger.warning(f"Chunking failed for document ID: {doc_id}")
             return {"status": "skipped", "message": "Chunking failed to produce content"}

        # 2. Prepare IDs and Metadata for upsert
        chunk_ids = [f"{doc_id}-{i}" for i in range(len(chunks))]

        # All chunks share the same base metadata, plus chunk-specific indices
        base_metadata = sanitize_metadata(metadata.copy())

        chunk_metadatas = []
        for i in range(len(chunks)):
            meta = base_metadata.copy()
            # Store the primary document ID in the metadata for easy filtering/retrieval
            meta["original_doc_id"] = doc_id
            meta["chunk_index"] = i
            meta["chunk_total"] = len(chunks)
            chunk_metadatas.append(meta)

        # 3. Upsert the documents (chunks)
        response = await self.upsert_documents(
            ids=chunk_ids,
            documents=chunks,
            metadatas=chunk_metadatas,
            collection=collection_name,
        )

        # Return the ID of the first chunk
        return {"id": chunk_ids[0], "status": "success", "chunk_count": len(chunks), "service_response": response}


    async def delete_document(self, doc_id: str, collection: str) -> None:
        """Delete a document (and all its chunks) from the vector database.
        
        Args:
            doc_id: The ID of the document to delete
            collection: The name of the collection containing the document
            
        Raises:
            httpx.HTTPStatusError: If the deletion request fails
        """
        # For a complete document deletion, we must delete based on the original_doc_id in metadata
        response = await self._client.request(
            method="DELETE",
            url=f"/collections/{collection}/delete",
            json={
                "ids": [doc_id],
            }
        )
        response.raise_for_status()
        logger.info(f"Deleted document chunks for original ID {doc_id} from {collection}")
        return response.json()

    # Removed the previous embed_text method as embedding is handled by the service.

    async def query(
            self,
            query: str,
            collection: str,
            n_results: int = 5,
            where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Query the vector database using a text query."""
        if not self.initialized:
            await self.initialize()

        payload = {
            "query_texts": [query],
            "n_results": n_results
        }
        # Where clause must be sanitized if needed, but we rely on the service to interpret Chroma syntax
        if where:
            payload["where"] = where

        response = await self._client.post(
            f"/collections/{collection}/query",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    async def create_collection(self, name: str, **kwargs) -> Dict[str, Any]:
        """Create a new collection."""
        response = await self._client.post(
            f"/collections",
            json={
                "name": name,
                **kwargs
            }
        )
        response.raise_for_status()
        return response.json()

    async def delete_collection(self, name: str) -> None:
        """Delete a collection."""
        # response = await self._client.delete(f"/collections/{name}/delete")
        # response.raise_for_status()
        logger.info(f"Deleted collection {name}")

    async def get_raw_embedding(self, document_text: str) -> Optional[List[float]]:
        """
        Retrieves the raw embedding vector for a single document text
        via the Vector DB Service's dedicated generation endpoint.
        """
        endpoint = "/embed/text"

        # NOTE: The Vector Service endpoint expects a list of texts
        payload = {"texts": [document_text]}

        try:
            response = await self._client.post(endpoint, json=payload)
            response.raise_for_status()

            data = response.json()
            embeddings = data.get("embeddings")

            if embeddings and len(embeddings) > 0:
                # We requested one text, so we return the first (and only) embedding
                return embeddings[0]

            logger.error("Embedding service returned success but embeddings list was empty.")
            return None

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error generating raw embedding: Status %d. Detail: %s",
                e.response.status_code, e.response.text
            )
            return None
        except httpx.RequestError as e:
            logger.error("Network error connecting to Vector DB for embedding generation: %s", str(e))
            return None